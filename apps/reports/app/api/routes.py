from __future__ import annotations

import logging
import os
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.schemas.models import (
    ActivityRow,
    AppointmentsRow,
    CasesRow,
    ExportAccepted,
    ExportRequest,
    ExportStatus,
    SecurityRow,
    SummaryOut,
    TopActorRow,
    Window,
)
from ..infrastructure.audit_client.client import audit_client
from ..infrastructure.jobs.rabbit import rabbit
from ..infrastructure.postgres.db import get_session
from ..infrastructure.postgres.models import actor_metrics
from ..infrastructure.postgres.repository import ReportsRepository
from ..infrastructure.redis_cache.cache import cache
from ..security.jwt import AuthUser, require_admin, require_auth
from ..settings import settings

logger = logging.getLogger("reports.api")

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, Any]:
    return {"ok": True, "service": settings.SERVICE_NAME, "env": settings.ENV}


def _utc_today() -> date:
    return datetime.now(timezone.utc).date()


def _window_range(window: Window) -> tuple[date, date]:
    today = _utc_today()
    if window == "24h":
        return (today - timedelta(days=1), today)
    if window == "7d":
        return (today - timedelta(days=6), today)
    return (today - timedelta(days=29), today)


def _cache_key(prefix: str, **kwargs: Any) -> str:
    parts = [prefix] + [f"{k}={kwargs[k]}" for k in sorted(kwargs.keys())]
    return "reports:" + "|".join(parts)


@router.get("/reports/summary", response_model=SummaryOut, dependencies=[Depends(require_admin)])
async def summary(
    window: Window = Query("7d"),
    session: Annotated[AsyncSession, Depends(get_session)] = None,  # type: ignore[assignment]
) -> SummaryOut:
    from_day, to_day = _window_range(window)
    key = _cache_key("summary", window=window, from_day=str(from_day), to_day=str(to_day))

    cached = await cache.get_json(key)
    if cached:
        return SummaryOut(**cached)

    repo = ReportsRepository(session)
    totals = await repo.totals_by_service(from_day=from_day, to_day=to_day)
    cases = [CasesRow(**r) for r in await repo.query_cases(from_day=from_day, to_day=to_day)]
    appts = [AppointmentsRow(**r) for r in await repo.query_appointments(from_day=from_day, to_day=to_day)]
    sec = [SecurityRow(**r) for r in await repo.query_security(from_day=from_day, to_day=to_day)]
    top = [TopActorRow(**r) for r in await repo.top_actors(from_day=from_day, to_day=to_day, limit=10)]

    out = SummaryOut(
        window=window,
        from_day=from_day,
        to_day=to_day,
        totals_by_service=totals,
        cases=cases,
        appointments=appts,
        security=sec,
        top_actors=top,
    )
    await cache.set_json(key, out.model_dump(mode="json"))
    return out


@router.get("/reports/activity", response_model=list[ActivityRow], dependencies=[Depends(require_admin)])
async def activity(
    from_: date = Query(..., alias="from"),
    to: date = Query(...),
    service: str | None = None,
    event_type: str | None = None,
    severity: str | None = None,
    role: str | None = None,
    session: Annotated[AsyncSession, Depends(get_session)] = None,  # type: ignore[assignment]
) -> list[ActivityRow]:
    key = _cache_key(
        "activity",
        **{"from": str(from_), "to": str(to), "service": service, "event_type": event_type, "severity": severity, "role": role},
    )
    cached = await cache.get_json(key)
    if cached:
        return [ActivityRow(**r) for r in cached]

    repo = ReportsRepository(session)
    rows = await repo.query_daily_activity(from_day=from_, to_day=to, service=service, event_type=event_type, severity=severity, role=role)
    await cache.set_json(key, rows)
    return [ActivityRow(**r) for r in rows]


@router.get("/reports/cases", response_model=list[CasesRow], dependencies=[Depends(require_admin)])
async def cases(
    from_: date = Query(..., alias="from"),
    to: date = Query(...),
    session: Annotated[AsyncSession, Depends(get_session)] = None,  # type: ignore[assignment]
) -> list[CasesRow]:
    key = _cache_key("cases", **{"from": str(from_), "to": str(to)})
    cached = await cache.get_json(key)
    if cached:
        return [CasesRow(**r) for r in cached]
    repo = ReportsRepository(session)
    rows = await repo.query_cases(from_day=from_, to_day=to)
    await cache.set_json(key, rows)
    return [CasesRow(**r) for r in rows]


@router.get("/reports/appointments", response_model=list[AppointmentsRow], dependencies=[Depends(require_admin)])
async def appointments(
    from_: date = Query(..., alias="from"),
    to: date = Query(...),
    session: Annotated[AsyncSession, Depends(get_session)] = None,  # type: ignore[assignment]
) -> list[AppointmentsRow]:
    key = _cache_key("appointments", **{"from": str(from_), "to": str(to)})
    cached = await cache.get_json(key)
    if cached:
        return [AppointmentsRow(**r) for r in cached]
    repo = ReportsRepository(session)
    rows = await repo.query_appointments(from_day=from_, to_day=to)
    await cache.set_json(key, rows)
    return [AppointmentsRow(**r) for r in rows]


@router.get("/reports/security", response_model=list[SecurityRow], dependencies=[Depends(require_admin)])
async def security(
    from_: date = Query(..., alias="from"),
    to: date = Query(...),
    session: Annotated[AsyncSession, Depends(get_session)] = None,  # type: ignore[assignment]
) -> list[SecurityRow]:
    key = _cache_key("security", **{"from": str(from_), "to": str(to)})
    cached = await cache.get_json(key)
    if cached:
        return [SecurityRow(**r) for r in cached]
    repo = ReportsRepository(session)
    rows = await repo.query_security(from_day=from_, to_day=to)
    await cache.set_json(key, rows)
    return [SecurityRow(**r) for r in rows]


@router.get("/reports/top-actors", response_model=list[TopActorRow], dependencies=[Depends(require_admin)])
async def top_actors(
    from_: date = Query(..., alias="from"),
    to: date = Query(...),
    limit: int = Query(10, ge=1, le=100),
    session: Annotated[AsyncSession, Depends(get_session)] = None,  # type: ignore[assignment]
) -> list[TopActorRow]:
    key = _cache_key("top_actors", **{"from": str(from_), "to": str(to), "limit": limit})
    cached = await cache.get_json(key)
    if cached:
        return [TopActorRow(**r) for r in cached]
    repo = ReportsRepository(session)
    rows = await repo.top_actors(from_day=from_, to_day=to, limit=limit)
    await cache.set_json(key, rows)
    return [TopActorRow(**r) for r in rows]


@router.get("/reports/mine")
async def mine(
    user: Annotated[AuthUser, Depends(require_auth)],
    from_: date = Query(..., alias="from"),
    to: date = Query(...),
    session: Annotated[AsyncSession, Depends(get_session)] = None,  # type: ignore[assignment]
) -> dict[str, Any]:
    if user.role == "admin":
        raise HTTPException(status_code=400, detail="Use admin endpoints")
    if not settings.REPORTS_PROFESSIONAL_CAN_VIEW_MINE:
        raise HTTPException(status_code=403, detail="Not enabled")

    stmt = (
        select(actor_metrics.c.actor, actor_metrics.c.role, func.sum(actor_metrics.c.count).label("count"))
        .where(and_(actor_metrics.c.day >= from_, actor_metrics.c.day <= to, actor_metrics.c.actor == user.email))
        .group_by(actor_metrics.c.actor, actor_metrics.c.role)
    )
    row = (await session.execute(stmt)).mappings().first()
    return {"actor": user.email, "from": str(from_), "to": str(to), "count": int(row["count"]) if row else 0, "role": user.role}


@router.get("/reports/audit")
async def audit_proxy(
    request: Request,
    user: Annotated[AuthUser, Depends(require_auth)],
) -> JSONResponse:
    if user.role != "admin":
        if not settings.REPORTS_PROFESSIONAL_CAN_VIEW_MINE:
            raise HTTPException(status_code=403, detail="Access denied")
        path = "/audit/mine"
    else:
        path = "/audit/events"

    params = dict(request.query_params)
    headers = {"Authorization": request.headers.get("Authorization", "")}

    try:
        resp = await audit_client.get(path, params=params, headers=headers)
        return JSONResponse(status_code=resp.status_code, content=resp.json())
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"audit-log unavailable: {e}")


@router.post("/reports/export", response_model=ExportAccepted)
async def export_async(
    payload: ExportRequest,
    user: Annotated[AuthUser, Depends(require_auth)],
    session: Annotated[AsyncSession, Depends(get_session)] = None,  # type: ignore[assignment]
) -> ExportAccepted:
    if user.role != "admin":
        if not settings.REPORTS_PROFESSIONAL_CAN_VIEW_MINE:
            raise HTTPException(status_code=403, detail="Access denied")
        if payload.type == "audit":
            raise HTTPException(status_code=403, detail="Audit export requires admin")

    job_id = uuid.uuid4().hex
    repo = ReportsRepository(session)
    await repo.create_export_job(
        job_id=job_id,
        type_=payload.type,
        params={
            "from": str(payload.from_),
            "to": str(payload.to),
            "format": payload.format,
            "filters": payload.filters or {},
            "requested_by": user.email,
            "role": user.role,
        },
    )
    await session.commit()

    try:
        await rabbit.publish(
            {
                "action": "export",
                "job_id": job_id,
                "type": payload.type,
                "params": {
                    "from": str(payload.from_),
                    "to": str(payload.to),
                    "format": payload.format,
                    "filters": payload.filters or {},
                    "requested_by": user.email,
                    "role": user.role,
                },
            }
        )
    except Exception as e:
        await repo.set_export_job_status(job_id=job_id, status="failed", error=f"RabbitMQ unavailable: {e}")
        await session.commit()
        raise HTTPException(status_code=503, detail="RabbitMQ unavailable (degraded mode)")

    return ExportAccepted(job_id=job_id)


@router.get("/reports/export/{job_id}", response_model=ExportStatus)
async def export_status(
    job_id: str,
    user: Annotated[AuthUser, Depends(require_auth)],
    session: Annotated[AsyncSession, Depends(get_session)] = None,  # type: ignore[assignment]
) -> ExportStatus:
    repo = ReportsRepository(session)
    job = await repo.get_export_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if user.role != "admin":
        if not settings.REPORTS_PROFESSIONAL_CAN_VIEW_MINE:
            raise HTTPException(status_code=403, detail="Access denied")
        if user.email not in (job.get("params_json") or ""):
            raise HTTPException(status_code=403, detail="Access denied")

    return ExportStatus(
        job_id=job["job_id"],
        status=job["status"],
        type=job["type"],
        created_at=str(job["created_at"]),
        updated_at=str(job["updated_at"]),
        file_path=job.get("file_path"),
        error=job.get("error"),
    )


@router.get("/reports/export/{job_id}/download")
async def export_download(
    job_id: str,
    user: Annotated[AuthUser, Depends(require_auth)],
    session: Annotated[AsyncSession, Depends(get_session)] = None,  # type: ignore[assignment]
) -> FileResponse:
    repo = ReportsRepository(session)
    job = await repo.get_export_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job no encontrado")

    if job["status"] != "ready" or not job.get("file_path"):
        raise HTTPException(status_code=409, detail="Aún no está listo")

    file_path = job["file_path"]

    # ✅ Validación real (si el archivo no existe, NO 500)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=410, detail="Archivo no existe en el servidor")

    # ✅ Autorización: admin global; professional solo si está habilitado y es el dueño
    if user.role != "admin":
        if not settings.REPORTS_PROFESSIONAL_CAN_VIEW_MINE:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        # check rápido: el params_json guarda requested_by
        if user.email not in (job.get("params_json") or ""):
            raise HTTPException(status_code=403, detail="Acceso denegado")

    # ✅ filename SIEMPRE definido
    filename = os.path.basename(file_path)

    # ✅ content-type correcto
    if filename.endswith(".csv"):
        media_type = "text/csv"
    elif filename.endswith(".xlsx"):
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif filename.endswith(".pdf"):
        media_type = "application/pdf"
    else:
        media_type = "application/octet-stream"

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
