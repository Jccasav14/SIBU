from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as redis

from ...settings import settings

logger = logging.getLogger("reports.cache")


class RedisCache:
    def __init__(self) -> None:
        self._client: redis.Redis | None = None

    async def connect(self) -> None:
        if self._client is not None:
            return
        try:
            self._client = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
            await self._client.ping()
            logger.info("redis connected")
        except Exception as e:
            logger.warning("redis unavailable (degraded mode)", extra={"error": str(e)})
            self._client = None

    async def get_json(self, key: str) -> Any | None:
        await self.connect()
        if self._client is None:
            return None
        try:
            raw = await self._client.get(key)
            return json.loads(raw) if raw else None
        except Exception:
            return None

    async def set_json(self, key: str, value: Any, ttl: int | None = None) -> None:
        await self.connect()
        if self._client is None:
            return
        try:
            raw = json.dumps(value, default=str)
            await self._client.set(key, raw, ex=ttl or settings.CACHE_TTL_SEC)
        except Exception:
            return


cache = RedisCache()
