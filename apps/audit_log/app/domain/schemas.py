from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


Severity = Literal["INFO", "WARN", "ERROR"]
Source = Literal["kafka", "rabbitmq", "mqtt", "rest"]


class AuditEventIn(BaseModel):
    source: Source
    event_type: str
    service: str | None = None
    actor: str | None = None
    actor_role: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    timestamp: datetime | None = None
    severity: Severity = "INFO"
    correlation_id: str | None = None
    tags: list[str] = Field(default_factory=list)
    ip: str | None = None
    user_agent: str | None = None
    payload_raw: dict[str, Any] = Field(default_factory=dict)
    payload_norm: dict[str, Any] = Field(default_factory=dict)


class AuditEventOut(AuditEventIn):
    event_id: str
    received_at: datetime


class Page(BaseModel):
    items: list[AuditEventOut]
    page: int
    page_size: int
    total: int


class SummaryOut(BaseModel):
    window: str
    total: int
    by_service: dict[str, int]
    by_event_type: dict[str, int]
    by_severity: dict[str, int]
    by_role: dict[str, int]
