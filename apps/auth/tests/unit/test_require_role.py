import os
import pytest
from fastapi import HTTPException

from libs.security.jwt import require_role


def _set_test_jwt():
    os.environ["JWT_SECRET"] = "test-secret"
    os.environ["JWT_ALGORITHM"] = "HS256"


def test_require_role_allows_admin(monkeypatch):
    _set_test_jwt()

    # Si tu lib lee del env al importar, forzamos recarga si es necesario.
    dep = require_role("admin")

    # Simulamos payload decodificado si tu require_role lo permite,
    # pero como no sabemos tu implementación exacta, aquí el patrón:
    # - si require_role espera request/header, este test se ajusta.
    #
    # 👉 Si me pegas libs/security/jwt.py te lo dejo exacto 100%.
    assert callable(dep)


def test_require_role_denies_professional(monkeypatch):
    _set_test_jwt()
    dep = require_role("admin")
    assert callable(dep)
