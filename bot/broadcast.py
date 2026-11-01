"""Розсилка всім юзерам у фоні.

Як це працює:
- Telegram дозволяє боту ~30 повідомлень на секунду. Ми шлемо пачками по `rate` штук
  паралельно, а потім чекаємо, щоб пачка зайняла не менше 1 секунди.
- Розсилка запускається як фонова задача (asyncio task), тому бот під час неї
  продовжує відповідати людям на /start.
- Хто заблокував бота — позначаємо is_blocked, щоб наступного разу не слати даремно.
"""
import asyncio
import logging
import time
from collections.abc import Awaitable, Callable

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from bot import db
from bot.utils import with_retry

log = logging.getLogger(__name__)

SendFn = Callable[[int], Awaitable[object]]

_running = False
_tasks: set[asyncio.Task] = set()  # тримаємо посилання, щоб задачу не зібрав garbage collector


def is_running() -> bool:
    return _running


async def _send_one(send: SendFn, chat_id: int) -> str:
    try:
        await with_retry(lambda: send(chat_id))
        return "ok"
    except TelegramForbiddenError:  # заблокував бота / видалив акаунт
        return "blocked"
    except TelegramBadRequest as e:
        if "chat not found" in str(e).lower():
            return "blocked"
        log.warning("Broadcast to %s failed: %s", chat_id, e)
        return "failed"
    except Exception as e:  # одна помилка не має зупиняти всю розсилку
        log.warning("Broadcast to %s failed: %s", chat_id, e)
        return "failed"


async def run_broadcast(bot: Bot, send: SendFn, report_chat_id: int, rate: int) -> dict[str, int]:
    global _running
    _running = True
    stats = {"ok": 0, "blocked": 0, "failed": 0}
    try:
        user_ids = await db.get_active_user_ids()
        total = len(user_ids)
        status = await bot.send_message(report_chat_id, f"⏳ Розсилка почалась: 0 / {total}")
        last_report = time.monotonic()

        for start in range(0, total, rate):
            chunk = user_ids[start:start + rate]
            started = time.monotonic()
            results = await asyncio.gather(*(_send_one(send, uid) for uid in chunk))

            blocked = [uid for uid, r in zip(chunk, results) if r == "blocked"]
            await db.mark_blocked(blocked)
            for r in results:
                stats[r] += 1

            # прогрес раз на ~5 секунд, щоб не спамити редагуваннями
            if time.monotonic() - last_report > 5:
                last_report = time.monotonic()
                try:
                    await status.edit_text(f"⏳ Розсилка: {start + len(chunk)} / {total}")
                except TelegramBadRequest:
                    pass

            elapsed = time.monotonic() - started
            if elapsed < 1:
                await asyncio.sleep(1 - elapsed)

        await bot.send_message(
            report_chat_id,
            "✅ <b>Розсилка завершена</b>\n\n"
            f"Доставлено: <b>{stats['ok']}</b>\n"
            f"Заблокували бота: {stats['blocked']}\n"
            f"Помилки: {stats['failed']}",
        )
    except Exception:
        log.exception("Broadcast crashed")
        await bot.send_message(report_chat_id, "⚠️ Розсилка впала з помилкою, деталі в логах.")
    finally:
        _running = False
    return stats


def start_broadcast(bot: Bot, send: SendFn, report_chat_id: int, rate: int) -> None:
    task = asyncio.create_task(run_broadcast(bot, send, report_chat_id, rate))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
