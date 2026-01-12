from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Callable

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError

from apps.appointments.app.settings import settings

bearer = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    email: str
    role: str


def _extract_email(payload: dict) -> Optional[str]:
    # Support both patterns: payload['email'] (preferred) and payload['sub'] (common)
    email = payload.get("email") or payload.get("sub")
    if isinstance(email, str) and email.strip():
        return email.strip()
    return None


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> CurrentUser:
    if settings.AUTH_DISABLED:
        # Dev mode fallback
        return CurrentUser(email="dev@local", role="admin")

    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    email = _extract_email(payload)
    role = payload.get("role")

    if not email or not role:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    return CurrentUser(email=email, role=str(role))


def require_roles(*allowed_roles: str) -> Callable:
    allowed = {r.lower() for r in allowed_roles}

    def _dep(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role.lower() not in allowed:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

    return _dep
