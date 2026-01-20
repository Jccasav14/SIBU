import pytest

from apps.auth.app.infrastructure.security.password import hash_password, verify_password


def test_hash_and_verify_password_ok():
    pwd = "Sibu123$"
    hashed = hash_password(pwd)

    assert isinstance(hashed, str)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True


def test_verify_password_fails_for_wrong_password():
    hashed = hash_password("correct")
    assert verify_password("wrong", hashed) is False
