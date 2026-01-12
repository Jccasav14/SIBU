import os
import sys
from datetime import datetime, timedelta, timezone

import fakeredis.aioredis
import pytest
import pytest_asyncio
from jose import jwt
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# Ensure repo root is on PYTHONPATH so `apps.*` imports work when tests are run from apps/claims
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


@pytest.fixture
def jwt_secret():
    return "test-secret"


@pytest.fixture
def jwt_algorithm():
    return "HS256"


@pytest.fixture
def make_token(jwt_secret, jwt_algorithm):
    def _mk(role: str, email: str = "user@example.com"):
        payload = {
            "email": email,
            "role": role,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        return jwt.encode(payload, jwt_secret, algorithm=jwt_algorithm)

    return _mk


@pytest_asyncio.fixture
async def fake_redis():
    r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    try:
        yield r
    finally:
        await r.close()


@pytest_asyncio.fixture
async def app(jwt_secret, jwt_algorithm, fake_redis):
    # Patch settings
    from apps.claims.app import settings as settings_module

    settings_module.settings.JWT_SECRET = jwt_secret
    settings_module.settings.JWT_ALGORITHM = jwt_algorithm
    settings_module.settings.REDIS_TTL_SECONDS = 60

    # Patch DB engine to sqlite for tests
    from apps.claims.app.infrastructure.postgres import session as session_module
    from apps.claims.app.infrastructure.postgres.base import Base

    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)

    session_module.engine = test_engine
    session_module.SessionLocal = TestSessionLocal

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Patch redis getter
    from apps.claims.app.infrastructure.redis_cache import client as redis_client_module

    redis_client_module.get_redis = lambda: fake_redis

    # Patch routes-level imported get_redis reference
    from apps.claims.app.api import routes as routes_module

    routes_module.get_redis = lambda: fake_redis

    # Disable external integrations
    settings_module.settings.AUDIT_LOG_ENABLED = False
    settings_module.settings.MONGO_ENABLED = False

    from apps.claims.app.main import app as fastapi_app

    return fastapi_app


@pytest_asyncio.fixture
async def client(app):
    import httpx

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
