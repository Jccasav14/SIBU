import pytest
from app.infrastructure.redis_cache.cache import RedisCache
from .conftest import FakeRedis


@pytest.mark.asyncio
async def test_cache_set_get_json_roundtrip():
    r = FakeRedis()
    c = RedisCache(r)  # type: ignore[arg-type]
    await c.set_json("k1", {"a": 1})
    assert await c.get_json("k1") == {"a": 1}


@pytest.mark.asyncio
async def test_delete_prefix_deletes_many_keys():
    r = FakeRedis()
    c = RedisCache(r)  # type: ignore[arg-type]
    await c.set_json("coverage:list", [1])
    await c.set_json("coverage:list:page:1", [2])
    await c.set_json("coverage:item:1", {"x": 1})

    await c.delete_prefix("coverage:list")
    assert await c.get_json("coverage:list") is None
    assert await c.get_json("coverage:list:page:1") is None
    assert await c.get_json("coverage:item:1") == {"x": 1}

