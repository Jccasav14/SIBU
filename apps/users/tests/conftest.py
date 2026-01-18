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

    # -----------------------------
    # 1) Override DB dependency
    # -----------------------------
    async def override_get_db():
        yield object()

    # OJO: aquí asumimos que el router usa routes_mod.get_db como dependencia
    app.dependency_overrides[routes_mod.get_db] = override_get_db

    # -----------------------------
    # 2) Mock ProfileService class
    # -----------------------------
    monkeypatch.setattr(routes_mod, "ProfileService", FakeProfileService)

    # -----------------------------
    # 3) Override auth deps (FastAPI-friendly)
    # -----------------------------
    # get_current_user suele ser una dependencia directa en Depends(...)
    def override_get_current_user():
        return {"email": "me@test.com", "role": "admin"}

    app.dependency_overrides[routes_mod.get_current_user] = override_get_current_user

    # require_role es tricky porque normalmente se usa así: Depends(require_role("admin"))
    # Entonces overrideamos la "factory" para que devuelva una dependencia que SIEMPRE pase.
    original_require_role = routes_mod.require_role

    def patched_require_role(*roles):
        dep = original_require_role(*roles)

        # Override específico para ESE callable dep
        # (FastAPI guarda el callable que retorna la factory, así que overrideamos ese)
        def allow_any_role():
            return None

        app.dependency_overrides[dep] = allow_any_role
        return dep

    monkeypatch.setattr(routes_mod, "require_role", patched_require_role)

    # -----------------------------
    # 4) Mock httpx AsyncClient (no red)
    # -----------------------------
    monkeypatch.setattr(routes_mod.httpx, "AsyncClient", FakeAsyncClient)

    yield app

    # cleanup
    app.dependency_overrides = {}


@pytest.fixture()
def client(app: FastAPI) -> TestClient:
    return TestClient(app)
