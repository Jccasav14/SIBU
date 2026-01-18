import pytest
from unittest.mock import AsyncMock, MagicMock

from apps.users.app.application.services.profile_service import ProfileService


@pytest.mark.asyncio
async def test_get_or_create_me_creates_when_missing():
    svc = ProfileService(db=None)  # type: ignore[arg-type]
    svc.repo = AsyncMock()
    svc.repo.get_by_email = AsyncMock(return_value=None)
    svc.repo.create = AsyncMock(return_value={"email": "a@b.com", "is_active": True})

    out = await svc.get_or_create_me("a@b.com")
    assert out["email"] == "a@b.com"
    svc.repo.create.assert_awaited()


@pytest.mark.asyncio
async def test_update_me_calls_repo_update():
    svc = ProfileService(db=None)  # type: ignore[arg-type]

    # lo que esperamos que retorne al final
    saved = {"email": "a@b.com", "full_name": "Juan"}

    # simula el "document/model" que repo.update_by_email retorna y que luego se hace .save()
    doc = MagicMock()
    doc.save = AsyncMock(return_value=saved)

    svc.repo = MagicMock()
    svc.repo.update_by_email = AsyncMock(return_value=doc)

    out = await svc.update_me("a@b.com", {"full_name": "Juan"})
    assert out["full_name"] == "Juan"

    svc.repo.update_by_email.assert_awaited()
    doc.save.assert_awaited()
