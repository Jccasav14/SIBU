from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from ...settings import settings


def create_engine() -> AsyncEngine:
    return create_async_engine(
        settings.ADMIN_POSTGRES_DSN,
        pool_pre_ping=True,
        future=True,
    )


engine = create_engine()
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
