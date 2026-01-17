import pytest
from pydantic import ValidationError

from apps.admin.app.api.schemas import CatalogCreate, CatalogUpdate, StatusPatch


def test_catalog_create_name_required_minlen():
    with pytest.raises(ValidationError):
        CatalogCreate.model_validate({"name": ""})


def test_catalog_create_default_enabled_true():
    m = CatalogCreate.model_validate({"name": "X"})
    assert m.enabled is True


def test_catalog_update_allows_partial():
    m = CatalogUpdate.model_validate({})
    assert m.name is None
    assert m.enabled is None


def test_status_patch_accepts_only_active_disabled():
    ok1 = StatusPatch.model_validate({"status": "active"})
    ok2 = StatusPatch.model_validate({"status": "disabled"})
    assert ok1.status == "active"
    assert ok2.status == "disabled"

    with pytest.raises(ValidationError):
        StatusPatch.model_validate({"status": "banned"})
