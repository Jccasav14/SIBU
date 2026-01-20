import pytest
from fastapi import HTTPException

from apps.admin.app.security.jwt import require_auth, require_admin, require_role, _decode
from apps.admin.app.settings import settings


def test_decode_invalid_token_401():
    with pytest.raises(HTTPException) as e:
        _decode("not-a-jwt")
    assert e.value.status_code == 401
    assert e.value.detail in ("Token inválido", "Token expirado")


def test_require_auth_missing_creds_401():
    with pytest.raises(HTTPException) as e:
        require_auth(None)
    assert e.value.status_code == 401
    assert e.value.detail == "Falta Authorization Bearer token"


def test_require_role_blocks_wrong_role():
    # create a fake AuthUser-like object
    user = type("U", (), {"email": "x@test.com", "role": "professional"})()
    dep = require_role("admin")
    with pytest.raises(HTTPException) as e:
        dep(user=user)  # bypass Depends by passing explicitly
    assert e.value.status_code == 403
    assert e.value.detail == "Access denied"


def test_require_admin_only_admin():
    user_ok = type("U", (), {"email": "a@test.com", "role": "admin"})()
    user_no = type("U", (), {"email": "p@test.com", "role": "professional"})()
    assert require_admin(user_ok).role == "admin"

    with pytest.raises(HTTPException) as e:
        require_admin(user_no)
    assert e.value.status_code == 403
    assert e.value.detail == "Access denied"
