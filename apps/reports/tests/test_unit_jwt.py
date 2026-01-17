import pytest
from fastapi import HTTPException


def test_require_auth_missing_token_401():
    from apps.reports.app.security.jwt import require_auth

    with pytest.raises(HTTPException) as e:
        require_auth(None)  # type: ignore[arg-type]
    assert e.value.status_code == 401


def test_require_auth_invalid_token_401():
    from apps.reports.app.security.jwt import require_auth
    from fastapi.security import HTTPAuthorizationCredentials

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="not-a-jwt")
    with pytest.raises(HTTPException) as e:
        require_auth(creds)
    assert e.value.status_code == 401


def test_require_auth_valid_token_ok(make_token):
    from apps.reports.app.security.jwt import require_auth
    from fastapi.security import HTTPAuthorizationCredentials

    token = make_token(email="u@e.com", role="admin")
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    u = require_auth(creds)
    assert u.email == "u@e.com"
    assert u.role == "admin"
