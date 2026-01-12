from __future__ import annotations

from typing import Any

import httpx

from ..settings import settings


async def emit_audit_event(
    *,
    auth_header: str | None,
    event_type: str,
    actor: str | None,
    actor_role: str | None,
    entity_type: str | None,
    entity_id: str | None,
    payload_raw: dict[str, Any] | None = None,
    payload_norm: dict[str, Any] | None = None,
    tags: list[str] | None = None,
    severity: str = "INFO",
) -> None:
    """Best-effort: send lightweight audit event to audit_log via REST.

    audit_log endpoint expects an admin JWT (currently require_admin). We forward the
    same Authorization header from the incoming request when available.
    """

    if not settings.AUDIT_LOG_URL:
        return
    url = settings.AUDIT_LOG_URL.rstrip("/") + "/audit/events"

    headers: dict[str, str] = {}
    if auth_header:
        headers["Authorization"] = auth_header

    body = {
        "source": "rest",
        "event_type": event_type,
        "service": settings.SERVICE_NAME,
        "actor": actor,
        "actor_role": actor_role,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "severity": severity,
        "tags": tags or [],
        "payload_raw": payload_raw or {},
        "payload_norm": payload_norm or {},
    }

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            await client.post(url, json=body, headers=headers)
    except Exception:
        # Do not fail the admin service if audit_log is down
        return
