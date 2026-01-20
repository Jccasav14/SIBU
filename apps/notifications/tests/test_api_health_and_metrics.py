def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_metrics_ok(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    # Prometheus text format usually includes HELP/TYPE lines
    assert "python" in r.text.lower() or "process" in r.text.lower() or "http" in r.text.lower()
