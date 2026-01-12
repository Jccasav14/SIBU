from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Callable

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..settings import settings


bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthUser:
    email: str
    role: str


def require_auth(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> AuthUser:
    if creds is None:
        raise HTTPException(status_code=401, detail="Missing token")

    token = creds.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    email = payload.get("email")
    role = payload.get("role")
    if not email or not role:
        raise HTTPException(status_code=401, detail="Invalid token claims")

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
