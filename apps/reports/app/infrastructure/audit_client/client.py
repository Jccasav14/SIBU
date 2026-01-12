from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from ...settings import settings

logger = logging.getLogger("reports.audit_client")


class AuditLogClient:
    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=settings.AUDIT_LOG_URL, timeout=settings.AUDIT_LOG_TIMEOUT_SEC)
        return self._client

    async def get(self, path: str, *, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> httpx.Response:
        client = self._get_client()
        last_exc: Exception | None = None
        for _ in range(max(1, settings.AUDIT_LOG_RETRY_COUNT + 1)):
            try:
                return await client.get(path, params=params, headers=headers)
            except Exception as e:
                last_exc = e
                await asyncio.sleep(0.2)
        assert last_exc is not None
        raise last_exc

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None


audit_client = AuditLogClient()
