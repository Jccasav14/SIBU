def test_protected_without_token_401(client):
    r = client.get("/cases")
    assert r.status_code == 401
    assert r.json()["detail"] == "Falta Authorization header"


def test_invalid_token_401(client):
    r = client.get("/cases", headers={"Authorization": "Bearer not-a-jwt"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Token inválido o expirado"
