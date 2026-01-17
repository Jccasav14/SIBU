import pytest
from pydantic import ValidationError

from apps.audit_log.app.domain.schemas import AuditEventIn
from apps.audit_log.app.infrastructure.repository import redact


def test_schema_source_literal_validation():
    with pytest.raises(ValidationError):
        AuditEventIn.model_validate({"source": "nope", "event_type": "x"})


def test_schema_default_severity_info():
    m = AuditEventIn.model_validate({"source": "kafka", "event_type": "x"})
    assert m.severity == "INFO"
    assert m.tags == []
    assert m.payload_raw == {}
    assert m.payload_norm == {}


def test_redact_hides_sensitive_keys_nested():
    obj = {
        "password": "123",
        "nested": {"token": "abc", "ok": 1},
        "list": [{"refresh_token": "zzz"}, {"x": "y"}],
    }
    out = redact(obj)
    assert out["password"] == "***REDACTED***"
    assert out["nested"]["token"] == "***REDACTED***"
    assert out["nested"]["ok"] == 1
    assert out["list"][0]["refresh_token"] == "***REDACTED***"
    assert out["list"][1]["x"] == "y"
