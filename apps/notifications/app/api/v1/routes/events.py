from __future__ import annotations

from fastapi import APIRouter, Query
from app.core.state import event_repo

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("/events")
def list_events(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    items = event_repo.list(limit=limit, offset=offset)
    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "case_id": e.case_id,
            "user_id": e.user_id,
            "received_at": e.received_at.isoformat(),
            "payload": e.payload,
        }
        for e in items
    ]
