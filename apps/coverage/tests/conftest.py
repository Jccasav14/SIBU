from __future__ import annotations

import os
import pathlib
import pytest
import pytest_asyncio
from jose import jwt
import fakeredis.aioredis

# Set env BEFORE importing the application modules
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("COVERAGE_POSTGRES_DSN", "sqlite+aiosqlite:///./coverage_test.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/4")
os.environ.setdefault("REDIS_TTL_SECONDS", "120")

from app.main import app  # noqa: E402
from app.settings import settings  # noqa: E402
from app.infrastructure.postgres.base import Base  # noqa: E402
from app.infrastructure.postgres.session import get_engine  # noqa: E402
from app.infrastructure.redis_cache import client as redis_client  # noqa: E402


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _prepare_db():
    # Ensure a clean sqlite db file for tests
    if settings.postgres_dsn.startswith("sqlite"):
        db_path = pathlib.Path("./coverage_test.db")
        if db_path.exists():
            db_path.unlink()

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture()
async def redis():
    r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    await r.flushdb()
    return r


@pytest_asyncio.fixture(autouse=True)
async def _patch_redis(redis, monkeypatch):
    monkeypatch.setattr(redis_client, "_client", redis)
    yield
    await redis.flushdb()


def make_token(role: str) -> str:
    payload = {"sub": "test-user", "role": role}
    return jwt.encode(payload, os.environ["JWT_SECRET"], algorithm=os.environ["JWT_ALGORITHM"])


@pytest_asyncio.fixture()
async def admin_token():
    return make_token("admin")


@pytest_asyncio.fixture()
async def insurance_token():
    return make_token("insurance")


@pytest_asyncio.fixture()
async def professional_token():
    return make_token("professional")
