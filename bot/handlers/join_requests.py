"""Автоматичний прийом заявок у закритий Telegram-канал.

Важливий нюанс Telegram: бот може написати людині, яка подала заявку, навіть якщо
вона ще не натискала /start — але ТІЛЬКИ поки заявка не оброблена (і до 5 хв).
Тому порядок такий: зберегти в базу -> надіслати меню -> схвалити заявку.
Так кожен, хто приходить у канал, автоматично потрапляє в базу для розсилок.
"""
import logging

from aiogram import Bot, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import ChatJoinRequest

from bot import db
from bot.config import Config
from bot.menu import send_menu
from bot.utils import with_retry

log = logging.getLogger(__name__)
router = Router(name="join_requests")


@router.chat_join_request()
async def on_join_request(request: ChatJoinRequest, bot: Bot, config: Config) -> None:
    if config.channel_id and request.chat.id != config.channel_id:
        return  # заявка в інший чат, де бот теж адмін — не чіпаємо

    await db.upsert_user(request.from_user, source="join_request")

    try:
        await with_retry(lambda: send_menu(bot, request.user_chat_id))
    except (TelegramForbiddenError, TelegramBadRequest) as e:
        log.info("Can't DM %s on join request: %s", request.from_user.id, e)

    try:
        await with_retry(request.approve)
    except TelegramBadRequest as e:
        # наприклад, заявку вже схвалив інший адмін вручну
        log.info("Can't approve %s: %s", request.from_user.id, e)
