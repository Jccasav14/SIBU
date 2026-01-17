import pytest
from pydantic import ValidationError
from datetime import datetime, timezone, timedelta

from apps.appointments.app.api.schemas import (
    CreateAvailabilityIn,
    CreateAppointmentIn,
    UpdateAppointmentStatusIn,
)


def test_create_availability_requires_fields():
    with pytest.raises(ValidationError):
        CreateAvailabilityIn.model_validate({})


def test_create_availability_invalid_enum_area():
    starts = datetime.now(timezone.utc)
    ends = starts + timedelta(minutes=30)
    with pytest.raises(ValidationError):
        CreateAvailabilityIn.model_validate(
            {"area": "NOT_A_REAL_AREA", "starts_at": starts, "ends_at": ends}
        )


def test_create_availability_ok_minimal():
    starts = datetime.now(timezone.utc)
    ends = starts + timedelta(minutes=30)
    m = CreateAvailabilityIn.model_validate(
        {"area": "PSYCHOLOGY", "starts_at": starts, "ends_at": ends}
    )
    assert m.area.value == "PSYCHOLOGY"
    assert m.location == ""


def test_create_appointment_requires_student_id():
    with pytest.raises(ValidationError):
        CreateAppointmentIn.model_validate({"slot_id": "x"})


def test_create_appointment_allows_slot_id_path():
    m = CreateAppointmentIn.model_validate({"slot_id": "slot-1", "student_id": "stu-1"})
    assert m.slot_id == "slot-1"
    assert m.student_id == "stu-1"


def test_update_status_requires_status():
    with pytest.raises(ValidationError):
        UpdateAppointmentStatusIn.model_validate({})


def test_update_status_invalid_enum():
    with pytest.raises(ValidationError):
        UpdateAppointmentStatusIn.model_validate({"status": "NOPE"})
