from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field


Window = Literal["24h", "7d", "30d"]


class ActivityRow(BaseModel):
    day: date
    service: str
    event_type: str
    severity: str
    role: str | None = None
    count: int


class CasesRow(BaseModel):
    day: date
    created: int
    shared: int
    closed: int


class AppointmentsRow(BaseModel):
    day: date
    created: int
    canceled: int
    completed: int


class SecurityRow(BaseModel):
    day: date
    login_failed: int
    access_denied: int
    suspicious_activity: int


class TopActorRow(BaseModel):
    actor: str
    role: str | None = None
    count: int


class SummaryOut(BaseModel):
    window: Window
    from_day: date
    to_day: date
    totals_by_service: list[dict[str, Any]]
    cases: list[CasesRow]
    appointments: list[AppointmentsRow]
    security: list[SecurityRow]
    top_actors: list[TopActorRow]


class ExportRequest(BaseModel):
    type: Literal["cases", "appointments", "security", "audit", "activity"]
    from_: date = Field(alias="from")
    to: date
    format: Literal["csv", "xlsx", "pdf"] = "csv"
    filters: dict[str, Any] | None = None

    model_config = {"populate_by_name": True}


class ExportAccepted(BaseModel):
    job_id: str


class ExportStatus(BaseModel):
    job_id: str
    status: str
    type: str
    created_at: str
    updated_at: str
    file_path: str | None = None
    error: str | None = None
