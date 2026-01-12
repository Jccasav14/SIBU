from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Service
    SERVICE_NAME: str = "reports"
    ENV: str = "local"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "http://localhost:5174,http://localhost:5173"

    # Security
    JWT_SECRET: str = "SIBU_SUPER_SECRET_CAMBIAME"
    JWT_ALGORITHM: str = "HS256"

    # Kafka
    KAFKA_BOOTSTRAP: str = "kafka:9092"
    KAFKA_TOPICS: str = "sibu.user.events,sibu.case.events,sibu.appointment.events"
    KAFKA_GROUP_ID: str = "reports-service"
    KAFKA_ENABLED: bool = True
    KAFKA_POLL_INTERVAL_SEC: int = 1
    KAFKA_RETRY_BACKOFF_SEC: int = 5

    # RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672/"
    RABBITMQ_QUEUE: str = "sibu.reports.queue"
    RABBITMQ_DLQ: str = "sibu.reports.dlq"
    RABBITMQ_PREFETCH: int = 10
    RABBITMQ_ENABLED: bool = True
    RABBITMQ_RETRY_BACKOFF_SEC: int = 5

    # Audit-log client
    AUDIT_LOG_URL: str = "http://audit_log:8006"
    AUDIT_LOG_TIMEOUT_SEC: float = 5.0
    AUDIT_LOG_RETRY_COUNT: int = 2

    # Persistence
    REPORTS_POSTGRES_DSN: str = "postgresql+asyncpg://reports:reports@reports_postgres:5432/reports"
    SQL_ECHO: bool = False

    # Redis cache
    REDIS_URL: str = "redis://redis:6379/1"
    CACHE_TTL_SEC: int = 120  # 60-300s recommended

    # Feature flags
    REPORTS_PROFESSIONAL_CAN_VIEW_MINE: bool = False

    # Exports
    EXPORT_DIR: str = "/tmp/exports"

    # Metrics
    PROMETHEUS_METRICS_ENABLED: bool = True


settings = Settings()
