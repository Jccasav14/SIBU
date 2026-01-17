import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from apps.users.app.api import routes as routes_mod


class FakeProfile:
    def __init__(self, email: str, is_active: bool = True, **kwargs):
        self.email = email
        self.is_active = is_active
        for k, v in kwargs.items():
            setattr(self, k, v)


class FakeProfileService:
    def __init__(self, db):  # db ignored
        self.db = db
        self.repo = self  # para admin_create_user cuando llama svc.repo.create(...)

    async def get_or_create_me(self, email: str):
        return {
            "email": email,
            "full_name": None,
            "phone": None,
            "career": None,
            "bio": None,
            "area": None,
            "is_active": True,
        }

    async def update_me(self, email: str, data: dict):
        base = await self.get_or_create_me(email)
        base.update(data)
        return base

    async def get_by_email(self, email: str):
        # simula encontrado
        return {
            "email": email,
            "full_name": "Test User",
            "phone": None,
            "career": None,
            "bio": None,
            "area": None,
            "is_active": True,
        }

    async def set_active(self, email: str, active: bool):
        return FakeProfile(email=email, is_active=active)

    async def create(self, email: str, is_active: bool = True):
        return FakeProfile(email=email, is_active=is_active)


class FakeHTTPXResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


class FakeAsyncClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, json=None, headers=None):
        # simula auth/admin/users devolviendo temp_password
        return FakeHTTPXResponse(status_code=200, payload={"temp_password": "TEMP-123"})


@pytest.fixture()
def app(monkeypatch) -> FastAPI:
    app = FastAPI()
    app.include_router(routes_mod.router)

    # 1) mock DB dependency (no toca Postgres)
    async def fake_get_db():
        yield object()

    monkeypatch.setattr(routes_mod, "get_db", fake_get_db)

    # 2) mock ProfileService
    monkeypatch.setattr(routes_mod, "ProfileService", FakeProfileService)

    # 3) mock auth deps
    def fake_require_role(*roles):
        def _dep():
            return None
        return _dep

    def fake_get_current_user():
        return {"email": "me@test.com", "role": "admin"}

    monkeypatch.setattr(routes_mod, "require_role", fake_require_role)
    monkeypatch.setattr(routes_mod, "get_current_user", fake_get_current_user)

    # 4) mock httpx AsyncClient (no red)
    monkeypatch.setattr(routes_mod.httpx, "AsyncClient", FakeAsyncClient)

    return app


@pytest.fixture()
def client(app: FastAPI) -> TestClient:
    return TestClient(app)
