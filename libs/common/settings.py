import os

class Settings:
    POSTGRES_DSN = os.getenv("POSTGRES_DSN", "postgresql+asyncpg://sibu:sibu@postgres:5432/sibu")
    JWT_SECRET = os.getenv("JWT_SECRET", "SIBU_SUPER_SECRET_CAMBIAME")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXP_MINUTES = int(os.getenv("JWT_EXP_MINUTES", "60"))

settings = Settings()
