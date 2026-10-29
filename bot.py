import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ChatJoinRequest
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
DONATELLO_URL = os.getenv("DONATELLO_URL")
MONOBANK_URL = os.getenv("MONOBANK_URL")

# Текст привітання
WELCOME_TEXT = (
    "👋 Всім привіт, на зв'язку <b>Кірпіч</b>!\n\n"
    "Приєднуйтесь до моїх соцмереж — там буде 🔥 двіж!\n\n"
    "💳 Підтримати донатом на карту можна сюди:\n"
    "<code>4874 1000 3461 1692</code>\n\n"
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
            [
                InlineKeyboardButton(
                    text="💸 Підтримати донатом (Donatello)",
                    url=DONATELLO_URL
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🏦 Підтримати донатом (Монобанка)",
                    url=MONOBANK_URL
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


@dp.chat_join_request()
async def handle_join_request(request: ChatJoinRequest) -> None:
    """Автоматично приймає заявки в канал через 10 секунд і надсилає повідомлення."""
    user = request.from_user
    logger.info(f"Заявка від: @{user.username} (id={user.id}) в чат {request.chat.id}")

    # Чекаємо 10 секунд
    await asyncio.sleep(10)

    # Приймаємо заявку
    await bot.approve_chat_join_request(
        chat_id=request.chat.id,
        user_id=user.id
    )
    logger.info(f"Заявку прийнято: @{user.username} (id={user.id})")

    # Надсилаємо повідомлення в приват з кнопками соцмереж
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📸 Instagram", url=INSTAGRAM_URL),
                InlineKeyboardButton(text="🎵 TikTok", url=TIKTOK_URL),
            ],
        ]
    )
    try:
        await bot.send_message(
            chat_id=user.id,
            text=(
                "Привіт! Твою заявку в канал схвалено 🔥\n\n"
                "Також не забудь залетіти в наш Instagram і TikTok!"
            ),
            reply_markup=keyboard
        )
    except Exception as e:
        # Якщо юзер не запускав бота раніше — повідомлення не надішлеться, це нормально
        logger.warning(f"Не вдалось надіслати повідомлення @{user.username}: {e}")


async def main() -> None:
    logger.info("Бот запускається...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
