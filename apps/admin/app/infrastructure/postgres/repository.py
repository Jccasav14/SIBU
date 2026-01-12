from __future__ import annotations

import json
from typing import Any

from sqlalchemy import Select, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .models import AdminAction, AdminCatalogArea, AdminCatalogService, AdminFlag, AdminSetting


class AdminRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ---------- Catalog: Areas ----------
    async def list_areas(self) -> list[AdminCatalogArea]:
        res = await self.session.execute(select(AdminCatalogArea).order_by(AdminCatalogArea.name.asc()))
        return list(res.scalars().all())

    async def create_area(self, name: str, enabled: bool = True) -> AdminCatalogArea:
        area = AdminCatalogArea(name=name, enabled=enabled)
        self.session.add(area)
        await self.session.commit()
        await self.session.refresh(area)
        return area

    async def update_area(self, area_id: int, *, name: str | None = None, enabled: bool | None = None) -> AdminCatalogArea | None:
        res = await self.session.execute(select(AdminCatalogArea).where(AdminCatalogArea.id == area_id))
        area = res.scalar_one_or_none()
        if not area:
            return None
        if name is not None:
            area.name = name
        if enabled is not None:
            area.enabled = enabled
        await self.session.commit()
        await self.session.refresh(area)
        return area

    # ---------- Catalog: Services ----------
    async def list_services(self) -> list[AdminCatalogService]:
        res = await self.session.execute(select(AdminCatalogService).order_by(AdminCatalogService.name.asc()))
        return list(res.scalars().all())

    async def create_service(self, name: str, enabled: bool = True) -> AdminCatalogService:
        svc = AdminCatalogService(name=name, enabled=enabled)
        self.session.add(svc)
        await self.session.commit()
        await self.session.refresh(svc)
        return svc

    async def update_service(self, svc_id: int, *, name: str | None = None, enabled: bool | None = None) -> AdminCatalogService | None:
        res = await self.session.execute(select(AdminCatalogService).where(AdminCatalogService.id == svc_id))
        svc = res.scalar_one_or_none()
        if not svc:
            return None
        if name is not None:
            svc.name = name
        if enabled is not None:
            svc.enabled = enabled
        await self.session.commit()
        await self.session.refresh(svc)
        return svc

    # ---------- Settings ----------
    async def list_settings(self) -> dict[str, Any]:
        res = await self.session.execute(select(AdminSetting))
        out: dict[str, Any] = {}
        for row in res.scalars().all():
            try:
                out[row.key] = json.loads(row.value_json)
            except Exception:
                out[row.key] = row.value_json
        return out

    async def put_setting(self, key: str, value: Any) -> None:
        value_json = json.dumps(value, ensure_ascii=False)
        res = await self.session.execute(select(AdminSetting).where(AdminSetting.key == key))
        row = res.scalar_one_or_none()
        if row:
            row.value_json = value_json
        else:
            self.session.add(AdminSetting(key=key, value_json=value_json))
        await self.session.commit()

    # ---------- Flags ----------
    async def list_flags(self) -> dict[str, bool]:
        res = await self.session.execute(select(AdminFlag))
        return {row.key: bool(row.enabled) for row in res.scalars().all()}

    async def put_flag(self, key: str, enabled: bool) -> None:
        res = await self.session.execute(select(AdminFlag).where(AdminFlag.key == key))
        row = res.scalar_one_or_none()
        if row:
            row.enabled = enabled
        else:
            self.session.add(AdminFlag(key=key, enabled=enabled))
        await self.session.commit()

    # ---------- Actions ----------
    async def add_action(self, actor: str, action: str, entity: str, entity_id: str | None) -> AdminAction:
        row = AdminAction(actor=actor, action=action, entity=entity, entity_id=entity_id)
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def counts(self) -> dict[str, int]:
        def _count(model):
            return select(func.count()).select_from(model)

        areas = (await self.session.execute(_count(AdminCatalogArea))).scalar_one()
        services = (await self.session.execute(_count(AdminCatalogService))).scalar_one()
        settings = (await self.session.execute(_count(AdminSetting))).scalar_one()
        flags = (await self.session.execute(_count(AdminFlag))).scalar_one()
        actions = (await self.session.execute(_count(AdminAction))).scalar_one()
        return {
            "catalog_areas": int(areas),
            "catalog_services": int(services),
            "settings": int(settings),
            "flags": int(flags),
            "actions": int(actions),
        }
