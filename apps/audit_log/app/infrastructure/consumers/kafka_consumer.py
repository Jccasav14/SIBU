from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from ...domain.schemas import AuditEventIn
from ..repository import AuditRepository, normalize_event, utcnow
from ...settings import settings


logger = logging.getLogger("audit-log.kafka")


async def run_kafka_consumer(stop_event: asyncio.Event, repo: AuditRepository) -> None:
    # Lazy import so the service can start (degraded) even if deps are missing in some environments.
    from aiokafka import AIOKafkaConsumer  # type: ignore
    topics = [t.strip() for t in settings.KAFKA_TOPICS.split(",") if t.strip()]
    if not topics:
        logger.warning("KAFKA_TOPICS vacío; consumidor kafka deshabilitado")
        return

    while not stop_event.is_set():
        consumer: AIOKafkaConsumer | None = None
        try:
            consumer = AIOKafkaConsumer(
                *topics,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP,
                group_id=settings.KAFKA_GROUP_ID,
                enable_auto_commit=True,
                auto_offset_reset="latest",
                value_deserializer=lambda v: v,
            )
            await consumer.start()
            logger.info("Kafka consumer conectado: bootstrap=%s topics=%s", settings.KAFKA_BOOTSTRAP, topics)

            async for msg in consumer:
                if stop_event.is_set():
                    break

                received_at = utcnow()
                raw_bytes = msg.value
                try:
                    payload = json.loads(raw_bytes.decode("utf-8")) if isinstance(raw_bytes, (bytes, bytearray)) else raw_bytes
                except Exception:
                    payload = {"raw": raw_bytes.decode("utf-8", errors="ignore") if isinstance(raw_bytes, (bytes, bytearray)) else str(raw_bytes)}

                # Best-effort normalization. Accepts a few common keys.
                event_type = payload.get("type") or payload.get("event_type") or msg.topic
                service = payload.get("service")
                actor = payload.get("actor") or payload.get("email") or payload.get("user")
                actor_role = payload.get("actor_role") or payload.get("role")
                entity_type = payload.get("entity_type")
                entity_id = payload.get("entity_id")
                correlation_id = payload.get("correlation_id") or payload.get("correlationId") or str(uuid.uuid4())
                severity = payload.get("severity") or "INFO"
                tags = payload.get("tags") or []

                ts = payload.get("timestamp")
                timestamp = None
                if isinstance(ts, str):
                    try:
                        timestamp = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    except Exception:
                        timestamp = None

                in_event = AuditEventIn(
                    source="kafka",
                    event_type=str(event_type),
                    service=service,
                    actor=actor,
                    actor_role=actor_role,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    timestamp=timestamp,
                    severity=severity,
                    correlation_id=correlation_id,
                    tags=tags if isinstance(tags, list) else [],
                    payload_raw=payload,
                    payload_norm={},
                )

                event_id = payload.get("event_id") or str(uuid.uuid4())
                doc = normalize_event(in_event, event_id=event_id, received_at=received_at, correlation_id=correlation_id)
                try:
                    await repo.insert_event(event_id, doc)
                except Exception as e:
                    logger.exception("Error insertando evento kafka: %s", e)

        except Exception as e:
            logger.warning("Kafka no disponible (%s). Reintentando en 5s...", e)
            await asyncio.sleep(5)
        finally:
            if consumer:
                try:
                    await consumer.stop()
                except Exception:
                    pass
