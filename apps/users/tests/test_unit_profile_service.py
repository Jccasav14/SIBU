import pytest
from unittest.mock import AsyncMock, MagicMock

from apps.users.app.application.services.profile_service import ProfileService


@pytest.mark.asyncio
async def test_update_me_calls_repo_update():
    svc = ProfileService(db=None)  # type: ignore[arg-type]

    # Simula que el perfil EXISTE (si no, tu service puede crear o lanzar error)
    svc.repo = AsyncMock()
    svc.repo.get_by_email = AsyncMock(return_value={"email": "a@b.com", "full_name": "Old"})

    saved = {"email": "a@b.com", "full_name": "Juan"}

    # update_by_email retorna un "doc" con save async
    doc = MagicMock()
    doc.save = AsyncMock(return_value=saved)

    svc.repo.update_by_email = AsyncMock(return_value=doc)

    out = await svc.update_me("a@b.com", {"full_name": "Juan"})

    assert out["full_name"] == "Juan"
    svc.repo.get_by_email.assert_awaited()
    svc.repo.update_by_email.assert_awaited()
    doc.save.assert_awaited()
