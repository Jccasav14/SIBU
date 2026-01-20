import os

# -------------------------------------------------------------------
# IMPORTANT: env vars must exist at IMPORT/COLLECTION time
# (app.settings instantiates Settings() on import)
# -------------------------------------------------------------------
os.environ.setdefault("SIBU_TESTING", "1")
os.environ.setdefault("JWT_SECRET", "TEST_SECRET_COVERAGE")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("COVERAGE_POSTGRES_DSN", "postgresql+asyncpg://user:pass@localhost:5432/coverage_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("REDIS_TTL_SECONDS", "60")

import sys
import types
from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

# -------------------------------------------------------------------
# Make `import app...` resolve to apps/coverage/app DURING COLLECTION
# -------------------------------------------------------------------
HERE = os.path.dirname(__file__)
SVC_ROOT = os.path.abspath(os.path.join(HERE, ".."))          # apps/coverage
APP_DIR = os.path.abspath(os.path.join(SVC_ROOT, "app"))      # apps/coverage/app

# `import app.*` -> needs APP_DIR in sys.path
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

# Keep service root too (sometimes useful)
if SVC_ROOT not in sys.path:
    sys.path.insert(0, SVC_ROOT)

# -------------------------------------------------------------------
# Optional dependency stubs (collection-safe)
# -------------------------------------------------------------------
try:
    import redis.asyncio  # noqa: F401
except Exception:
    redis_mod = types.ModuleType("redis")
    redis_asyncio_mod = types.ModuleType("redis.asyncio")

    class Redis:  # minimal placeholder
        pass

    redis_asyncio_mod.Redis = Redis
    redis_mod.asyncio = redis_asyncio_mod
    sys.modules["redis"] = redis_mod
    sys.modules["redis.asyncio"] = redis_asyncio_mod


class FakeRedis:
    def __init__(self):
        self.store: dict[str, str] = {}

    async def get(self, key: str):
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None):
        self.store[key] = value
        return True

    async def delete(self, *keys: str):
        for k in keys:
            self.store.pop(k, None)
        return 1

    async def scan(self, cursor: int = 0, match: str | None = None, count: int = 200):
        if not match or "*" not in match:
            return 0, []
        prefix = match.split("*", 1)[0]
        keys = [k for k in list(self.store.keys()) if k.startswith(prefix)]
        return 0, keys


@pytest.fixture()
def fake_policy():
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=uuid4(),
        claim_type=SimpleNamespace(value="ACCIDENT"),
        name="Policy A",
        description="Desc",
        max_coverage_amount=Decimal("123.45"),
        currency="USD",
        requires_documents=["invoice"],
        waiting_days=0,
        is_active=True,
        valid_from=date(2025, 1, 1),
        valid_to=None,
        created_at=now,
        updated_at=now,
    )
