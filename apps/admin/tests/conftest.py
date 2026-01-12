import os
import importlib

import pytest
import fakeredis.aioredis


@pytest.fixture(scope="session")
def event_loop():
    # pytest-asyncio compatibility
    import asyncio

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def app():
    # Configure env BEFORE importing the app/settings
    os.environ["JWT_SECRET"] = "test-secret"
    os.environ["JWT_ALGORITHM"] = "HS256"
    os.environ["ADMIN_POSTGRES_DSN"] = "sqlite+aiosqlite:///:memory:"
    os.environ["REDIS_URL"] = "redis://fakeredis"  # only a marker

    # Reload modules to re-read env
    from apps.admin.app import settings as settings_mod

    importlib.reload(settings_mod)

    from apps.admin.app.infrastructure.redis_cache import client as cache_mod

    importlib.reload(cache_mod)

    # Replace real redis with fakeredis
    fake = fakeredis.aioredis.FakeRedis()

    async def _connect():
        cache_mod.cache._redis = fake

    async def _close():
        await fake.close()
        cache_mod.cache._redis = None

    cache_mod.cache.connect = _connect  # type: ignore
    cache_mod.cache.close = _close  # type: ignore

    from apps.admin.app import main as main_mod

    importlib.reload(main_mod)
    return main_mod.app
