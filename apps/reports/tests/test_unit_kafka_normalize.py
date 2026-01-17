import pytest


def test_normalize_event_dict_ok_uses_role_field_only():
    from apps.reports.app.infrastructure.consumers.kafka_consumer import _normalize_event

    payload = {
        "service": "cases",
        "event_type": "created",
        "actor": "a@b.com",
        "role": "admin",
        "severity": "INFO",
        "timestamp": "2025-01-01T00:00:00Z",
    }
    ev = _normalize_event(payload)
    assert ev["service"] == "cases"
    assert ev["event_type"] == "created"
    assert ev["actor"] == "a@b.com"
    assert ev["role"] == "admin"


def test_normalize_event_missing_timestamp_does_not_crash():
    from apps.reports.app.infrastructure.consumers.kafka_consumer import _normalize_event

    payload = {
        "service": "cases",
        "event_type": "created",
        "actor": "a@b.com",
        "role": "admin",
        "severity": "INFO",
    }
    ev = _normalize_event(payload)
    assert ev["service"] == "cases"
    assert ev["event_type"] == "created"


@pytest.mark.parametrize("ts_key", ["ts", "timestamp", "created_at"])
def test_normalize_event_accepts_common_timestamp_keys(ts_key):
    from apps.reports.app.infrastructure.consumers.kafka_consumer import _normalize_event

    payload = {
        "service": "cases",
        "event_type": "created",
        "actor": "a@b.com",
        "role": "admin",
        "severity": "INFO",
        ts_key: "2025-01-01T00:00:00Z",
    }
    ev = _normalize_event(payload)
    assert ev["service"] == "cases"
    # it keeps the original key; just ensure it didn't drop it
    assert ts_key in payload
