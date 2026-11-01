"""Відправка головного меню-хабу (використовується в /start і при прийомі заявок)."""
from aiogram import Bot

from bot import db
from bot.content import CARD_BLOCK, MENU_FOOTER
from bot.keyboards import main_menu

CAPTION_LIMIT = 1024  # Telegram обмежує підпис до фото 1024 символами


def build_text(settings: dict[str, str]) -> str:
    parts = [settings["welcome_text"]]
    if settings.get("card"):
        parts.append(CARD_BLOCK.format(card=settings["card"]))
    parts.append(MENU_FOOTER)
    return "\n\n".join(parts)


async def send_menu(bot: Bot, chat_id: int) -> None:
    settings = await db.get_settings()
    text = build_text(settings)
    keyboard = main_menu(settings)
    photo = settings.get("welcome_photo")
    if photo and len(text) <= CAPTION_LIMIT:
        await bot.send_photo(chat_id, photo, caption=text, reply_markup=keyboard)
    else:
        await bot.send_message(chat_id, text, reply_markup=keyboard)
