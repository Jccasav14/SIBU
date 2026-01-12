from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.appointments.app.api.schemas import (
    CreateAvailabilityIn,
    AvailabilityOut,
    CreateAppointmentIn,
    AppointmentOut,
    UpdateAppointmentStatusIn,
    AppointmentStatus,
)
from apps.appointments.app.infrastructure.db.session import get_session
from apps.appointments.app.infrastructure.db.models import AvailabilitySlot, Appointment
from apps.appointments.app.infrastructure.security.auth import CurrentUser, require_roles, get_current_user
from apps.appointments.app.infrastructure.kafka.producer import publish_event

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok"}


def _ensure_time_range(starts_at: datetime, ends_at: datetime):
    if ends_at <= starts_at:
        raise HTTPException(status_code=422, detail="ends_at must be greater than starts_at")


@router.post("/availability", response_model=AvailabilityOut)
async def create_availability(
    payload: CreateAvailabilityIn,
    user: CurrentUser = Depends(require_roles("admin", "professional")),
    db: AsyncSession = Depends(get_session),
):
    _ensure_time_range(payload.starts_at, payload.ends_at)

    # The platform currently identifies professionals by email.
    # - professional: always create for self
    # - admin: can create for others via professional_email
    professional_email = user.email
    if user.role.lower() == "admin" and payload.professional_email:
        professional_email = payload.professional_email.strip()

    slot = AvailabilitySlot(
        professional_email=professional_email,
        area=payload.area,
        location=payload.location or "",
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        is_booked=False,
    )
    db.add(slot)
    await db.commit()
    await db.refresh(slot)

    await publish_event(
        "availability.created",
        {
            "id": slot.id,
            "professional_email": slot.professional_email,
            "area": slot.area,
            "starts_at": slot.starts_at.isoformat(),
            "ends_at": slot.ends_at.isoformat(),
            "actor_user": user.email,
            "actor_role": user.role,
        },
    )

    return slot


@router.get("/availability", response_model=List[AvailabilityOut])
async def list_availability(
    professional_email: Optional[str] = Query(default=None),
    from_: Optional[datetime] = Query(default=None, alias="from"),
    to: Optional[datetime] = Query(default=None),
    only_open: bool = Query(default=False),
    user: CurrentUser = Depends(require_roles("admin", "professional")),
    db: AsyncSession = Depends(get_session),
):
    # professionals can only see their own availability unless admin
    pe = professional_email
    if user.role.lower() != "admin":
        pe = user.email

    stmt = select(AvailabilitySlot)
    if pe:
        stmt = stmt.where(AvailabilitySlot.professional_email == pe)
    if from_:
        stmt = stmt.where(AvailabilitySlot.starts_at >= from_)
    if to:
        stmt = stmt.where(AvailabilitySlot.ends_at <= to)
    if only_open:
        stmt = stmt.where(AvailabilitySlot.is_booked.is_(False))

    stmt = stmt.order_by(AvailabilitySlot.starts_at.asc())
    rows = (await db.execute(stmt)).scalars().all()
    return list(rows)


@router.post("/appointments", response_model=AppointmentOut)
async def create_appointment(
    payload: CreateAppointmentIn,
    user: CurrentUser = Depends(require_roles("admin", "professional")),
    db: AsyncSession = Depends(get_session),
):
    """Create an appointment by reserving an available 30-minute slot.

    Accepted payload:
      - slot_id + student_id
      - starts_at + area + student_id (+ professional_email for admin)
    """

    # Determine professional email
    pe = payload.professional_email
    if user.role == "professional":
        pe = user.email
    if not pe:
        raise HTTPException(status_code=422, detail="professional_email is required for admin")

    # Resolve slot
    slot: Optional[AvailabilitySlot] = None
    if payload.slot_id:
        stmt = select(AvailabilitySlot).where(AvailabilitySlot.id == payload.slot_id)
        slot = (await db.execute(stmt)).scalar_one_or_none()
        if slot is None:
            raise HTTPException(status_code=404, detail="Slot not found")
    else:
        if payload.starts_at is None or payload.area is None:
            raise HTTPException(status_code=422, detail="Either slot_id or (starts_at + area) is required")
        starts_at = payload.starts_at
        ends_at = starts_at + timedelta(minutes=30)
        stmt = select(AvailabilitySlot).where(
            AvailabilitySlot.professional_email == pe,
            AvailabilitySlot.area == payload.area,
            AvailabilitySlot.starts_at == starts_at,
            AvailabilitySlot.ends_at == ends_at,
        )
        slot = (await db.execute(stmt)).scalar_one_or_none()
        if slot is None:
            # auto-create the slot (fixed 30 min)
            slot = AvailabilitySlot(
                professional_email=pe,
                area=payload.area,
                location="",
                starts_at=starts_at,
                ends_at=ends_at,
                is_booked=False,
            )
            db.add(slot)
            await db.flush()

    # Guard booking
    if slot.is_booked:
        raise HTTPException(status_code=409, detail="Slot already booked")

    slot.is_booked = True

    appt = Appointment(
        slot_id=slot.id,
        professional_email=slot.professional_email,
        student_id=payload.student_id,
        status=AppointmentStatus.CONFIRMED,
        reason=payload.reason or "",
        created_by=user.email,
    )
    db.add(appt)
    await db.commit()
    await db.refresh(appt)

    await publish_event(
        "appointment.created",
        {
            "id": appt.id,
            "slot_id": appt.slot_id,
            "professional_email": appt.professional_email,
            "student_id": appt.student_id,
            "status": appt.status,
        },
    )

    return appt

@router.get("/appointments/mine", response_model=List[AppointmentOut])
async def list_my_appointments(
    from_: Optional[datetime] = Query(default=None, alias="from"),
    to: Optional[datetime] = Query(default=None),
    user: CurrentUser = Depends(require_roles("admin", "professional")),
    db: AsyncSession = Depends(get_session),
):
    # Professional -> appointments for their email; Admin -> own created ones by default
    stmt = select(Appointment)
    if user.role.lower() == "professional":
        stmt = stmt.where(Appointment.professional_email == user.email)
    else:
        stmt = stmt.where(Appointment.created_by == user.email)

    if from_:
        stmt = stmt.where(Appointment.created_at >= from_)
    if to:
        stmt = stmt.where(Appointment.created_at <= to)

    stmt = stmt.order_by(Appointment.created_at.desc())
    rows = (await db.execute(stmt)).scalars().all()
    return list(rows)


@router.patch("/appointments/{appointment_id}/status", response_model=AppointmentOut)
async def update_appointment_status(
    appointment_id: str,
    payload: UpdateAppointmentStatusIn,
    user: CurrentUser = Depends(require_roles("admin", "professional")),
    db: AsyncSession = Depends(get_session),
):
    stmt = select(Appointment).where(Appointment.id == appointment_id)
    appt = (await db.execute(stmt)).scalar_one_or_none()
    if appt is None:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # Professionals can only update appointments in their area (by email)
    if user.role.lower() == "professional" and appt.professional_email != user.email:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    old_status = appt.status
    appt.status = payload.status

    # If canceled, reopen the slot
    if payload.status == AppointmentStatus.CANCELED:
        slot_stmt = select(AvailabilitySlot).where(AvailabilitySlot.id == appt.slot_id)
        slot = (await db.execute(slot_stmt)).scalar_one_or_none()
        if slot:
            slot.is_booked = False

    await db.commit()
    await db.refresh(appt)

    await publish_event(
        "appointment.status_changed",
        {
            "id": appt.id,
            "old_status": old_status,
            "new_status": appt.status,
            "actor_user": user.email,
            "actor_role": user.role,
        },
    )

    return appt
