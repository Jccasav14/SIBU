from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any

from aiokafka import AIOKafkaConsumer

from ...settings import settings
from ..postgres.db import SessionLocal
from ..postgres.repository import ReportsRepository

logger = logging.getLogger("reports.kafka")


def _parse_dt(v: Any) -> datetime | None:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        # epoch seconds
        return datetime.utcfromtimestamp(v)
    if isinstance(v, str):
        try:
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        except Exception:
            return None
    return None


def _normalize_event(payload: dict[str, Any]) -> dict[str, Any]:
    # Try common shapes from other services
    ts = payload.get("ts") or payload.get("timestamp") or payload.get("created_at")
    service = payload.get("service") or payload.get("source") or payload.get("aggregate") or "unknown"
    event_type = payload.get("event_type") or payload.get("type") or payload.get("event") or "unknown"
    severity = payload.get("severity") or payload.get("level") or "info"
    actor = payload.get("actor") or payload.get("user") or payload.get("email")
    role = payload.get("role")
    return {
        "ts": _parse_dt(ts),
        "service": str(service),
        "event_type": str(event_type),
        "severity": str(severity),
        "actor": str(actor) if actor else None,
        "role": str(role) if role else None,
    }


def _signals(event_type: str) -> tuple[str | None, str | None]:
    et = event_type.lower()
    if "case" in et:
        if "created" in et:
            return ("case", "created")
        if "shared" in et:
            return ("case", "shared")
        if "closed" in et:
            return ("case", "closed")
    if "appointment" in et:
        if "created" in et:
            return ("appointment", "created")
        if "cancel" in et:
            return ("appointment", "canceled")
        if "complete" in et:
            return ("appointment", "completed")
    if "login_failed" in et or ("login" in et and "fail" in et):
        return ("security", "login_failed")
    if "access_denied" in et or ("access" in et and "denied" in et):
        return ("security", "access_denied")
    if "suspicious" in et:
        return ("security", "suspicious_activity")
    return (None, None)


async def run_kafka_consumer(stop_event: asyncio.Event) -> None:
    topics = [t.strip() for t in settings.KAFKA_TOPICS.split(",") if t.strip()]
    if not topics:
        logger.warning("no kafka topics configured")
        return

    while not stop_event.is_set():
        consumer: AIOKafkaConsumer | None = None
        try:
            consumer = AIOKafkaConsumer(
                *topics,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP,
                group_id=settings.KAFKA_GROUP_ID,
                enable_auto_commit=True,
                auto_offset_reset="earliest",
            )
            await consumer.start()
            logger.info("kafka consumer started", extra={"topics": topics})

            async for msg in consumer:
                if stop_event.is_set():
                    break
                try:
                    payload = json.loads(msg.value.decode("utf-8"))
                    if not isinstance(payload, dict):
                        continue
                except Exception:
                    continue

                norm = _normalize_event(payload)
                sig_group, sig_name = _signals(norm["event_type"])

                async with SessionLocal() as session:
                    repo = ReportsRepository(session)
                    await repo.record_event(
                        ts=norm["ts"],
                        service=norm["service"],
                        event_type=norm["event_type"],
                        severity=norm["severity"],
                        actor=norm["actor"],
                        role=norm["role"],
                    )
                    if sig_group == "case":
                        await repo.record_case_signal(ts=norm["ts"], signal=sig_name or "created")
                    elif sig_group == "appointment":
                        await repo.record_appointment_signal(ts=norm["ts"], signal=sig_name or "created")
                    elif sig_group == "security":
                        await repo.record_security_signal(ts=norm["ts"], signal=sig_name or "login_failed")
                    await session.commit()

        except Exception as e:
            logger.warning("kafka unavailable (degraded mode)", extra={"error": str(e)})
            await asyncio.sleep(settings.KAFKA_RETRY_BACKOFF_SEC)
        finally:
            if consumer is not None:
                try:
                    await consumer.stop()
                except Exception:
                    pass

    logger.info("kafka consumer stopped")
