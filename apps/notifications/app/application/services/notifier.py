from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from app.domain.models.event import NotificationEvent
from app.infrastructure.repositories.in_memory_event_repo import InMemoryEventRepository

class NotifierService:
    """Application service: decides what to do when an event arrives."""

    def __init__(self, repo: InMemoryEventRepository) -> None:
        self.repo = repo

    def handle_case_event(self, event_type: str, payload: Dict[str, Any]) -> NotificationEvent:
        case_id: Optional[str] = payload.get("case_id") or payload.get("id")
        user_id: Optional[str] = payload.get("created_by") or payload.get("created_by_user_id") or payload.get("user_id")

        ev = NotificationEvent(
            id=str(uuid4()),
            event_type=event_type,
            payload=payload,
            received_at=datetime.now(timezone.utc),
            case_id=str(case_id) if case_id else None,
            user_id=str(user_id) if user_id else None,
        )

        self.repo.add(ev)

        pretty = json.dumps(payload, ensure_ascii=False)
        print(f"[notifications] event={event_type} case_id={ev.case_id} user={ev.user_id} payload={pretty}")

        return ev
