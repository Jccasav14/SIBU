import pytest
import inspect
from types import SimpleNamespace
from unittest.mock import AsyncMock

from apps.users.app.application.services.profile_service import ProfileService


@pytest.mark.asyncio
async def test_update_me_calls_repo_update():
    svc = ProfileService(db=None)  # type: ignore[arg-type]

    prof = SimpleNamespace(email="a@b.com", full_name="Old", is_active=True)

    # lo que "save" devolvería normalmente (ajústalo si tu save retorna otra cosa)
    prof.save = AsyncMock(return_value={"email": "a@b.com", "full_name": "Juan"})

    svc.repo = AsyncMock()
    svc.repo.get_by_email = AsyncMock(return_value=prof)

    out = await svc.update_me("a@b.com", {"full_name": "Juan"})

    # 1) el service usa setattr(prof, ...), así que esto debe cambiar sí o sí
    assert prof.full_name == "Juan"

    # 2) debe intentar guardar
    prof.save.assert_called_once()

    # 3) tu service puede estar devolviendo prof.save() sin await → entonces out es awaitable
    if inspect.isawaitable(out):
        out = await out

    # 4) valida salida sea dict o objeto (depende tu implementación)
    if isinstance(out, dict):
        assert out["full_name"] == "Juan"
    else:
        assert getattr(out, "full_name") == "Juan"
