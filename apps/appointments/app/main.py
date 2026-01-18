from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.appointments.app.settings import settings
from apps.appointments.app.api.routes import router
from apps.appointments.app.infrastructure.db.session import engine
from apps.appointments.app.infrastructure.db.session import Base
from apps.appointments.app.infrastructure.kafka.producer import close_producer

app = FastAPI(title="SIBU Appointments Service", version="0.1.0")
from prometheus_fastapi_instrumentator import Instrumentator

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

@app.on_event("startup")
async def _startup():
    # Create tables (simple dev approach)s
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.on_event("shutdown")
async def _shutdown():
    await close_producer()
