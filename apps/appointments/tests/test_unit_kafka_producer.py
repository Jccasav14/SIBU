from apps.appointments.app.infrastructure.kafka.producer import _guess_entity_type


def test_guess_entity_type_availability():
    assert _guess_entity_type("availability.created") == "availability"


def test_guess_entity_type_appointment():
    assert _guess_entity_type("appointment.created") == "appointment"


def test_guess_entity_type_unknown():
    assert _guess_entity_type("something.else") == "unknown"
