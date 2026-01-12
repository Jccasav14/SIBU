from __future__ import annotations

import logging
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient

from ..settings import settings

logger = logging.getLogger(__name__)


class MongoArchive:
    """Optional long-term archive storage for non-sensitive timeline events.

    If Mongo is unavailable, the service continues (degraded mode).
    """

    def __init__(self):
        self.enabled = settings.MONGO_ENABLED and bool(settings.MONGO_URI)
        self.client: AsyncIOMotorClient | None = None
        self.db = None

    async def connect(self) -> None:
        if not self.enabled:
            return
        try:
            self.client = AsyncIOMotorClient(settings.MONGO_URI)
            self.db = self.client[settings.MONGO_DB]
            # best-effort ping
            await self.client.admin.command("ping")
        except Exception as e:
            logger.warning("Mongo connect failed (degraded mode): %s", e)
            self.enabled = False
            self.client = None
            self.db = None

    async def close(self) -> None:
        if self.client:
            self.client.close()

    async def archive_event(self, *, claim_id: str, actor: str, event_type: str, payload: dict[str, Any]) -> None:
        if not self.enabled or not self.db:
            return
        try:
            await self.db.claim_events.insert_one(
                {"claim_id": claim_id, "actor": actor, "event_type": event_type, "payload": payload}
            )
        except Exception as e:
            logger.warning("Mongo archive failed (degraded mode): %s", e)
