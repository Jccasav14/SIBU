import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    # DB
    POSTGRES_DSN: str = "postgresql+asyncpg://sibu:sibu@localhost:5433/sibu"

    # Auth/JWT
    JWT_SECRET: str = "SIBU_SUPER_SECRET_CAMBIAME"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXP_MINUTES: int = 60

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173"

    # Kafka (optional)
    KAFKA_BOOTSTRAP: str = os.getenv("KAFKA_BOOTSTRAP", "")
    KAFKA_TOPIC_APPOINTMENT_EVENTS: str = "sibu.appointment.events"
    KAFKA_CLIENT_ID: str = "appointments-service"

    AUTH_DISABLED: bool = False

    def cors_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

settings = Settings()
