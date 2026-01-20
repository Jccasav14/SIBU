from datetime import date


def test_admin_endpoint_without_token_401(client):
    r = client.get("/reports/summary")
    assert r.status_code == 401


def test_admin_endpoint_with_non_admin_403(client, make_token):
    token = make_token(role="professional")
    r = client.get("/reports/summary", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_admin_endpoint_with_admin_200(client, make_token):
    token = make_token(role="admin")
    r = client.get("/reports/summary", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert "totals_by_service" in r.json()


def test_activity_requires_from_and_to_422(client, make_token):
    token = make_token(role="admin")
    r = client.get("/reports/activity", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 422


def test_top_actors_limit_validation_422(client, make_token):
    token = make_token(role="admin")
    r = client.get(
        "/reports/top-actors?from=2025-01-01&to=2025-01-02&limit=0",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 422
