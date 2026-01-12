from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from ..infrastructure.postgres.models import ClaimStatus, ClaimType, DocumentType, PaymentStatus


class HealthResponse(BaseModel):
    ok: bool
    service: str


class ClaimCreateIn(BaseModel):
    student_id: str = Field(..., min_length=3, max_length=64)
    claim_type: ClaimType
    occurred_at: datetime
    reported_at: datetime
    description: str = Field(..., min_length=3)
    requested_amount: float = Field(..., ge=0)
    coverage_cap: float = Field(..., ge=0)


class ClaimPatchIn(BaseModel):
    description: str | None = Field(None, min_length=3)
    requested_amount: float | None = Field(None, ge=0)
    coverage_cap: float | None = Field(None, ge=0)


class ClaimReviewIn(BaseModel):
    # UIs often send APPROVED/REJECTED. Backend will normalize to APPROVE/REJECT.
    decision: str = Field(..., description="APPROVE/REJECT (also accepts APPROVED/REJECTED)")
    approved_amount: float | None = Field(None, ge=0)
    # Accept both `notes` and legacy `note` key from UIs.
    notes: str | None = Field(None, alias="note")

    model_config = {"populate_by_name": True}


class ClaimPaymentIn(BaseModel):
    payment_method: str = Field(..., min_length=2, max_length=32)
    payment_reference: str = Field(..., min_length=2, max_length=128)
    paid_amount: float | None = Field(None, ge=0)


class ClaimDocumentIn(BaseModel):
    doc_type: DocumentType
    file_url: str = Field(..., min_length=5, max_length=512)
    file_hash: str = Field(..., min_length=8, max_length=128)


class ClaimDocumentOut(BaseModel):
    id: uuid.UUID
    claim_id: uuid.UUID
    doc_type: DocumentType
    file_url: str
    file_hash: str
    created_at: datetime


class ClaimOut(BaseModel):
    id: uuid.UUID
    student_id: str
    claim_type: ClaimType
    status: ClaimStatus
    occurred_at: datetime
    reported_at: datetime
    description: str
    requested_amount: float
    coverage_cap: float
    approved_amount: float | None
    payment_status: PaymentStatus
    paid_amount: float | None
    paid_at: datetime | None
    payment_method: str | None
    payment_reference: str | None
    created_at: datetime
    updated_at: datetime


class ClaimEventOut(BaseModel):
    id: uuid.UUID
    claim_id: uuid.UUID
    actor: str
    event_type: str
    payload: dict[str, Any]
    created_at: datetime


class ClaimsOverviewOut(BaseModel):
    total: int
    by_status: dict[str, int]
    total_paid: float


class ListClaimsOut(BaseModel):
    items: list[ClaimOut]
    limit: int
    offset: int