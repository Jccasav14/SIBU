import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .jwt import decode_token, get_current_user_from_payload, CurrentUser

bearer_scheme = HTTPBearer(auto_error=False)

def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUser:
    if os.getenv("AUTH_DISABLED", "false").lower() == "true":
        return CurrentUser(user_id="dev-user", roles=["admin"])

    if creds is None or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta Authorization header",
        )

    token = creds.credentials
    payload = decode_token(token)

    return get_current_user_from_payload(payload)

def require_roles(*required: str):
    def _checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not required:
            return user
        if any(r in user.roles for r in required):
            return user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    return _checker
