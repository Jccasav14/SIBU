from apps.users.tests.conftest import FakeProfileService


def test_get_by_email_404(client):
    r = client.get("/users/nope@test.com")
    assert r.status_code == 404


def test_get_by_email_200(client):
    # Pre-carga perfil fake
    FakeProfileService.store["a@b.com"] = FakeProfileService.store.get("a@b.com") or None
    # Llama /users para crearlo (más realista)
    client.get("/users/me")

    r = client.get("/users/me@test.com")  # current user fake email
    assert r.status_code == 200, r.text
    assert r.json()["email"] == "me@test.com"


def test_set_active_patch(client):
    r = client.patch("/users/x@test.com/active?active=false")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["email"] == "x@test.com"
    assert body["is_active"] is False

    r2 = client.patch("/users/x@test.com/active?active=true")
    assert r2.status_code == 200, r2.text
    assert r2.json()["is_active"] is True


def test_set_user_status(client):
    r = client.patch("/users/z@test.com/status", json={"status": "disabled"})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "disabled"

    r2 = client.patch("/users/z@test.com/status", json={"status": "active"})
    assert r2.status_code == 200, r2.text
    assert r2.json()["status"] == "active"


def test_set_professional_status(client):
    r = client.patch("/professionals/p@test.com/status", json={"status": "disabled"})
    assert r.status_code == 200, r.text
    assert r.json()["email"] == "p@test.com"
    assert r.json()["status"] == "disabled"
