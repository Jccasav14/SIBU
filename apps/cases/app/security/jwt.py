import os
from dataclasses import dataclass
from typing import Any, Optional

import jwt
from jwt import PyJWTError
from fastapi import HTTPException, status

@dataclass
class CurrentUser:
    user_id: str
    roles: list[str]
    area: str | None = None

def _get_secret() -> str:
    return os.getenv("JWT_SECRET") or "SIBU_SUPER_SECRET_CAMBIAME"

def _get_alg() -> str:
    return os.getenv("JWT_ALGORITHM") or "HS256"

def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, _get_secret(), algorithms=[_get_alg()])
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )

def get_current_user_from_payload(payload: dict[str, Any]) -> CurrentUser:
    # Acepta sub/user_id (ideal) y si no existe, usa email (tu auth actual)
    user_id = payload.get("sub") or payload.get("user_id") or payload.get("email")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token sin 'sub' ni 'email'")

    # roles puede venir como lista (roles) o string (role)
    roles = payload.get("roles") or payload.get("role") or []
    if isinstance(roles, str):
        roles = [roles]

    area = payload.get("area") or payload.get("department") or payload.get("unit")
    if area is not None:
        area = str(area)
    return CurrentUser(user_id=str(user_id), roles=[str(r) for r in roles], area=area)
