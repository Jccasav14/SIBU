import os
import asyncio
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router as cases_router
from .infrastructure.db.session import engine
from .infrastructure.db.models import Base
from .infrastructure.messaging.kafka import get_producer
from aiokafka import AIOKafkaProducer
from .infrastructure.messaging import state as kafka_state
from prometheus_fastapi_instrumentator import Instrumentator
logger = logging.getLogger("cases")

def create_app() -> FastAPI:
    
###ssss
    

    app = FastAPI(title="SIBU Cases Service", version="1.0.0")
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

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "cases"}

    app.include_router(cases_router)

    @app.on_event("startup")
    async def _startup():
        Base.metadata.create_all(bind=engine)
        # Kafka is used for event emission, but the API should still run even if Kafka
        # is temporarily unavailable (common during local docker startup ordering).
        # Set KAFKA_REQUIRED=true if you want to fail fast.
        required = os.getenv("KAFKA_REQUIRED", "false").lower() == "true"
        retries = int(os.getenv("KAFKA_STARTUP_RETRIES", "20"))
        delay = float(os.getenv("KAFKA_STARTUP_DELAY_SECONDS", "0.5"))

        last_err: Exception | None = None
        for attempt in range(1, retries + 1):
            try:
                kafka_state.producer = await get_producer()
                logger.info("Kafka producer started")
                last_err = None
                break
            except Exception as e:
                last_err = e
                kafka_state.producer = None
                logger.warning(
                    "Kafka not ready (attempt %s/%s). Continuing to retry... (%s)",
                    attempt,
                    retries,
                    e,
                )
                await asyncio.sleep(delay)

        if required and kafka_state.producer is None:
            # Fail startup if explicitly required.
            raise RuntimeError(f"Kafka required but unavailable after {retries} attempts") from last_err
        if kafka_state.producer is None:
            logger.warning("Kafka unavailable. API will run without event publishing.")

    @app.on_event("shutdown")
    async def _shutdown():
        if kafka_state.producer:
            await kafka_state.producer.stop()
            kafka_state.producer = None

    return app

app = create_app()
