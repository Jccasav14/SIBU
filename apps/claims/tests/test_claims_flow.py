from datetime import datetime, timezone

import pytest


@pytest.mark.asyncio
async def test_claim_lifecycle_approve_pay(client, make_token):
    token = make_token("insurance", email="ins@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create = {
        "student_id": "0102030405",
        "claim_type": "ACCIDENT",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "reported_at": datetime.now(timezone.utc).isoformat(),
        "description": "Broken leg injury",
        "requested_amount": 80,
        "coverage_cap": 100
    }
    r = await client.post("/claims", json=create, headers=headers)
    assert r.status_code == 200
    claim = r.json()
    assert claim["status"] == "DRAFT"
    cid = claim["id"]

    # patch draft
    r = await client.patch(f"/claims/{cid}", json={"requested_amount": 90}, headers=headers)
    assert r.status_code == 200

    # submit
    r = await client.post(f"/claims/{cid}/submit", headers=headers)
    assert r.status_code == 200
    assert r.json()["status"] == "SUBMITTED"

    # approve
    r = await client.post(f"/claims/{cid}/review", json={"decision": "APPROVE", "approved_amount": 95}, headers=headers)
    assert r.status_code == 200
    assert r.json()["status"] == "APPROVED"

    # pay
    r = await client.post(f"/claims/{cid}/payment", json={"payment_method": "BANK_TRANSFER", "payment_reference": "REF-123"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["status"] == "CLOSED"
    assert r.json()["payment_status"] == "PAID"


@pytest.mark.asyncio
async def test_claim_reject_closes_later(client, make_token):
    token = make_token("admin", email="admin@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create = {
        "student_id": "STU-2",
        "claim_type": "FAMILY_DEATH",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "reported_at": datetime.now(timezone.utc).isoformat(),
        "description": "Family death support",
        "requested_amount": 100,
        "coverage_cap": 100
    }
    r = await client.post("/claims", json=create, headers=headers)
    cid = r.json()["id"]

    await client.post(f"/claims/{cid}/submit", headers=headers)
    r = await client.post(f"/claims/{cid}/review", json={"decision": "REJECT", "notes": "Not covered"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["status"] == "REJECTED"
