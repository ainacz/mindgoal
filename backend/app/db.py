"""Движок, фабрика сессий и зависимость для FastAPI."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings

_settings = get_settings()

engine: AsyncEngine = create_async_engine(
    _settings.database_url,
    echo=_settings.db_echo,
    pool_pre_ping=True,  # бесплатный тариф рвёт простаивающие соединения
    pool_size=5,
    max_overflow=5,
)

SessionFactory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # объекты остаются пригодными после commit
    autoflush=False,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Сессия на запрос. Коммитит роутер, откат — здесь."""
    async with SessionFactory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
