from datetime import datetime, timezone


def test_ingest_rest_requires_admin_403_for_professional(client, make_token):
    token = make_token(email="pro@u.edu", role="professional")
    payload = {"source": "kafka", "event_type": "x", "service": "auth"}
    r = client.post("/audit/events", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
    assert r.json()["detail"] == "Access denied"


def test_ingest_rest_invalid_payload_422(client, make_token):
    token = make_token(role="admin")
    # missing required: source + event_type
    r = client.post("/audit/events", json={"service": "auth"}, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 422


def test_ingest_rest_ok_forces_source_rest(client, make_token):
    token = make_token(role="admin")
    payload = {
        "source": "kafka",
        "event_type": "user.created",
        "service": "auth",
        "actor": "admin@u.edu",
        "actor_role": "admin",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload_raw": {"token": "LEAK?"},
    }
    r = client.post("/audit/events", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["source"] == "rest"
    assert data["payload_raw"]["token"] == "***REDACTED***"
    assert "event_id" in data


def test_export_csv_ok_and_has_header(client, make_token):
    token = make_token(role="admin")
    r = client.get("/audit/export.csv", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("text/csv")
    text = r.text
    assert "event_id,timestamp,received_at" in text.replace("\r\n", "\n").split("\n")[0]
