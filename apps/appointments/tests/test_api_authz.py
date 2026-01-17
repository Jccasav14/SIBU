from datetime import datetime, timedelta, timezone


def test_protected_endpoint_without_token_401(client):
    r = client.get("/availability")
    assert r.status_code in (401, 403)


def test_protected_endpoint_with_invalid_token_401(client):
    r = client.get("/availability", headers={"Authorization": "Bearer not-a-jwt"})
    assert r.status_code == 401


def test_protected_endpoint_with_wrong_role_403(client, make_token):
    token = make_token(email="student@test.com", role="student")
    r = client.get("/availability", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
    assert r.json().get("detail") in ("Insufficient permissions",)


def test_list_availability_with_valid_token_200_empty(client, make_token):
    token = make_token(email="pro1@test.com", role="professional")
    r = client.get("/availability", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json() == []


def test_create_availability_invalid_timerange_422(client, make_token):
    token = make_token(email="pro1@test.com", role="professional")
    starts = datetime.now(timezone.utc) + timedelta(hours=1)
    ends = starts - timedelta(minutes=1)

    payload = {
        "area": "PSYCHOLOGY",
        "location": "X",
        "starts_at": starts.isoformat(),
        "ends_at": ends.isoformat(),
    }
    r = client.post("/availability", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 422
    assert r.json().get("detail") == "ends_at must be greater than starts_at"
