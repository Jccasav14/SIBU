from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

@dataclass(frozen=True)
class NotificationEvent:
    id: str
    event_type: str
    payload: Dict[str, Any]
    received_at: datetime
    case_id: Optional[str] = None
    user_id: Optional[str] = None
