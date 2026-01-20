from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router
from .infrastructure.postgres.db import engine
from .infrastructure.postgres.models import Base
from .infrastructure.redis_cache.client import cache
from .settings import settings

from prometheus_fastapi_instrumentator import Instrumentator


@asynccontextmanager
async def lifespan(app: FastAPI):
    # DB init (simple - no Alembic for now)sss
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Redis is mandatorysssss
    await cache.connect()
    try:
        yield
    finally:
        await cache.close()


app = FastAPI(title="SIBU Admin", version="1.0.0", lifespan=lifespan)
Instrumentator().instrument(app).expose(app, endpoint="/metrics")
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost", 
        "http://localhost:5174",
        "http://localhost:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5173",
        "http://10.0.2.2",
        "http://10.0.2.2:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
