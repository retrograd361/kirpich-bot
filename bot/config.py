"""Налаштування бота зі змінних оточення (.env локально, Variables на Railway)."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _split(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _normalize_db_url(url: str) -> str:
    # Railway/Neon дають "postgresql://..." або "postgres://...",
    # а SQLAlchemy для асинхронної роботи потрібен драйвер asyncpg.
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]
    return url


@dataclass(frozen=True)
class Config:
    bot_token: str
    database_url: str
    admin_usernames: frozenset[str]
    admin_ids: frozenset[int]
    channel_id: int | None
    broadcast_rate: int


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN не задано. Додай його в .env або у Variables на Railway.")

    channel_id = os.getenv("CHANNEL_ID", "").strip()
    return Config(
        bot_token=token,
        database_url=_normalize_db_url(os.getenv("DATABASE_URL", "sqlite+aiosqlite:///bot.db")),
        # юзернейми порівнюємо без "@" і без урахування регістру
        admin_usernames=frozenset(u.lstrip("@").lower() for u in _split(os.getenv("ADMIN_USERNAMES", ""))),
        admin_ids=frozenset(int(i) for i in _split(os.getenv("ADMIN_IDS", ""))),
        channel_id=int(channel_id) if channel_id else None,
        broadcast_rate=int(os.getenv("BROADCAST_RATE", "25")),
    )
