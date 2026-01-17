import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any, AsyncGenerator, Optional

import pytest
from jose import jwt


@pytest.fixture(scope="session", autouse=True)
def _testing_env() -> None:
    os.environ.setdefault("SIBU_TESTING", "1")
    os.environ.setdefault("KAFKA_BOOTSTRAP", "")


def _entity_from_stmt(stmt: Any) -> Optional[type]:
    try:
        cds = getattr(stmt, "column_descriptions", None)
        if not cds:
            return None
        return cds[0].get("entity")
    except Exception:
        return None


class _FakeScalars:
    def __init__(self, rows: list[Any]):
        self._rows = rows

    def all(self) -> list[Any]:
        return list(self._rows)


class _FakeResult:
    def __init__(self, *, scalar: Any = None, rows: Optional[list[Any]] = None):
        self._scalar = scalar
        self._rows = rows or []

    def scalar_one_or_none(self) -> Any:
        return self._scalar

    def scalars(self) -> _FakeScalars:
        return _FakeScalars(self._rows)


class FakeAsyncSession:
    def __init__(self):
        self.added: list[Any] = []
        self._scalar_by_entity: dict[type, Any] = {}
        self._rows_by_entity: dict[type, list[Any]] = {}

    def set_scalar(self, entity: type, value: Any) -> None:
        self._scalar_by_entity[entity] = value

    def set_rows(self, entity: type, rows: list[Any]) -> None:
        self._rows_by_entity[entity] = rows

    async def execute(self, stmt: Any) -> _FakeResult:
        entity = _entity_from_stmt(stmt)
        if entity is None:
            return _FakeResult(rows=[])
        if entity in self._scalar_by_entity:
            return _FakeResult(scalar=self._scalar_by_entity[entity])
        if entity in self._rows_by_entity:
            return _FakeResult(rows=self._rows_by_entity[entity])
        return _FakeResult(rows=[])

    def add(self, obj: Any) -> None:
        self.added.append(obj)

    async def flush(self) -> None:
        return None

    async def commit(self) -> None:
        return None

    async def refresh(self, obj: Any) -> None:
        if getattr(obj, "id", None) in (None, ""):
            obj.id = "test-id-" + str(len(self.added))
        if getattr(obj, "created_at", None) is None:
            obj.created_at = datetime.now(timezone.utc)

    async def close(self) -> None:
        return None


@pytest.fixture()
def make_token():
    from apps.appointments.app.settings import settings

    def _mk(email: str = "pro1@test.com", role: str = "professional") -> str:
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
    """
    TestClient without triggering real startup (DB/Kafka):
    - patch app.router.startup/shutdown to no-op
    - override get_session with FakeAsyncSession
    """
    from fastapi.testclient import TestClient
    from apps.appointments.app import main as main_mod
    from apps.appointments.app.infrastructure.db import session as session_mod

    # IMPORTANT: avoid app startup/shutdown handlers (they create DB tables)
    async def _noop() -> None:
        return None

    monkeypatch.setattr(main_mod.app.router, "startup", _noop)
    monkeypatch.setattr(main_mod.app.router, "shutdown", _noop)

    # Override DB dependency
    fake_db = FakeAsyncSession()

    async def _override_get_session() -> AsyncGenerator[FakeAsyncSession, None]:
        yield fake_db

    main_mod.app.dependency_overrides[session_mod.get_session] = _override_get_session

    with TestClient(main_mod.app) as c:
        c.fake_db = fake_db  # type: ignore[attr-defined]
        yield c

    main_mod.app.dependency_overrides.clear()
