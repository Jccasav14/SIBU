from __future__ import annotations

import os
import sys
import types
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pytest


# -----------------------------
# Hard stubs for optional deps
# -----------------------------
class _StubAIOKafkaConsumer:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.started = False
        self.stopped = False

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.stopped = True

    def __aiter__(self):
        async def _empty():
            if False:  # pragma: no cover
                yield None

        return _empty()


class _StubRedisClient:
    def __init__(self):
        self.store: Dict[str, str] = {}

    async def ping(self) -> bool:
        return True

    async def get(self, key: str) -> Optional[str]:
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> None:
        self.store[key] = value


def _install_stub_modules() -> None:
    # aiokafka
    aiokafka_mod = types.SimpleNamespace(AIOKafkaConsumer=_StubAIOKafkaConsumer)
    sys.modules.setdefault("aiokafka", aiokafka_mod)

    # aio_pika (only to satisfy imports)
    async def _connect_robust(*args, **kwargs):
        class _Conn:
            async def channel(self):
                class _Ch:
                    async def set_qos(self, *a, **k):  # noqa: ANN001
                        return None

                return _Ch()

            async def close(self):
                return None

        return _Conn()

    aio_pika_mod = types.SimpleNamespace(connect_robust=_connect_robust, Message=object, ExchangeType=types.SimpleNamespace(DIRECT="direct"))
    sys.modules.setdefault("aio_pika", aio_pika_mod)

    # redis.asyncio
    redis_asyncio = types.SimpleNamespace(from_url=lambda *a, **k: _StubRedisClient(), Redis=_StubRedisClient)
    redis_pkg = types.SimpleNamespace(asyncio=redis_asyncio)
    sys.modules.setdefault("redis", redis_pkg)
    sys.modules.setdefault("redis.asyncio", redis_asyncio)


_install_stub_modules()


# ---------------------------------
# Deterministic in-memory test deps
# ---------------------------------
class InMemoryCache:
    def __init__(self) -> None:
        self.data: Dict[str, Any] = {}

    async def get_json(self, key: str) -> Any | None:
        return self.data.get(key)

    async def set_json(self, key: str, value: Any, ttl: int | None = None) -> None:  # noqa: ARG002
        self.data[key] = value


@dataclass
class FakeResp:
    status_code: int
    _json: Any

    def json(self) -> Any:
        return self._json


class FakeRepo:
    async def totals_by_service(self, from_day, to_day):  # noqa: ANN001
        return [
            {"service": "cases", "count": 3},
            {"service": "appointments", "count": 2},
            {"service": "security", "count": 1},
        ]


    async def query_cases(self, from_day, to_day):  # noqa: ANN001
        # CasesRow exige: day, created, shared, closed
        return [{"day": str(from_day), "created": 3, "shared": 1, "closed": 0}]

    async def query_appointments(self, from_day, to_day):  # noqa: ANN001
        return [{"day": str(from_day), "created": 2, "canceled": 0, "completed": 1}]


    async def query_security(self, from_day, to_day):  # noqa: ANN001
        return [
            {
                "day": str(from_day),
                "login_failed": 1,
                "access_denied": 0,
                "suspicious_activity": 0,
            }
        ]


    async def top_actors(self, from_day, to_day, limit: int = 10):  # noqa: ANN001
        return [{"actor": "admin@local", "role": "admin", "count": min(limit, 7)}]

    async def query_daily_activity(
        self,
        from_day,
        to_day,
        service=None,
        event_type=None,
        severity=None,
        role=None,
    ):  # noqa: ANN001
        # ActivityRow: day, service, event_type, severity, role, count
        return [
            {
                "day": str(from_day),
                "service": service or "cases",
                "event_type": event_type or "created",
                "severity": severity or "INFO",
                "role": role or "admin",
                "count": 1,
            }
        ]

    async def create_export_job(self, job_id: str, type_: str, params: Dict[str, Any]):  # noqa: ARG002
        return None


@pytest.fixture(scope="session", autouse=True)
def _env() -> None:
    # disable background consumers in lifespan
    os.environ.setdefault("KAFKA_ENABLED", "false")
    os.environ.setdefault("RABBITMQ_ENABLED", "false")
    os.environ.setdefault("PROMETHEUS_METRICS_ENABLED", "true")


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch):
    from fastapi.testclient import TestClient

    # import AFTER env + stubs
    from apps.reports.app import main as main_mod
    from apps.reports.app.api import routes as routes_mod

    # Avoid real DB init
    async def _noop_init_db() -> None:
        return None

    monkeypatch.setattr(main_mod, "init_db", _noop_init_db)

    # Replace cache + repo + rabbit + audit client
    monkeypatch.setattr(routes_mod, "cache", InMemoryCache())
    monkeypatch.setattr(routes_mod, "ReportsRepository", lambda session: FakeRepo())  # noqa: ARG005

    async def _rabbit_publish(*args, **kwargs):  # noqa: ANN001
        return None

    monkeypatch.setattr(routes_mod.rabbit, "publish", _rabbit_publish)

    async def _audit_get(path: str, params=None, headers=None):  # noqa: ANN001
        # minimal deterministic proxy response
        return FakeResp(200, {"path": path, "params": params or {}, "auth": (headers or {}).get("Authorization", "")})

    monkeypatch.setattr(routes_mod.audit_client, "get", _audit_get)

    return TestClient(main_mod.app)


@pytest.fixture()
def make_token():
    import jwt

    from apps.reports.app.settings import settings

    def _mk(email: str = "admin@local", role: str = "admin") -> str:
        return jwt.encode({"email": email, "role": role}, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    return _mk
