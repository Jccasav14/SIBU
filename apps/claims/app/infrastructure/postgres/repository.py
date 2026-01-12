from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional

from sqlalchemy import Select, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Claim, ClaimDocument, ClaimEvent, ClaimEventType, ClaimStatus, ClaimType, DocumentType, PaymentStatus


@dataclass
class Overview:
    total: int
    by_status: dict[str, int]
    total_paid: float


class ClaimsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_claim(
        self,
        *,
        student_id: str,
        claim_type: ClaimType,
        occurred_at: datetime,
        reported_at: datetime,
        description: str,
        requested_amount: float,
        coverage_cap: float,
    ) -> Claim:
        claim = Claim(
            student_id=student_id,
            claim_type=claim_type,
            status=ClaimStatus.DRAFT,
            occurred_at=occurred_at,
            reported_at=reported_at,
            description=description,
            requested_amount=requested_amount,
            coverage_cap=coverage_cap,
            payment_status=PaymentStatus.NONE,
        )
        self.session.add(claim)
        await self.session.flush()
        return claim

    async def get_claim(self, claim_id: uuid.UUID) -> Claim | None:
        res = await self.session.execute(select(Claim).where(Claim.id == claim_id))
        return res.scalar_one_or_none()

    async def list_claims(
        self,
        *,
        status: ClaimStatus | None = None,
        claim_type: ClaimType | None = None,
        student_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Claim]:
        q = select(Claim).order_by(Claim.created_at.desc()).limit(limit).offset(offset)
        conds = []
        if status:
            conds.append(Claim.status == status)
        if claim_type:
            conds.append(Claim.claim_type == claim_type)
        if student_id:
            conds.append(Claim.student_id == student_id)
        if conds:
            q = q.where(and_(*conds))
        res = await self.session.execute(q)
        return list(res.scalars().all())

    async def update_draft_fields(
        self,
        claim: Claim,
        *,
        description: str | None = None,
        requested_amount: float | None = None,
        coverage_cap: float | None = None,
    ) -> Claim:
        if description is not None:
            claim.description = description
        if requested_amount is not None:
            claim.requested_amount = requested_amount
        if coverage_cap is not None:
            claim.coverage_cap = coverage_cap
        await self.session.flush()
        return claim

    async def add_document(
        self,
        *,
        claim_id: uuid.UUID,
        doc_type: DocumentType,
        file_url: str,
        file_hash: str,
    ) -> ClaimDocument:
        doc = ClaimDocument(claim_id=claim_id, doc_type=doc_type, file_url=file_url, file_hash=file_hash)
        self.session.add(doc)
        await self.session.flush()
        return doc

    async def list_documents(self, claim_id: uuid.UUID) -> list[ClaimDocument]:
        res = await self.session.execute(
            select(ClaimDocument).where(ClaimDocument.claim_id == claim_id).order_by(ClaimDocument.created_at.desc())
        )
        return list(res.scalars().all())

    async def add_event(
        self,
        *,
        claim_id: uuid.UUID,
        actor: str,
        event_type: ClaimEventType,
        payload: dict,
    ) -> ClaimEvent:
        evt = ClaimEvent(claim_id=claim_id, actor=actor, event_type=event_type, payload_json=json.dumps(payload))
        self.session.add(evt)
        await self.session.flush()
        return evt

    async def list_events(self, claim_id: uuid.UUID) -> list[ClaimEvent]:
        res = await self.session.execute(
            select(ClaimEvent).where(ClaimEvent.claim_id == claim_id).order_by(ClaimEvent.created_at.asc())
        )
        return list(res.scalars().all())

    async def overview(self) -> Overview:
        total = (await self.session.execute(select(func.count()).select_from(Claim))).scalar_one()
        status_rows = await self.session.execute(select(Claim.status, func.count()).group_by(Claim.status))
        by_status = {str(s.value): int(c) for s, c in status_rows.all()}
        total_paid = (
            await self.session.execute(
                select(func.coalesce(func.sum(Claim.paid_amount), 0)).where(Claim.payment_status == PaymentStatus.PAID)
            )
        ).scalar_one()
        return Overview(total=int(total), by_status=by_status, total_paid=float(total_paid))
