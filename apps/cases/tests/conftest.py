import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any, AsyncGenerator, Dict, List, Optional
from uuid import uuid4

import pytest
import jwt as pyjwt


@pytest.fixture(scope="session", autouse=True)
def _testing_env() -> None:
    os.environ.setdefault("SIBU_TESTING", "1")
    os.environ.setdefault("AUTH_DISABLED", "false")
    os.environ.setdefault("JWT_SECRET", "TEST_SECRET_CASES")
    os.environ.setdefault("JWT_ALGORITHM", "HS256")
    # make sure producer is never required
    os.environ.setdefault("KAFKA_REQUIRED", "false")


def _now() -> datetime:
    return datetime.now(timezone.utc)


class FakeCaseService:
    """
    In-memory CaseService replacement (NO DB).
    Returns objects with attributes (FastAPI uses from_attributes=True).
    """

    def __init__(self, _db: Any):
        # store in module-level singleton to keep state across requests in same test
        # (client fixture recreates this class patch each test, but state lives here)
        pass

    # shared state
    _cases: Dict[str, Any] = {}
    _notes: Dict[str, List[Any]] = {}
    _timeline: Dict[str, List[Any]] = {}

    def _ensure_case(self, case_id: str):
        if case_id not in self._cases:
            from apps.cases.app.domain.exceptions import NotFoundError
            raise NotFoundError("Case not found")
        return self._cases[case_id]

    def _can_access(self, case: Any, user: Any) -> None:
        # simplified: admin always; otherwise creator/assigned/owner_area
        from apps.cases.app.domain.exceptions import ForbiddenError
        if "admin" in (user.roles or []):
            return
        if case.created_by_user_id == user.user_id:
            return
        if case.assigned_professional_id and case.assigned_professional_id == user.user_id:
            return
        if user.area and user.area == case.owner_area:
            return
        raise ForbiddenError("Forbidden")

    def create_case(
        self,
        *,
        student_id: str,
        owner_area: str,
        title: str,
        description: str,
        priority: Any,
        user: Any,
    ):
        from apps.cases.app.domain.enums import CaseStatus

        case_id = str(uuid4())
        now = _now()
        obj = SimpleNamespace(
            id=case_id,
            student_id=student_id,
            owner_area=owner_area,
            created_by_user_id=user.user_id,
            assigned_professional_id=None,
            title=title,
            description=description,
            status=CaseStatus.OPEN,
            priority=priority,
            created_at=now,
            updated_at=now,
        )
        self._cases[case_id] = obj
        self._notes.setdefault(case_id, [])
        self._timeline.setdefault(case_id, [])
        self._timeline[case_id].append(
            SimpleNamespace(
                id=str(uuid4()),
                case_id=case_id,
                type="CREATED",
                data={"title": title},
                actor_user_id=user.user_id,
                created_at=now,
            )
        )
        return obj

    def list_cases(self, *, status=None, priority=None, mine: bool, user: Any, limit: int, offset: int):
        items = list(self._cases.values())
        # filter mine
        if mine:
            items = [c for c in items if c.created_by_user_id == user.user_id]
        # naive filters
        if status is not None:
            items = [c for c in items if c.status == status]
        if priority is not None:
            items = [c for c in items if c.priority == priority]
        return items[offset : offset + limit]

    def list_cases_by_student(self, *, student_id: str, status=None, priority=None, user: Any, limit: int, offset: int):
        items = [c for c in self._cases.values() if c.student_id == student_id]
        # access check per-case
        out = []
        for c in items:
            try:
                self._can_access(c, user)
                out.append(c)
            except Exception:
                continue
        if status is not None:
            out = [c for c in out if c.status == status]
        if priority is not None:
            out = [c for c in out if c.priority == priority]
        return out[offset : offset + limit]

    def get_case(self, case_id: str, user: Any):
        c = self._ensure_case(case_id)
        self._can_access(c, user)
        return c

    def update_case(self, case_id: str, *, title=None, description=None, priority=None, user: Any):
        from apps.cases.app.domain.exceptions import BadRequestError

        c = self._ensure_case(case_id)
        self._can_access(c, user)

        if title is None and description is None and priority is None:
            raise BadRequestError("No fields to update")

        if title is not None:
            c.title = title
        if description is not None:
            c.description = description
        if priority is not None:
            c.priority = priority
        c.updated_at = _now()

        self._timeline[case_id].append(
            SimpleNamespace(
                id=str(uuid4()),
                case_id=case_id,
                type="UPDATED",
                data={"title": title, "description": description},
                actor_user_id=user.user_id,
                created_at=_now(),
            )
        )
        return c

    def assign(self, case_id: str, professional_id: str, user: Any):
        c = self._ensure_case(case_id)
        self._can_access(c, user)
        c.assigned_professional_id = professional_id
        c.updated_at = _now()
        self._timeline[case_id].append(
            SimpleNamespace(
                id=str(uuid4()),
                case_id=case_id,
                type="ASSIGNED",
                data={"professional_id": professional_id},
                actor_user_id=user.user_id,
                created_at=_now(),
            )
        )
        return c

    def change_status(self, case_id: str, new_status: Any, user: Any):
        c = self._ensure_case(case_id)
        self._can_access(c, user)
        c.status = new_status
        c.updated_at = _now()
        self._timeline[case_id].append(
            SimpleNamespace(
                id=str(uuid4()),
                case_id=case_id,
                type="STATUS_CHANGED",
                data={"status": str(new_status)},
                actor_user_id=user.user_id,
                created_at=_now(),
            )
        )
        return c

    def share(self, case_id: str, *, user_id=None, area=None, permission=None, user: Any):
        c = self._ensure_case(case_id)
        self._can_access(c, user)
        # we don't persist sharing rules here; just timeline
        self._timeline[case_id].append(
            SimpleNamespace(
                id=str(uuid4()),
                case_id=case_id,
                type="SHARED",
                data={"user_id": user_id, "area": area, "permission": str(permission)},
                actor_user_id=user.user_id,
                created_at=_now(),
            )
        )
        c.updated_at = _now()
        return c

    def add_note(self, case_id: str, *, kind: str, content: str, user: Any):
        c = self._ensure_case(case_id)
        self._can_access(c, user)
        note = SimpleNamespace(
            id=str(uuid4()),
            case_id=case_id,
            author_user_id=user.user_id,
            author_area=user.area or "unknown",
            kind=kind,
            content=content,
            created_at=_now(),
        )
        self._notes.setdefault(case_id, []).append(note)
        self._timeline[case_id].append(
            SimpleNamespace(
                id=str(uuid4()),
                case_id=case_id,
                type="NOTE_ADDED",
                data={"note_id": note.id, "kind": kind},
                actor_user_id=user.user_id,
                created_at=_now(),
            )
        )
        return note

    def list_notes(self, case_id: str, user: Any, *, limit: int, offset: int):
        c = self._ensure_case(case_id)
        self._can_access(c, user)
        notes = self._notes.get(case_id, [])
        return notes[offset : offset + limit]

    def timeline_for_case(self, case_id: str, user: Any, *, limit: int, offset: int):
        c = self._ensure_case(case_id)
        self._can_access(c, user)
        events = self._timeline.get(case_id, [])
        return events[offset : offset + limit]


@pytest.fixture()
def make_token():
    def _mk(sub: str = "admin-1", roles=None, area: str | None = "PSY"):
        if roles is None:
            roles = ["admin"]
        now = _now()
        payload = {
            "sub": sub,
            "roles": roles,
            "area": area,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=30)).timestamp()),
        }
        return pyjwt.encode(payload, os.environ["JWT_SECRET"], algorithm=os.environ["JWT_ALGORITHM"])
    return _mk


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch):
    from fastapi.testclient import TestClient

    # Import after env
    from apps.cases.app import main as main_mod
    from apps.cases.app.api import routes as routes_mod
    from apps.cases.app.infrastructure.db import session as session_mod
    from apps.cases.app.infrastructure.messaging import state as kafka_state

    # No DB tables + no kafka startup
    async def _noop() -> None:
        return None

    monkeypatch.setattr(main_mod.app.router, "startup", _noop)
    monkeypatch.setattr(main_mod.app.router, "shutdown", _noop)

    # ensure producer is None so routes won't send events
    kafka_state.producer = None

    # Patch service used by routes
    monkeypatch.setattr(routes_mod, "CaseService", FakeCaseService)

    # Override DB dependency
    async def _override_get_db() -> AsyncGenerator[None, None]:
        yield None

    main_mod.app.dependency_overrides[session_mod.get_db] = _override_get_db

    with TestClient(main_mod.app) as c:
        yield c

    main_mod.app.dependency_overrides.clear()
