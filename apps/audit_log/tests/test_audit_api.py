import asyncio
from datetime import datetime, timezone

import jwt
import pytest
import httpx

from app.main import app
from app.settings import settings
from app.api import routes as routes_mod


class FakeRepo:
    def __init__(self):
        self.docs = []

    async def find_events(self, *, filters, page, page_size, sort):
        # Extremely small stub for tests: filter by actor/service/event_type
        items = self.docs
        for k in ["service", "event_type", "actor", "severity", "source"]:
            if filters.get(k):
                items = [d for d in items if d.get(k) == filters[k]]
        total = len(items)
        return items[(page - 1) * page_size : (page - 1) * page_size + page_size], total

    async def get_event(self, event_id: str):
        for d in self.docs:
            if d.get("event_id") == event_id:
                return d
        return None

    async def find_by_entity(self, entity_type: str, entity_id: str, limit: int = 200):
        items = [d for d in self.docs if d.get("entity_type") == entity_type and d.get("entity_id") == entity_id]
        return items[:limit]

    async def aggregate_summary(self, since: datetime):
        return {"total": len(self.docs), "by_service": {}, "by_event_type": {}, "by_severity": {}, "by_role": {}}


def token(email: str, role: str) -> str:
    return jwt.encode({"email": email, "role": role}, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


@pytest.mark.asyncio
async def test_admin_can_list_events(monkeypatch):
    fake = FakeRepo()
    fake.docs.append(
        {
            "event_id": "e1",
            "source": "kafka",
            "event_type": "user.created",
            "service": "auth",
            "actor": "admin@u.edu",
            "actor_role": "admin",
            "entity_type": "user",
            "entity_id": "u1",
            "timestamp": datetime.now(timezone.utc),
            "received_at": datetime.now(timezone.utc),
            "correlation_id": "c1",
            "ip": None,
            "user_agent": None,
            "severity": "INFO",
            "tags": [],
            "payload_raw": {"token": "SHOULD_NOT_LEAK"},
            "payload_norm": {},
        }
    )

    app.dependency_overrides[routes_mod.get_repo] = lambda: fake

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get(
            "/audit/events",
            headers={"Authorization": f"Bearer {token('admin@u.edu', 'admin')}"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 1
        assert data["items"][0]["payload_raw"]["token"] == "***REDACTED***"

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_professional_denied_global(monkeypatch):
    fake = FakeRepo()
    app.dependency_overrides[routes_mod.get_repo] = lambda: fake

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get(
            "/audit/events",
            headers={"Authorization": f"Bearer {token('pro@u.edu', 'professional')}"},
        )
        assert r.status_code == 403

    app.dependency_overrides = {}
