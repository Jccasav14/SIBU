import pytest
from fastapi import HTTPException

from apps.appointments.app.infrastructure.security.auth import (
    _extract_email,
    get_current_user,
    require_roles,
)
from apps.appointments.app.settings import settings


def test_extract_email_prefers_email():
    assert _extract_email({"email": "a@b.com", "sub": "x@y.com"}) == "a@b.com"


def test_extract_email_falls_back_to_sub():
    assert _extract_email({"sub": "x@y.com"}) == "x@y.com"


def test_extract_email_strips_whitespace():
    assert _extract_email({"email": "  a@b.com  "}) == "a@b.com"


def test_get_current_user_auth_disabled(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_DISABLED", True)
    u = get_current_user(None)  # bearer auto_error=False => can be None
    assert u.email == "dev@local"
    assert u.role == "admin"
    monkeypatch.setattr(settings, "AUTH_DISABLED", False)


def test_get_current_user_missing_bearer_401(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_DISABLED", False)
    with pytest.raises(HTTPException) as e:
        get_current_user(None)
    assert e.value.status_code == 401


def test_require_roles_allows_admin_when_auth_disabled(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_DISABLED", True)
    dep = require_roles("admin")
    # bypass Depends by passing user explicitly
    u = dep(user=get_current_user(None))
    assert u.role == "admin"
    monkeypatch.setattr(settings, "AUTH_DISABLED", False)


def test_require_roles_denies_non_allowed_role(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_DISABLED", True)
    dep = require_roles("professional")  # admin shouldn't be allowed here if strict
    with pytest.raises(HTTPException) as e:
        dep(user=get_current_user(None))
    assert e.value.status_code == 403
    monkeypatch.setattr(settings, "AUTH_DISABLED", False)
