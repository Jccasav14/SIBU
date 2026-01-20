import pytest
from pydantic import ValidationError
from datetime import date

from app.api.schemas import CoveragePolicyCreate, CoveragePolicyUpdate
from app.infrastructure.postgres.models import ClaimType


def test_create_valid_to_not_before_valid_from_raises():
    with pytest.raises(ValidationError):
        CoveragePolicyCreate.model_validate(
            {
                "claim_type": ClaimType.ACCIDENT,
                "name": "Ok",
                "description": "Ok",
                "max_coverage_amount": 10,
                "currency": "USD",
                "requires_documents": [],
                "waiting_days": 0,
                "is_active": True,
                "valid_from": date(2025, 1, 10),
                "valid_to": date(2025, 1, 1),
            }
        )


def test_update_valid_to_not_before_valid_from_raises():
    with pytest.raises(ValidationError):
        CoveragePolicyUpdate.model_validate(
            {"valid_from": date(2025, 2, 10), "valid_to": date(2025, 2, 1)}
        )


def test_name_min_length_enforced():
    with pytest.raises(ValidationError):
        CoveragePolicyCreate.model_validate(
            {
                "claim_type": ClaimType.ILLNESS,
                "name": "x",
                "description": "Ok",
                "max_coverage_amount": 10,
                "valid_from": date(2025, 1, 1),
            }
        )


def test_max_coverage_amount_gt_0_enforced():
    with pytest.raises(ValidationError):
        CoveragePolicyCreate.model_validate(
            {
                "claim_type": ClaimType.OTHER,
                "name": "Ok",
                "description": "Ok",
                "max_coverage_amount": 0,
                "valid_from": date(2025, 1, 1),
            }
        )
