from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Boolean, ForeignKey, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.appointments.app.api.schemas import Area, AppointmentStatus
from apps.appointments.app.infrastructure.db.session import Base


class AvailabilitySlot(Base):
    __tablename__ = "availability_slots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    professional_email: Mapped[str] = mapped_column(String(255), index=True)
    area: Mapped[Area] = mapped_column(Enum(Area, name="area_enum"))
    location: Mapped[str] = mapped_column(String(255), default="")
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    is_booked: Mapped[bool] = mapped_column(Boolean, default=False)

    appointment: Mapped["Appointment"] = relationship(back_populates="slot", uselist=False)


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    slot_id: Mapped[str] = mapped_column(String(36), ForeignKey("availability_slots.id"), index=True)
    professional_email: Mapped[str] = mapped_column(String(255), index=True)
    student_id: Mapped[str] = mapped_column(String(255), index=True)
    status: Mapped[AppointmentStatus] = mapped_column(Enum(AppointmentStatus, name="appointment_status_enum"), default=AppointmentStatus.PENDING)
    reason: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.utcnow())

    slot: Mapped[AvailabilitySlot] = relationship(back_populates="appointment")
