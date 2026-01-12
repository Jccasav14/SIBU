from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_cache_set_get_and_invalidation(admin_token, insurance_token, redis):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        payload = {
            "claim_type": "ILLNESS",
            "name": "Illness Basic",
            "description": "Basic illness coverage",
            "max_coverage_amount": 50,
            "currency": "USD",
            "requires_documents": [],
            "waiting_days": 2,
            "is_active": True,
            "valid_from": "2026-01-01",
            "valid_to": None,
        }
        create = await ac.post("/coverage", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
        assert create.status_code == 201
        policy_id = create.json()["id"]

        # list should set cache
        res1 = await ac.get("/coverage", headers={"Authorization": f"Bearer {insurance_token}"})
        assert res1.status_code == 200
        assert await redis.get("coverage:list") is not None

        # item should set cache
        res2 = await ac.get(f"/coverage/{policy_id}", headers={"Authorization": f"Bearer {insurance_token}"})
        assert res2.status_code == 200
        assert await redis.get(f"coverage:item:{policy_id}") is not None

        # type should set cache
        res3 = await ac.get("/coverage/by-claim-type/ILLNESS", headers={"Authorization": f"Bearer {insurance_token}"})
        assert res3.status_code == 200
        assert await redis.get("coverage:type:ILLNESS") is not None

        # creating another policy invalidates list + type prefix
        payload2 = {
            "claim_type": "OTHER",
            "name": "Other Basic",
            "description": "Other coverage",
            "max_coverage_amount": 10,
            "currency": "USD",
            "requires_documents": [],
            "waiting_days": 0,
            "is_active": True,
            "valid_from": "2026-01-01",
            "valid_to": None,
        }
        res4 = await ac.post("/coverage", json=payload2, headers={"Authorization": f"Bearer {admin_token}"})
        assert res4.status_code == 201

        assert await redis.get("coverage:list") is None
        # old illness type cache invalidated by prefix delete, should be removed
        assert await redis.get("coverage:type:ILLNESS") is None
