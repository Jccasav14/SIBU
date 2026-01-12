import os
import asyncio

from libs.messaging.kafka import get_consumer

from ..db.session import SessionLocal
from ..db.repositories import UserProfileRepository


async def kafka_user_events_worker():
    topic = os.getenv("KAFKA_TOPIC_USER_EVENTS", "sibu.user.events")
    group_id = os.getenv("KAFKA_GROUP_ID", "users-service")

    # Reintentar conexión hasta que Kafka esté listo
    consumer = None
    while consumer is None:
        try:
            consumer = await get_consumer(topic, group_id)
        except Exception as e:
            print(f"[WARN] Kafka not ready yet: {e}. Retrying in 3s...")
            await asyncio.sleep(3)

    try:
        async for msg in consumer:
            event = msg.value or {}

            if event.get("type") != "user.created":
                continue

            email = event.get("email")
            if not email:
                continue

            # Idempotente: si ya existe, no hace nada
            async with SessionLocal() as db:
                repo = UserProfileRepository(db)
                exists = await repo.get_by_email(email)
                if not exists:
                    # create() hace commit
                    await repo.create(email=email, is_active=True)

    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"[WARN] Kafka consumer error: {e}")
    finally:
        try:
            await consumer.stop()
        except Exception:
            pass
