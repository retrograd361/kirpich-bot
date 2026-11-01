from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject, User

from bot.config import Config


class IsAdmin(BaseFilter):
    """Пропускає тільки тих, чий @username є в ADMIN_USERNAMES (або id в ADMIN_IDS)."""

    async def __call__(self, event: TelegramObject, event_from_user: User | None, config: Config) -> bool:
        if event_from_user is None:
            return False
        if event_from_user.id in config.admin_ids:
            return True
        username = (event_from_user.username or "").lower()
        return bool(username) and username in config.admin_usernames
