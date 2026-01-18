def test_get_me_200(client):
    r = client.get("/users/me")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["email"] == "me@test.com"
    assert body["is_active"] is True


def test_update_me_200(client):
    r = client.put(
        "/users/me",
        json={"full_name": "Juan", "bio": "Hola"},
        headers={"Authorization": "Bearer ANY"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["email"] == "me@test.com"
    assert body["full_name"] == "Juan"
    assert body["bio"] == "Hola"
