import pytest
from unittest.mock import AsyncMock

from apps.users.app.application.services.profile_service import ProfileService
from apps.users.app.infrastructure.db.models import UserProfile


@pytest.mark.asyncio
async def test_get_or_create_me_returns_existing():
    svc = ProfileService(db=None)  # type: ignore[arg-type]
    svc.repo = AsyncMock()

    existing = UserProfile(email="a@b.com", is_active=True)
    svc.repo.get_by_email = AsyncMock(return_value=existing)

    out = await svc.get_or_create_me("a@b.com")
    assert out.email == "a@b.com"
    svc.repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_get_or_create_me_creates_when_missing():
    svc = ProfileService(db=None)  # type: ignore[arg-type]
    svc.repo = AsyncMock()

    svc.repo.get_by_email = AsyncMock(return_value=None)
    created = UserProfile(email="a@b.com", is_active=True)
    svc.repo.create = AsyncMock(return_value=created)

    out = await svc.get_or_create_me("a@b.com")
    assert out.email == "a@b.com"
    svc.repo.create.assert_awaited()


@pytest.mark.asyncio
async def test_update_me_updates_existing_and_saves():
    svc = ProfileService(db=None)  # type: ignore[arg-type]
    svc.repo = AsyncMock()

    prof = UserProfile(email="a@b.com", is_active=True)
    svc.repo.get_by_email = AsyncMock(return_value=prof)
    svc.repo.save = AsyncMock(return_value=prof)

    out = await svc.update_me("a@b.com", {"full_name": "Juan", "bio": "Hola"})
    assert out.full_name == "Juan"
    assert out.bio == "Hola"
    svc.repo.save.assert_awaited()


@pytest.mark.asyncio
async def test_update_me_creates_new_when_missing_and_saves():
    svc = ProfileService(db=None)  # type: ignore[arg-type]
    svc.repo = AsyncMock()

    svc.repo.get_by_email = AsyncMock(return_value=None)

    # lo que repo.save debe devolver
    saved = UserProfile(email="a@b.com", is_active=True)
    saved.full_name = "Juan"
    svc.repo.save = AsyncMock(return_value=saved)

    out = await svc.update_me("a@b.com", {"full_name": "Juan"})
    assert out.email == "a@b.com"
    assert out.full_name == "Juan"
    svc.repo.save.assert_awaited()


@pytest.mark.asyncio
async def test_get_by_email_delegates_to_repo():
    svc = ProfileService(db=None)  # type: ignore[arg-type]
    svc.repo = AsyncMock()

    prof = UserProfile(email="a@b.com", is_active=True)
    svc.repo.get_by_email = AsyncMock(return_value=prof)

    out = await svc.get_by_email("a@b.com")
    assert out.email == "a@b.com"
    svc.repo.get_by_email.assert_awaited()


@pytest.mark.asyncio
async def test_set_active_creates_when_missing():
    svc = ProfileService(db=None)  # type: ignore[arg-type]
    svc.repo = AsyncMock()

    svc.repo.get_by_email = AsyncMock(return_value=None)
    created = UserProfile(email="x@test.com", is_active=False)
    svc.repo.create = AsyncMock(return_value=created)

    out = await svc.set_active("x@test.com", False)
    assert out.email == "x@test.com"
    assert out.is_active is False
    svc.repo.create.assert_awaited()


@pytest.mark.asyncio
async def test_set_active_updates_existing_and_saves():
    svc = ProfileService(db=None)  # type: ignore[arg-type]
    svc.repo = AsyncMock()

    prof = UserProfile(email="x@test.com", is_active=True)
    svc.repo.get_by_email = AsyncMock(return_value=prof)
    svc.repo.save = AsyncMock(return_value=prof)

    out = await svc.set_active("x@test.com", False)
    assert out.is_active is False
    svc.repo.save.assert_awaited()
