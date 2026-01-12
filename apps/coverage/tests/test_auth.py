from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_missing_token_401():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        res = await ac.get("/coverage")
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_professional_forbidden_403(professional_token):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        res = await ac.get("/coverage", headers={"Authorization": f"Bearer {professional_token}"})
        assert res.status_code == 403


@pytest.mark.asyncio
async def test_insurance_read_only(insurance_token, admin_token):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # insurance can read
        res = await ac.get("/coverage", headers={"Authorization": f"Bearer {insurance_token}"})
        assert res.status_code == 200

        # insurance cannot create
        payload = {
            "claim_type": "ACCIDENT",
            "name": "Accident Basic",
            "description": "Basic accident coverage",
            "max_coverage_amount": 100,
            "currency": "USD",
            "requires_documents": ["invoice"],
            "waiting_days": 0,
            "is_active": True,
            "valid_from": "2026-01-01",
            "valid_to": "2026-12-31",
        }
        res2 = await ac.post("/coverage", json=payload, headers={"Authorization": f"Bearer {insurance_token}"})
        assert res2.status_code == 403

        # admin can create
        res3 = await ac.post("/coverage", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
        assert res3.status_code == 201
