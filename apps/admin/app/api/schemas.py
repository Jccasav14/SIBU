from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, ConfigDict


class CatalogItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    enabled: bool


class CatalogCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    enabled: bool = True


class CatalogUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    enabled: bool | None = None


class SettingValue(BaseModel):
    value: Any


class FlagValue(BaseModel):
    enabled: bool


Status = Literal["active", "disabled"]


class StatusPatch(BaseModel):
    status: Status


class OverviewOut(BaseModel):
    counts: dict[str, int]
    flags: dict[str, bool]
    settings: dict[str, Any]
    catalog: dict[str, list[CatalogItem]]
    users_service: dict[str, Any] | None = None
