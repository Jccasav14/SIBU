import pytest
from fastapi import HTTPException

from apps.audit_log.app.security.jwt import _decode, require_admin, require_role
from apps.audit_log.app.api.routes import _parse_dt


def test_parse_dt_none_returns_none():
    assert _parse_dt(None) is None


def test_parse_dt_invalid_raises_400():
    with pytest.raises(HTTPException) as e:
        _parse_dt("NOT_A_DATE")
    assert e.value.status_code == 400


def test_decode_invalid_token_401():
    with pytest.raises(HTTPException) as e:
        _decode("not-a-jwt")
    assert e.value.status_code == 401
    assert e.value.detail in ("Token inválido", "Token expirado")


def test_require_role_blocks_wrong_role():
    dep = require_role("admin")
    user = type("U", (), {"email": "p@u.edu", "role": "professional"})()
    with pytest.raises(HTTPException) as e:
        dep(user=user)  # bypass Depends by passing explicitly
    assert e.value.status_code == 403
    assert e.value.detail == "Access denied"


def test_require_admin_only_admin():
    user_ok = type("U", (), {"email": "a@u.edu", "role": "admin"})()
    user_no = type("U", (), {"email": "p@u.edu", "role": "professional"})()

    assert require_admin(user_ok).role == "admin"
    with pytest.raises(HTTPException) as e:
        require_admin(user_no)
    assert e.value.status_code == 403
