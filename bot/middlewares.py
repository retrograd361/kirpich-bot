"""Middleware — код, який виконується перед кожним хендлером."""
import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

from bot import db

SEEN_TTL = 600  # секунд: не оновлюємо юзера в БД частіше ніж раз на 10 хв


class TrackUsersMiddleware(BaseMiddleware):
    """Записує в базу кожного, хто пише боту в особисті.

    Щоб при масовому наплині не робити запис у БД на кожен клік,
    памʼятаємо, кого вже бачили за останні 10 хвилин.
    """

    def __init__(self) -> None:
        self._seen: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user: User | None = data.get("event_from_user")
        chat = data.get("event_chat")
        if user and not user.is_bot and chat and chat.type == "private":
            now = time.monotonic()
            if now - self._seen.get(user.id, 0) > SEEN_TTL:
                self._seen[user.id] = now
                await db.upsert_user(user, source="start")
            if len(self._seen) > 100_000:  # щоб памʼять не росла безкінечно
                self._seen.clear()
        return await handler(event, data)
