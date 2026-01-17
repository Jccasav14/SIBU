def test_requires_auth_missing_token_401(client):
    r = client.get("/catalog/areas")
    assert r.status_code == 401
    assert r.json()["detail"] == "Falta Authorization Bearer token"


def test_requires_admin_professional_403(client, make_token):
    token = make_token(email="pro@test.com", role="professional")
    r = client.get("/admin/catalog/areas", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
    assert r.json()["detail"] == "Access denied"


def test_invalid_token_401(client):
    r = client.get("/catalog/areas", headers={"Authorization": "Bearer nope"})
    assert r.status_code == 401
    assert r.json()["detail"] in ("Token inválido", "Token expirado", "Token sin claims requeridos")
