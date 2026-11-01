import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from aiogram.exceptions import TelegramRetryAfter

T = TypeVar("T")


async def with_retry(call: Callable[[], Awaitable[T]], attempts: int = 3) -> T:
    """Виконати запит до Telegram; якщо він каже "зачекай N секунд" (flood limit) — чекаємо і пробуємо ще."""
    for attempt in range(attempts):
        try:
            return await call()
        except TelegramRetryAfter as e:
            if attempt == attempts - 1:
                raise
            await asyncio.sleep(e.retry_after + 0.5)
    raise RuntimeError("unreachable")
