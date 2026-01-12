from datetime import datetime, timezone

import pytest


@pytest.mark.asyncio
async def test_documents_add_list(client, make_token):
    token = make_token("insurance")
    headers = {"Authorization": f"Bearer {token}"}

    create = {
        "student_id": "STU-DOC",
        "claim_type": "ILLNESS",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "reported_at": datetime.now(timezone.utc).isoformat(),
        "description": "Illness reimbursement",
        "requested_amount": 50,
        "coverage_cap": 100
    }
    r = await client.post("/claims", json=create, headers=headers)
    cid = r.json()["id"]

    doc = {
        "doc_type": "medical_report",
        "file_url": "s3://bucket/path/report.pdf",
        "file_hash": "hash12345678"
    }
    r = await client.post(f"/claims/{cid}/documents", json=doc, headers=headers)
    assert r.status_code == 200

    r = await client.get(f"/claims/{cid}/documents", headers=headers)
    assert r.status_code == 200
    docs = r.json()
    assert len(docs) == 1
    assert docs[0]["file_hash"] == "hash12345678"
