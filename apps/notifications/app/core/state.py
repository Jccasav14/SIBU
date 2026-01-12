from __future__ import annotations

from app.infrastructure.repositories.in_memory_event_repo import InMemoryEventRepository
from app.application.services.notifier import NotifierService
from app.infrastructure.broker.kafka_consumer import KafkaConsumerRunner

# Singletons initialized at import-time (simple MVP).
event_repo = InMemoryEventRepository(maxlen=1000)
notifier_service = NotifierService(event_repo)
kafka_runner = KafkaConsumerRunner(notifier=notifier_service)
