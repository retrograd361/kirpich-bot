"""Адмінка: /admin. Доступна тільки юзернеймам з ADMIN_USERNAMES.

Покрокові діалоги (стрім, пост, налаштування) зроблені через FSM —
"машину станів": бот памʼятає, на якому кроці адмін, і чекає відповідного повідомлення.
"""
from html import escape

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from bot import broadcast, db
from bot import keyboards as kb
from bot.config import Config
from bot.content import DEFAULTS, EDITABLE, STREAM_PLATFORMS
from bot.filters import IsAdmin
from bot.menu import CAPTION_LIMIT, send_menu

router = Router(name="admin")
router.message.filter(F.chat.type == "private", IsAdmin())
router.callback_query.filter(IsAdmin())

PANEL_TEXT = "⚙️ <b>Адмінка</b>\n\nОбирай, що робимо:"


class Stream(StatesGroup):
    platform = State()
    photo = State()
    text = State()


class Post(StatesGroup):
    content = State()
    buttons = State()


class EditSetting(StatesGroup):
    value = State()


class Broadcast(StatesGroup):
    confirm = State()


# ---------- Меню адмінки ----------

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(PANEL_TEXT, reply_markup=kb.admin_menu())


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Скасовано.\n\n" + PANEL_TEXT, reply_markup=kb.admin_menu())


@router.callback_query(F.data == "adm:cancel")
async def cb_cancel(cb: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await cb.message.answer("Скасовано.\n\n" + PANEL_TEXT, reply_markup=kb.admin_menu())
    await cb.answer()


@router.callback_query(F.data == "adm:menu")
async def cb_menu(cb: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await _edit_or_send(cb, PANEL_TEXT, kb.admin_menu())


@router.callback_query(F.data == "adm:close")
async def cb_close(cb: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    try:
        await cb.message.delete()
    except TelegramBadRequest:
        pass
    await cb.answer()


@router.callback_query(F.data == "adm:stats")
async def cb_stats(cb: CallbackQuery) -> None:
    s = await db.get_stats()
    text = (
        "📊 <b>Статистика</b>\n\n"
        f"Всього юзерів: <b>{s['total']}</b>\n"
        f"Активні (отримують розсилку): <b>{s['active']}</b>\n"
        f"Заблокували бота: {s['blocked']}\n\n"
        f"Нових за добу: {s['new_day']}\n"
        f"Нових за тиждень: {s['new_week']}\n"
        f"Прийшли через заявку в канал: {s['from_channel']}"
    )
    await _edit_or_send(cb, text, kb.back_to_admin())


@router.callback_query(F.data == "adm:preview")
async def cb_preview(cb: CallbackQuery, bot: Bot) -> None:
    await send_menu(bot, cb.message.chat.id)
    await cb.answer("Ось так бачать меню підписники 👆")


# ---------- 🔴 Стрім почався ----------

@router.callback_query(F.data == "adm:stream")
async def stream_start(cb: CallbackQuery, state: FSMContext) -> None:
    if broadcast.is_running():
        await cb.answer("Зараз уже йде розсилка, зачекай поки закінчиться", show_alert=True)
        return
    await state.set_state(Stream.platform)
    await _edit_or_send(cb, "🔴 <b>Де стрім?</b>", kb.stream_platforms())


@router.callback_query(Stream.platform, F.data.startswith("stream:"))
async def stream_platform(cb: CallbackQuery, state: FSMContext) -> None:
    platform = cb.data.split(":", 1)[1]
    if platform not in STREAM_PLATFORMS:
        await cb.answer()
        return
    await state.update_data(platform=platform)
    await state.set_state(Stream.photo)
    await _edit_or_send(
        cb, "🖼 Надішли <b>картинку</b> для анонсу стріму.",
        kb.skip("stream:nophoto", "⏭ Без картинки"),
    )


@router.message(Stream.photo, F.photo)
async def stream_photo(message: Message, state: FSMContext) -> None:
    await state.update_data(photo=message.photo[-1].file_id)  # [-1] = найбільший розмір
    await _ask_stream_text(message, state)


@router.callback_query(Stream.photo, F.data == "stream:nophoto")
async def stream_no_photo(cb: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(photo=None)
    await _ask_stream_text(cb.message, state)
    await cb.answer()


@router.message(Stream.photo)
async def stream_photo_wrong(message: Message) -> None:
    await message.answer("Чекаю саме картинку (фото, не файлом). Або тисни «Без картинки».")


async def _ask_stream_text(message: Message, state: FSMContext) -> None:
    await state.set_state(Stream.text)
    settings = await db.get_settings()
    await message.answer(
        "✍️ Надішли <b>текст</b> анонсу.\n\nАбо використай шаблон:\n\n" + settings["stream_text"],
        reply_markup=kb.skip("stream:default", "📝 Використати шаблон"),
    )


@router.message(Stream.text, F.text)
async def stream_text(message: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    if data.get("photo") and len(message.text) > CAPTION_LIMIT:
        await message.answer(f"Текст під картинкою має бути до {CAPTION_LIMIT} символів. Скороти, будь ласка.")
        return
    await _stream_preview(message.chat.id, state, bot, message.html_text)


@router.callback_query(Stream.text, F.data == "stream:default")
async def stream_default_text(cb: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    settings = await db.get_settings()
    await _stream_preview(cb.message.chat.id, state, bot, settings["stream_text"])
    await cb.answer()


async def _stream_preview(chat_id: int, state: FSMContext, bot: Bot, text: str) -> None:
    await state.update_data(kind="stream", text=text)
    await _send_stream_post(bot, chat_id, await state.get_data())
    await _ask_confirm(bot, chat_id, state)


async def _send_stream_post(bot: Bot, chat_id: int, data: dict) -> None:
    settings = await db.get_settings()
    markup = kb.stream_buttons(STREAM_PLATFORMS[data["platform"]], settings)
    if data.get("photo"):
        await bot.send_photo(chat_id, data["photo"], caption=data["text"], reply_markup=markup)
    else:
        await bot.send_message(chat_id, data["text"], reply_markup=markup)


# ---------- 📢 Новий пост ----------

@router.callback_query(F.data == "adm:post")
async def post_start(cb: CallbackQuery, state: FSMContext) -> None:
    if broadcast.is_running():
        await cb.answer("Зараз уже йде розсилка, зачекай поки закінчиться", show_alert=True)
        return
    await state.set_state(Post.content)
    await _edit_or_send(
        cb,
        "📢 Надішли пост — текст, фото з підписом, відео, гіф, що завгодно.\n"
        "Я розішлю його всім <b>точно в такому вигляді</b>.",
        kb.cancel_only(),
    )


@router.message(Post.content, ~F.text.startswith("/"))  # команди не вважаємо постом
async def post_content(message: Message, state: FSMContext) -> None:
    await state.update_data(from_chat_id=message.chat.id, message_id=message.message_id)
    await state.set_state(Post.buttons)
    await message.answer(
        "🔗 Додати кнопки-посилання під пост?\n\n"
        "Надішли їх так, кожна з нового рядка:\n"
        "<code>Дивитись стрім | https://kick.com/kirpich-7</code>\n"
        "<code>Донат | https://donatello.to/DanielKyrpychnyk</code>",
        reply_markup=kb.skip("post:nobuttons", "⏭ Без кнопок"),
    )


@router.message(Post.buttons, F.text)
async def post_buttons(message: Message, state: FSMContext, bot: Bot) -> None:
    markup = kb.parse_buttons(message.text)
    if markup is None:
        await message.answer("Не зрозумів формат 🤔 Треба: <code>Назва | https://посилання</code>")
        return
    await state.update_data(buttons=markup.model_dump(mode="json", exclude_none=True))
    await _post_preview(message.chat.id, state, bot)


@router.callback_query(Post.buttons, F.data == "post:nobuttons")
async def post_no_buttons(cb: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    await state.update_data(buttons=None)
    await _post_preview(cb.message.chat.id, state, bot)
    await cb.answer()


async def _post_preview(chat_id: int, state: FSMContext, bot: Bot) -> None:
    await state.update_data(kind="post")
    await _send_post(bot, chat_id, await state.get_data())
    await _ask_confirm(bot, chat_id, state)


async def _send_post(bot: Bot, chat_id: int, data: dict) -> None:
    markup = InlineKeyboardMarkup.model_validate(data["buttons"]) if data.get("buttons") else None
    # copy_message = переслати без підпису "Переслано від", з усім форматуванням і медіа
    await bot.copy_message(chat_id, data["from_chat_id"], data["message_id"], reply_markup=markup)


# ---------- Підтвердження і запуск розсилки ----------

async def _ask_confirm(bot: Bot, chat_id: int, state: FSMContext) -> None:
    await state.set_state(Broadcast.confirm)
    count = len(await db.get_active_user_ids())
    await bot.send_message(
        chat_id, "👆 Так виглядатиме пост.\n\nРозсилаємо всім?", reply_markup=kb.confirm_broadcast(count)
    )


@router.callback_query(Broadcast.confirm, F.data == "bc:go")
async def broadcast_go(cb: CallbackQuery, state: FSMContext, bot: Bot, config: Config) -> None:
    if broadcast.is_running():
        await cb.answer("Зараз уже йде розсилка, зачекай поки закінчиться", show_alert=True)
        return
    data = await state.get_data()
    await state.clear()

    sender = _send_stream_post if data["kind"] == "stream" else _send_post

    async def send(chat_id: int) -> None:
        await sender(bot, chat_id, data)

    broadcast.start_broadcast(bot, send, cb.message.chat.id, config.broadcast_rate)
    await _edit_or_send(cb, "🚀 Розсилку запущено! Напишу, коли закінчиться.", None)


# ---------- 🔗 Посилання і тексти ----------

@router.callback_query(F.data == "adm:settings")
async def settings_menu(cb: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await _edit_or_send(cb, "🔗 <b>Що змінюємо?</b>", kb.settings_list(await db.get_settings()))


@router.callback_query(F.data.startswith("set:"))
async def setting_pick(cb: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    key = cb.data.split(":", 1)[1]
    meta = EDITABLE.get(key)
    if meta is None:
        await cb.answer()
        return
    await state.set_state(EditSetting.value)
    await state.update_data(key=key)
    current = (await db.get_settings()).get(key, "")

    hints = {
        "url": "Надішли нове посилання (починається з https://).\n«-» — прибрати кнопку з меню.",
        "plain": "Надішли нове значення.\n«-» — прибрати з меню.",
        "text": "Надішли новий текст (жирний/курсив зберігаються).\n«-» — повернути стандартний.",
        "photo": "Надішли нову картинку.\n«-» — прибрати картинку.",
    }
    await cb.message.answer(f"<b>{meta.title}</b>\n\nЗараз: {_show_value(meta.kind, current)}\n\n{hints[meta.kind]}",
                            reply_markup=kb.skip("adm:settings", "⬅️ Назад"))
    if meta.kind == "photo" and current:
        await bot.send_photo(cb.message.chat.id, current)
    await cb.answer()


@router.message(EditSetting.value)
async def setting_save(message: Message, state: FSMContext) -> None:
    key = (await state.get_data())["key"]
    meta = EDITABLE[key]

    if message.text and message.text.strip() == "-":
        value = DEFAULTS[key] if meta.kind == "text" else ""
    elif meta.kind == "photo":
        if not message.photo:
            await message.answer("Чекаю картинку (фото) або «-».")
            return
        value = message.photo[-1].file_id
    elif not message.text:
        await message.answer("Чекаю текст.")
        return
    elif meta.kind == "url":
        value = message.text.strip()
        if not value.startswith(("http://", "https://")):
            await message.answer("Посилання має починатись з https://")
            return
    elif meta.kind == "text":
        value = message.html_text
    else:
        value = message.text.strip()

    await db.set_setting(key, value)
    await state.clear()
    await message.answer(f"✅ Збережено: <b>{meta.title}</b>", reply_markup=kb.settings_list(await db.get_settings()))


def _show_value(kind: str, value: str) -> str:
    if not value:
        return "<i>порожньо</i>"
    if kind == "photo":
        return "картинка 👇"
    if kind == "text":
        return "\n" + value
    return escape(value)


# ---------- Допоміжне ----------

async def _edit_or_send(cb: CallbackQuery, text: str, markup: InlineKeyboardMarkup | None) -> None:
    """Редагуємо повідомлення з кнопкою; якщо не можна (напр. це фото) — шлемо нове."""
    try:
        await cb.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest:
        await cb.message.answer(text, reply_markup=markup)
    await cb.answer()
