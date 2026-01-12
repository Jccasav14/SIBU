from __future__ import annotations

from typing import Any

import httpx

from ..settings import settings


async def users_health() -> dict[str, Any]:
    if not settings.USERS_URL:
        return {"available": False, "reason": "USERS_URL not configured"}
    url = settings.USERS_URL.rstrip("/") + "/health"
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            r = await client.get(url)
            return {"available": r.status_code < 500, "status_code": r.status_code}
    except Exception as e:
        return {"available": False, "reason": str(e)}


async def patch_status(
    *,
    kind: str,
    email: str,
    status: str,
    auth_header: str | None,
) -> dict[str, Any]:
    """Best-effort call to users service to change status.

    kind: "user" or "professional"
    """
    if not settings.USERS_URL:
        return {"ok": False, "reason": "USERS_URL not configured"}

    if kind == "user":
        path = settings.USERS_PATCH_USER_STATUS_ENDPOINT
    else:
        path = settings.USERS_PATCH_PROFESSIONAL_STATUS_ENDPOINT

    url = settings.USERS_URL.rstrip("/") + path.format(email=email)
    headers: dict[str, str] = {}
    if auth_header:
        headers["Authorization"] = auth_header
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            r = await client.patch(url, json={"status": status}, headers=headers)
            if r.status_code >= 500:
                return {"ok": False, "status_code": r.status_code, "detail": "users service error"}
            try:
                data = r.json()
            except Exception:
                data = {"text": r.text}
            return {"ok": r.is_success, "status_code": r.status_code, "data": data}
    except Exception as e:
        return {"ok": False, "reason": str(e)}
