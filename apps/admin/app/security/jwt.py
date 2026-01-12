from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Callable

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..settings import settings


bearer = HTTPBearer(auto_error=False)


@dataclass
class AuthUser:
    email: str
    role: str


def _decode(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")


def require_auth(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> AuthUser:
    if not creds or not creds.credentials:
        raise HTTPException(status_code=401, detail="Falta Authorization Bearer token")

    payload = _decode(creds.credentials)
    email = payload.get("email")
    role = payload.get("role")
    if not email or not role:
        raise HTTPException(status_code=401, detail="Token sin claims requeridos")
    return AuthUser(email=email, role=role)


def require_role(*roles: str) -> Callable[[AuthUser], AuthUser]:
    allowed = set(roles)

    def _dep(user: Annotated[AuthUser, Depends(require_auth)]) -> AuthUser:
        if user.role not in allowed:
            raise HTTPException(status_code=403, detail="Access denied")
        return user

    return _dep


def require_admin(user: Annotated[AuthUser, Depends(require_auth)]) -> AuthUser:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return user
