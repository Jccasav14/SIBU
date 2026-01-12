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


logger = logging.getLogger("audit-log.rabbit")


def _parse_timestamp(val: Any) -> datetime | None:
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except Exception:
            return None
    return None


async def run_rabbit_consumer(stop_event: asyncio.Event, repo: AuditRepository) -> None:
    import aio_pika  # type: ignore
    queue_name = settings.RABBITMQ_QUEUE
    if not queue_name:
        logger.warning("RABBITMQ_QUEUE vacío; consumidor rabbit deshabilitado")
        return

    while not stop_event.is_set():
        connection = None
        try:
            connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=settings.RABBITMQ_PREFETCH)
            queue = await channel.declare_queue(queue_name, durable=True)

            logger.info("Rabbit consumer conectado: %s queue=%s", settings.RABBITMQ_URL, queue_name)

            async with queue.iterator() as qiter:
                async for message in qiter:
                    if stop_event.is_set():
                        break

                    received_at = utcnow()
                    try:
                        async with message.process(requeue=False):
                            payload: dict[str, Any]
                            try:
                                payload = json.loads(message.body.decode("utf-8"))
                            except Exception:
                                payload = {"raw": message.body.decode("utf-8", errors="ignore")}

                            # Expected job-ish shape, but be permissive
                            event_type = payload.get("type") or payload.get("event_type") or payload.get("job_type") or "rabbit.message"
                            service = payload.get("service")
                            actor = payload.get("actor") or payload.get("email")
                            actor_role = payload.get("actor_role") or payload.get("role")
                            entity_type = payload.get("entity_type")
                            entity_id = payload.get("entity_id")
                            correlation_id = payload.get("correlation_id") or payload.get("correlationId") or str(uuid.uuid4())

                            status = payload.get("status") or "received"
                            error_message = payload.get("error_message") or payload.get("error")

                            tags = payload.get("tags") or []
                            if isinstance(tags, list):
                                tags = tags + [f"job_status:{status}"]
                            else:
                                tags = [f"job_status:{status}"]
                            if error_message:
                                tags.append("job_error")

                            severity = payload.get("severity") or ("ERROR" if error_message else "INFO")
                            timestamp = _parse_timestamp(payload.get("timestamp"))

                            in_event = AuditEventIn(
                                source="rabbitmq",
                                event_type=str(event_type),
                                service=service,
                                actor=actor,
                                actor_role=actor_role,
                                entity_type=entity_type,
                                entity_id=entity_id,
                                timestamp=timestamp,
                                severity=severity,
                                correlation_id=correlation_id,
                                tags=tags,
                                payload_raw=payload,
                                payload_norm={
                                    "queue": queue_name,
                                    "status": status,
                                    "error_message": error_message,
                                },
                            )

                            event_id = payload.get("event_id") or str(uuid.uuid4())
                            doc = normalize_event(
                                in_event,
                                event_id=event_id,
                                received_at=received_at,
                                correlation_id=correlation_id,
                            )
                            await repo.insert_event(event_id, doc)

                    except Exception as e:
                        # Strategy: do not crash the service; log and continue.
                        # DLQ: we rely on producer/retry strategy; alternatively, declare a DLQ exchange+queue.
                        logger.exception("Error procesando mensaje RabbitMQ: %s", e)

        except Exception as e:
            logger.warning("RabbitMQ no disponible (%s). Reintentando en 5s...", e)
            await asyncio.sleep(5)
        finally:
            if connection:
                try:
                    await connection.close()
                except Exception:
                    pass
