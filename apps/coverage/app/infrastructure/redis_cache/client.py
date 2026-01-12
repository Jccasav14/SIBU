from __future__ import annotations

from redis.asyncio import Redis, from_url

from app.settings import settings

_client: Redis | None = None


def get_redis() -> Redis:
    global _client
    if _client is None:
        _client = from_url(settings.redis_url, decode_responses=True)
    return _client
