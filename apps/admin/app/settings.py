from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    SERVICE_NAME: str = "admin"

    # Security
    JWT_SECRET: str = "dev-secret"
    JWT_ALGORITHM: str = "HS256"

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174"

    # Persistence
    ADMIN_POSTGRES_DSN: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/sibu_admin"

    # Redis (mandatory)
    REDIS_URL: str = "redis://redis:6379/2"
    REDIS_TTL_SECONDS: int = 120
    REDIS_ENCODING: str = "utf-8"

    # Integrations (optional)
    USERS_URL: str | None = None  # e.g. http://users:8000
    AUDIT_LOG_URL: str | None = None  # e.g. http://audit-log:8000

    # Paths in users service (override if your users API differs)
    USERS_LIST_ENDPOINT: str = "/users"  # GET
    USERS_PATCH_USER_STATUS_ENDPOINT: str = "/users/admin/users/{email}/status"
    USERS_PATCH_PROFESSIONAL_STATUS_ENDPOINT: str = "/users/admin/professionals/{email}/status"


settings = Settings()
