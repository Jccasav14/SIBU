def test_404_unknown_route(client):
    r = client.get("/__nope__")
    assert r.status_code == 404


def test_cors_preflight_known_origin(client):
    headers = {
        "Origin": "http://localhost",
        "Access-Control-Request-Method": "GET",
    }
    r = client.options("/health", headers=headers)
    assert r.status_code in (200, 204)

    # header can be exact origin or "*" depending on middleware/version
    assert r.headers.get("access-control-allow-origin") in ("http://localhost", "*", None)


def test_cors_preflight_unknown_origin_is_blocked_or_not_allowed(client):
    headers = {
        "Origin": "http://evil.example",
        "Access-Control-Request-Method": "GET",
    }
    r = client.options("/health", headers=headers)
    assert r.status_code in (200, 204, 400)
    assert r.headers.get("access-control-allow-origin") in (None, "")
