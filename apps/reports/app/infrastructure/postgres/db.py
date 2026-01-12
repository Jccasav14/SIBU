from __future__ import annotations

from datetime import datetime
from typing import AsyncIterator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from ...settings import settings


metadata = MetaData()


def make_engine() -> AsyncEngine:
    return create_async_engine(settings.REPORTS_POSTGRES_DSN, echo=settings.SQL_ECHO, pool_pre_ping=True)


engine: AsyncEngine = make_engine()
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
