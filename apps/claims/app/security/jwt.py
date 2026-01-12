from __future__ import annotations

from typing import Any, Dict

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from ..settings import settings

bearer = HTTPBearer(auto_error=False)


def _forbidden(detail: str = "Forbidden") -> None:
    raise HTTPException(status_code=403, detail=detail)


def _unauthorized(detail: str = "Unauthorized") -> None:
    raise HTTPException(status_code=401, detail=detail)


def decode_jwt(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as e:
        _unauthorized(f"Invalid token: {str(e)}")


def require_insurance_or_admin(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> Dict[str, Any]:
    if creds is None or not creds.credentials:
        _unauthorized("Missing bearer token")

    payload = decode_jwt(creds.credentials)
    role = payload.get("role")
    email = payload.get("email")

    if not role or not email:
        _unauthorized("Token missing required claims")

    if role not in ("insurance", "admin"):
        _forbidden("This service is restricted to insurance and admin roles")

    return {"email": email, "role": role, "raw": payload}
