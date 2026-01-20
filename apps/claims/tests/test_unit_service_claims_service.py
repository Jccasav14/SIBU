import pytest
from fastapi import HTTPException
from types import SimpleNamespace
from datetime import datetime, timezone
from unittest.mock import AsyncMock

from apps.claims.app.services.claims_service import ClaimsService
from apps.claims.app.infrastructure.postgres.models import ClaimStatus, PaymentStatus


@pytest.mark.asyncio
async def test_create_claim_rejects_requested_amount_over_cap():
    svc = ClaimsService(session=None)  # type: ignore[arg-type]
    svc.repo = AsyncMock()
    with pytest.raises(HTTPException) as e:
        await svc.create_claim(
            actor="a",
            student_id="stu",
            claim_type="ACCIDENT",
            occurred_at=datetime.now(timezone.utc),
            reported_at=datetime.now(timezone.utc),
            description="ok",
            requested_amount=200,
            coverage_cap=100,
        )
    assert e.value.status_code == 400
    assert e.value.detail == "Requested amount exceeds coverage cap"


@pytest.mark.asyncio
async def test_patch_claim_only_allows_draft():
    svc = ClaimsService(session=None)  # type: ignore[arg-type]
    claim = SimpleNamespace(id="c1", status=ClaimStatus.SUBMITTED)
    svc.repo = AsyncMock()
    svc.repo.get_claim = AsyncMock(return_value=claim)

    with pytest.raises(HTTPException) as e:
        await svc.patch_claim_draft(claim_id="c1", actor="a", description="x", requested_amount=None, coverage_cap=None)
    assert e.value.status_code == 400
    assert e.value.detail == "Only DRAFT claims can be edited"


@pytest.mark.asyncio
async def test_review_accepts_approved_and_sets_payment_pending():
    svc = ClaimsService(session=None)  # type: ignore[arg-type]
    claim = SimpleNamespace(
        id="c1",
        status=ClaimStatus.SUBMITTED,
        coverage_cap=200.0,
        approved_amount=None,
        payment_status=PaymentStatus.NONE,
    )
    svc.repo = AsyncMock()
    svc.repo.get_claim = AsyncMock(return_value=claim)
    svc.repo.add_event = AsyncMock()

    out = await svc.review(claim_id="c1", actor="a", decision="APPROVED", approved_amount=150, notes="ok")
    assert out.status.value == "APPROVED"
    assert float(out.approved_amount) == 150
    assert out.payment_status.value == "PAYMENT_PENDING"


@pytest.mark.asyncio
async def test_review_reject_sets_rejected_and_payment_none():
    svc = ClaimsService(session=None)  # type: ignore[arg-type]
    claim = SimpleNamespace(
        id="c1",
        status=ClaimStatus.SUBMITTED,
        coverage_cap=200.0,
        approved_amount=None,
        payment_status=PaymentStatus.NONE,
    )
    svc.repo = AsyncMock()
    svc.repo.get_claim = AsyncMock(return_value=claim)
    svc.repo.add_event = AsyncMock()

    out = await svc.review(claim_id="c1", actor="a", decision="REJECTED", approved_amount=None, notes="no")
    assert out.status.value == "REJECTED"
    assert out.payment_status.value == "NONE"


@pytest.mark.asyncio
async def test_pay_requires_approved():
    svc = ClaimsService(session=None)  # type: ignore[arg-type]
    claim = SimpleNamespace(id="c1", status=ClaimStatus.SUBMITTED, approved_amount=10)
    svc.repo = AsyncMock()
    svc.repo.get_claim = AsyncMock(return_value=claim)

    with pytest.raises(HTTPException) as e:
        await svc.pay(claim_id="c1", actor="a", payment_method="x", payment_reference="y", paid_amount=1)
    assert e.value.status_code == 400
    assert e.value.detail == "Only APPROVED claims can be paid"
