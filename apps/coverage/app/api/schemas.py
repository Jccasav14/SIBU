from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.infrastructure.postgres.models import ClaimType


class CoveragePolicyBase(BaseModel):
    claim_type: ClaimType
    name: str = Field(min_length=2, max_length=200)
    description: str = Field(min_length=2)
    max_coverage_amount: float = Field(gt=0)
    currency: str = Field(default="USD", min_length=1, max_length=8)
    requires_documents: List[str] = Field(default_factory=list)
    waiting_days: int = Field(default=0, ge=0)
    is_active: bool = True
    valid_from: date
    valid_to: Optional[date] = None

    @field_validator("valid_to")
    @classmethod
    def valid_to_not_before_from(cls, v: Optional[date], info):
        valid_from = info.data.get("valid_from")
        if v is not None and valid_from is not None and v < valid_from:
            raise ValueError("valid_to cannot be before valid_from")
        return v


class CoveragePolicyCreate(CoveragePolicyBase):
    pass


class CoveragePolicyUpdate(BaseModel):
    claim_type: Optional[ClaimType] = None
    name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    description: Optional[str] = Field(default=None, min_length=2)
    max_coverage_amount: Optional[float] = Field(default=None, gt=0)
    currency: Optional[str] = Field(default=None, min_length=1, max_length=8)
    requires_documents: Optional[List[str]] = None
    waiting_days: Optional[int] = Field(default=None, ge=0)
    is_active: Optional[bool] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None

    @field_validator("valid_to")
    @classmethod
    def valid_to_not_before_from(cls, v: Optional[date], info):
        valid_from = info.data.get("valid_from")
        if v is not None and valid_from is not None and v < valid_from:
            raise ValueError("valid_to cannot be before valid_from")
        return v


class CoveragePolicyOut(BaseModel):
    id: uuid.UUID
    claim_type: ClaimType
    name: str
    description: str
    max_coverage_amount: float
    currency: str
    requires_documents: List[str]
    waiting_days: int
    is_active: bool
    valid_from: date
    valid_to: Optional[date]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
