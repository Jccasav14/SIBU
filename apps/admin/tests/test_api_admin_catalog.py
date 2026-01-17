def test_admin_list_areas_ok(client, make_token):
    token = make_token(role="admin")
    r = client.get("/admin/catalog/areas", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_admin_create_area_422_invalid_payload(client, make_token):
    token = make_token(role="admin")
    r = client.post("/admin/catalog/areas", json={"name": ""}, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 422


def test_admin_create_area_409_conflict(client, make_token):
    token = make_token(role="admin")
    client.fake_repo.raise_integrity_on_create_area = True
    r = client.post("/admin/catalog/areas", json={"name": "DUP", "enabled": True}, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 409
    assert r.json()["detail"] == "Área ya existe"
    client.fake_repo.raise_integrity_on_create_area = False


def test_admin_patch_area_404_when_missing(client, make_token):
    token = make_token(role="admin")
    r = client.patch("/admin/catalog/areas/999", json={"enabled": True}, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 404
    assert r.json()["detail"] == "No encontrado"
