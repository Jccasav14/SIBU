import pytest
from fastapi import HTTPException

from apps.claims.app.security.jwt import decode_jwt, require_insurance_or_admin


def test_decode_jwt_invalid_raises_401():
    with pytest.raises(HTTPException) as e:
        decode_jwt("not-a-jwt")
    assert e.value.status_code == 401


def test_require_insurance_or_admin_missing_token_401():
    with pytest.raises(HTTPException) as e:
        require_insurance_or_admin(creds=None)
    assert e.value.status_code == 401
    assert e.value.detail == "Missing bearer token"


def test_require_insurance_or_admin_missing_claims_401(monkeypatch):
    # patch decode_jwt to return missing role/email
    monkeypatch.setattr("apps.claims.app.security.jwt.decode_jwt", lambda _t: {"role": "admin"})
    with pytest.raises(HTTPException) as e:
        require_insurance_or_admin(creds=type("C", (), {"credentials": "x"})())
    assert e.value.status_code == 401
    assert e.value.detail == "Token missing required claims"


def test_require_insurance_or_admin_wrong_role_403(monkeypatch):
    monkeypatch.setattr("apps.claims.app.security.jwt.decode_jwt", lambda _t: {"email": "x", "role": "student"})
    with pytest.raises(HTTPException) as e:
        require_insurance_or_admin(creds=type("C", (), {"credentials": "x"})())
    assert e.value.status_code == 403
    assert e.value.detail == "This service is restricted to insurance and admin roles"
