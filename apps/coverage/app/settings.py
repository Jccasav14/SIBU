from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_name: str = "SIBU Coverage"
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
        ]
    )

    # Security
    jwt_secret: str = Field(alias="JWT_SECRET")
    jwt_algorithm: str = Field(alias="JWT_ALGORITHM")

    # Postgres
    postgres_dsn: str = Field(alias="COVERAGE_POSTGRES_DSN")

    # Redis
    redis_url: str = Field(alias="REDIS_URL")
    redis_ttl_seconds: int = Field(default=120, alias="REDIS_TTL_SECONDS")


settings = Settings()
