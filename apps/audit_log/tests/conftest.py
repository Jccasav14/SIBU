import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncGenerator, Optional

import pytest
import jwt


@pytest.fixture(scope="session", autouse=True)
def _testing_env() -> None:
    # Required by your global rule
    os.environ.setdefault("SIBU_TESTING", "1")
    # Extra safety (even if we bypass lifespan)
    os.environ.setdefault("AUDIT_CONSUMERS_ENABLED", "false")
    os.environ.setdefault("KAFKA_BOOTSTRAP", "")
    os.environ.setdefault("RABBITMQ_URL", "")
    os.environ.setdefault("MQTT_BROKER", "")


class FakeCursor:
    def __init__(self, docs: list[dict[str, Any]]):
        self._docs = docs
        self._i = 0

    def sort(self, *args, **kwargs):
        return self

    def limit(self, n: int):
        self._docs = self._docs[:n]
        return self

    async def to_list(self, length: int = 100):
        return self._docs[:length]

    def __aiter__(self):
        self._i = 0
        return self

    async def __anext__(self):
        if self._i >= len(self._docs):
            raise StopAsyncIteration
        item = self._docs[self._i]
        self._i += 1
        return item


class FakeCollection:
    def __init__(self, docs: list[dict[str, Any]]):
        self.docs = docs
        self.last_aggregate_pipeline = None
        self.last_find_query = None

    # IMPORTANT: in motor/pymongo, aggregate() is sync and returns a cursor-like object
    def aggregate(self, pipeline):
        self.last_aggregate_pipeline = pipeline
        return FakeCursor(
            [
                {"_id": "admin@u.edu", "count": 3, "roles": ["admin"]},
                {"_id": "pro@u.edu", "count": 1, "roles": ["professional"]},
            ]
        )

    def find(self, q, projection=None):
        self.last_find_query = q
        return FakeCursor([d for d in self.docs])



class FakeRepo:
    def __init__(self):
        now = datetime.now(timezone.utc)
        self.docs: list[dict[str, Any]] = [
            {
                "event_id": "e1",
                "source": "kafka",
                "event_type": "user.created",
                "service": "auth",
                "actor": "admin@u.edu",
                "actor_role": "admin",
                "entity_type": "user",
                "entity_id": "u1",
                "timestamp": now,
                "received_at": now,
                "correlation_id": "c1",
                "ip": None,
                "user_agent": None,
                "severity": "INFO",
                "tags": [],
                "payload_raw": {"token": "SHOULD_NOT_LEAK"},
                "payload_norm": {"password": "NOPE"},
            }
        ]
        self.col = FakeCollection(self.docs)

        # knobs
        self._force_find_empty = False

    async def find_events(self, *, filters, page, page_size, sort):
        if self._force_find_empty:
            return [], 0
        items = list(self.docs)
        for k in [
            "service",
            "event_type",
            "actor",
            "actor_role",
            "entity_type",
            "entity_id",
            "severity",
            "source",
            "correlation_id",
        ]:
            if filters.get(k):
                items = [d for d in items if d.get(k) == filters[k]]

        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        return items[start:end], total

    async def get_event(self, event_id: str):
        for d in self.docs:
            if d.get("event_id") == event_id:
                return d
        return None

    async def find_by_entity(self, entity_type: str, entity_id: str, limit: int = 200):
        items = [d for d in self.docs if d.get("entity_type") == entity_type and d.get("entity_id") == entity_id]
        return items[:limit]

    async def aggregate_summary(self, since: datetime):
        # minimal deterministic summary
        return {
            "total": len(self.docs),
            "by_service": {"auth": 1},
            "by_event_type": {"user.created": 1},
            "by_severity": {"INFO": 1},
            "by_role": {"admin": 1},
        }

    async def insert_event(self, event_id: str, doc: dict[str, Any]) -> None:
        now = datetime.now(timezone.utc)
        self.docs.append({"event_id": event_id, "received_at": now, **doc})


@pytest.fixture()
def make_token():
    from apps.audit_log.app.settings import settings

    def _mk(email: str = "admin@u.edu", role: str = "admin") -> str:
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
    from apps.audit_log.app import main as main_mod
    from apps.audit_log.app.api import routes as routes_mod

    # Bypass lifespan (avoids mongo.connect + consumers)
    @asynccontextmanager
    async def _dummy_lifespan(_app):
        yield

    if hasattr(main_mod.app.router, "lifespan_context"):
        monkeypatch.setattr(main_mod.app.router, "lifespan_context", _dummy_lifespan)
    else:
        async def _noop() -> None:
            return None
        monkeypatch.setattr(main_mod.app.router, "startup", _noop)
        monkeypatch.setattr(main_mod.app.router, "shutdown", _noop)

    fake_repo = FakeRepo()

    async def _override_repo() -> FakeRepo:
        return fake_repo

    main_mod.app.dependency_overrides[routes_mod.get_repo] = _override_repo

    with TestClient(main_mod.app) as c:
        c.fake_repo = fake_repo  # type: ignore[attr-defined]
        yield c

    main_mod.app.dependency_overrides.clear()
