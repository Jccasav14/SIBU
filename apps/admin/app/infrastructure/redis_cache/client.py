from __future__ import annotations

import json
import datetime
from typing import Any

import orjson
import redis.asyncio as redis

from ...settings import settings


def _orjson_default(obj: Any):
    """Best-effort JSON serialization for cache payloads."""
    # Pydantic v2
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    # Pydantic v1
    if hasattr(obj, "dict"):
        return obj.dict()
    # Datetimes / dates
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    # UUID
    if hasattr(obj, "hex") and obj.__class__.__name__ == "UUID":
        return str(obj)
    # Fallback to string
    return str(obj)



class RedisCache:
    def __init__(self, url: str | None = None):
        self.url = url or settings.REDIS_URL
        self._redis: redis.Redis | None = None

    async def connect(self) -> None:
        # Importante: guardamos bytes (orjson.dumps) => decode_responses=False
        self._redis = redis.from_url(
            self.url,
            encoding="utf-8",          # no hace daño aunque sea bytes
            decode_responses=False,    # <- clave para que get() devuelva bytes
        )
        # valida conexión al iniciar
        await self._redis.ping()

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.close()
            self._redis = None

    @property
    def r(self) -> redis.Redis:
        if self._redis is None:
            raise RuntimeError("Redis not connected")
        return self._redis

    async def get_json(self, key: str) -> Any | None:
        data = await self.r.get(key)
        if data is None:
            return None

        # Esperamos bytes; por seguridad toleramos str
        if isinstance(data, (bytes, bytearray, memoryview)):
            raw = bytes(data)
            try:
                return orjson.loads(raw)
            except Exception:
                return json.loads(raw.decode("utf-8", errors="ignore"))

        if isinstance(data, str):
            try:
                return orjson.loads(data.encode("utf-8"))
            except Exception:
                return json.loads(data)

        # fallback
        return None

    async def set_json(self, key: str, value: Any, ttl: int | None = None) -> None:
        ttl = ttl or settings.REDIS_TTL_SECONDS
        payload = orjson.dumps(value, default=_orjson_default)  # bytes
        await self.r.set(key, payload, ex=ttl)

    async def invalidate_prefix(self, prefix: str) -> int:
        """Delete all keys matching <prefix>* . Returns deleted count."""
        pattern = f"{prefix}*"
        deleted = 0
        # Use scan to be safe in prod
        async for key in self.r.scan_iter(match=pattern, count=200):
            await self.r.delete(key)
            deleted += 1
        return deleted


cache = RedisCache()
