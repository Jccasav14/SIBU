from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.postgres.models import ClaimType, CoveragePolicy


class CoverageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all(self) -> list[CoveragePolicy]:
        stmt = select(CoveragePolicy).order_by(CoveragePolicy.claim_type, CoveragePolicy.valid_from.desc())
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get(self, policy_id: uuid.UUID) -> CoveragePolicy | None:
        stmt = select(CoveragePolicy).where(CoveragePolicy.id == policy_id)
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def list_by_claim_type(self, claim_type: ClaimType) -> list[CoveragePolicy]:
        stmt = (
            select(CoveragePolicy)
            .where(CoveragePolicy.claim_type == claim_type)
            .order_by(CoveragePolicy.valid_from.desc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def create(self, policy: CoveragePolicy) -> CoveragePolicy:
        self.session.add(policy)
        await self.session.commit()
        await self.session.refresh(policy)
        return policy

    async def update_fields(self, policy_id: uuid.UUID, fields: dict) -> CoveragePolicy | None:
        stmt = update(CoveragePolicy).where(CoveragePolicy.id == policy_id).values(**fields).returning(CoveragePolicy)
        res = await self.session.execute(stmt)
        row = res.fetchone()
        if row is None:
            await self.session.rollback()
            return None
        await self.session.commit()
        return row[0]

    async def exists_active_overlap(
        self,
        claim_type: ClaimType,
        valid_from: date,
        valid_to: date | None,
        exclude_id: uuid.UUID | None = None,
    ) -> bool:
        # Overlap between [valid_from, valid_to] and existing [e.valid_from, e.valid_to]
        overlap = and_(
            or_(CoveragePolicy.valid_to.is_(None), CoveragePolicy.valid_to >= valid_from),
            or_(valid_to is None, CoveragePolicy.valid_from <= valid_to),
        )

        stmt = select(CoveragePolicy.id).where(
            CoveragePolicy.claim_type == claim_type,
            CoveragePolicy.is_active.is_(True),
            overlap,
        )
        if exclude_id is not None:
            stmt = stmt.where(CoveragePolicy.id != exclude_id)

        res = await self.session.execute(stmt.limit(1))
        return res.first() is not None
