import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def _normalize_db_url(url: str) -> str:
    # Accept both POSTGRES_DSN and SQLAlchemy-style DSNs
    # If user passes async DSN like postgresql+asyncpg, switch to sync psycopg2.
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return url

def get_database_url() -> str:
    return _normalize_db_url(
        os.getenv("POSTGRES_DSN") or os.getenv("DATABASE_URL") or "sqlite:///./cases.db"
    )

DATABASE_URL = get_database_url()

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
