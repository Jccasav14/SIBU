from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.infrastructure.repositories.in_memory_event_repo import InMemoryEventRepository
from app.application.services.notifier import NotifierService
from app.infrastructure.broker.kafka_consumer import KafkaConsumerRunner
from prometheus_fastapi_instrumentator import Instrumentator
from app.core import state

def create_app() -> FastAPI:
    app = FastAPI(
        title="SIBU Notifications Service",
        version="1.0.0",
        openapi_url="/openapi.json",
    )
    

    Instrumentator().instrument(app).expose(app, endpoint="/metrics")


    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
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

    app.include_router(api_router)

    @app.on_event("startup")
    async def _startup():
        await state.kafka_runner.start()

    @app.on_event("shutdown")
    async def _shutdown():
        await state.kafka_runner.stop()
#
    return app

app = create_app()
