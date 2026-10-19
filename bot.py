import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

# Завантажуємо змінні з .env файлу
load_dotenv()

# Налаштування логів
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Читаємо конфіг
BOT_TOKEN = os.getenv("BOT_TOKEN")
INSTAGRAM_URL = os.getenv("INSTAGRAM_URL")
TIKTOK_URL = os.getenv("TIKTOK_URL")
TELEGRAM_CHANNEL_URL = os.getenv("TELEGRAM_CHANNEL_URL")

# Текст привітання
WELCOME_TEXT = (
    "👋 Всім привіт, на зв'язку <b>Кірпіч</b>!\n\n"
    "Приєднуйтесь до моїх соцмереж — там буде 🔥 двіж!\n\n"
    "⬇️ Обирай де зустрінемось:"
)


def get_socials_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура з посиланнями на соцмережі."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📸 Instagram",
                    url=INSTAGRAM_URL
                ),
                InlineKeyboardButton(
                    text="🎵 TikTok",
                    url=TIKTOK_URL
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✈️ Telegram канал",
                    url=TELEGRAM_CHANNEL_URL
                ),
            ],
        ]
    )


# Ініціалізуємо бота і диспетчер
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()


@dp.message(CommandStart())
async def handle_start(message: Message) -> None:
    """Відповідає на команду /start."""
    logger.info(f"Новий користувач: @{message.from_user.username} (id={message.from_user.id})")
    await message.answer(
        text=WELCOME_TEXT,
        reply_markup=get_socials_keyboard()
    )


async def main() -> None:
    logger.info("Бот запускається...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
