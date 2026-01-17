from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router as auth_router
from .infrastructure.db.models import Base
from .infrastructure.db.session import engine
import os
from .infrastructure.kafka_publisher import kafka_start, kafka_stop
from prometheus_fastapi_instrumentator import Instrumentator

from libs.security.jwt import require_role


app = FastAPI(title="SIBU Auth")
Instrumentator().instrument(app).expose(app, endpoint="/metrics")
# CORS: required for browser-based frontends (Vue/React) served from a different origin
# Example: http://localhost:5174  ->  http://localhost:8000
# This middleware also answers preflight OPTIONS requests (fixes 405 preflight).
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


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Start Kafka producer (degraded mode if Kafka is down)sds
    bootstrap = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
    await kafka_start(bootstrap)




@app.on_event("shutdown")
async def shutdown():
    await kafka_stop()

app.include_router(auth_router)


@app.get("/health")
def health():
    return {"ok": True, "service": "auth"}


@app.get("/admin-only")
def admin_only(user=Depends(require_role("admin"))):
    return {"msg": "Bienvenido admin", "user": user}
