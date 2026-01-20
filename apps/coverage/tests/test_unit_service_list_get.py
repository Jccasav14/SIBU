import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from app.services.coverage_service import CoverageService


@pytest.mark.asyncio
async def test_list_coverage_returns_cached_when_present(monkeypatch):
    svc = CoverageService(session=None, cache=AsyncMock())  # type: ignore[arg-type]
    svc.cache.get_json = AsyncMock(return_value=[{"id": "1"}])
    svc.repo = AsyncMock()

    out = await svc.list_coverage()
    assert out == [{"id": "1"}]
    svc.repo.list_all.assert_not_called()


@pytest.mark.asyncio
async def test_get_coverage_returns_none_when_repo_none():
    svc = CoverageService(session=None, cache=AsyncMock())  # type: ignore[arg-type]
    svc.cache.get_json = AsyncMock(return_value=None)
    svc.repo = AsyncMock()
    svc.repo.get = AsyncMock(return_value=None)

    out = await svc.get_coverage(uuid4())
    assert out is None


@pytest.mark.asyncio
async def test_get_coverage_sets_cache_when_found(fake_policy):
    svc = CoverageService(session=None, cache=AsyncMock())  # type: ignore[arg-type]
    svc.cache.get_json = AsyncMock(return_value=None)
    svc.cache.set_json = AsyncMock()
    svc.repo = AsyncMock()
    svc.repo.get = AsyncMock(return_value=fake_policy)

    out = await svc.get_coverage(fake_policy.id)
    assert out["name"] == "Policy A"
    assert out["max_coverage_amount"] == 123.45
    svc.cache.set_json.assert_called_once()
