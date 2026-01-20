def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True, "service": "claims"}


def test_metrics_ok(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    assert isinstance(r.text, str)
    assert len(r.text) > 0
