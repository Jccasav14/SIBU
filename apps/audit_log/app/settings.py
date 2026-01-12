from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Service
    SERVICE_NAME: str = "audit-log"
    ENV: str = "local"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "http://localhost:5174,http://localhost:5173"

    # Security
    JWT_SECRET: str = "SIBU_SUPER_SECRET_CAMBIAME"
    JWT_ALGORITHM: str = "HS256"
    AUDIT_PROFESSIONAL_CAN_VIEW_MINE: bool = False

    # Mongo
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB: str = "audit"

    # Kafka
    KAFKA_BOOTSTRAP: str = "localhost:9092"
    KAFKA_TOPICS: str = "sibu.events,sibu.user.events,sibu.cases.events,sibu.appointments.events"
    KAFKA_GROUP_ID: str = "audit-log"

    # Rabbit
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    RABBITMQ_QUEUE: str = "sibu.audit.queue"
    RABBITMQ_PREFETCH: int = 50

    # MQTT
    MQTT_BROKER: str = "localhost"
    MQTT_PORT: int = 1883
    MQTT_TOPICS: str = "sibu/professionals/+/status,sibu/system/#,sibu/telemetry/#"
    MQTT_USERNAME: str | None = None
    MQTT_PASSWORD: str | None = None

    # Runtime toggles
    AUDIT_CONSUMERS_ENABLED: bool = True


settings = Settings()
