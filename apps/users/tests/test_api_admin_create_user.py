from apps.users.tests.conftest import FakeAsyncClient, FakeProfileService


def test_admin_create_user_200(client):
    r = client.post(
        "/users",
        json={
            "email": "new@test.com",
            "role": "student",
            "area": "QA",
            "full_name": "Nuevo",
        },
        headers={"Authorization": "Bearer ADMIN"},
    )
    assert r.status_code == 200, r.text
    body = r.json()

    assert body["email"] == "new@test.com"
    assert body["role"] == "student"
    assert body["temp_password"] == "TEMP-123"

    # Verifica que pegó al auth y pasó el header
    assert FakeAsyncClient.last_url is not None
    assert "/auth/admin/users" in FakeAsyncClient.last_url
    assert FakeAsyncClient.last_headers["Authorization"] == "Bearer ADMIN"

    # Asegura que creó/actualizó perfil en "DB" fake
    prof = FakeProfileService.store.get("new@test.com")
    assert prof is not None
    assert prof.full_name == "Nuevo"
    assert prof.area == "QA"


def test_admin_create_user_propagates_auth_error(client):
    FakeAsyncClient.next_status_code = 401
    FakeAsyncClient.next_text = "Unauthorized"

    r = client.post(
        "/users",
        json={
            "email": "bad@test.com",
            "role": "student",
            "area": "QA",
            "full_name": "Bad",
        },
        headers={"Authorization": "Bearer BAD"},
    )
    assert r.status_code == 401
