from __future__ import annotations

from typing import Optional
from aiokafka import AIOKafkaProducer

# Shared producer instance, set on startup in app.main
producer: Optional[AIOKafkaProducer] = None
