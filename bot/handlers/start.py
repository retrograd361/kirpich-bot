"""Звичайні юзери: /start і будь-яке повідомлення в особисті -> головне меню."""
from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.menu import send_menu

router = Router(name="start")
router.message.filter(F.chat.type == "private")


@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot) -> None:
    await send_menu(bot, message.chat.id)


@router.message()
async def any_message(message: Message, bot: Bot) -> None:
    # хаб: на будь-яке повідомлення просто показуємо меню
    await send_menu(bot, message.chat.id)
