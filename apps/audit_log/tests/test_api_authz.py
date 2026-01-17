def test_admin_endpoint_missing_token_401(client):
    r = client.get("/audit/events")
    assert r.status_code == 401
    assert r.json()["detail"] == "Falta Authorization Bearer token"


def test_invalid_token_401(client):
    r = client.get("/audit/events", headers={"Authorization": "Bearer nope"})
    assert r.status_code == 401
    assert r.json()["detail"] in ("Token inválido", "Token expirado", "Token sin claims requeridos")


def test_wrong_role_403(client, make_token):
    token = make_token(email="pro@u.edu", role="professional")
    r = client.get("/audit/events", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
    assert r.json()["detail"] == "Access denied"
