import asyncio

import pytest

from apps.claims.app.infrastructure.redis_cache.cache import RedisCache


class _R:
    def __init__(self):
        self.store = {}

    async def get(self, k):
        return self.store.get(k)

    async def set(self, k, v, ex=None):
        self.store[k] = v

    async def delete(self, *keys):
        for k in keys:
            self.store.pop(k, None)

    async def scan(self, cursor=0, match=None, count=200):
        prefix = (match or "").split("*", 1)[0]
        keys = [k for k in self.store.keys() if k.startswith(prefix)]
        return 0, keys


@pytest.mark.asyncio
async def test_cache_set_get_json_roundtrip():
    r = _R()
    c = RedisCache(r)
    await c.set_json("k1", {"a": 1})
    val = await c.get_json("k1")
    assert val == {"a": 1}


@pytest.mark.asyncio
async def test_invalidate_prefix_deletes_matching_keys():
    r = _R()
    c = RedisCache(r)
    await c.set_json("claims:list:x", {"x": 1})
    await c.set_json("claims:list:y", {"y": 2})
    await c.set_json("claims:item:1", {"z": 3})

    deleted = await c.invalidate_prefix("claims:list:")
    assert deleted == 2
    assert await c.get_json("claims:item:1") == {"z": 3}
