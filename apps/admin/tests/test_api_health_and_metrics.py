def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["service"] == "admin"


def test_metrics_ok(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    assert isinstance(r.text, str)
    assert len(r.text) > 0


def test_404_unknown_route(client):
    r = client.get("/__nope__")
    assert r.status_code == 404
