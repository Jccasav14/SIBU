from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Service
    SERVICE_NAME: str = "claims"
    PORT: int = 8009

    # Security
    JWT_SECRET: str = "dev-secret"
    JWT_ALGORITHM: str = "HS256"

    # Postgres (mandatory)
    CLAIMS_POSTGRES_DSN: str = "postgresql+asyncpg://claims:claims@claims-postgres:5432/claims"

    # Redis (mandatory)
    REDIS_URL: str = "redis://redis:6379/3"
    REDIS_TTL_SECONDS: int = Field(default=120, ge=30, le=3600)

    # Integrations (optional)
    COVERAGE_URL: AnyHttpUrl | None = "http://coverage:8010"  # noqa: E501
    COVERAGE_TIMEOUT_SECONDS: int = Field(default=2, ge=1, le=10)

    USERS_URL: AnyHttpUrl | None = "http://users:8000"  # noqa: E501

    AUDIT_LOG_ENABLED: bool = False
    AUDIT_LOG_URL: AnyHttpUrl | None = "http://audit_log:8006"  # noqa: E501
    AUDIT_LOG_TIMEOUT_SECONDS: int = Field(default=2, ge=1, le=10)

    # Mongo (optional)
    MONGO_ENABLED: bool = False
    MONGO_URI: str | None = None
    MONGO_DB: str = "claims_history"


settings = Settings()
