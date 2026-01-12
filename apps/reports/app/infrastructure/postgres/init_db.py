from __future__ import annotations

import logging

from sqlalchemy import text

from .db import engine, metadata


logger = logging.getLogger("reports.db")


async def init_db() -> None:
    # Simple startup-time schema creation (no Alembic for now).
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
        # small sanity query
        await conn.execute(text("SELECT 1"))
    logger.info("DB initialized (tables ensured).")
