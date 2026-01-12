from __future__ import annotations

import json
import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..infrastructure.postgres.models import ClaimStatus, ClaimType, DocumentType
from ..infrastructure.postgres.repository import ClaimsRepository
from ..infrastructure.postgres.session import get_session
from ..infrastructure.redis_cache.cache import RedisCache
from ..infrastructure.redis_cache.client import get_redis
from ..integrations.audit_log_client import AuditLogClient
from ..integrations.mongo_archive import MongoArchive
from ..integrations.users_client import UsersClient
from ..security.jwt import require_insurance_or_admin
from ..services.claims_service import ClaimsService
from .schemas import (
    ClaimCreateIn,
    ClaimDocumentIn,
    ClaimDocumentOut,
    ClaimEventOut,
    ClaimOut,
    ClaimPatchIn,
    ClaimPaymentIn,
    ClaimReviewIn,
    ClaimsOverviewOut,
    HealthResponse,
    ListClaimsOut,
)

router = APIRouter()

users_client = UsersClient()
audit_client = AuditLogClient()
mongo_archive = MongoArchive()


def _to_claim_out(c) -> dict[str, Any]:
    return {
        "id": str(c.id),
        "student_id": c.student_id,
        "claim_type": c.claim_type,
        "status": c.status,
        "occurred_at": c.occurred_at.isoformat(),
        "reported_at": c.reported_at.isoformat(),
        "description": c.description,
        "requested_amount": float(c.requested_amount),
        "coverage_cap": float(c.coverage_cap),
        "approved_amount": float(c.approved_amount) if c.approved_amount is not None else None,
        "payment_status": c.payment_status,
        "paid_amount": float(c.paid_amount) if c.paid_amount is not None else None,
        "paid_at": c.paid_at.isoformat() if c.paid_at is not None else None,
        "payment_method": c.payment_method,
        "payment_reference": c.payment_reference,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


def _to_doc_out(d) -> dict[str, Any]:
    return {
        "id": str(d.id),
        "claim_id": str(d.claim_id),
        "doc_type": d.doc_type,
        "file_url": d.file_url,
        "file_hash": d.file_hash,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }


def _parse_event_payload(payload_json: str) -> dict[str, Any]:
    try:
        return json.loads(payload_json or "{}")
    except Exception:
        return {}


async def _invalidate_claims_cache(cache: RedisCache, claim_id: str | None = None) -> None:
    await cache.invalidate_prefix("claims:list:")
    await cache.delete("claims:overview")
    if claim_id:
        await cache.delete(f"claims:item:{claim_id}")
        await cache.delete(f"claims:docs:{claim_id}")
        await cache.delete(f"claims:timeline:{claim_id}")


@router.on_event("startup")
async def _mongo_startup():
    await mongo_archive.connect()


@router.on_event("shutdown")
async def _mongo_shutdown():
    await mongo_archive.close()


@router.get("/health", response_model=HealthResponse)
async def health():
    return {"ok": True, "service": "claims"}


@router.post("/claims", dependencies=[Depends(require_insurance_or_admin)], response_model=ClaimOut)
async def create_claim(
    request: Request,
    body: ClaimCreateIn,
    bg: BackgroundTasks,
    user=Depends(require_insurance_or_admin),
    session: AsyncSession = Depends(get_session),
):
    ok, warning = await users_client.validate_student_exists(body.student_id)

    auth_header = request.headers.get('authorization')
    policy, cov_warning = await coverage_client.get_active_policy_for_claim_type(
        body.claim_type.value, authorization=auth_header
    )
    derived_cap = None
    if policy and policy.get('max_coverage_amount') is not None:
        try:
            derived_cap = float(policy['max_coverage_amount'])
        except Exception:
            derived_cap = None

    svc = ClaimsService(session)
    claim = await svc.create_claim(
        actor=user["email"],
        student_id=body.student_id,
        claim_type=body.claim_type,
        occurred_at=body.occurred_at,
        reported_at=body.reported_at,
        description=body.description,
        requested_amount=body.requested_amount,
        coverage_cap=(derived_cap if derived_cap is not None else (body.coverage_cap or 0)),
    )
    await session.commit()

    redis = get_redis()
    cache = RedisCache(redis)
    await _invalidate_claims_cache(cache, str(claim.id))
    await redis.close()

    bg.add_task(audit_client.emit, actor=user["email"], action="claim_created", entity_id=str(claim.id), payload={"student_id": body.student_id, "claim_type": body.claim_type.value})
    bg.add_task(mongo_archive.archive_event, claim_id=str(claim.id), actor=user["email"], event_type="CREATED", payload={"student_id": body.student_id, "claim_type": body.claim_type.value})

    out = _to_claim_out(claim)
    merged_warning = None
    if warning and cov_warning:
        merged_warning = f"{warning}; {cov_warning}"
    elif warning:
        merged_warning = warning
    elif cov_warning:
        merged_warning = cov_warning

    if merged_warning:
        out["warning"] = merged_warning
    return out


@router.get("/claims", dependencies=[Depends(require_insurance_or_admin)], response_model=ListClaimsOut)
async def list_claims(
    status: ClaimStatus | None = Query(None),
    type: ClaimType | None = Query(None, alias="type"),
    student_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user=Depends(require_insurance_or_admin),
    session: AsyncSession = Depends(get_session),
):
    key = f"claims:list:status={status.value if status else ''}:type={type.value if type else ''}:student={student_id or ''}:limit={limit}:offset={offset}"
    redis = get_redis()
    cache = RedisCache(redis)
    cached = await cache.get_json(key)
    if cached is not None:
        await redis.close()
        return cached

    repo = ClaimsRepository(session)
    items = await repo.list_claims(status=status, claim_type=type, student_id=student_id, limit=limit, offset=offset)
    payload = {
        "items": [_to_claim_out(c) for c in items],
        "limit": limit,
        "offset": offset,
    }
    await cache.set_json(key, payload)
    await redis.close()
    return payload


@router.get("/claims/overview", dependencies=[Depends(require_insurance_or_admin)], response_model=ClaimsOverviewOut)
async def overview(
    user=Depends(require_insurance_or_admin),
    session: AsyncSession = Depends(get_session),
):
    redis = get_redis()
    cache = RedisCache(redis)
    cached = await cache.get_json("claims:overview")
    if cached is not None:
        await redis.close()
        return cached

    repo = ClaimsRepository(session)
    ov = await repo.overview()
    payload = {"total": ov.total, "by_status": ov.by_status, "total_paid": ov.total_paid}
    await cache.set_json("claims:overview", payload)
    await redis.close()
    return payload


@router.get("/claims/{claim_id}", dependencies=[Depends(require_insurance_or_admin)], response_model=ClaimOut)
async def get_claim(
    claim_id: uuid.UUID,
    user=Depends(require_insurance_or_admin),
    session: AsyncSession = Depends(get_session),
):
    key = f"claims:item:{claim_id}"
    redis = get_redis()
    cache = RedisCache(redis)
    cached = await cache.get_json(key)
    if cached is not None:
        await redis.close()
        return cached

    repo = ClaimsRepository(session)
    claim = await repo.get_claim(claim_id)
    if claim is None:
        await redis.close()
        raise HTTPException(status_code=404, detail="Claim not found")
    payload = _to_claim_out(claim)
    await cache.set_json(key, payload)
    await redis.close()
    return payload


@router.patch("/claims/{claim_id}", dependencies=[Depends(require_insurance_or_admin)], response_model=ClaimOut)
async def patch_claim(
    claim_id: uuid.UUID,
    body: ClaimPatchIn,
    bg: BackgroundTasks,
    user=Depends(require_insurance_or_admin),
    session: AsyncSession = Depends(get_session),
):
    svc = ClaimsService(session)
    claim = await svc.patch_claim_draft(
        claim_id=claim_id,
        actor=user["email"],
        description=body.description,
        requested_amount=body.requested_amount,
        coverage_cap=(derived_cap if derived_cap is not None else (body.coverage_cap or 0)),
    )
    await session.commit()

    redis = get_redis()
    cache = RedisCache(redis)
    await _invalidate_claims_cache(cache, str(claim_id))
    await redis.close()

    bg.add_task(audit_client.emit, actor=user["email"], action="claim_updated", entity_id=str(claim_id), payload={"fields": body.model_dump(exclude_none=True)})
    bg.add_task(mongo_archive.archive_event, claim_id=str(claim_id), actor=user["email"], event_type="UPDATED", payload={"fields": body.model_dump(exclude_none=True)})

    return _to_claim_out(claim)


@router.post("/claims/{claim_id}/submit", dependencies=[Depends(require_insurance_or_admin)], response_model=ClaimOut)
async def submit_claim(
    claim_id: uuid.UUID,
    bg: BackgroundTasks,
    user=Depends(require_insurance_or_admin),
    session: AsyncSession = Depends(get_session),
):
    svc = ClaimsService(session)
    claim = await svc.submit(claim_id=claim_id, actor=user["email"])
    await session.commit()

    redis = get_redis()
    cache = RedisCache(redis)
    await _invalidate_claims_cache(cache, str(claim_id))
    await redis.close()

    bg.add_task(audit_client.emit, actor=user["email"], action="claim_submitted", entity_id=str(claim_id), payload={})
    bg.add_task(mongo_archive.archive_event, claim_id=str(claim_id), actor=user["email"], event_type="SUBMITTED", payload={})

    return _to_claim_out(claim)


@router.post("/claims/{claim_id}/review", dependencies=[Depends(require_insurance_or_admin)], response_model=ClaimOut)
async def review_claim(
    claim_id: uuid.UUID,
    body: ClaimReviewIn,
    bg: BackgroundTasks,
    user=Depends(require_insurance_or_admin),
    session: AsyncSession = Depends(get_session),
):
    svc = ClaimsService(session)
    claim = await svc.review(
        claim_id=claim_id,
        actor=user["email"],
        decision=body.decision,
        approved_amount=body.approved_amount,
        notes=body.notes,
    )
    await session.commit()

    redis = get_redis()
    cache = RedisCache(redis)
    await _invalidate_claims_cache(cache, str(claim_id))
    await redis.close()

    bg.add_task(audit_client.emit, actor=user["email"], action="claim_reviewed", entity_id=str(claim_id), payload=body.model_dump())
    bg.add_task(mongo_archive.archive_event, claim_id=str(claim_id), actor=user["email"], event_type="REVIEWED", payload=body.model_dump())

    return _to_claim_out(claim)


@router.post("/claims/{claim_id}/payment", dependencies=[Depends(require_insurance_or_admin)], response_model=ClaimOut)
async def pay_claim(
    claim_id: uuid.UUID,
    body: ClaimPaymentIn,
    bg: BackgroundTasks,
    user=Depends(require_insurance_or_admin),
    session: AsyncSession = Depends(get_session),
):
    svc = ClaimsService(session)
    claim = await svc.pay(
        claim_id=claim_id,
        actor=user["email"],
        payment_method=body.payment_method,
        payment_reference=body.payment_reference,
        paid_amount=body.paid_amount,
    )
    await session.commit()

    redis = get_redis()
    cache = RedisCache(redis)
    await _invalidate_claims_cache(cache, str(claim_id))
    await redis.close()

    bg.add_task(audit_client.emit, actor=user["email"], action="claim_paid", entity_id=str(claim_id), payload=body.model_dump())
    bg.add_task(mongo_archive.archive_event, claim_id=str(claim_id), actor=user["email"], event_type="PAID", payload=body.model_dump())

    return _to_claim_out(claim)


@router.post("/claims/{claim_id}/documents", dependencies=[Depends(require_insurance_or_admin)], response_model=ClaimDocumentOut)
async def add_document(
    claim_id: uuid.UUID,
    body: ClaimDocumentIn,
    bg: BackgroundTasks,
    user=Depends(require_insurance_or_admin),
    session: AsyncSession = Depends(get_session),
):
    svc = ClaimsService(session)
    doc = await svc.add_document(
        claim_id=claim_id,
        actor=user["email"],
        doc_type=body.doc_type,
        file_url=body.file_url,
        file_hash=body.file_hash,
    )
    await session.commit()

    redis = get_redis()
    cache = RedisCache(redis)
    await _invalidate_claims_cache(cache, str(claim_id))
    await redis.close()

    bg.add_task(audit_client.emit, actor=user["email"], action="claim_document_added", entity_id=str(claim_id), payload=body.model_dump())
    bg.add_task(mongo_archive.archive_event, claim_id=str(claim_id), actor=user["email"], event_type="DOCUMENT_ADDED", payload=body.model_dump())

    return _to_doc_out(doc)


@router.get("/claims/{claim_id}/documents", dependencies=[Depends(require_insurance_or_admin)], response_model=list[ClaimDocumentOut])
async def list_documents(
    claim_id: uuid.UUID,
    user=Depends(require_insurance_or_admin),
    session: AsyncSession = Depends(get_session),
):
    key = f"claims:docs:{claim_id}"
    redis = get_redis()
    cache = RedisCache(redis)
    cached = await cache.get_json(key)
    if cached is not None:
        await redis.close()
        return cached

    repo = ClaimsRepository(session)
    docs = await repo.list_documents(claim_id)
    payload = [_to_doc_out(d) for d in docs]
    await cache.set_json(key, payload)
    await redis.close()
    return payload


@router.get("/claims/{claim_id}/timeline", dependencies=[Depends(require_insurance_or_admin)], response_model=list[ClaimEventOut])
async def timeline(
    claim_id: uuid.UUID,
    user=Depends(require_insurance_or_admin),
    session: AsyncSession = Depends(get_session),
):
    key = f"claims:timeline:{claim_id}"
    redis = get_redis()
    cache = RedisCache(redis)
    cached = await cache.get_json(key)
    if cached is not None:
        await redis.close()
        return cached

    repo = ClaimsRepository(session)
    events = await repo.list_events(claim_id)
    payload = [
        {
            "id": str(e.id),
            "claim_id": str(e.claim_id),
            "actor": e.actor,
            "event_type": e.event_type.value,
            "payload": _parse_event_payload(e.payload_json),
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]
    await cache.set_json(key, payload)
    await redis.close()
    return payload
