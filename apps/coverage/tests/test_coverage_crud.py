from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_admin_crud_and_activate_deactivate(admin_token):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        payload = {
            "claim_type": "FAMILY_DEATH",
            "name": "Family Death",
            "description": "Family death coverage",
            "max_coverage_amount": 500,
            "currency": "USD",
            "requires_documents": ["death_certificate"],
            "waiting_days": 0,
            "is_active": True,
            "valid_from": "2026-01-01",
            "valid_to": "2026-12-31",
        }
        create = await ac.post("/coverage", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
        assert create.status_code == 201
        policy_id = create.json()["id"]

        patch = await ac.patch(
            f"/coverage/{policy_id}",
            json={"max_coverage_amount": 600},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert patch.status_code == 200
        assert float(patch.json()["max_coverage_amount"]) == 600.0

        deact = await ac.post(f"/coverage/{policy_id}/deactivate", headers={"Authorization": f"Bearer {admin_token}"})
        assert deact.status_code == 200
        assert deact.json()["is_active"] is False

        act = await ac.post(f"/coverage/{policy_id}/activate", headers={"Authorization": f"Bearer {admin_token}"})
        assert act.status_code == 200
        assert act.json()["is_active"] is True


@pytest.mark.asyncio
async def test_active_policy_overlap_validation(admin_token):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        payload1 = {
            "claim_type": "ACCIDENT",
            "name": "Accident A",
            "description": "Accident coverage A",
            "max_coverage_amount": 100,
            "currency": "USD",
            "requires_documents": [],
            "waiting_days": 0,
            "is_active": True,
            "valid_from": "2026-01-01",
            "valid_to": "2026-12-31",
        }
        res1 = await ac.post("/coverage", json=payload1, headers={"Authorization": f"Bearer {admin_token}"})
        assert res1.status_code == 201

        # Overlapping active policy should fail
        payload2 = {
            "claim_type": "ACCIDENT",
            "name": "Accident B",
            "description": "Accident coverage B",
            "max_coverage_amount": 120,
            "currency": "USD",
            "requires_documents": [],
            "waiting_days": 0,
            "is_active": True,
            "valid_from": "2026-06-01",
            "valid_to": "2027-01-01",
        }
        res2 = await ac.post("/coverage", json=payload2, headers={"Authorization": f"Bearer {admin_token}"})
        assert res2.status_code == 409

        # Non-overlapping active policy should work
        payload3 = {
            "claim_type": "ACCIDENT",
            "name": "Accident C",
            "description": "Accident coverage C",
            "max_coverage_amount": 130,
            "currency": "USD",
            "requires_documents": [],
            "waiting_days": 0,
            "is_active": True,
            "valid_from": "2027-01-02",
            "valid_to": None,
        }
        res3 = await ac.post("/coverage", json=payload3, headers={"Authorization": f"Bearer {admin_token}"})
        assert res3.status_code == 201
