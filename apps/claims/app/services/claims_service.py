from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..infrastructure.postgres.models import Claim, ClaimEventType, ClaimStatus, ClaimType, DocumentType, PaymentStatus
from ..infrastructure.postgres.repository import ClaimsRepository


def _bad_request(detail: str) -> None:
    raise HTTPException(status_code=400, detail=detail)


def _not_found(detail: str = "Not found") -> None:
    raise HTTPException(status_code=404, detail=detail)


class ClaimsService:
    def __init__(self, session: AsyncSession):
        self.repo = ClaimsRepository(session)
        self.session = session

    async def create_claim(self, *, actor: str, **kwargs) -> Claim:
        requested_amount = float(kwargs.get('requested_amount') or 0)
        coverage_cap = float(kwargs.get('coverage_cap') or 0)
        if coverage_cap > 0 and requested_amount > coverage_cap:
            _bad_request('Requested amount exceeds coverage cap')
        claim = await self.repo.create_claim(**kwargs)
        await self.repo.add_event(claim_id=claim.id, actor=actor, event_type=ClaimEventType.CREATED, payload={"status": claim.status.value})
        return claim

    async def get_claim_or_404(self, claim_id: uuid.UUID) -> Claim:
        claim = await self.repo.get_claim(claim_id)
        if claim is None:
            _not_found("Claim not found")
        return claim

    async def patch_claim_draft(self, *, claim_id: uuid.UUID, actor: str, description: str | None, requested_amount: float | None, coverage_cap: float | None) -> Claim:
        claim = await self.get_claim_or_404(claim_id)
        if claim.status != ClaimStatus.DRAFT:
            _bad_request("Only DRAFT claims can be edited")
        await self.repo.update_draft_fields(claim, description=description, requested_amount=requested_amount, coverage_cap=coverage_cap)
        await self.repo.add_event(claim_id=claim.id, actor=actor, event_type=ClaimEventType.UPDATED, payload={"fields": {"description": description is not None, "requested_amount": requested_amount is not None, "coverage_cap": coverage_cap is not None}})
        return claim

    async def submit(self, *, claim_id: uuid.UUID, actor: str) -> Claim:
        claim = await self.get_claim_or_404(claim_id)
        if claim.status != ClaimStatus.DRAFT:
            _bad_request("Only DRAFT claims can be submitted")
        claim.status = ClaimStatus.SUBMITTED
        claim.reported_at = claim.reported_at or datetime.now(timezone.utc)
        await self.repo.add_event(claim_id=claim.id, actor=actor, event_type=ClaimEventType.SUBMITTED, payload={"status": claim.status.value})
        return claim

    async def review(self, *, claim_id: uuid.UUID, actor: str, decision: str, approved_amount: float | None, notes: str | None) -> Claim:
        claim = await self.get_claim_or_404(claim_id)
        if claim.status not in (ClaimStatus.SUBMITTED, ClaimStatus.UNDER_REVIEW):
            _bad_request("Claim must be SUBMITTED or UNDER_REVIEW to review")

        # Accept both API-friendly verbs (APPROVE/REJECT) and common past-tense values
        # that UIs may send (APPROVED/REJECTED).
        decision_u = (decision or "").upper().strip()
        decision_map = {
            "APPROVE": "APPROVE",
            "APPROVED": "APPROVE",
            "REJECT": "REJECT",
            "REJECTED": "REJECT",
        }
        decision_u = decision_map.get(decision_u)
        if decision_u not in ("APPROVE", "REJECT"):
            _bad_request("decision must be APPROVE or REJECT")

        claim.status = ClaimStatus.UNDER_REVIEW

        if decision_u == "APPROVE":
            if approved_amount is None:
                _bad_request("approved_amount is required when approving")
            if float(approved_amount) > float(claim.coverage_cap):
                _bad_request("approved_amount must be <= coverage_cap")
            claim.approved_amount = approved_amount
            claim.status = ClaimStatus.APPROVED
            claim.payment_status = PaymentStatus.PAYMENT_PENDING
        else:
            claim.status = ClaimStatus.REJECTED
            claim.payment_status = PaymentStatus.NONE

        await self.repo.add_event(
            claim_id=claim.id,
            actor=actor,
            event_type=ClaimEventType.REVIEWED,
            payload={"decision": decision_u, "approved_amount": approved_amount, "notes": notes},
        )
        return claim

    async def pay(self, *, claim_id: uuid.UUID, actor: str, payment_method: str, payment_reference: str, paid_amount: float | None = None) -> Claim:
        claim = await self.get_claim_or_404(claim_id)
        if claim.status != ClaimStatus.APPROVED:
            _bad_request("Only APPROVED claims can be paid")

        amount = paid_amount if paid_amount is not None else (claim.approved_amount or 0)
        if claim.approved_amount is not None and float(amount) > float(claim.approved_amount):
            _bad_request("paid_amount cannot exceed approved_amount")

        claim.payment_status = PaymentStatus.PAID
        claim.paid_amount = amount
        claim.paid_at = datetime.now(timezone.utc)
        claim.payment_method = payment_method
        claim.payment_reference = payment_reference
        claim.status = ClaimStatus.CLOSED

        await self.repo.add_event(
            claim_id=claim.id,
            actor=actor,
            event_type=ClaimEventType.PAID,
            payload={"paid_amount": float(amount), "payment_method": payment_method, "payment_reference": payment_reference},
        )
        await self.repo.add_event(claim_id=claim.id, actor=actor, event_type=ClaimEventType.CLOSED, payload={"status": claim.status.value})
        return claim

    async def add_document(self, *, claim_id: uuid.UUID, actor: str, doc_type: DocumentType, file_url: str, file_hash: str):
        claim = await self.get_claim_or_404(claim_id)
        doc = await self.repo.add_document(claim_id=claim.id, doc_type=doc_type, file_url=file_url, file_hash=file_hash)
        await self.repo.add_event(
            claim_id=claim.id,
            actor=actor,
            event_type=ClaimEventType.DOCUMENT_ADDED,
            payload={"doc_type": doc_type.value, "file_url": file_url, "file_hash": file_hash},
        )
        return doc