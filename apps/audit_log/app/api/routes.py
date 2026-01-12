from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from ..domain.schemas import AuditEventIn, AuditEventOut, Page, SummaryOut
from ..infrastructure.repository import AuditRepository, redact
from ..settings import settings
from ..security.jwt import AuthUser, require_admin, require_auth


router = APIRouter(tags=["audit"])


async def get_repo() -> AuditRepository:
    return AuditRepository()


def _parse_dt(val: str | None) -> datetime | None:
    if not val:
        return None
    try:
        # Accept ISO-8601; if no tz, assume UTC
        dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        raise HTTPException(status_code=400, detail=f"Fecha inválida: {val}")


def _secure_event(doc: dict[str, Any]) -> dict[str, Any]:
    doc = dict(doc)
    if "payload_raw" in doc:
        doc["payload_raw"] = redact(doc.get("payload_raw"))
    if "payload_norm" in doc:
        doc["payload_norm"] = redact(doc.get("payload_norm"))
    return doc


@router.get("/health")
def health():
    return {"ok": True, "service": settings.SERVICE_NAME}


@router.get("/audit/events", response_model=Page)
async def list_events(
    user: Annotated[AuthUser, Depends(require_admin)],
    repo: Annotated[AuditRepository, Depends(get_repo)],
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = None,
    service: str | None = None,
    event_type: str | None = None,
    actor: str | None = None,
    actor_role: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    severity: str | None = None,
    source: str | None = None,
    correlation_id: str | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 25,
    sort: str = "timestamp_desc",
):
    filters = {
        "from": _parse_dt(from_),
        "to": _parse_dt(to),
        "service": service,
        "event_type": event_type,
        "actor": actor,
        "actor_role": actor_role,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "severity": severity,
        "source": source,
        "correlation_id": correlation_id,
        "q": q,
    }
    page = max(page, 1)
    page_size = min(max(page_size, 1), 200)
    if sort not in {"timestamp_desc", "timestamp_asc"}:
        raise HTTPException(status_code=400, detail="sort inválido")

    items, total = await repo.find_events(filters=filters, page=page, page_size=page_size, sort=sort)
    safe_items = [_secure_event(d) for d in items]
    return Page(items=safe_items, page=page, page_size=page_size, total=total)


@router.get("/audit/events/{event_id}", response_model=AuditEventOut)
async def get_event(
    event_id: str,
    user: Annotated[AuthUser, Depends(require_admin)],
    repo: Annotated[AuditRepository, Depends(get_repo)],
):
    doc = await repo.get_event(event_id)
    if not doc:
        raise HTTPException(status_code=404, detail="No encontrado")
    return _secure_event(doc)


@router.get("/audit/entities/{entity_type}/{entity_id}", response_model=list[AuditEventOut])
async def by_entity(
    entity_type: str,
    entity_id: str,
    user: Annotated[AuthUser, Depends(require_admin)],
    repo: Annotated[AuditRepository, Depends(get_repo)],
    limit: int = 200,
):
    limit = min(max(limit, 1), 500)
    docs = await repo.find_by_entity(entity_type, entity_id, limit=limit)
    return [_secure_event(d) for d in docs]


@router.get("/audit/summary", response_model=list[SummaryOut])
async def summary(
    user: Annotated[AuthUser, Depends(require_admin)],
    repo: Annotated[AuditRepository, Depends(get_repo)],
):
    now = datetime.now(timezone.utc)
    windows = [("24h", now - timedelta(hours=24)), ("7d", now - timedelta(days=7))]
    out: list[SummaryOut] = []
    for label, since in windows:
        agg = await repo.aggregate_summary(since)
        out.append(SummaryOut(window=label, **agg))
    return out


@router.get("/audit/top-actors")
async def top_actors(
    user: Annotated[AuthUser, Depends(require_admin)],
    repo: Annotated[AuditRepository, Depends(get_repo)],
    hours: int = 24,
    limit: int = 20,
):
    hours = min(max(hours, 1), 24 * 30)
    limit = min(max(limit, 1), 100)
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    pipeline = [
        {"$match": {"timestamp": {"$gte": since}, "actor": {"$ne": None}}},
        {"$group": {"_id": "$actor", "count": {"$sum": 1}, "roles": {"$addToSet": "$actor_role"}}},
        {"$sort": {"count": -1}},
        {"$limit": limit},
    ]
    res = await repo.col.aggregate(pipeline).to_list(length=limit)
    return [{"actor": r.get("_id"), "count": r.get("count", 0), "roles": r.get("roles", [])} for r in res]


@router.get("/audit/security")
async def security_feed(
    user: Annotated[AuthUser, Depends(require_admin)],
    repo: Annotated[AuditRepository, Depends(get_repo)],
    hours: int = 24,
    limit: int = 100,
):
    hours = min(max(hours, 1), 24 * 30)
    limit = min(max(limit, 1), 500)
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    # Heurística simple: eventos sensibles por type/severity/tags
    q = {
        "timestamp": {"$gte": since},
        "$or": [
            {"event_type": {"$regex": "login_failed|access_denied|password|token|role", "$options": "i"}},
            {"severity": "ERROR"},
            {"tags": {"$in": ["job_error", "security", "access_denied"]}},
        ],
    }
    cursor = repo.col.find(q, {"_id": 0}).sort("timestamp", -1).limit(limit)
    docs = [doc async for doc in cursor]
    return [_secure_event(d) for d in docs]


@router.get("/audit/export.csv")
async def export_csv(
    user: Annotated[AuthUser, Depends(require_admin)],
    repo: Annotated[AuditRepository, Depends(get_repo)],
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = None,
    service: str | None = None,
    event_type: str | None = None,
    actor: str | None = None,
    severity: str | None = None,
    source: str | None = None,
    q: str | None = None,
):
    filters = {
        "from": _parse_dt(from_),
        "to": _parse_dt(to),
        "service": service,
        "event_type": event_type,
        "actor": actor,
        "severity": severity,
        "source": source,
        "q": q,
    }

    async def _iter():
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            "event_id",
            "timestamp",
            "received_at",
            "source",
            "service",
            "event_type",
            "actor",
            "actor_role",
            "entity_type",
            "entity_id",
            "severity",
            "correlation_id",
            "tags",
        ])
        yield buf.getvalue()
        buf.seek(0)
        buf.truncate(0)

        # Stream in chunks by pages
        page = 1
        page_size = 500
        while True:
            items, total = await repo.find_events(filters=filters, page=page, page_size=page_size, sort="timestamp_desc")
            if not items:
                break
            for d in items:
                d = _secure_event(d)
                writer.writerow([
                    d.get("event_id"),
                    d.get("timestamp"),
                    d.get("received_at"),
                    d.get("source"),
                    d.get("service"),
                    d.get("event_type"),
                    d.get("actor"),
                    d.get("actor_role"),
                    d.get("entity_type"),
                    d.get("entity_id"),
                    d.get("severity"),
                    d.get("correlation_id"),
                    ";".join(d.get("tags") or []),
                ])
            yield buf.getvalue()
            buf.seek(0)
            buf.truncate(0)
            page += 1

    return StreamingResponse(_iter(), media_type="text/csv")


@router.get("/audit/mine", response_model=Page)
async def my_events(
    user: Annotated[AuthUser, Depends(require_auth)],
    repo: Annotated[AuditRepository, Depends(get_repo)],
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = None,
    service: str | None = None,
    event_type: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    severity: str | None = None,
    source: str | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 25,
    sort: str = "timestamp_desc",
):
    if user.role == "admin":
        # Admin can just use /audit/events
        raise HTTPException(status_code=400, detail="Usa /audit/events")
    if not settings.AUDIT_PROFESSIONAL_CAN_VIEW_MINE:
        raise HTTPException(status_code=403, detail="Feature deshabilitado")

    filters = {
        "from": _parse_dt(from_),
        "to": _parse_dt(to),
        "service": service,
        "event_type": event_type,
        "actor": user.email,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "severity": severity,
        "source": source,
        "q": q,
    }
    page = max(page, 1)
    page_size = min(max(page_size, 1), 200)
    if sort not in {"timestamp_desc", "timestamp_asc"}:
        raise HTTPException(status_code=400, detail="sort inválido")

    items, total = await repo.find_events(filters=filters, page=page, page_size=page_size, sort=sort)
    safe_items = [_secure_event(d) for d in items]
    return Page(items=safe_items, page=page, page_size=page_size, total=total)


@router.post("/audit/events", response_model=AuditEventOut)
async def ingest_rest(
    payload: AuditEventIn,
    req: Request,
    user: Annotated[AuthUser, Depends(require_admin)],
    repo: Annotated[AuditRepository, Depends(get_repo)],
):
    # Service-to-service auth can be added later (mTLS / shared secret / client credentials).
    received_at = datetime.now(timezone.utc)
    correlation_id = payload.correlation_id or str(uuid.uuid4())

    ip = req.client.host if req.client else None
    ua = req.headers.get("user-agent")
    payload.source = "rest"  # force
    payload.ip = payload.ip or ip
    payload.user_agent = payload.user_agent or ua

    event_id = str(uuid.uuid4())
    doc = {
        "source": "rest",
        "event_type": payload.event_type,
        "service": payload.service,
        "actor": payload.actor,
        "actor_role": payload.actor_role,
        "entity_type": payload.entity_type,
        "entity_id": payload.entity_id,
        "timestamp": payload.timestamp or received_at,
        "received_at": received_at,
        "correlation_id": correlation_id,
        "ip": payload.ip,
        "user_agent": payload.user_agent,
        "severity": payload.severity,
        "tags": payload.tags,
        "payload_raw": payload.payload_raw,
        "payload_norm": payload.payload_norm,
    }
    await repo.insert_event(event_id, doc)
    doc["event_id"] = event_id
    return _secure_event(doc)
