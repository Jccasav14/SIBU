from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import (
    CatalogCreate,
    CatalogItem,
    CatalogUpdate,
    FlagValue,
    OverviewOut,
    SettingValue,
    StatusPatch,
)
from ..infrastructure.audit_client import emit_audit_event
from ..infrastructure.postgres.db import get_session
from ..infrastructure.postgres.repository import AdminRepository
from ..infrastructure.redis_cache.client import cache
from ..infrastructure.users_client import patch_status, users_health
from ..security.jwt import AuthUser, require_admin, require_auth
from ..settings import settings


router = APIRouter(tags=["admin"])


@router.get("/health")
async def health():
    return {"ok": True, "service": settings.SERVICE_NAME}


async def get_repo(session: Annotated[AsyncSession, Depends(get_session)]) -> AdminRepository:
    return AdminRepository(session)


def _auth_header(req: Request) -> str | None:
    return req.headers.get("authorization")


# ------------------ Catalog Areas (lectura) ------------------
@router.get("/catalog/areas", response_model=list[CatalogItem])
async def list_areas_public(
    user: Annotated[AuthUser, Depends(require_auth)],
    repo: Annotated[AdminRepository, Depends(get_repo)],
):
    """Lectura de catálogo para UI (profesional/admin)."""
    key = "admin:catalog:areas:enabled"
    cached = await cache.get_json(key)
    if cached is not None:
        return [CatalogItem(**x) for x in cached]

    items = await repo.list_areas()
    out = [CatalogItem.model_validate(x) for x in items if x.enabled]
    await cache.set_json(key, [i.model_dump() for i in out], ttl=settings.REDIS_TTL_SECONDS)
    return out

# ------------------ Catalog Areas ------------------
@router.get("/admin/catalog/areas", response_model=list[CatalogItem])
async def list_areas(
    user: Annotated[AuthUser, Depends(require_admin)],
    repo: Annotated[AdminRepository, Depends(get_repo)],
):
    key = "admin:catalog:areas"
    cached = await cache.get_json(key)
    if cached is not None:
        return cached
    areas = await repo.list_areas()
    out = [CatalogItem(id=a.id, name=a.name, enabled=a.enabled) for a in areas]
    await cache.set_json(key, out, ttl=settings.REDIS_TTL_SECONDS)
    return out


@router.post("/admin/catalog/areas", response_model=CatalogItem)
async def create_area(
    payload: CatalogCreate,
    req: Request,
    bg: BackgroundTasks,
    user: Annotated[AuthUser, Depends(require_admin)],
    repo: Annotated[AdminRepository, Depends(get_repo)],
):
    try:
        area = await repo.create_area(name=payload.name, enabled=payload.enabled)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Área ya existe")
    await repo.add_action(user.email, "catalog.area.create", "admin_catalog_areas", str(area.id))
    await cache.invalidate_prefix("admin:catalog:")

    bg.add_task(
        emit_audit_event,
        auth_header=_auth_header(req),
        event_type="catalog.area.create",
        actor=user.email,
        actor_role=user.role,
        entity_type="admin_catalog_areas",
        entity_id=str(area.id),
        payload_raw={"name": payload.name, "enabled": payload.enabled},
        tags=["admin"],
    )

    return CatalogItem(id=area.id, name=area.name, enabled=area.enabled)


@router.patch("/admin/catalog/areas/{area_id}", response_model=CatalogItem)
async def patch_area(
    area_id: int,
    payload: CatalogUpdate,
    req: Request,
    bg: BackgroundTasks,
    user: Annotated[AuthUser, Depends(require_admin)],
    repo: Annotated[AdminRepository, Depends(get_repo)],
):
    area = await repo.update_area(area_id, name=payload.name, enabled=payload.enabled)
    if not area:
        raise HTTPException(status_code=404, detail="No encontrado")
    await repo.add_action(user.email, "catalog.area.update", "admin_catalog_areas", str(area_id))
    await cache.invalidate_prefix("admin:catalog:")

    bg.add_task(
        emit_audit_event,
        auth_header=_auth_header(req),
        event_type="catalog.area.update",
        actor=user.email,
        actor_role=user.role,
        entity_type="admin_catalog_areas",
        entity_id=str(area_id),
        payload_raw={"name": payload.name, "enabled": payload.enabled},
        tags=["admin"],
    )
    return CatalogItem(id=area.id, name=area.name, enabled=area.enabled)


# ------------------ Catalog Services (optional) ------------------
@router.get("/admin/catalog/services", response_model=list[CatalogItem])
async def list_services(
    user: Annotated[AuthUser, Depends(require_admin)],
    repo: Annotated[AdminRepository, Depends(get_repo)],
):
    key = "admin:catalog:services"
    cached = await cache.get_json(key)
    if cached is not None:
        return cached
    svcs = await repo.list_services()
    out = [CatalogItem(id=s.id, name=s.name, enabled=s.enabled) for s in svcs]
    await cache.set_json(key, out, ttl=settings.REDIS_TTL_SECONDS)
    return out


@router.post("/admin/catalog/services", response_model=CatalogItem)
async def create_service(
    payload: CatalogCreate,
    req: Request,
    bg: BackgroundTasks,
    user: Annotated[AuthUser, Depends(require_admin)],
    repo: Annotated[AdminRepository, Depends(get_repo)],
):
    try:
        svc = await repo.create_service(name=payload.name, enabled=payload.enabled)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Servicio ya existe")
    await repo.add_action(user.email, "catalog.service.create", "admin_catalog_services", str(svc.id))
    await cache.invalidate_prefix("admin:catalog:")
    bg.add_task(
        emit_audit_event,
        auth_header=_auth_header(req),
        event_type="catalog.service.create",
        actor=user.email,
        actor_role=user.role,
        entity_type="admin_catalog_services",
        entity_id=str(svc.id),
        payload_raw={"name": payload.name, "enabled": payload.enabled},
        tags=["admin"],
    )
    return CatalogItem(id=svc.id, name=svc.name, enabled=svc.enabled)


@router.patch("/admin/catalog/services/{service_id}", response_model=CatalogItem)
async def patch_service(
    service_id: int,
    payload: CatalogUpdate,
    req: Request,
    bg: BackgroundTasks,
    user: Annotated[AuthUser, Depends(require_admin)],
    repo: Annotated[AdminRepository, Depends(get_repo)],
):
    svc = await repo.update_service(service_id, name=payload.name, enabled=payload.enabled)
    if not svc:
        raise HTTPException(status_code=404, detail="No encontrado")
    await repo.add_action(user.email, "catalog.service.update", "admin_catalog_services", str(service_id))
    await cache.invalidate_prefix("admin:catalog:")
    bg.add_task(
        emit_audit_event,
        auth_header=_auth_header(req),
        event_type="catalog.service.update",
        actor=user.email,
        actor_role=user.role,
        entity_type="admin_catalog_services",
        entity_id=str(service_id),
        payload_raw={"name": payload.name, "enabled": payload.enabled},
        tags=["admin"],
    )
    return CatalogItem(id=svc.id, name=svc.name, enabled=svc.enabled)


# ------------------ Settings ------------------
@router.get("/admin/settings")
async def get_settings(
    user: Annotated[AuthUser, Depends(require_admin)],
    repo: Annotated[AdminRepository, Depends(get_repo)],
):
    key = "admin:settings"
    cached = await cache.get_json(key)
    if cached is not None:
        return cached
    out = await repo.list_settings()
    await cache.set_json(key, out, ttl=settings.REDIS_TTL_SECONDS)
    return out


@router.put("/admin/settings/{key}")
async def put_setting(
    key: str,
    payload: SettingValue,
    req: Request,
    bg: BackgroundTasks,
    user: Annotated[AuthUser, Depends(require_admin)],
    repo: Annotated[AdminRepository, Depends(get_repo)],
):
    await repo.put_setting(key, payload.value)
    await repo.add_action(user.email, "settings.put", "admin_settings", key)
    await cache.invalidate_prefix("admin:")
    bg.add_task(
        emit_audit_event,
        auth_header=_auth_header(req),
        event_type="settings.put",
        actor=user.email,
        actor_role=user.role,
        entity_type="admin_settings",
        entity_id=key,
        payload_raw={"value": payload.value},
        tags=["admin"],
    )
    return {"ok": True, "key": key}


# ------------------ Flags ------------------
@router.get("/admin/flags")
async def get_flags(
    user: Annotated[AuthUser, Depends(require_admin)],
    repo: Annotated[AdminRepository, Depends(get_repo)],
):
    key = "admin:flags"
    cached = await cache.get_json(key)
    if cached is not None:
        return cached
    out = await repo.list_flags()
    await cache.set_json(key, out, ttl=settings.REDIS_TTL_SECONDS)
    return out


@router.put("/admin/flags/{key}")
async def put_flag(
    key: str,
    payload: FlagValue,
    req: Request,
    bg: BackgroundTasks,
    user: Annotated[AuthUser, Depends(require_admin)],
    repo: Annotated[AdminRepository, Depends(get_repo)],
):
    await repo.put_flag(key, payload.enabled)
    await repo.add_action(user.email, "flags.put", "admin_flags", key)
    await cache.invalidate_prefix("admin:")
    bg.add_task(
        emit_audit_event,
        auth_header=_auth_header(req),
        event_type="flags.put",
        actor=user.email,
        actor_role=user.role,
        entity_type="admin_flags",
        entity_id=key,
        payload_raw={"enabled": payload.enabled},
        tags=["admin"],
    )
    return {"ok": True, "key": key, "enabled": payload.enabled}


# ------------------ Moderation (via users service) ------------------
@router.patch("/admin/users/{email}/status")
async def patch_user_status(
    email: str,
    payload: StatusPatch,
    req: Request,
    bg: BackgroundTasks,
    user: Annotated[AuthUser, Depends(require_admin)],
    repo: Annotated[AdminRepository, Depends(get_repo)],
):
    # best-effort external call
    result = await patch_status(kind="user", email=email, status=payload.status, auth_header=_auth_header(req))

    await repo.add_action(user.email, "users.status.patch", "user", email)
    bg.add_task(
        emit_audit_event,
        auth_header=_auth_header(req),
        event_type="users.status.patch",
        actor=user.email,
        actor_role=user.role,
        entity_type="user",
        entity_id=email,
        payload_raw={"status": payload.status, "users_call": result},
        tags=["admin", "moderation"],
    )
    if not result.get("ok") and result.get("status_code"):
        # degrade, but still 200 to avoid crashing UI; message is explicit
        return {"ok": True, "degraded": True, "users": result}
    return {"ok": True, "users": result}


@router.patch("/admin/professionals/{email}/status")
async def patch_professional_status(
    email: str,
    payload: StatusPatch,
    req: Request,
    bg: BackgroundTasks,
    user: Annotated[AuthUser, Depends(require_admin)],
    repo: Annotated[AdminRepository, Depends(get_repo)],
):
    result = await patch_status(kind="professional", email=email, status=payload.status, auth_header=_auth_header(req))
    await repo.add_action(user.email, "professionals.status.patch", "professional", email)
    bg.add_task(
        emit_audit_event,
        auth_header=_auth_header(req),
        event_type="professionals.status.patch",
        actor=user.email,
        actor_role=user.role,
        entity_type="professional",
        entity_id=email,
        payload_raw={"status": payload.status, "users_call": result},
        tags=["admin", "moderation"],
    )
    if not result.get("ok") and result.get("status_code"):
        return {"ok": True, "degraded": True, "users": result}
    return {"ok": True, "users": result}


# ------------------ Dashboard (cached) ------------------
@router.get("/admin/overview", response_model=OverviewOut)
async def overview(
    req: Request,
    user: Annotated[AuthUser, Depends(require_admin)],
    repo: Annotated[AdminRepository, Depends(get_repo)],
):
    key = "admin:overview"
    cached = await cache.get_json(key)
    if cached is not None:
        return cached

    counts = await repo.counts()
    flags = await repo.list_flags()
    settings_dict = await repo.list_settings()
    areas = [CatalogItem(id=a.id, name=a.name, enabled=a.enabled) for a in await repo.list_areas()]
    svcs = [CatalogItem(id=s.id, name=s.name, enabled=s.enabled) for s in await repo.list_services()]

    # optional: show whether users service is up
    users_state = await users_health()
    out: dict[str, Any] = {
        "counts": counts,
        "flags": flags,
        "settings": settings_dict,
        "catalog": {"areas": areas, "services": svcs},
        "users_service": users_state,
    }
    await cache.set_json(key, out, ttl=max(60, min(settings.REDIS_TTL_SECONDS, 300)))
    return out
