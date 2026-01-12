import pytest

from apps.claims.app.infrastructure.redis_cache.cache import RedisCache


@pytest.mark.asyncio
async def test_cache_set_get_invalidate(fake_redis):
    cache = RedisCache(fake_redis)
    await cache.set_json("claims:list:test", {"a": 1}, ttl_seconds=60)
    assert await cache.get_json("claims:list:test") == {"a": 1}

    await cache.set_json("claims:list:other", {"b": 2}, ttl_seconds=60)
    deleted = await cache.invalidate_prefix("claims:list:")
    assert deleted >= 2
    assert await cache.get_json("claims:list:test") is None
