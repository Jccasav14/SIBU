import pytest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from fastapi import HTTPException

from apps.appointments.app.api.routes import _ensure_time_range, create_appointment
from apps.appointments.app.api.schemas import CreateAppointmentIn
from apps.appointments.app.infrastructure.db.models import AvailabilitySlot


class _ScalarResult:
    def __init__(self, scalar):
        self._scalar = scalar

    def scalar_one_or_none(self):
        return self._scalar


class FakeDb:
    def __init__(self, slot: AvailabilitySlot):
        self._slot = slot
        self.added = []

    async def execute(self, stmt):
        # In this unit test we only care that the slot is returned when selecting AvailabilitySlot
        return _ScalarResult(self._slot)

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        return None

    async def refresh(self, obj):
        if getattr(obj, "id", None) in (None, ""):
            obj.id = "appt-1"
        if getattr(obj, "created_at", None) is None:
            obj.created_at = datetime.now(timezone.utc)


def test_ensure_time_range_raises_422():
    starts = datetime.now(timezone.utc)
    ends = starts
    with pytest.raises(HTTPException) as e:
        _ensure_time_range(starts, ends)
    assert e.value.status_code == 422


@pytest.mark.asyncio
async def test_create_appointment_slot_already_booked_409():
    starts = datetime.now(timezone.utc)
    ends = starts + timedelta(minutes=30)

    slot = SimpleNamespace(
        id="slot-1",
        professional_email="pro@test.com",
        area="PSYCHOLOGY",
        location="",
        starts_at=starts,
        ends_at=ends,
        is_booked=True,
    )
    db = FakeDb(slot=slot)

    payload = CreateAppointmentIn.model_validate(
        {"slot_id": "slot-1", "student_id": "stu-1", "reason": "x"}
    )
    user = SimpleNamespace(email="pro@test.com", role="professional")

    with pytest.raises(HTTPException) as e:
        await create_appointment(payload=payload, user=user, db=db)

    assert e.value.status_code == 409
    assert e.value.detail == "Slot already booked"
