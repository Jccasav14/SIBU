import httpx
import pytest

from apps.admin.app.infrastructure.redis_cache.client import cache
from apps.admin.app.settings import settings

from .utils import make_token


@pytest.mark.asyncio
async def test_cache_get_set_invalidate(app):
    token = make_token(secret=settings.JWT_SECRET, alg=settings.JWT_ALGORITHM, email="admin@sibu.ec", role="admin")
    transport = httpx.ASGITransport(app=app, lifespan="on")

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # First call populates cache
        r1 = await client.get("/admin/flags", headers={"Authorization": f"Bearer {token}"})
        assert r1.status_code == 200
        assert await cache.r.exists("admin:flags") == 1

        # Invalidate by prefix
        deleted = await cache.invalidate_prefix("admin:")
        assert deleted >= 1
        assert await cache.r.exists("admin:flags") == 0
