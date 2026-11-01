"""Наскрізна перевірка бота без справжнього Telegram.

Підміняємо мережеву сесію aiogram на фейкову: вона записує всі запити бота
і повертає правдоподібні відповіді (з затримкою, як справжня мережа).
Запуск:  python -m tests.smoke_test
"""
import asyncio
import os
import sys
import time
from datetime import datetime

os.environ["BOT_TOKEN"] = "123456:TEST"
os.environ["ADMIN_USERNAMES"] = "@TestAdmin"
# можна прогнати і на Postgres: TEST_DATABASE_URL=postgresql://... python -m tests.smoke_test
os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///test_smoke.db")

from aiogram import Bot  # noqa: E402
from aiogram.client.session.base import BaseSession  # noqa: E402
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter  # noqa: E402
from aiogram.methods import ApproveChatJoinRequest, TelegramMethod  # noqa: E402
from aiogram.types import Message, MessageId  # noqa: E402

from bot import broadcast, db  # noqa: E402
from bot.__main__ import build_dispatcher  # noqa: E402
from bot.config import load_config  # noqa: E402

LATENCY = 0.05  # 50 мс на кожен запит до "Telegram"
ADMIN_ID = 1


class FakeSession(BaseSession):
    def __init__(self) -> None:
        super().__init__()
        self.calls: list[TelegramMethod] = []
        self.blocked_ids: set[int] = set()
        self.flood_once: set[int] = set()  # цим chat_id один раз повернемо "зачекай"
        self._msg_id = 1000

    async def make_request(self, bot, method, timeout=None):
        await asyncio.sleep(LATENCY)
        chat_id = getattr(method, "chat_id", None)
        if chat_id in self.flood_once:
            self.flood_once.discard(chat_id)
            raise TelegramRetryAfter(method=method, message="Flood", retry_after=0)
        if chat_id in self.blocked_ids:
            raise TelegramForbiddenError(method=method, message="Forbidden: bot was blocked by the user")
        self.calls.append(method)
        returning = method.__returning__
        if returning is Message or returning == Message | bool:
            self._msg_id += 1
            return Message.model_validate(
                {"message_id": self._msg_id, "date": datetime.now(),
                 "chat": {"id": chat_id or 0, "type": "private"}, "text": "x"},
                context={"bot": bot},
            )
        if returning is MessageId:
            return MessageId(message_id=1)
        return True

    async def stream_content(self, *a, **kw):  # не використовується
        yield b""

    async def close(self) -> None:
        pass

    def of(self, name: str) -> list:
        return [c for c in self.calls if type(c).__name__ == name]


_upd = 0


def _user(uid: int, username: str | None = None) -> dict:
    return {"id": uid, "is_bot": False, "first_name": f"U{uid}", "username": username}


def msg_update(uid: int, text: str | None = None, photo: bool = False, username: str | None = None) -> dict:
    global _upd
    _upd += 1
    message = {"message_id": _upd, "date": int(time.time()), "chat": {"id": uid, "type": "private"},
               "from": _user(uid, username)}
    if photo:
        message["photo"] = [{"file_id": "small", "file_unique_id": "s", "width": 90, "height": 90},
                            {"file_id": "BIG_PHOTO", "file_unique_id": "b", "width": 1280, "height": 720}]
    else:
        message["text"] = text
        if text and text.startswith("/"):
            message["entities"] = [{"type": "bot_command", "offset": 0, "length": len(text.split()[0])}]
    return {"update_id": _upd, "message": message}


def cb_update(uid: int, data: str, username: str | None = None) -> dict:
    global _upd
    _upd += 1
    return {"update_id": _upd, "callback_query": {
        "id": str(_upd), "from": _user(uid, username), "chat_instance": "ci", "data": data,
        "message": {"message_id": 1, "date": int(time.time()), "chat": {"id": uid, "type": "private"},
                    "from": {"id": 123456, "is_bot": True, "first_name": "bot"}, "text": "panel"},
    }}


def join_update(uid: int, channel_id: int = -100777) -> dict:
    global _upd
    _upd += 1
    return {"update_id": _upd, "chat_join_request": {
        "chat": {"id": channel_id, "type": "channel", "title": "Kirpich"},
        "from": _user(uid), "user_chat_id": uid, "date": int(time.time()),
    }}


def check(cond: bool, label: str) -> None:
    print(("  OK   " if cond else "  FAIL ") + label)
    if not cond:
        check.failed = True


check.failed = False


async def main() -> None:
    if os.path.exists("test_smoke.db"):
        os.remove("test_smoke.db")
    config = load_config()
    await db.init_db(config.database_url)
    async with db._engine.begin() as conn:  # чиста база для тесту
        await conn.run_sync(db.Base.metadata.drop_all)
        await conn.run_sync(db.Base.metadata.create_all)
    session = FakeSession()
    bot = Bot(config.bot_token, session=session)
    dp = build_dispatcher(config)
    feed = lambda u: dp.feed_raw_update(bot, u)  # noqa: E731

    print("1. /start показує меню-хаб")
    await feed(msg_update(1001, "/start"))
    sent = session.of("SendMessage")[-1]
    buttons = [b for row in sent.reply_markup.inline_keyboard for b in row]
    urls = {b.url for b in buttons if b.url}
    check("4874 1000 3461 1692" in sent.text, "номер картки в тексті")
    check("https://kick.com/kirpich-7" in urls and "https://send.monobank.ua/jar/rpRzAmNiq" in urls, "кнопки з посиланнями")
    check(any(b.copy_text and b.copy_text.text == "4874100034611692" for b in buttons), "кнопка копіювання картки")

    print("2. 300 людей одночасно тиснуть /start")
    session.calls.clear()
    started = time.monotonic()
    await asyncio.gather(*(feed(msg_update(5000 + i, "/start")) for i in range(300)))
    took = time.monotonic() - started
    check(len(session.of("SendMessage")) == 300, f"всі 300 отримали меню (за {took:.2f} с)")
    check(took < 300 * LATENCY / 3, f"паралельно, а не по черзі (по черзі було б ~{300 * LATENCY * 2:.0f} с)")
    check((await db.get_stats())["total"] == 301, "всі 301 юзер у базі")

    print("3. Заявка в канал: спершу меню в особисті, потім схвалення")
    session.calls.clear()
    await feed(join_update(2001))
    names = [type(c).__name__ for c in session.calls]
    check(names == ["SendMessage", "ApproveChatJoinRequest"], f"порядок запитів: {names}")
    check((await db.get_stats())["from_channel"] == 1, "юзер записаний з джерелом join_request")

    print("4. Доступ до /admin")
    session.calls.clear()
    await feed(msg_update(1001, "/admin", username="randomguy"))
    check("Адмінка" not in (session.of("SendMessage")[-1].text or ""), "чужий не бачить адмінку")
    await feed(msg_update(ADMIN_ID, "/admin", username="testadmin"))
    check("Адмінка" in session.of("SendMessage")[-1].text, "адмін (регістр/@ не важливі) бачить адмінку")

    print("5. Анонс стріму з картинкою -> розсилка")
    session.blocked_ids = {5000, 5001, 5002}
    session.flood_once = {5010}
    a = dict(uid=ADMIN_ID, username="testadmin")
    await feed(cb_update(data="adm:stream", **a))
    await feed(cb_update(data="stream:both", **a))
    await feed(msg_update(ADMIN_ID, photo=True, username="testadmin"))
    session.calls.clear()
    await feed(cb_update(data="stream:default", **a))
    preview = session.of("SendPhoto")[-1]
    stream_urls = [b.url for row in preview.reply_markup.inline_keyboard for b in row]
    check(preview.photo == "BIG_PHOTO", "превʼю з найбільшою версією картинки")
    check(stream_urls == ["https://kick.com/kirpich-7", "https://www.tiktok.com/@kirpichnik7/live"], f"кнопки стріму: {stream_urls}")
    session.calls.clear()
    active_before = (await db.get_stats())["active"]
    await feed(cb_update(data="bc:go", **a))
    while broadcast.is_running() or broadcast._tasks:
        await asyncio.sleep(0.05)
    photos = [c for c in session.of("SendPhoto")]
    check(len(photos) == active_before - 3, f"доставлено {len(photos)} з {active_before} (3 заблокували)")
    check(any(c.chat_id == 5010 for c in photos), "після flood-limit повторили і доставили")
    check((await db.get_stats())["blocked"] == 3, "заблоковані позначені в базі")
    report = session.of("SendMessage")[-1].text
    check("Розсилка завершена" in report, "адмін отримав звіт")

    print("6. Довільний пост з кнопками -> copy_message")
    await feed(cb_update(data="adm:post", **a))
    await feed(msg_update(ADMIN_ID, "Новий кліп вже в тіктоці!", username="testadmin"))
    session.calls.clear()
    await feed(msg_update(ADMIN_ID, "Дивитись | https://www.tiktok.com/@kirpichnik7", username="testadmin"))
    copies = session.of("CopyMessage")
    check(len(copies) == 1 and copies[0].reply_markup.inline_keyboard[0][0].text == "Дивитись", "превʼю посту з кнопкою")
    await feed(cb_update(data="bc:go", **a))
    while broadcast.is_running() or broadcast._tasks:
        await asyncio.sleep(0.05)
    check(len(session.of("CopyMessage")) == 1 + (await db.get_stats())["active"], "пост розіслано всім активним")

    print("7. Адмін змінює посилання на Kick")
    await feed(cb_update(data="set:kick", **a))
    await feed(msg_update(ADMIN_ID, "не посилання", username="testadmin"))
    check("https://" in session.of("SendMessage")[-1].text, "невалідне посилання відхилено")
    await feed(msg_update(ADMIN_ID, "https://kick.com/new-channel", username="testadmin"))
    await feed(msg_update(1001, "/start"))
    urls = {b.url for row in session.of("SendMessage")[-1].reply_markup.inline_keyboard for b in row}
    check("https://kick.com/new-channel" in urls, "юзер бачить нове посилання")

    print("8. Статистика")
    session.calls.clear()
    await feed(cb_update(data="adm:stats", **a))
    edit = session.of("EditMessageText")[-1]
    # 1001 + 300 одночасних + 2001 із заявки + сам адмін
    check("Всього юзерів: <b>303</b>" in edit.text, "статистика рахує юзерів")

    await db.close_db()
    if os.path.exists("test_smoke.db"):
        os.remove("test_smoke.db")
    print("\nРЕЗУЛЬТАТ:", "Є ПОМИЛКИ" if check.failed else "все працює ✅")
    sys.exit(1 if check.failed else 0)


if __name__ == "__main__":
    asyncio.run(main())
