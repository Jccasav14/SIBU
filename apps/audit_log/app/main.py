from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router
from .infrastructure.mongo import mongo
from .infrastructure.repository import AuditRepository
from .infrastructure.consumers.kafka_consumer import run_kafka_consumer
from .infrastructure.consumers.rabbit_consumer import run_rabbit_consumer
from .infrastructure.consumers.mqtt_subscriber import run_mqtt_subscriber
from .settings import settings

from prometheus_fastapi_instrumentator import Instrumentator



def _setup_logging() -> None:
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    _setup_logging()
    logger = logging.getLogger("audit-log")

    try:
        mongo.connect()
    except ImportError as e:
        logger.warning("Mongo driver no disponible (%s). API inicia, pero repos real fallará.", e)
    repo = AuditRepository()
    try:
        await repo.ensure_indexes()
    except Exception as e:
        logger.warning("No se pudieron crear índices en Mongo (continuando): %s", e)

    stop_event = asyncio.Event()
    tasks: list[asyncio.Task] = []

    if settings.AUDIT_CONSUMERS_ENABLED:
        tasks.append(asyncio.create_task(run_kafka_consumer(stop_event, repo)))
        tasks.append(asyncio.create_task(run_rabbit_consumer(stop_event, repo)))
        tasks.append(asyncio.create_task(run_mqtt_subscriber(stop_event, repo)))
    else:
        logger.warning("AUDIT_CONSUMERS_ENABLED=false -> consumers deshabilitados")

    yield

    stop_event.set()
    for t in tasks:
        t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    await mongo.close()


app = FastAPI(title="SIBU Audit Log", lifespan=lifespan)
Instrumentator().instrument(app).expose(app, endpoint="/metrics")
# CORSa
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
