def test_audit_proxy_without_token_401(client):
    r = client.get("/reports/audit")
    assert r.status_code == 401


def test_audit_proxy_admin_routes_to_audit_events(client, make_token):
    token = make_token(role="admin")
    r = client.get("/reports/audit?limit=10", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["path"] == "/audit/events"
    assert "Bearer" in body["auth"]


def test_export_without_token_401(client):
    r = client.post("/reports/export", json={"type": "cases", "from": "2025-01-01", "to": "2025-01-02", "format": "csv"})
    assert r.status_code == 401


def test_export_invalid_payload_422(client, make_token):
    token = make_token(role="admin")
    r = client.post("/reports/export", headers={"Authorization": f"Bearer {token}"}, json={"type": "cases"})
    assert r.status_code == 422
