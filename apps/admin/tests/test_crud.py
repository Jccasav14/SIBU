import httpx
import pytest

from apps.admin.app.settings import settings

from .utils import make_token


@pytest.mark.asyncio
async def test_crud_catalog_and_settings(app):
    token = make_token(secret=settings.JWT_SECRET, alg=settings.JWT_ALGORITHM, email="admin@sibu.ec", role="admin")
    transport = httpx.ASGITransport(app=app, lifespan="on")

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # create area
        r = await client.post(
            "/admin/catalog/areas",
            json={"name": "Psicología", "enabled": True},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        area = r.json()
        assert area["name"] == "Psicología"

        # list areas
        r2 = await client.get("/admin/catalog/areas", headers={"Authorization": f"Bearer {token}"})
        assert r2.status_code == 200
        assert any(x["name"] == "Psicología" for x in r2.json())

        # patch area
        r3 = await client.patch(
            f"/admin/catalog/areas/{area['id']}",
            json={"enabled": False},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r3.status_code == 200
        assert r3.json()["enabled"] is False

        # settings put/get
        r4 = await client.put(
            "/admin/settings/reports_professional_can_view_mine",
            json={"value": True},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r4.status_code == 200
        r5 = await client.get("/admin/settings", headers={"Authorization": f"Bearer {token}"})
        assert r5.status_code == 200
        assert r5.json()["reports_professional_can_view_mine"] is True
