from __future__ import annotations

from redis.asyncio import Redis

from ...settings import settings


def get_redis() -> Redis:
    return Redis.from_url(settings.REDIS_URL, decode_responses=True)
