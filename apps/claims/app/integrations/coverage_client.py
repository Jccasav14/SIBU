from __future__ import annotations

from typing import Any

import httpx

from ..settings import settings


class CoverageClient:
    def __init__(self) -> None:
        self.base_url = str(settings.COVERAGE_URL) if settings.COVERAGE_URL else None
        self.timeout = float(getattr(settings, "COVERAGE_TIMEOUT_SECONDS", 2))

    async def get_active_policy_for_claim_type(
        self, claim_type: str, *, authorization: str | None
    ) -> tuple[dict[str, Any] | None, str | None]:
        """Best-effort lookup. Degrades gracefully.

        Returns (policy, warning). If coverage service is unreachable, returns (None, warning).
        """
        if not self.base_url:
            return None, None

        url = f"{self.base_url}/coverage/by-claim-type/{claim_type}"
        headers: dict[str, str] = {}
        if authorization:
            headers["Authorization"] = authorization

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.get(url, headers=headers)
                if r.status_code == 404:
                    return None, None
                if r.status_code >= 400:
                    return None, "Coverage service returned an error; using request payload coverage_cap"
                data = r.json()
        except Exception:
            return None, "Coverage service unreachable; using request payload coverage_cap"

        items: list[dict[str, Any]]
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict) and isinstance(data.get("items"), list):
            items = data["items"]
        else:
            items = []

        if not items:
            return None, None

        # prefer active if present
        policy = next((p for p in items if isinstance(p, dict) and p.get("is_active") is True), None) or items[0]
        return policy, None


coverage_client = CoverageClient()
