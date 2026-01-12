from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any

from ...domain.schemas import AuditEventIn
from ..repository import AuditRepository, normalize_event, utcnow
from ...settings import settings


logger = logging.getLogger("audit-log.mqtt")


def _parse_timestamp(val: Any) -> datetime | None:
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except Exception:
            return None
    return None


async def run_mqtt_subscriber(stop_event: asyncio.Event, repo: AuditRepository) -> None:
    from asyncio_mqtt import Client, MqttError  # type: ignore
    topics = [t.strip() for t in settings.MQTT_TOPICS.split(",") if t.strip()]
    if not topics:
        logger.warning("MQTT_TOPICS vacío; suscriptor mqtt deshabilitado")
        return

    while not stop_event.is_set():
        try:
            async with Client(
                hostname=settings.MQTT_BROKER,
                port=settings.MQTT_PORT,
                username=settings.MQTT_USERNAME,
                password=settings.MQTT_PASSWORD,
            ) as client:
                logger.info(
                    "MQTT conectado: %s:%s topics=%s",
                    settings.MQTT_BROKER,
                    settings.MQTT_PORT,
                    topics,
                )

                for t in topics:
                    await client.subscribe(t)

                async with client.unfiltered_messages() as messages:
                    async for message in messages:
                        if stop_event.is_set():
                            break
                        received_at = utcnow()

                        topic = message.topic.value if hasattr(message.topic, "value") else str(message.topic)
                        body = message.payload
                        try:
                            payload = json.loads(body.decode("utf-8"))
                        except Exception:
                            payload = {"raw": body.decode("utf-8", errors="ignore")}

                        # Derive a reasonable event_type from topic + optional type field
                        event_type = payload.get("type") or payload.get("event_type") or f"mqtt.{topic}"

                        # Extract presence/state for professionals: sibu/professionals/<email>/status
                        actor = payload.get("actor") or payload.get("email")
                        entity_type = payload.get("entity_type")
                        entity_id = payload.get("entity_id")
                        if topic.startswith("sibu/professionals/") and topic.endswith("/status"):
                            parts = topic.split("/")
                            if len(parts) >= 3:
                                actor = actor or parts[2]
                                entity_type = entity_type or "professional"
                                entity_id = entity_id or parts[2]
                                event_type = payload.get("type") or "professional.status"

                        correlation_id = payload.get("correlation_id") or payload.get("correlationId") or str(uuid.uuid4())
                        severity = payload.get("severity") or "INFO"
                        timestamp = _parse_timestamp(payload.get("timestamp"))
                        tags = payload.get("tags") or []
                        if not isinstance(tags, list):
                            tags = []
                        tags.append(f"mqtt_topic:{topic}")

                        in_event = AuditEventIn(
                            source="mqtt",
                            event_type=str(event_type),
                            service=payload.get("service") or "mqtt",
                            actor=actor,
                            actor_role=payload.get("actor_role") or payload.get("role"),
                            entity_type=entity_type,
                            entity_id=entity_id,
                            timestamp=timestamp,
                            severity=severity,
                            correlation_id=correlation_id,
                            tags=tags,
                            payload_raw=payload,
                            payload_norm={"topic": topic},
                        )

                        event_id = payload.get("event_id") or str(uuid.uuid4())
                        doc = normalize_event(in_event, event_id=event_id, received_at=received_at, correlation_id=correlation_id)
                        try:
                            await repo.insert_event(event_id, doc)
                        except Exception as e:
                            logger.exception("Error insertando evento mqtt: %s", e)

        except MqttError as e:
            # Degraded mode: keep API up, retry.
            logger.warning("MQTT no disponible (%s). Reintentando en 5s...", e)
            await asyncio.sleep(5)
        except Exception as e:
            logger.warning("MQTT error (%s). Reintentando en 5s...", e)
            await asyncio.sleep(5)
