import pytest
from pydantic import ValidationError

from apps.cases.app.api.schemas import CaseCreate, CaseShare, CaseNoteCreate


def test_case_create_requires_min_lengths():
    with pytest.raises(ValidationError):
        CaseCreate.model_validate(
            {"student_id": "s1", "owner_area": "PSY", "title": "x", "description": "y", "priority": "LOW"}
        )


def test_case_share_requires_user_id_or_area():
    with pytest.raises(ValidationError):
        CaseShare.model_validate({"permission": "READ"})


def test_case_share_accepts_user_id():
    m = CaseShare.model_validate({"user_id": "u1", "permission": "READ"})
    assert m.user_id == "u1"
    assert m.area is None


def test_note_create_content_required():
    with pytest.raises(ValidationError):
        CaseNoteCreate.model_validate({"kind": "NOTE", "content": ""})
