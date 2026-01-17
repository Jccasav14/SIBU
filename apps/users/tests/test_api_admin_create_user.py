def test_admin_create_user_200(client):
    r = client.post(
        "/users",
        json={"email": "new@test.com", "role": "student", "full_name": "Nuevo"},
        headers={"Authorization": "Bearer ADMIN"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == "new@test.com"
    assert body["role"] == "student"
    assert body["temp_password"] == "TEMP-123"
