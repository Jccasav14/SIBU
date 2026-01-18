import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from apps.users.app.application.services.profile_service import ProfileService


@pytest.mark.asyncio
async def test_update_me_calls_repo_update():
    svc = ProfileService(db=None)  # type: ignore[arg-type]

    prof = SimpleNamespace(email="a@b.com", full_name="Old", is_active=True)
    prof.save = AsyncMock(return_value=None)  # porque tu service parece NO usar el return de save()

    svc.repo = AsyncMock()
    svc.repo.get_by_email = AsyncMock(return_value=prof)

    out = await svc.update_me("a@b.com", {"full_name": "Juan"})

    # tu service retorna el objeto, no dict
    assert out.full_name == "Juan"
    svc.repo.get_by_email.assert_awaited()
    prof.save.assert_awaited()
