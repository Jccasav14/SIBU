from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import aio_pika

from ...settings import settings

logger = logging.getLogger("reports.rabbit")


class RabbitBroker:
    def __init__(self) -> None:
        self._connection: aio_pika.RobustConnection | None = None
        self._channel: aio_pika.abc.AbstractRobustChannel | None = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        async with self._lock:
            if self._channel is not None:
                return
            self._connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            self._channel = await self._connection.channel()
            await self._channel.set_qos(prefetch_count=settings.RABBITMQ_PREFETCH)
            # declare queues (durable)
            await self._channel.declare_queue(settings.RABBITMQ_QUEUE, durable=True)
            if settings.RABBITMQ_DLQ:
                await self._channel.declare_queue(settings.RABBITMQ_DLQ, durable=True)

    async def close(self) -> None:
        async with self._lock:
            try:
                if self._channel is not None:
                    await self._channel.close()
            finally:
                self._channel = None
            try:
                if self._connection is not None:
                    await self._connection.close()
            finally:
                self._connection = None

    async def publish(self, payload: dict[str, Any], queue: str | None = None) -> None:
        if not settings.RABBITMQ_ENABLED:
            raise RuntimeError("RabbitMQ disabled")
        if self._channel is None:
            await self.connect()
        assert self._channel is not None
        routing_key = queue or settings.RABBITMQ_QUEUE
        msg = aio_pika.Message(
            body=json.dumps(payload).encode("utf-8"),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        await self._channel.default_exchange.publish(msg, routing_key=routing_key)


rabbit = RabbitBroker()
