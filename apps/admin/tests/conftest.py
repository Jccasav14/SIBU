import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any, AsyncGenerator

import pytest
import jwt


@pytest.fixture(scope="session", autouse=True)
def _testing_env() -> None:
    # Required by your global testing rule (even if service doesn't use it)
    os.environ.setdefault("SIBU_TESTING", "1")


class FakeCache:
    def __init__(self):
        self._store: dict[str, Any] = {}

    async def get_json(self, key: str):
        return self._store.get(key)

    async def set_json(self, key: str, value: Any, ttl: int | None = None) -> None:
        self._store[key] = value

    async def invalidate_prefix(self, prefix: str) -> int:
        keys = [k for k in self._store.keys() if k.startswith(prefix)]
        for k in keys:
            del self._store[k]
        return len(keys)


class FakeRepo:
    def __init__(self):
        # seed
        self.areas = [
            SimpleNamespace(id=1, name="PSYCHOLOGY", enabled=True),
            SimpleNamespace(id=2, name="NUTRITION", enabled=False),
        ]
        self.services = [
            SimpleNamespace(id=10, name="SERVICE_A", enabled=True),
        ]
        self.flags = {"feature_x": True}
        self.settings = {"ui_theme": "dark"}
        self._actions: list[tuple[str, str, str, str | None]] = []

        # knobs for specific tests
        self.raise_integrity_on_create_area = False

    # Catalog: Areas
    async def list_areas(self):
        return list(self.areas)

    async def create_area(self, name: str, enabled: bool = True):
        if self.raise_integrity_on_create_area:
            # match routes.py except clause: sqlalchemy.exc.IntegrityError
            from sqlalchemy.exc import IntegrityError
            raise IntegrityError("stmt", "params", Exception("dup"))
        new_id = max([a.id for a in self.areas] or [0]) + 1
        area = SimpleNamespace(id=new_id, name=name, enabled=enabled)
        self.areas.append(area)
        return area

    async def update_area(self, area_id: int, *, name: str | None = None, enabled: bool | None = None):
        for a in self.areas:
            if a.id == area_id:
                if name is not None:
                    a.name = name
                if enabled is not None:
                    a.enabled = enabled
                return a
        return None

    # Catalog: Services
    async def list_services(self):
        return list(self.services)

    async def create_service(self, name: str, enabled: bool = True):
        new_id = max([s.id for s in self.services] or [0]) + 1
        svc = SimpleNamespace(id=new_id, name=name, enabled=enabled)
        self.services.append(svc)
        return svc

    async def update_service(self, svc_id: int, *, name: str | None = None, enabled: bool | None = None):
        for s in self.services:
            if s.id == svc_id:
                if name is not None:
                    s.name = name
                if enabled is not None:
                    s.enabled = enabled
                return s
        return None

    # Settings/Flags
    async def list_settings(self):
        return dict(self.settings)

    async def put_setting(self, key: str, value: Any):
        self.settings[key] = value

    async def list_flags(self):
        return dict(self.flags)

    async def put_flag(self, key: str, enabled: bool):
        self.flags[key] = bool(enabled)

    # Actions/Counts
    async def add_action(self, actor: str, action: str, entity: str, entity_id: str | None):
        self._actions.append((actor, action, entity, entity_id))
        return SimpleNamespace(id=len(self._actions), actor=actor, action=action, entity=entity, entity_id=entity_id)

    async def counts(self):
        return {
            "catalog_areas": len(self.areas),
            "catalog_services": len(self.services),
            "settings": len(self.settings),
            "flags": len(self.flags),
            "actions": len(self._actions),
        }


@pytest.fixture()
def make_token():
    from apps.admin.app.settings import settings

    def _mk(email: str = "admin@test.com", role: str = "admin") -> str:
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
    Avoid DB/Redis real connections by bypassing lifespan, and override deps/caches.
    """
    from fastapi.testclient import TestClient
    from apps.admin.app import main as main_mod
    from apps.admin.app.api import routes as routes_mod
    from apps.admin.app.infrastructure.postgres import db as db_mod

    # 1) BYPASS lifespan (it creates DB tables + connects Redis)
    @asynccontextmanager
    async def _dummy_lifespan(_app):
        yield

    # Starlette stores lifespan handler here in newer versions
    if hasattr(main_mod.app.router, "lifespan_context"):
        monkeypatch.setattr(main_mod.app.router, "lifespan_context", _dummy_lifespan)
    else:
        # fallback: at least neutralize startup/shutdown
        async def _noop() -> None:
            return None
        monkeypatch.setattr(main_mod.app.router, "startup", _noop)
        monkeypatch.setattr(main_mod.app.router, "shutdown", _noop)

    # 2) Override repo dependency (avoid DB)
    fake_repo = FakeRepo()

    async def _override_repo():
        return fake_repo

    main_mod.app.dependency_overrides[routes_mod.get_repo] = _override_repo

    # 3) Override DB session dependency to avoid accidental DB usage
    async def _override_get_session() -> AsyncGenerator[None, None]:
        yield None

    main_mod.app.dependency_overrides[db_mod.get_session] = _override_get_session

    # 4) Patch cache methods to in-memory
    fake_cache = FakeCache()
    monkeypatch.setattr(routes_mod, "cache", fake_cache)

    with TestClient(main_mod.app) as c:
        c.fake_repo = fake_repo  # type: ignore[attr-defined]
        c.fake_cache = fake_cache  # type: ignore[attr-defined]
        yield c

    main_mod.app.dependency_overrides.clear()
