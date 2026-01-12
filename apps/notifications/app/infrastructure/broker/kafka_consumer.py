from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

from aiokafka import AIOKafkaConsumer

from app.application.services.notifier import NotifierService
from app.core.config import settings

@dataclass
class KafkaConsumerRunner:
    notifier: NotifierService
    _consumer: Optional[AIOKafkaConsumer] = None
    _task: Optional[asyncio.Task] = None
    _stop_event: Optional[asyncio.Event] = None

    async def start(self) -> None:
        if not settings.kafka_enabled:
            print("[notifications] Kafka disabled (KAFKA_ENABLED=false).")
            return
        self._stop_event = asyncio.Event()
        self._task = asyncio.create_task(self._run_loop(), name="kafka-consumer-loop")

    async def stop(self) -> None:
        if self._stop_event:
            self._stop_event.set()
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=10)
            except asyncio.TimeoutError:
                self._task.cancel()
        if self._consumer:
            await self._consumer.stop()

    async def _ensure_consumer(self) -> AIOKafkaConsumer:
        if self._consumer is not None:
            return self._consumer

        consumer = AIOKafkaConsumer(
            settings.kafka_topic_case_events,
            bootstrap_servers=settings.kafka_bootstrap,
            group_id=settings.kafka_group_id,
            auto_offset_reset=settings.kafka_auto_offset_reset,
            enable_auto_commit=True,
            value_deserializer=lambda v: v,  # raw bytes
        )
        await consumer.start()
        self._consumer = consumer
        print(f"[notifications] Kafka consumer started topic={settings.kafka_topic_case_events} bootstrap={settings.kafka_bootstrap}")
        return consumer

    async def _run_loop(self) -> None:
        backoff = 1
        while self._stop_event and not self._stop_event.is_set():
            try:
                consumer = await self._ensure_consumer()
                backoff = 1

                async for msg in consumer:
                    if self._stop_event.is_set():
                        break

                    try:
                        raw = msg.value.decode("utf-8") if isinstance(msg.value, (bytes, bytearray)) else str(msg.value)
                        data: Dict[str, Any] = json.loads(raw) if raw else {}
                    except Exception:
                        data = {"raw": (msg.value.decode("utf-8", errors="ignore") if isinstance(msg.value, (bytes, bytearray)) else str(msg.value))}

                    event_type = (
                        data.get("event_type")
                        or data.get("event")
                        or data.get("type")
                        or "case.event"
                    )

                    payload = data.get("payload") if isinstance(data.get("payload"), dict) else data
                    self.notifier.handle_case_event(str(event_type), payload)

            except Exception as e:
                print(f"[notifications] Kafka loop error: {e}. Retrying in {backoff}s")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)
                if self._consumer:
                    try:
                        await self._consumer.stop()
                    except Exception:
                        pass
                    self._consumer = None
