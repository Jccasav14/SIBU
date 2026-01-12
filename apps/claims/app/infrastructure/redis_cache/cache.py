from __future__ import annotations

import json
from typing import Any, Optional

import orjson
from redis.asyncio import Redis

from ...settings import settings


def _dumps(obj: Any) -> str:
    return orjson.dumps(obj).decode("utf-8")


def _loads(data: str) -> Any:
    return orjson.loads(data)


class RedisCache:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def get_json(self, key: str) -> Optional[Any]:
        val = await self.redis.get(key)
        if val is None:
            return None
        return _loads(val)

    async def set_json(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        ttl = ttl_seconds or settings.REDIS_TTL_SECONDS
        await self.redis.set(key, _dumps(value), ex=ttl)

    async def delete(self, key: str) -> None:
        await self.redis.delete(key)

    async def invalidate_prefix(self, prefix: str) -> int:
        """Delete keys matching prefix* using SCAN to avoid blocking."""
        pattern = f"{prefix}*"
        deleted = 0
        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(cursor=cursor, match=pattern, count=200)
            if keys:
                await self.redis.delete(*keys)
                deleted += len(keys)
            if cursor == 0:
                break
        return deleted
