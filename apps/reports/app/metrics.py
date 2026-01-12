from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from fastapi import APIRouter, Response

router = APIRouter()


@router.get("/metrics")
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
