import os
import json

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer


def _bootstrap_servers() -> str:
    # Read at call time so containers can override via env without rebuild.
    return os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")


async def get_producer() -> AIOKafkaProducer:
    producer = AIOKafkaProducer(
        bootstrap_servers=_bootstrap_servers(),
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    await producer.start()
    return producer


async def get_consumer(topic: str, group_id: str) -> AIOKafkaConsumer:
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=_bootstrap_servers(),
        group_id=group_id,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda b: json.loads(b.decode("utf-8")),
    )
    await consumer.start()
    return consumer
