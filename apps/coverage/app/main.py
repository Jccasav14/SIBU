from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.infrastructure.postgres.base import Base
from app.infrastructure.postgres.session import get_engine
from app.infrastructure.redis_cache.client import get_redis
from app.settings import settings

logger = logging.getLogger("coverage")

from prometheus_fastapi_instrumentator import Instrumentator


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB tables (lightweight, migration-less)
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Warm up Redis connection
    try:
        redis = get_redis()
        await redis.ping()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis not available at startup: %s", exc)

    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

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
