import json
import logging
from typing import Optional, Dict, Any

from aiokafka import AIOKafkaProducer

logger = logging.getLogger("auth.kafka")

_producer: Optional[AIOKafkaProducer] = None


async def kafka_start(bootstrap: str) -> None:
    """Start Kafka producer. If it fails, keep service running (degraded mode)."""
    global _producer
    if _producer:
        return
    try:
        _producer = AIOKafkaProducer(bootstrap_servers=bootstrap)
        await _producer.start()
        logger.info("Kafka producer conectado: bootstrap=%s", bootstrap)
    except Exception as e:
        _producer = None
        logger.warning("Kafka NO disponible (producer). Modo degradado. Error: %s", e)


async def kafka_stop() -> None:
    global _producer
    if _producer:
        try:
            await _producer.stop()
        except Exception:
            pass
        _producer = None


async def publish_event(topic: str, event: Dict[str, Any]) -> None:
    """Publish event to Kafka. If Kafka is down, do nothing (do not break auth)."""
    if not _producer:
        return
    try:
        payload = json.dumps(event, ensure_ascii=False).encode("utf-8")
        await _producer.send_and_wait(topic, payload)
    except Exception as e:
        logger.warning("No se pudo publicar evento Kafka. Se ignora. Error: %s", e)