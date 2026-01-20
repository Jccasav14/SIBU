def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["service"] == "reports"
    assert "env" in body


def test_metrics_ok(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "python" in r.text.lower() or "process" in r.text.lower()
