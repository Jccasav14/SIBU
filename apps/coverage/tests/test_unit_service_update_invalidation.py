import pytest
from unittest.mock import AsyncMock
from datetime import date
from pydantic import ValidationError

from app.services.coverage_service import CoverageService
from app.api.schemas import CoveragePolicyUpdate
from app.infrastructure.postgres.models import ClaimType


@pytest.mark.asyncio
async def test_update_coverage_raises_validationerror_when_valid_to_before_valid_from(fake_policy):
    # Schema validation happens BEFORE service call
    with pytest.raises(ValidationError) as e:
        CoveragePolicyUpdate.model_validate({"valid_from": date(2025, 2, 10), "valid_to": date(2025, 2, 1)})
    assert "valid_to cannot be before valid_from" in str(e.value)


@pytest.mark.asyncio
async def test_update_coverage_invalidates_caches_when_claim_type_changes(fake_policy):
    svc = CoverageService(session=None, cache=AsyncMock())  # type: ignore[arg-type]
    svc.cache.delete_prefix = AsyncMock()
    svc.cache.delete = AsyncMock()

    old = fake_policy
    old.claim_type = ClaimType.ACCIDENT

    updated = type("P", (), {})()
    updated.id = old.id
    updated.claim_type = ClaimType.ILLNESS
    updated.name = old.name
    updated.description = old.description
    updated.max_coverage_amount = old.max_coverage_amount
    updated.currency = old.currency
    updated.requires_documents = old.requires_documents
    updated.waiting_days = old.waiting_days
    updated.is_active = old.is_active
    updated.valid_from = old.valid_from
    updated.valid_to = old.valid_to
    updated.created_at = old.created_at
    updated.updated_at = old.updated_at

    svc.repo = AsyncMock()
    svc.repo.get = AsyncMock(return_value=old)
    svc.repo.exists_active_overlap = AsyncMock(return_value=False)
    svc.repo.update_fields = AsyncMock(return_value=updated)

    payload = CoveragePolicyUpdate.model_validate({"claim_type": ClaimType.ILLNESS})
    out = await svc.update_coverage(old.id, payload)

    assert out["claim_type"] == "ILLNESS"
    assert svc.cache.delete_prefix.call_count >= 2
    svc.cache.delete.assert_called()
