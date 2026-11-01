"""Точка входу: python -m bot"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, LinkPreviewOptions

from bot import db
from bot.config import load_config
from bot.handlers import get_routers
from bot.middlewares import TrackUsersMiddleware


def build_dispatcher(config) -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    dp["config"] = config  # стане доступним у хендлерах і фільтрах як аргумент `config`
    tracker = TrackUsersMiddleware()
    dp.message.outer_middleware(tracker)
    dp.callback_query.outer_middleware(tracker)
    dp.include_routers(*get_routers())
    return dp


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    config = load_config()
    if not config.admin_usernames and not config.admin_ids:
        logging.warning("ADMIN_USERNAMES порожній — /admin нікому не буде доступний")

    await db.init_db(config.database_url)
    bot = Bot(
        config.bot_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            link_preview=LinkPreviewOptions(is_disabled=True),
        ),
    )
    dp = build_dispatcher(config)

    await bot.set_my_commands([BotCommand(command="start", description="Головне меню")])
    await bot.delete_webhook()
    try:
        # allowed_updates: просимо в Telegram лише ті типи подій, які обробляємо
        # (в т.ч. chat_join_request — без цього заявки в канал не приходять)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await db.close_db()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
