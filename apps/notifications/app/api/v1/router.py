from __future__ import annotations

from fastapi import APIRouter
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.events import router as events_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(events_router)
