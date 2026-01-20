import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from apps.auth.app.application.services.auth_service import AuthService


@pytest.mark.asyncio
async def test_register_success_creates_user():
    repo = Mock()
    repo.get_by_email = AsyncMock(return_value=None)

    fake_user = SimpleNamespace(email="a@b.com", role="admin")
    repo.create = AsyncMock(return_value=fake_user)

    db = Mock()

    svc = AuthService(user_repo=repo)

    out = await svc.register(db=db, email="a@b.com", password="Sibu12345", role="admin")

    # tu método devuelve dict (según firma) — verificamos que contenga el emails
    assert out["email"] == "a@b.com"

    repo.get_by_email.assert_awaited_once()
    repo.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_register_fails_if_email_exists():
    repo = Mock()
    repo.get_by_email = AsyncMock(return_value={"id": "1", "email": "a@b.com"})
    repo.create = AsyncMock()

    db = Mock()

    svc = AuthService(user_repo=repo)

    with pytest.raises(Exception):
        await svc.register(db=db, email="a@b.com", password="Sibu12345", role="admin")

    repo.get_by_email.assert_awaited_once()
    repo.create.assert_not_called()
