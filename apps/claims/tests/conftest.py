import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any, AsyncGenerator
import sys
import types

import pytest
from jose import jwt


@pytest.fixture(scope="session", autouse=True)
def _testing_env() -> None:
    # Must be set BEFORE importing the app
    os.environ.setdefault("SIBU_TESTING", "1")
    os.environ.setdefault("JWT_SECRET", "TEST_SECRET_CLAIMS")
    os.environ.setdefault("JWT_ALGORITHM", "HS256")
    os.environ.setdefault("MONGO_ENABLED", "false")
    os.environ.setdefault("AUDIT_LOG_ENABLED", "false")

    # --- STUB motor to avoid optional dependency import error ---
    # apps.claims.app.integrations.mongo_archive imports:
    # from motor.motor_asyncio import AsyncIOMotorClient
    if "motor" not in sys.modules:
        motor_mod = types.ModuleType("motor")
        motor_asyncio_mod = types.ModuleType("motor.motor_asyncio")

        class AsyncIOMotorClient:  # minimal stub
            def __init__(self, *args, **kwargs):
                pass

            def __getitem__(self, name: str):
                return {}

            def close(self):
                return None

        motor_asyncio_mod.AsyncIOMotorClient = AsyncIOMotorClient
        motor_mod.motor_asyncio = motor_asyncio_mod

        sys.modules["motor"] = motor_mod
        sys.modules["motor.motor_asyncio"] = motor_asyncio_mod



class FakeRedis:
    def __init__(self):
        self.store: dict[str, str] = {}

    async def get(self, key: str):
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None):
        self.store[key] = value
        return True

    async def delete(self, *keys: str):
        n = 0
        for k in keys:
            if k in self.store:
                del self.store[k]
                n += 1
        return n

    async def scan(self, cursor: int = 0, match: str | None = None, count: int = 200):
        # naive prefix* support used by invalidate_prefix
        if not match or "*" not in match:
            return 0, []
        prefix = match.split("*", 1)[0]
        keys = [k for k in list(self.store.keys()) if k.startswith(prefix)]
        return 0, keys

    async def close(self):
        return None


class FakeClaimsRepo:
    def __init__(self, session: Any):
        self.session = session
        self._claims = {}
        self._docs = {}
        self._events = {}

        now = datetime.now(timezone.utc)
        cid = "11111111-1111-1111-1111-111111111111"
        self._claims[cid] = SimpleNamespace(
            id=cid,
            student_id="stu-001",
            claim_type="ACCIDENT",
            status="DRAFT",
            occurred_at=now,
            reported_at=now,
            description="desc ok",
            requested_amount=50.0,
            coverage_cap=200.0,
            approved_amount=None,
            payment_status="NONE",
            paid_amount=None,
            paid_at=None,
            payment_method=None,
            payment_reference=None,
            created_at=now,
            updated_at=now,
        )
        self._docs[cid] = [
            SimpleNamespace(
                id="22222222-2222-2222-2222-222222222222",
                claim_id=cid,
                doc_type="invoice",
                file_url="https://example.com/inv.pdf",
                file_hash="abcdef0123456789",
                created_at=now,
            )
        ]
        self._events[cid] = [
            SimpleNamespace(
                id="33333333-3333-3333-3333-333333333333",
                claim_id=cid,
                actor="ins@u.edu",
                event_type=SimpleNamespace(value="CREATED"),
                payload_json='{"status":"DRAFT"}',
                created_at=now,
            )
        ]

    async def list_claims(self, status=None, claim_type=None, student_id=None, limit: int = 50, offset: int = 0):
        items = list(self._claims.values())
        if student_id:
            items = [c for c in items if c.student_id == student_id]
        return items[offset : offset + limit]

    async def get_claim(self, claim_id):
        key = str(claim_id)
        return self._claims.get(key)

    async def overview(self):
        # shape: ov.total, ov.by_status, ov.total_paid
        return SimpleNamespace(total=len(self._claims), by_status={"DRAFT": len(self._claims)}, total_paid=0.0)

    async def list_documents(self, claim_id):
        return self._docs.get(str(claim_id), [])

    async def list_events(self, claim_id):
        return self._events.get(str(claim_id), [])


@pytest.fixture()
def make_token():
    from apps.claims.app.settings import settings

    def _mk(email: str = "ins@u.edu", role: str = "insurance") -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "email": email,
            "role": role,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=30)).timestamp()),
        }
        return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    return _mk


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch):
    from fastapi.testclient import TestClient

    # Import after env is set
    from apps.claims.app import main as main_mod
    from apps.claims.app.api import routes as routes_mod
    from apps.claims.app.infrastructure.postgres import session as session_mod

    # Bypass ALL startup/shutdown events (DB create_all + mongo connect)
    @asynccontextmanager
    async def _dummy_lifespan(_app):
        yield

    if hasattr(main_mod.app.router, "lifespan_context"):
        monkeypatch.setattr(main_mod.app.router, "lifespan_context", _dummy_lifespan)

    # Override DB session dependency
    async def _override_session() -> AsyncGenerator[None, None]:
        yield None

    main_mod.app.dependency_overrides[session_mod.get_session] = _override_session

    # Fake Redis used by RedisCache
    fake_redis = FakeRedis()
    monkeypatch.setattr(routes_mod, "get_redis", lambda: fake_redis)

    # Fake repository (avoids real DB)
    monkeypatch.setattr(routes_mod, "ClaimsRepository", FakeClaimsRepo)

    with TestClient(main_mod.app) as c:
        c.fake_redis = fake_redis  # type: ignore[attr-defined]
        yield c

    main_mod.app.dependency_overrides.clear()
    