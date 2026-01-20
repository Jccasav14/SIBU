import httpx
import pytest


@pytest.mark.asyncio
async def test_health_ok(app):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body.get("ok") is True
        assert body.get("service") == "auth"


@pytest.mark.asyncio
async def test_admin_only_requires_auth(app):
    # Según tu implementación de auth puede ser 401 o 403.
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/admin-only")
        assert r.status_code in {401, 403}
