import pytest
from unittest.mock import AsyncMock
from datetime import date
from fastapi import HTTPException
from uuid import uuid4

from app.services.coverage_service import CoverageService
from app.api.schemas import CoveragePolicyCreate
from app.infrastructure.postgres.models import ClaimType


@pytest.mark.asyncio
async def test_create_coverage_conflict_when_active_overlap(monkeypatch):
    svc = CoverageService(session=None, cache=AsyncMock())  # type: ignore[arg-type]
    svc.repo = AsyncMock()
    svc.repo.exists_active_overlap = AsyncMock(return_value=True)

    payload = CoveragePolicyCreate.model_validate(
        {
            "claim_type": ClaimType.ACCIDENT,
            "name": "Ok",
            "description": "Ok",
            "max_coverage_amount": 10,
            "currency": "USD",
            "requires_documents": [],
            "waiting_days": 0,
            "is_active": True,
            "valid_from": date(2025, 1, 1),
            "valid_to": None,
        }
    )

    with pytest.raises(HTTPException) as e:
        await svc.create_coverage(payload)
    assert e.value.status_code == 409
    assert "Another active policy already exists" in e.value.detail


@pytest.mark.asyncio
async def test_validate_overlap_skips_when_inactive():
    svc = CoverageService(session=None, cache=AsyncMock())  # type: ignore[arg-type]
    svc.repo = AsyncMock()
    svc.repo.exists_active_overlap = AsyncMock(return_value=True)

    # is_active False should bypass overlap check
    await svc._validate_active_overlap(  # noqa: SLF001
        claim_type=ClaimType.OTHER,
        valid_from=date(2025, 1, 1),
        valid_to=None,
        is_active=False,
        exclude_id=None,
    )
    svc.repo.exists_active_overlap.assert_not_called()


@pytest.mark.asyncio
async def test_set_active_true_conflict_raises(fake_policy):
    svc = CoverageService(session=None, cache=AsyncMock())  # type: ignore[arg-type]
    svc.repo = AsyncMock()
    svc.repo.get = AsyncMock(return_value=fake_policy)
    svc.repo.exists_active_overlap = AsyncMock(return_value=True)

    with pytest.raises(HTTPException) as e:
        await svc.set_active(fake_policy.id, True)
    assert e.value.status_code == 409
