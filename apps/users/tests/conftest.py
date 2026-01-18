import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from apps.users.app.api import routes as routes_mod


# -----------------------------
# Fakes para API tests
# -----------------------------
class FakeProfile:
    def __init__(self, email: str, is_active: bool = True, **kwargs):
        self.email = email
        self.is_active = is_active
        self.full_name = kwargs.get("full_name")
        self.phone = kwargs.get("phone")
        self.career = kwargs.get("career")
        self.bio = kwargs.get("bio")
        self.area = kwargs.get("area")


class FakeProfileService:
    """
    Simula ProfileService sin DB real.
    routes.py instancia ProfileService(db) dentro de cada handler,
    así que parcheamos ProfileService por esta clase.
    """

    # "DB" en memoria por email
    store: dict[str, FakeProfile] = {}

    def __init__(self, db):
        self.db = db
        self.repo = self  # para admin_create_user que llama svc.repo.create(...)

    async def get_or_create_me(self, email: str):
        prof = self.store.get(email)
        if not prof:
            prof = FakeProfile(email=email, is_active=True)
            self.store[email] = prof
        return prof

    async def update_me(self, email: str, data: dict):
        prof = self.store.get(email)
        if not prof:
            prof = FakeProfile(email=email, is_active=True)
            self.store[email] = prof
        for k, v in data.items():
            setattr(prof, k, v)
        return prof

    async def get_by_email(self, email: str):
        return self.store.get(email)

    async def set_active(self, email: str, active: bool):
        prof = self.store.get(email)
        if not prof:
            prof = FakeProfile(email=email, is_active=active)
            self.store[email] = prof
        prof.is_active = active
        return prof

    async def create(self, email: str, is_active: bool = True):
        prof = FakeProfile(email=email, is_active=is_active)
        self.store[email] = prof
        return prof


class FakeHTTPXResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


class FakeAsyncClient:
    """
    Simula httpx.AsyncClient sin red.
    Guarda la última request para asserts si quieres.
    """
    last_url = None
    last_json = None
    last_headers = None
    next_status_code = 200
    next_payload = {"temp_password": "TEMP-123"}
    next_text = ""

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, json=None, headers=None):
        FakeAsyncClient.last_url = url
        FakeAsyncClient.last_json = json
        FakeAsyncClient.last_headers = headers
        return FakeHTTPXResponse(
            status_code=FakeAsyncClient.next_status_code,
            payload=FakeAsyncClient.next_payload,
            text=FakeAsyncClient.next_text,
        )


@pytest.fixture()
def app(monkeypatch) -> FastAPI:
    # App mínima: solo router de users (evita startup de main.py)
    app = FastAPI()
    app.include_router(routes_mod.router)

    # 1) override DB dependency
    async def override_get_db():
        yield object()

    app.dependency_overrides[routes_mod.get_db] = override_get_db

    # 2) override current user
    def override_get_current_user():
        return {"email": "me@test.com", "role": "admin"}

    app.dependency_overrides[routes_mod.get_current_user] = override_get_current_user

    # 3) override roles (factory -> callable)
    # FastAPI usa Depends(require_role("...")) donde require_role retorna un callable.
    # Para que no bloquee, interceptamos la factory y overrideamos cada callable creado.
    original_require_role = routes_mod.require_role

    def patched_require_role(*roles):
        dep = original_require_role(*roles)

        def allow_any_role():
            return None

        app.dependency_overrides[dep] = allow_any_role
        return dep

    monkeypatch.setattr(routes_mod, "require_role", patched_require_role)

    # 4) fake ProfileService
    FakeProfileService.store = {}  # limpia entre tests
    monkeypatch.setattr(routes_mod, "ProfileService", FakeProfileService)

    # 5) fake httpx AsyncClient
    FakeAsyncClient.next_status_code = 200
    FakeAsyncClient.next_payload = {"temp_password": "TEMP-123"}
    FakeAsyncClient.next_text = ""
    FakeAsyncClient.last_url = None
    FakeAsyncClient.last_json = None
    FakeAsyncClient.last_headers = None
    monkeypatch.setattr(routes_mod.httpx, "AsyncClient", FakeAsyncClient)

    yield app

    app.dependency_overrides = {}


@pytest.fixture()
def client(app: FastAPI) -> TestClient:
    return TestClient(app)
