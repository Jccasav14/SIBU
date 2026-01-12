import pytest
from httpx import AsyncClient

from app.settings import settings
from app.infrastructure.postgres.repository import ReportsRepository
from datetime import datetime, timezone, date


@pytest.mark.asyncio
async def test_auth_roles(app, override_db, jwt_secret, test_sessionmaker):
    admin_token = __import__("app.tests.conftest", fromlist=["make_token"]).make_token("admin@test.com", "admin", jwt_secret)
    pro_token = __import__("app.tests.conftest", fromlist=["make_token"]).make_token("pro@test.com", "professional", jwt_secret)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/reports/summary?window=7d", headers={"Authorization": f"Bearer {admin_token}"})
        assert r.status_code == 200

        r2 = await ac.get("/reports/summary?window=7d", headers={"Authorization": f"Bearer {pro_token}"})
        assert r2.status_code in (401, 403)


@pytest.mark.asyncio
async def test_insert_and_read_models(app, override_db, jwt_secret, test_sessionmaker):
    # seed metrics
    async with test_sessionmaker() as session:
        repo = ReportsRepository(session)
        ts = datetime.now(timezone.utc)
        await repo.record_event(ts=ts, service="cases", event_type="case.created", severity="info", actor="pro@test.com", role="professional")
        await repo.record_case_signal(ts=ts, signal="created")
        await session.commit()

    admin_token = __import__("app.tests.conftest", fromlist=["make_token"]).make_token("admin@test.com", "admin", jwt_secret)
    today = date.today().isoformat()

    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get(f"/reports/activity?from={today}&to={today}", headers={"Authorization": f"Bearer {admin_token}"})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)

        r2 = await ac.get(f"/reports/cases?from={today}&to={today}", headers={"Authorization": f"Bearer {admin_token}"})
        assert r2.status_code == 200


@pytest.mark.asyncio
async def test_summary_cache(app, override_db, jwt_secret, monkeypatch):
    # patch cache with in-memory dict
    from app.infrastructure.redis_cache import cache as cachemod

    store = {}

    async def fake_get(key):
        return store.get(key)

    async def fake_set(key, value, ttl_sec=None):
        store[key] = value

    monkeypatch.setattr(cachemod.cache, "get_json", fake_get)
    monkeypatch.setattr(cachemod.cache, "set_json", fake_set)

    admin_token = __import__("app.tests.conftest", fromlist=["make_token"]).make_token("admin@test.com", "admin", jwt_secret)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        r1 = await ac.get("/reports/summary?window=7d", headers={"Authorization": f"Bearer {admin_token}"})
        assert r1.status_code == 200
        r2 = await ac.get("/reports/summary?window=7d", headers={"Authorization": f"Bearer {admin_token}"})
        assert r2.status_code == 200
        assert len(store) >= 1
