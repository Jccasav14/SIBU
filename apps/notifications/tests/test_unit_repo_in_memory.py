from datetime import datetime, timezone

from app.domain.models.event import NotificationEvent
from app.infrastructure.repositories.in_memory_event_repo import InMemoryEventRepository


def test_repo_add_and_list_order_newest_first():
    repo = InMemoryEventRepository(maxlen=10)

    e1 = NotificationEvent(id="1", event_type="t1", payload={}, received_at=datetime.now(timezone.utc))
    e2 = NotificationEvent(id="2", event_type="t2", payload={}, received_at=datetime.now(timezone.utc))

    repo.add(e1)
    repo.add(e2)

    items = repo.list(limit=10, offset=0)
    assert [e.id for e in items] == ["2", "1"]


def test_repo_list_limit_and_offset_slice():
    repo = InMemoryEventRepository(maxlen=10)

    for i in range(5):
        repo.add(
            NotificationEvent(
                id=str(i),
                event_type="t",
                payload={"i": i},
                received_at=datetime.now(timezone.utc),
            )
        )

    # newest ids are 4,3,2,1,0
    items = repo.list(limit=2, offset=1)
    assert [e.id for e in items] == ["3", "2"]


def test_repo_maxlen_eviction_keeps_last_n():
    repo = InMemoryEventRepository(maxlen=2)

    repo.add(NotificationEvent(id="a", event_type="t", payload={}, received_at=datetime.now(timezone.utc)))
    repo.add(NotificationEvent(id="b", event_type="t", payload={}, received_at=datetime.now(timezone.utc)))
    repo.add(NotificationEvent(id="c", event_type="t", payload={}, received_at=datetime.now(timezone.utc)))

    assert repo.count() == 2
    items = repo.list(limit=10, offset=0)
    assert [e.id for e in items] == ["c", "b"]
