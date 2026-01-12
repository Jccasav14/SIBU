import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from uuid import uuid4

from aiokafka import AIOKafkaProducer

from apps.appointments.app.settings import settings

logger = logging.getLogger("appointments.kafka")

_producer: Optional[AIOKafkaProducer] = None


async def get_producer() -> Optional[AIOKafkaProducer]:
    """Lazy-init del producer.

    - Si KAFKA_BOOTSTRAP no está configurado -> None (modo degradado).
    - Si Kafka está caído -> None (no rompe el servicio).
    """
    global _producer

    if _producer is not None:
        return _producer

    bootstrap = (settings.KAFKA_BOOTSTRAP or "").strip()
    if not bootstrap:
        return None

    p = AIOKafkaProducer(bootstrap_servers=bootstrap, client_id=settings.KAFKA_CLIENT_ID)
    try:
        await p.start()
        _producer = p
        logger.info("Kafka producer conectado: bootstrap=%s", bootstrap)
        return _producer
    except Exception as e:
        # Evita warning de producer no cerrado si falla el start
        try:
            await p.stop()
        except Exception:
            pass
        _producer = None
        logger.warning("Kafka NO disponible (producer). Modo degradado. Error: %s", e)
        return None


def _guess_entity_type(event_type: str) -> str:
    if event_type.startswith("availability."):
        return "availability"
    if event_type.startswith("appointment."):
        return "appointment"
    return "unknown"


async def publish_event(event_type: str, payload: Dict[str, Any], *, severity: str = "INFO") -> None:
    """Publica un evento de appointments al topic configurado.

    No rompe el servicio si Kafka cae.
    """
    try:
        producer = await get_producer()
        if producer is None:
            return

        actor = payload.get("actor") or payload.get("actor_user") or payload.get("professional_email")
        actor_role = payload.get("actor_role")
        entity_type = payload.get("entity_type") or _guess_entity_type(event_type)
        entity_id = payload.get("entity_id") or payload.get("id")

        event = {
            "event_id": str(uuid4()),
            "event_type": event_type,
            "service": "appointments",
            "actor": actor,
            "actor_role": actor_role,
            "entity_type": entity_type,
            "entity_id": str(entity_id) if entity_id is not None else None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": severity,
            "correlation_id": payload.get("correlation_id") or str(uuid4()),
            "payload": payload,
        }

        topic = settings.KAFKA_TOPIC_APPOINTMENT_EVENTS
        await producer.send_and_wait(topic, json.dumps(event, ensure_ascii=False).encode("utf-8"))
    except Exception as e:
        logger.warning("No se pudo publicar evento Kafka. Se ignora. Error: %s", e)


async def close_producer() -> None:
    """Cierra el producer en el shutdown de FastAPI."""
    global _producer
    if _producer is None:
        return
    try:
        await _producer.stop()
        logger.info("Kafka producer cerrado.")
    except Exception as e:
        logger.warning("Error cerrando Kafka producer: %s", e)
    finally:
        _producer = None
