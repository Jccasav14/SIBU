import pytest
from pydantic import ValidationError

from apps.auth.app.api.schemas import UserRegister, UserLogin


def test_user_register_accepts_valid_email():
    m = UserRegister(email="a@b.com", password="Sibu12345", role="admin")
    assert m.email == "a@b.com"


def test_user_register_rejects_invalid_email():
    with pytest.raises(ValidationError):
        UserRegister(email="no-es-email", password="Sibu12345", role="admin")


def test_user_register_rejects_short_password():
    with pytest.raises(ValidationError):
        UserRegister(email="a@b.com", password="1234567", role="admin")


def test_user_login_valid():
    m = UserLogin(email="user@sibu.ec", password="Sibu12345")
    assert m.email == "user@sibu.ec"
