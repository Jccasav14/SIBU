from __future__ import annotations

from collections import deque
from typing import Deque, List

from app.domain.models.event import NotificationEvent

class InMemoryEventRepository:
    """Simple repo for debugging/demo. Keeps last N events in memory."""

    def __init__(self, maxlen: int = 1000) -> None:
        self._events: Deque[NotificationEvent] = deque(maxlen=maxlen)

    def add(self, event: NotificationEvent) -> None:
        self._events.appendleft(event)

    def list(self, limit: int = 50, offset: int = 0) -> List[NotificationEvent]:
        items = list(self._events)
        return items[offset: offset + limit]

    def count(self) -> int:
        return len(self._events)
