import os
import pytest
from fastapi import HTTPException
from jose import jwt as jose_jwt

from app.security.jwt import decode_token, require_admin, require_admin_or_insurance


def _make_token(role: str = "admin", secret: str | None = None) -> str:
    if secret is None:
        secret = os.environ.get("JWT_SECRET", "TEST_SECRET_COVERAGE")
    payload = {"role": role, "sub": "u1", "exp": 9999999999}
    return jose_jwt.encode(payload, secret, algorithm=os.environ.get("JWT_ALGORITHM", "HS256"))


def test_decode_token_invalid_raises_401():
    with pytest.raises(HTTPException) as e:
        decode_token("not-a-jwt")
    assert e.value.status_code == 401
    assert e.value.detail == "Invalid token"


def test_require_admin_or_insurance_allows_admin():
    payload = {"role": "admin"}
    assert require_admin_or_insurance(payload=payload) == payload


def test_require_admin_or_insurance_denies_other_role_403():
    with pytest.raises(HTTPException) as e:
        require_admin_or_insurance(payload={"role": "student"})
    assert e.value.status_code == 403
    assert e.value.detail == "Forbidden"


def test_require_admin_denies_insurance_403():
    with pytest.raises(HTTPException) as e:
        require_admin(payload={"role": "insurance"})
    assert e.value.status_code == 403
    assert e.value.detail == "Forbidden"
