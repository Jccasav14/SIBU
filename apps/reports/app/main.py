from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router as api_router
from .infrastructure.consumers.kafka_consumer import run_kafka_consumer
from .infrastructure.consumers.rabbit_worker import run_rabbit_worker
from .infrastructure.postgres.init_db import init_db
from .metrics import router as metrics_router
from .settings import settings

logger = logging.getLogger("reports")


def _build_cors_origins(cors_origins: str) -> list[str]:
    base = [o.strip() for o in (cors_origins or "").split(",") if o.strip()]
    expanded: list[str] = []
    for o in base:
        expanded.append(o)
        if "localhost" in o:
            expanded.append(o.replace("localhost", "127.0.0.1"))
        if "127.0.0.1" in o:
            expanded.append(o.replace("127.0.0.1", "localhost"))

    # dedupe keep order
    seen = set()
    out: list[str] = []
    for o in expanded:
        if o not in seen:
            out.append(o)
            seen.add(o)

    if not out:
        out = [
            "http://localhost:5174",
            "http://localhost:5173",
            "http://127.0.0.1:5174",
            "http://127.0.0.1:5173",
        ]
    return out


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    logger.info("starting reports", extra={"env": settings.ENV})

    await init_db()

    stop_event = asyncio.Event()
    app.state.stop_event = stop_event

    tasks: list[asyncio.Task[Any]] = []

    if settings.KAFKA_ENABLED:
        tasks.append(asyncio.create_task(run_kafka_consumer(stop_event), name="kafka_consumer"))
    else:
        logger.warning("kafka disabled")

    if settings.RABBITMQ_ENABLED:
        tasks.append(asyncio.create_task(run_rabbit_worker(stop_event), name="rabbit_worker"))
    else:
        logger.warning("rabbit disabled")

    try:
        yield
    finally:
        stop_event.set()
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("reports stopped")


app = FastAPI(title="SIBU Reports", version="0.1.0", lifespan=lifespan)

origins = _build_cors_origins(settings.CORS_ORIGINS)
origins = [
    "http://localhost", 
        "http://localhost:5174",
        "http://localhost:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5173",
        "http://10.0.2.2",
        "http://10.0.2.2:8000",
]


from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app, endpoint="/metrics")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

app.include_router(api_router)

if settings.PROMETHEUS_METRICS_ENABLED:
    app.include_router(metrics_router)
