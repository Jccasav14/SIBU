from __future__ import annotations

import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    service_name: str = "sibu-notifications"
    host: str = "0.0.0.0"
    port: int = 8004

    # Kafka
    kafka_bootstrap: str = os.getenv("KAFKA_BOOTSTRAP", "kafka:29092")
    kafka_topic_case_events: str = os.getenv("KAFKA_TOPIC_CASE_EVENTS", "sibu.case.events")
    kafka_group_id: str = os.getenv("KAFKA_GROUP_ID", "notifications-service")
    kafka_auto_offset_reset: str = os.getenv("KAFKA_AUTO_OFFSET_RESET", "latest")
    kafka_enabled: bool = os.getenv("KAFKA_ENABLED", "true").lower() == "true"

    # CORS
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:5173")

settings = Settings()
