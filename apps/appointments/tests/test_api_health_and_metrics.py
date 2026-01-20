def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_metrics_ok(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    # Prometheus text format should include HELP/TYPE or at least some metric lines
    assert isinstance(r.text, str)
    assert len(r.text) > 0
