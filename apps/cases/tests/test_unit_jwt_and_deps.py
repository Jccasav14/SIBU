import os
import pytest
import jwt as pyjwt
from fastapi import HTTPException

from apps.cases.app.security.jwt import decode_token, get_current_user_from_payload
from apps.cases.app.security.deps import get_current_user, require_roles


def test_decode_token_invalid_401():
    with pytest.raises(HTTPException) as e:
        decode_token("nope")
    assert e.value.status_code == 401
    assert e.value.detail == "Token inválido o expirado"


def test_get_current_user_from_payload_accepts_role_string():
    u = get_current_user_from_payload({"email": "a@b.com", "role": "admin"})
    assert u.user_id == "a@b.com"
    assert u.roles == ["admin"]


def test_get_current_user_from_payload_requires_id():
    with pytest.raises(HTTPException) as e:
        get_current_user_from_payload({"role": "admin"})
    assert e.value.status_code == 401


def test_get_current_user_auth_disabled_returns_admin(monkeypatch):
    monkeypatch.setenv("AUTH_DISABLED", "true")
    u = get_current_user(None)
    assert u.user_id == "dev-user"
    assert "admin" in u.roles
    monkeypatch.setenv("AUTH_DISABLED", "false")


def test_require_roles_allows_and_denies(monkeypatch):
    user_admin = get_current_user_from_payload({"sub": "u1", "roles": ["admin"]})
    user_pro = get_current_user_from_payload({"sub": "u2", "roles": ["professional"]})

    dep = require_roles("admin")
    assert dep(user=user_admin).user_id == "u1"

    with pytest.raises(HTTPException) as e:
        dep(user=user_pro)
    assert e.value.status_code == 403
    assert e.value.detail == "No autorizado"


def test_token_roundtrip_decode_ok():
    token = pyjwt.encode(
        {"sub": "u1", "roles": ["admin"], "exp": 9999999999},
        os.environ.get("JWT_SECRET", "TEST_SECRET_CASES"),
        algorithm=os.environ.get("JWT_ALGORITHM", "HS256"),
    )
    payload = decode_token(token)
    assert payload["sub"] == "u1"
