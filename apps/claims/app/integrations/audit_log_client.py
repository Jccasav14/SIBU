from __future__ import annotations

import logging
from typing import Any

import httpx

from ..settings import settings

logger = logging.getLogger(__name__)


class AuditLogClient:
    def __init__(self):
        self.enabled = settings.AUDIT_LOG_ENABLED
        self.base_url = str(settings.AUDIT_LOG_URL) if settings.AUDIT_LOG_URL else None
        self.timeout = settings.AUDIT_LOG_TIMEOUT_SECONDS

    async def emit(self, *, actor: str, action: str, entity_id: str, payload: dict[str, Any]) -> None:
        """Fire-and-forget, best-effort."""
        if not self.enabled or not self.base_url:
            return

        url = f"{self.base_url}/audit/events"
        body = {
            "service": "claims",
            "actor": actor,
            "action": action,
            "entity": "claim",
            "entity_id": entity_id,
            "payload": payload,
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                await client.post(url, json=body)
        except Exception as e:
            logger.warning("audit_log emit failed (degraded mode): %s", e)
