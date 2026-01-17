from types import SimpleNamespace

from app.application.services.notifier import NotifierService
from app.domain.models.event import NotificationEvent


class FakeRepo:
    def __init__(self):
        self.added: list[NotificationEvent] = []

    def add(self, event: NotificationEvent) -> None:
        self.added.append(event)


def test_handle_case_event_extracts_case_id_from_case_id():
    repo = FakeRepo()
    svc = NotifierService(repo)  # type: ignore[arg-type]

    ev = svc.handle_case_event("case.created", {"case_id": "C-1", "created_by": "U-1"})

    assert ev.case_id == "C-1"
    assert ev.user_id == "U-1"
    assert repo.added[-1].id == ev.id


def test_handle_case_event_falls_back_case_id_from_id():
    repo = FakeRepo()
    svc = NotifierService(repo)  # type: ignore[arg-type]

    ev = svc.handle_case_event("case.updated", {"id": 123})

    assert ev.case_id == "123"


def test_handle_case_event_user_id_priority_created_by_then_created_by_user_id_then_user_id():
    repo = FakeRepo()
    svc = NotifierService(repo)  # type: ignore[arg-type]

    ev1 = svc.handle_case_event("e", {"case_id": "1", "created_by": "A", "user_id": "Z"})
    assert ev1.user_id == "A"

    ev2 = svc.handle_case_event("e", {"case_id": "1", "created_by_user_id": "B", "user_id": "Z"})
    assert ev2.user_id == "B"

    ev3 = svc.handle_case_event("e", {"case_id": "1", "user_id": "C"})
    assert ev3.user_id == "C"


def test_handle_case_event_returns_notification_event_and_repo_add_called():
    repo = FakeRepo()
    svc = NotifierService(repo)  # type: ignore[arg-type]

    payload = {"case_id": "X", "created_by": "Y", "k": "v"}
    ev = svc.handle_case_event("case.event", payload)

    assert isinstance(ev, NotificationEvent)
    assert ev.payload == payload
    assert repo.added and repo.added[-1] == ev
    assert ev.received_at.tzinfo is not None
