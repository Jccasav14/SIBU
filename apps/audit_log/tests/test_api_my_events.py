def test_my_events_admin_gets_400_use_events(client, make_token):
    token = make_token(role="admin")
    r = client.get("/audit/mine", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 400
    assert r.json()["detail"] == "Usa /audit/events"


def test_my_events_professional_feature_disabled_403(client, make_token):
    token = make_token(email="pro@u.edu", role="professional")
    r = client.get("/audit/mine", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
    assert r.json()["detail"] == "Feature deshabilitado"


def test_my_events_requires_auth_401(client):
    r = client.get("/audit/mine")
    assert r.status_code == 401
