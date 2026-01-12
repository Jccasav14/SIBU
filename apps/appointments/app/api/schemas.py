from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Area(str, Enum):
    PSYCHOLOGY = "PSYCHOLOGY"
    SOCIAL_WORK = "SOCIAL_WORK"
    MEDICINE = "MEDICINE"
    ACADEMIC = "ACADEMIC"
    LEGAL = "LEGAL"


class AppointmentStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"


class CreateAvailabilityIn(BaseModel):
    # IMPORTANT: We do NOT require professional_id because the platform currently identifies professionals by email.
    # - professional role: taken from JWT (email/sub)
    # - admin role: can provide professional_email to create availability for someone else
    professional_email: Optional[str] = Field(default=None, description="Only for admin: email of the professional owner")
    area: Area
    location: Optional[str] = ""
    starts_at: datetime
    ends_at: datetime


class AvailabilityOut(BaseModel):
    id: str
    professional_email: str
    area: Area
    location: Optional[str] = ""
    starts_at: datetime
    ends_at: datetime
    is_booked: bool

    class Config:
        from_attributes = True



class CreateAppointmentIn(BaseModel):
    # Either provide slot_id OR (starts_at + area).
    slot_id: Optional[str] = None
    starts_at: Optional[datetime] = None
    area: Optional[Area] = None
    professional_email: Optional[str] = None  # admin can specify
    student_id: str = Field(description="Student identifier used across the platform (e.g., national ID or student code)")
    reason: Optional[str] = ""
class AppointmentOut(BaseModel):
    id: str
    slot_id: str
    professional_email: str
    student_id: str
    status: AppointmentStatus
    reason: Optional[str] = ""
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateAppointmentStatusIn(BaseModel):
    status: AppointmentStatus
