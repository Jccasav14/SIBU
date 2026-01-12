from __future__ import annotations

import uuid
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import CoveragePolicyCreate, CoveragePolicyUpdate
from app.infrastructure.postgres.models import ClaimType, CoveragePolicy
from app.infrastructure.postgres.repository import CoverageRepository
from app.infrastructure.redis_cache.cache import RedisCache


class CoverageService:
    def __init__(self, session: AsyncSession, cache: RedisCache):
        self.repo = CoverageRepository(session)
        self.cache = cache

    @staticmethod
    def _list_key() -> str:
        return "coverage:list"

    @staticmethod
    def _item_key(policy_id: uuid.UUID) -> str:
        return f"coverage:item:{policy_id}"

    @staticmethod
    def _type_key(claim_type: ClaimType) -> str:
        return f"coverage:type:{claim_type.value}"

    async def list_coverage(self) -> list[CoveragePolicy]:
        key = self._list_key()
        cached = await self.cache.get_json(key)
        if cached is not None:
            return cached
        items = await self.repo.list_all()
        out = [self._to_dict(i) for i in items]
        await self.cache.set_json(key, out)
        return out

    async def get_coverage(self, policy_id: uuid.UUID):
        key = self._item_key(policy_id)
        cached = await self.cache.get_json(key)
        if cached is not None:
            return cached
        policy = await self.repo.get(policy_id)
        if policy is None:
            return None
        out = self._to_dict(policy)
        await self.cache.set_json(key, out)
        return out

    async def list_by_claim_type(self, claim_type: ClaimType):
        key = self._type_key(claim_type)
        cached = await self.cache.get_json(key)
        if cached is not None:
            return cached
        items = await self.repo.list_by_claim_type(claim_type)
        out = [self._to_dict(i) for i in items]
        await self.cache.set_json(key, out)
        return out

    async def create_coverage(self, payload: CoveragePolicyCreate):
        await self._validate_active_overlap(
            claim_type=payload.claim_type,
            valid_from=payload.valid_from,
            valid_to=payload.valid_to,
            is_active=payload.is_active,
        )
        policy = CoveragePolicy(
            claim_type=payload.claim_type,
            name=payload.name,
            description=payload.description,
            max_coverage_amount=payload.max_coverage_amount,
            currency=payload.currency,
            requires_documents=payload.requires_documents,
            waiting_days=payload.waiting_days,
            is_active=payload.is_active,
            valid_from=payload.valid_from,
            valid_to=payload.valid_to,
        )
        created = await self.repo.create(policy)
        await self._invalidate_after_write(claim_type=created.claim_type, policy_id=created.id)
        return self._to_dict(created)

    async def update_coverage(self, policy_id: uuid.UUID, payload: CoveragePolicyUpdate):
        current = await self.repo.get(policy_id)
        if current is None:
            return None

        fields = payload.model_dump(exclude_unset=True)
        new_claim_type = fields.get("claim_type", current.claim_type)
        new_valid_from = fields.get("valid_from", current.valid_from)
        new_valid_to = fields.get("valid_to", current.valid_to)
        new_is_active = fields.get("is_active", current.is_active)

        if new_valid_to is not None and new_valid_to < new_valid_from:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="valid_to cannot be before valid_from")

        await self._validate_active_overlap(
            claim_type=new_claim_type,
            valid_from=new_valid_from,
            valid_to=new_valid_to,
            is_active=new_is_active,
            exclude_id=policy_id,
        )

        updated = await self.repo.update_fields(policy_id, fields)
        if updated is None:
            return None

        # Invalidate type caches for old and new claim_type if changed
        await self.cache.delete_prefix("coverage:list")
        await self.cache.delete(self._item_key(policy_id))
        if current.claim_type != updated.claim_type:
            await self.cache.delete_prefix(f"coverage:type:{current.claim_type.value}")
        await self.cache.delete_prefix(f"coverage:type:{updated.claim_type.value}")
        return self._to_dict(updated)

    async def set_active(self, policy_id: uuid.UUID, is_active: bool):
        current = await self.repo.get(policy_id)
        if current is None:
            return None

        if is_active:
            await self._validate_active_overlap(
                claim_type=current.claim_type,
                valid_from=current.valid_from,
                valid_to=current.valid_to,
                is_active=True,
                exclude_id=policy_id,
            )

        updated = await self.repo.update_fields(policy_id, {"is_active": is_active})
        if updated is None:
            return None

        await self._invalidate_after_write(claim_type=updated.claim_type, policy_id=updated.id)
        return self._to_dict(updated)

    async def _validate_active_overlap(
        self,
        claim_type: ClaimType,
        valid_from: date,
        valid_to: date | None,
        is_active: bool,
        exclude_id: uuid.UUID | None = None,
    ) -> None:
        if not is_active:
            return
        exists = await self.repo.exists_active_overlap(
            claim_type=claim_type,
            valid_from=valid_from,
            valid_to=valid_to,
            exclude_id=exclude_id,
        )
        if exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Another active policy already exists for this claim_type and date range",
            )

    async def _invalidate_after_write(self, claim_type: ClaimType, policy_id: uuid.UUID) -> None:
        await self.cache.delete_prefix("coverage:list")
        await self.cache.delete(self._item_key(policy_id))
        await self.cache.delete_prefix(f"coverage:type:{claim_type.value}")

    @staticmethod
    def _to_dict(p: CoveragePolicy) -> dict:
        return {
            "id": str(p.id),
            "claim_type": p.claim_type.value,
            "name": p.name,
            "description": p.description,
            "max_coverage_amount": float(p.max_coverage_amount),
            "currency": p.currency,
            "requires_documents": list(p.requires_documents or []),
            "waiting_days": p.waiting_days,
            "is_active": p.is_active,
            "valid_from": p.valid_from,
            "valid_to": p.valid_to,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
        }
