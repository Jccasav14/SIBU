import os
import importlib
import pytest
import jwt
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from fastapi import FastAPI

# Ensure test-friendly env
os.environ.setdefault("REPORTS_POSTGRES_DSN", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("KAFKA_ENABLED", "false")
os.environ.setdefault("RABBITMQ_ENABLED", "false")
os.environ.setdefault("PROMETHEUS_METRICS_ENABLED", "false")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")  # unused in tests

from app.settings import settings  # noqa: E402
from app.main import app as real_app  # noqa: E402
from app.infrastructure.postgres import db as dbmod  # noqa: E402
from app.infrastructure.postgres import init_db as initmod  # noqa: E402


@pytest.fixture(scope="session")
def app() -> FastAPI:
    return real_app


@pytest.fixture(scope="session")
def jwt_secret() -> str:
    return settings.JWT_SECRET


def make_token(email: str, role: str, secret: str) -> str:
    payload = {"email": email, "role": role, "exp": datetime.now(timezone.utc) + timedelta(hours=1)}
    return jwt.encode(payload, secret, algorithm=settings.JWT_ALGORITHM)


@pytest.fixture()
async def test_sessionmaker():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    # init schema
    async with engine.begin() as conn:
        await conn.run_sync(dbmod.metadata.create_all)
    yield SessionLocal
    await engine.dispose()


@pytest.fixture()
async def override_db(app: FastAPI, test_sessionmaker):
    async def _get_session():
        async with test_sessionmaker() as s:
            yield s

    app.dependency_overrides[dbmod.get_session] = _get_session
    yield
    app.dependency_overrides.clear()
