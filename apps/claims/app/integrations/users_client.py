from __future__ import annotations

from typing import Any

import httpx

from ..settings import settings


class UsersClient:
    def __init__(self):
        self.base_url = str(settings.USERS_URL) if settings.USERS_URL else None

    async def validate_student_exists(self, student_id: str) -> tuple[bool, str | None]:
        """Best-effort validation. Degrades gracefully.

        Returns (ok, warning). If users service is unreachable, ok=True but with warning.
        """
        if not self.base_url:
            return True, None

        url = f"{self.base_url}/health"
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                r = await client.get(url)
                if r.status_code >= 400:
                    return True, "Users service responded with an error; validation skipped"
            return True, None
        except Exception:
            return True, "Users service is unavailable; validation skipped"
