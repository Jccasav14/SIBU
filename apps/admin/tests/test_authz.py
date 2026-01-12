import httpx
import pytest

from apps.admin.app.settings import settings

from .utils import make_token


@pytest.mark.asyncio
async def test_admin_ok_vs_professional_403(app):
    admin_token = make_token(secret=settings.JWT_SECRET, alg=settings.JWT_ALGORITHM, email="admin@sibu.ec", role="admin")
    pro_token = make_token(secret=settings.JWT_SECRET, alg=settings.JWT_ALGORITHM, email="pro@sibu.ec", role="professional")

    transport = httpx.ASGITransport(app=app, lifespan="on")

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/admin/flags", headers={"Authorization": f"Bearer {admin_token}"})
        assert r.status_code == 200

        r2 = await client.get("/admin/flags", headers={"Authorization": f"Bearer {pro_token}"})
        assert r2.status_code == 403
