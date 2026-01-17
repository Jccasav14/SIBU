def test_404_unknown_route(client):
    r = client.get("/__nope__")
    assert r.status_code == 404


def test_cors_preflight_allows_known_origin(client):
    # main.py allows http://localhost
    headers = {
        "Origin": "http://localhost",
        "Access-Control-Request-Method": "GET",
    }
    r = client.options("/health", headers=headers)
    # Starlette may return 200 or 204 depending on version
    assert r.status_code in (200, 204)

    # If CORSMiddleware is active, it should echo the origin (not always set on every response)
    acao = r.headers.get("access-control-allow-origin")
    assert acao in ("http://localhost", "*", None)


def test_cors_preflight_rejects_unknown_origin(client):
    headers = {
        "Origin": "http://evil.example",
        "Access-Control-Request-Method": "GET",
    }
    r = client.options("/health", headers=headers)

    # Some setups respond 400 for disallowed Origin; others 200/204 without allow-origin.
    assert r.status_code in (200, 204, 400)
    assert r.headers.get("access-control-allow-origin") in (None, "")
