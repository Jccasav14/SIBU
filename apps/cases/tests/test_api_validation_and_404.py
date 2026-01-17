def test_create_case_invalid_payload_422(client, make_token):
    token = make_token()
    r = client.post(
        "/cases",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "student_id": "s6",
            "owner_area": "PSY",
            "title": "x",  # too short (min 3)
            "description": "ok",
            "priority": "LOW",
        },
    )
    assert r.status_code == 422


def test_get_case_not_found_404(client, make_token):
    token = make_token()
    r = client.get("/cases/does-not-exist", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 404


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
