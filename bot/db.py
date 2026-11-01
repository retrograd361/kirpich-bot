"""База даних: юзери бота і налаштування (посилання/тексти), які змінює адмін.

Працює і з SQLite (локально), і з PostgreSQL (Railway/Neon) — залежить від DATABASE_URL.
"""
from datetime import datetime, timedelta, timezone

from aiogram.types import User as TgUser
from sqlalchemy import BigInteger, Boolean, DateTime, String, Text, func, select, update
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from bot.content import DEFAULTS


def utcnow() -> datetime:
    # зберігаємо час у UTC без таймзони — однаково для SQLite і Postgres
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram user id
    username: Mapped[str | None] = mapped_column(String(64))
    first_name: Mapped[str | None] = mapped_column(String(128))
    source: Mapped[str] = mapped_column(String(32), default="start")  # start | join_request
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text)


_engine: AsyncEngine | None = None
_session: async_sessionmaker | None = None
# Налаштування читаються на кожен /start — тримаємо їх у памʼяті,
# щоб під навантаженням не смикати БД зайвий раз.
_settings_cache: dict[str, str] | None = None


async def init_db(url: str) -> None:
    global _engine, _session
    kwargs = {} if url.startswith("sqlite") else {"pool_size": 10, "max_overflow": 20, "pool_pre_ping": True}
    _engine = create_async_engine(url, **kwargs)
    _session = async_sessionmaker(_engine, expire_on_commit=False)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    if _engine is not None:
        await _engine.dispose()


def _insert():
    # INSERT ... ON CONFLICT пишеться трохи по-різному для різних БД
    if _engine.dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    else:
        from sqlalchemy.dialects.sqlite import insert
    return insert


# ---------- Юзери ----------

async def upsert_user(user: TgUser, source: str = "start") -> None:
    """Додати юзера або оновити його дані. source записується лише при першому додаванні."""
    now = utcnow()
    stmt = _insert()(User).values(
        id=user.id, username=user.username, first_name=user.first_name,
        source=source, is_blocked=False, created_at=now, last_seen=now,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=[User.id],
        set_={
            "username": stmt.excluded.username,
            "first_name": stmt.excluded.first_name,
            "is_blocked": False,  # написав боту => точно не заблокував
            "last_seen": now,
        },
    )
    async with _session() as s:
        await s.execute(stmt)
        await s.commit()


async def get_active_user_ids() -> list[int]:
    async with _session() as s:
        rows = await s.execute(select(User.id).where(User.is_blocked.is_(False)).order_by(User.id))
        return list(rows.scalars())


async def mark_blocked(user_ids: list[int]) -> None:
    if not user_ids:
        return
    async with _session() as s:
        await s.execute(update(User).where(User.id.in_(user_ids)).values(is_blocked=True))
        await s.commit()


async def get_stats() -> dict[str, int]:
    now = utcnow()
    async with _session() as s:
        async def count(*where) -> int:
            return (await s.execute(select(func.count()).select_from(User).where(*where))).scalar_one()

        return {
            "total": await count(),
            "active": await count(User.is_blocked.is_(False)),
            "blocked": await count(User.is_blocked.is_(True)),
            "new_day": await count(User.created_at >= now - timedelta(days=1)),
            "new_week": await count(User.created_at >= now - timedelta(days=7)),
            "from_channel": await count(User.source == "join_request"),
        }


# ---------- Налаштування ----------

async def get_settings() -> dict[str, str]:
    """Усі налаштування: дефолти з content.py, перекриті значеннями з БД."""
    global _settings_cache
    if _settings_cache is None:
        async with _session() as s:
            rows = await s.execute(select(Setting.key, Setting.value))
            _settings_cache = {**DEFAULTS, **dict(rows.all())}
    return _settings_cache


async def set_setting(key: str, value: str) -> None:
    global _settings_cache
    stmt = _insert()(Setting).values(key=key, value=value)
    stmt = stmt.on_conflict_do_update(index_elements=[Setting.key], set_={"value": value})
    async with _session() as s:
        await s.execute(stmt)
        await s.commit()
    _settings_cache = None  # наступне читання підтягне свіжі значення
