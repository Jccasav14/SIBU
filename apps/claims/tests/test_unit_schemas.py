import pytest
from pydantic import ValidationError

from apps.claims.app.api.schemas import ClaimCreateIn, ClaimDocumentIn, ClaimPatchIn, ClaimReviewIn


def test_claim_create_requires_min_fields_and_lengths():
    with pytest.raises(ValidationError):
        ClaimCreateIn.model_validate(
            {
                "student_id": "a",
                "claim_type": "ACCIDENT",
                "occurred_at": "2024-01-01T00:00:00Z",
                "reported_at": "2024-01-01T00:00:00Z",
                "description": "x",
                "requested_amount": 1,
                "coverage_cap": 1,
            }
        )


def test_claim_patch_optional_fields_validate():
    m = ClaimPatchIn.model_validate({"description": "ok ok", "requested_amount": 0})
    assert m.description == "ok ok"
    assert m.requested_amount == 0


def test_review_accepts_alias_note_key():
    m = ClaimReviewIn.model_validate({"decision": "APPROVED", "note": "hello"})
    assert m.decision == "APPROVED"
    assert m.notes == "hello"


def test_document_in_validates_hash_min_len():
    with pytest.raises(ValidationError):
        ClaimDocumentIn.model_validate(
            {"doc_type": "invoice", "file_url": "https://x.y/z", "file_hash": "short"}
        )
