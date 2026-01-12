from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Iterable

# Avoid hard dependency at import time; Mongo uses 1 / -1 for sort directions.
ASCENDING = 1
DESCENDING = -1

from ..domain.schemas import AuditEventIn
from .mongo import mongo


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


SENSITIVE_KEYS = {
    "password",
    "pass",
    "pwd",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "secret",
    "api_key",
    "jwt",
}


def redact(obj: Any) -> Any:
    """Redacts sensitive values recursively for API responses.

    NOTE: We still store raw payload in MongoDB for audit integrity,
    but we must never expose secrets back to clients.
    """
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if str(k).lower() in SENSITIVE_KEYS:
                out[k] = "***REDACTED***"
            else:
                out[k] = redact(v)
        return out
    if isinstance(obj, list):
        return [redact(x) for x in obj]
    return obj


class AuditRepository:
    def __init__(self) -> None:
        self._col_name = "audit_events"
        # Create indexes best-effort
        self._indexes_created = False

    @property
    def col(self):
        return mongo.db[self._col_name]

    @property
    def col(self):
        return mongo.db[self._col_name]

    async def ensure_indexes(self) -> None:
        if self._indexes_created:
            return
        # These calls are idempotent in Mongo
        await self.col.create_index([("event_id", ASCENDING)], unique=True)
        await self.col.create_index([("timestamp", DESCENDING)])
        await self.col.create_index([("received_at", DESCENDING)])
        await self.col.create_index([("service", ASCENDING), ("event_type", ASCENDING)])
        await self.col.create_index([("actor", ASCENDING)])
        await self.col.create_index([("entity_type", ASCENDING), ("entity_id", ASCENDING)])
        await self.col.create_index([("severity", ASCENDING)])
        await self.col.create_index([("source", ASCENDING)])
        self._indexes_created = True

    async def insert_event(self, event_id: str, doc: dict[str, Any]) -> None:
        await self.ensure_indexes()
        await self.col.insert_one({"event_id": event_id, **doc})

    async def get_event(self, event_id: str) -> dict[str, Any] | None:
        await self.ensure_indexes()
        return await self.col.find_one({"event_id": event_id}, {"_id": 0})

    async def find_events(
        self,
        *,
        filters: dict[str, Any],
        page: int,
        page_size: int,
        sort: str,
    ) -> tuple[list[dict[str, Any]], int]:
        await self.ensure_indexes()
        q: dict[str, Any] = {}
        # Time range
        if filters.get("from") or filters.get("to"):
            q["timestamp"] = {}
            if filters.get("from"):
                q["timestamp"]["$gte"] = filters["from"]
            if filters.get("to"):
                q["timestamp"]["$lte"] = filters["to"]

        # Exact matches
        for key in [
            "service",
            "event_type",
            "actor",
            "actor_role",
            "entity_type",
            "entity_id",
            "severity",
            "source",
            "correlation_id",
        ]:
            if filters.get(key):
                q[key] = filters[key]

        # Free text query
        if filters.get("q"):
            pat = re.escape(filters["q"])
            rx = {"$regex": pat, "$options": "i"}
            q["$or"] = [
                {"event_type": rx},
                {"service": rx},
                {"actor": rx},
                {"entity_id": rx},
                {"entity_type": rx},
                {"correlation_id": rx},
            ]

        sort_field, sort_dir = ("timestamp", DESCENDING)
        if sort == "timestamp_asc":
            sort_field, sort_dir = ("timestamp", ASCENDING)

        total = await self.col.count_documents(q)
        cursor = (
            self.col.find(q, {"_id": 0})
            .sort(sort_field, sort_dir)
            .skip((page - 1) * page_size)
            .limit(page_size)
        )

        items = [doc async for doc in cursor]
        return items, total

    async def find_by_entity(self, entity_type: str, entity_id: str, limit: int = 200) -> list[dict[str, Any]]:
        await self.ensure_indexes()
        cursor = (
            self.col.find({"entity_type": entity_type, "entity_id": entity_id}, {"_id": 0})
            .sort("timestamp", DESCENDING)
            .limit(limit)
        )
        return [doc async for doc in cursor]

    async def aggregate_summary(self, since: datetime) -> dict[str, Any]:
        await self.ensure_indexes()
        pipeline = [
            {"$match": {"timestamp": {"$gte": since}}},
            {
                "$facet": {
                    "total": [{"$count": "count"}],
                    "by_service": [
                        {"$group": {"_id": "$service", "count": {"$sum": 1}}},
                        {"$sort": {"count": -1}},
                        {"$limit": 20},
                    ],
                    "by_event_type": [
                        {"$group": {"_id": "$event_type", "count": {"$sum": 1}}},
                        {"$sort": {"count": -1}},
                        {"$limit": 20},
                    ],
                    "by_severity": [
                        {"$group": {"_id": "$severity", "count": {"$sum": 1}}},
                    ],
                    "by_role": [
                        {"$group": {"_id": "$actor_role", "count": {"$sum": 1}}},
                    ],
                }
            },
        ]
        res = await self.col.aggregate(pipeline).to_list(length=1)
        if not res:
            return {"total": 0, "by_service": {}, "by_event_type": {}, "by_severity": {}, "by_role": {}}
        r = res[0]
        total = (r.get("total") or [{"count": 0}])[0].get("count", 0)
        return {
            "total": total,
            "by_service": {d["_id"] or "unknown": d["count"] for d in r.get("by_service", [])},
            "by_event_type": {d["_id"] or "unknown": d["count"] for d in r.get("by_event_type", [])},
            "by_severity": {d["_id"] or "unknown": d["count"] for d in r.get("by_severity", [])},
            "by_role": {d["_id"] or "unknown": d["count"] for d in r.get("by_role", [])},
        }


def normalize_event(in_event: AuditEventIn, *, event_id: str, received_at: datetime, correlation_id: str) -> dict[str, Any]:
    ts = in_event.timestamp or received_at
    return {
        "source": in_event.source,
        "event_type": in_event.event_type,
        "service": in_event.service,
        "actor": in_event.actor,
        "actor_role": in_event.actor_role,
        "entity_type": in_event.entity_type,
        "entity_id": in_event.entity_id,
        "timestamp": ts,
        "received_at": received_at,
        "correlation_id": correlation_id,
        "ip": in_event.ip,
        "user_agent": in_event.user_agent,
        "severity": in_event.severity,
        "tags": in_event.tags,
        "payload_raw": in_event.payload_raw,
        "payload_norm": in_event.payload_norm,
    }
