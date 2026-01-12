from __future__ import annotations

import json
from typing import Any

from redis.asyncio import Redis

from app.settings import settings


class RedisCache:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def get_json(self, key: str) -> Any | None:
        val = await self.redis.get(key)
        if val is None:
            return None
        return json.loads(val)

    async def set_json(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else settings.redis_ttl_seconds
        await self.redis.set(key, json.dumps(value, default=str), ex=ttl)

    async def delete(self, key: str) -> None:
        await self.redis.delete(key)

    async def delete_prefix(self, prefix: str) -> None:
        # Use SCAN to avoid blocking
        cursor = 0
        pattern = f"{prefix}*"
        while True:
            cursor, keys = await self.redis.scan(cursor=cursor, match=pattern, count=200)
            if keys:
                await self.redis.delete(*keys)
            if cursor == 0:
                break
