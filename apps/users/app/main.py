import asyncio
from fastapi import FastAPI

from libs.db.postgres import engine
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router as users_router
from .infrastructure.db.models import Base
from .infrastructure.messaging.user_events_worker import kafka_user_events_worker
from prometheus_fastapi_instrumentator import Instrumentator


#s
app = FastAPI(title="SIBU Users")
Instrumentator().instrument(app).expose(app, endpoint="/metrics")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",
        "http://localhost:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

consumer_task: asyncio.Task | None = None



@app.on_event("startup")
async def startup():
    # Crear tablas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Arrancar worker kafka
    global consumer_task
    consumer_task = asyncio.create_task(kafka_user_events_worker())


@app.on_event("shutdown")
async def shutdown():
    global consumer_task
    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except Exception:
            pass


@app.get("/health")
def health():
    return {"ok": True, "service": "users"}


app.include_router(users_router)
