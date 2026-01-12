from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import CoveragePolicyCreate, CoveragePolicyOut, CoveragePolicyUpdate
from app.infrastructure.postgres.models import ClaimType
from app.infrastructure.postgres.session import get_session
from app.security.jwt import require_admin, require_admin_or_insurance
from app.services.coverage_service import CoverageService
from app.infrastructure.redis_cache.client import get_redis
from app.infrastructure.redis_cache.cache import RedisCache

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok"}


def get_service(session: AsyncSession = Depends(get_session)) -> CoverageService:
    cache = RedisCache(get_redis())
    return CoverageService(session=session, cache=cache)


@router.get(
    "/coverage",
    response_model=list[CoveragePolicyOut],
    dependencies=[Depends(require_admin_or_insurance)],
)
async def list_coverage(service: CoverageService = Depends(get_service)):
    return await service.list_coverage()


@router.get(
    "/coverage/{policy_id}",
    response_model=CoveragePolicyOut,
    dependencies=[Depends(require_admin_or_insurance)],
)
async def get_coverage(policy_id: uuid.UUID, service: CoverageService = Depends(get_service)):
    policy = await service.get_coverage(policy_id)
    if policy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    return policy


@router.get(
    "/coverage/by-claim-type/{claim_type}",
    response_model=list[CoveragePolicyOut],
    dependencies=[Depends(require_admin_or_insurance)],
)
async def get_by_claim_type(claim_type: ClaimType, service: CoverageService = Depends(get_service)):
    return await service.list_by_claim_type(claim_type)


@router.post(
    "/coverage",
    response_model=CoveragePolicyOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_coverage(payload: CoveragePolicyCreate, service: CoverageService = Depends(get_service)):
    return await service.create_coverage(payload)


@router.patch(
    "/coverage/{policy_id}",
    response_model=CoveragePolicyOut,
    dependencies=[Depends(require_admin)],
)
async def update_coverage(policy_id: uuid.UUID, payload: CoveragePolicyUpdate, service: CoverageService = Depends(get_service)):
    updated = await service.update_coverage(policy_id, payload)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    return updated


@router.post(
    "/coverage/{policy_id}/activate",
    response_model=CoveragePolicyOut,
    dependencies=[Depends(require_admin)],
)
async def activate_policy(policy_id: uuid.UUID, service: CoverageService = Depends(get_service)):
    updated = await service.set_active(policy_id, True)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    return updated


@router.post(
    "/coverage/{policy_id}/deactivate",
    response_model=CoveragePolicyOut,
    dependencies=[Depends(require_admin)],
)
async def deactivate_policy(policy_id: uuid.UUID, service: CoverageService = Depends(get_service)):
    updated = await service.set_active(policy_id, False)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    return updated
