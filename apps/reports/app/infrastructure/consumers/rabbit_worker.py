from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import date
from typing import Any

import aio_pika

from ...settings import settings
from ..postgres.db import SessionLocal
from ..postgres.repository import ReportsRepository

logger = logging.getLogger("reports.rabbit_worker")


def _to_date(v: Any) -> date:
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        return date.fromisoformat(v)
    raise ValueError("invalid date value")


async def _export_rows(repo: ReportsRepository, type_: str, from_day: Any, to_day: Any) -> list[dict[str, Any]]:
    fd = _to_date(from_day)
    td = _to_date(to_day)

    if type_ == "cases":
        return await repo.query_cases(from_day=fd, to_day=td)
    if type_ == "appointments":
        return await repo.query_appointments(from_day=fd, to_day=td)
    if type_ == "security":
        return await repo.query_security(from_day=fd, to_day=td)
    # audit export is handled by reports API as proxy to audit-log; for local file export we store minimal stub
    if type_ == "audit":
        return await repo.query_daily_activity(from_day=fd, to_day=td, service="audit_log", event_type=None, severity=None, role=None)

    # default: activity
    return await repo.query_daily_activity(from_day=fd, to_day=td, service=None, event_type=None, severity=None, role=None)


async def _write_csv(path: str, rows: list[dict[str, Any]]) -> None:
    import csv

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        if not rows:
            f.write("")
            return
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


async def _write_xlsx(path: str, rows: list[dict[str, Any]], sheet_name: str) -> None:
    from openpyxl import Workbook

    os.makedirs(os.path.dirname(path), exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = (sheet_name or "Sheet1")[:31]
    if rows:
        headers = list(rows[0].keys())
        ws.append(headers)
        for r in rows:
            ws.append([r.get(h) for h in headers])
    wb.save(path)


async def _write_pdf(path: str, rows: list[dict[str, Any]], title: str) -> None:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas

    os.makedirs(os.path.dirname(path), exist_ok=True)
    c = canvas.Canvas(path, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 14)
    c.drawString(0.75 * inch, height - 0.75 * inch, f"Reporte: {title}")

    c.setFont("Helvetica", 10)
    y = height - 1.15 * inch

    if not rows:
        c.drawString(0.75 * inch, y, "Sin datos para el rango seleccionado.")
        c.showPage()
        c.save()
        return

    headers = list(rows[0].keys())
    # simple table-like layout
    max_cols = min(len(headers), 6)  # keep it readable
    headers = headers[:max_cols]

    col_width = (width - 1.5 * inch) / max_cols

    # header row
    c.setFont("Helvetica-Bold", 9)
    for i, h in enumerate(headers):
        c.drawString(0.75 * inch + i * col_width, y, str(h)[:25])
    y -= 0.2 * inch
    c.setFont("Helvetica", 8)

    for r in rows[:200]:  # avoid huge PDFs
        if y < 0.75 * inch:
            c.showPage()
            y = height - 0.75 * inch
            c.setFont("Helvetica-Bold", 9)
            for i, h in enumerate(headers):
                c.drawString(0.75 * inch + i * col_width, y, str(h)[:25])
            y -= 0.2 * inch
            c.setFont("Helvetica", 8)

        for i, h in enumerate(headers):
            v = r.get(h)
            c.drawString(0.75 * inch + i * col_width, y, str(v)[:30] if v is not None else "")
        y -= 0.17 * inch

    c.showPage()
    c.save()


def _ext_for_format(fmt: str) -> str:
    fmt = (fmt or "csv").lower().strip()
    if fmt == "xlsx":
        return "xlsx"
    if fmt == "pdf":
        return "pdf"
    return "csv"


async def _process_export(payload: dict[str, Any]) -> None:
    job_id = payload["job_id"]
    type_ = payload.get("type") or "activity"
    params = payload.get("params") or {}
    fmt = (params.get("format") or "csv").lower().strip()
    from_day = params.get("from")
    to_day = params.get("to")

    async with SessionLocal() as session:
        repo = ReportsRepository(session)
        await repo.set_export_job_status(job_id=job_id, status="running", error=None)
        await session.commit()

        try:
            rows = await _export_rows(repo, type_, from_day, to_day)

            export_dir = settings.EXPORT_DIR
            os.makedirs(export_dir, exist_ok=True)

            ext = _ext_for_format(fmt)
            path = os.path.join(export_dir, f"{job_id}.{ext}")

            if ext == "xlsx":
                await _write_xlsx(path, rows, sheet_name=type_)
            elif ext == "pdf":
                await _write_pdf(path, rows, title=type_)
            else:
                await _write_csv(path, rows)

            await repo.set_export_job_status(job_id=job_id, status="ready", file_path=path, error=None)
            await session.commit()
            logger.info("export ready", extra={"job_id": job_id, "path": path, "format": ext})
        except Exception as e:
            await repo.set_export_job_status(job_id=job_id, status="failed", error=str(e))
            await session.commit()
            logger.exception("export failed", extra={"job_id": job_id})
            raise


async def run_rabbit_worker(stop_event: asyncio.Event) -> None:
    # Degraded mode: keep retrying forever, never crash the service.
    backoff = max(1, int(settings.RABBITMQ_RETRY_BACKOFF_SEC))
    while not stop_event.is_set():
        try:
            connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            async with connection:
                channel = await connection.channel()
                await channel.set_qos(prefetch_count=settings.RABBITMQ_PREFETCH)

                queue = await channel.declare_queue(settings.RABBITMQ_QUEUE, durable=True)
                # DLQ is optional: declare so it's visible even if you don't bind in broker policy
                if settings.RABBITMQ_DLQ:
                    await channel.declare_queue(settings.RABBITMQ_DLQ, durable=True)

                async with queue.iterator() as it:
                    async for msg in it:
                        if stop_event.is_set():
                            break
                        async with msg.process(requeue=False):
                            try:
                                body = msg.body.decode("utf-8")
                                payload = json.loads(body)
                                if not isinstance(payload, dict):
                                    continue
                                if payload.get("action") == "export":
                                    await _process_export(payload)
                            except Exception:
                                # message will be acked (requeue=False). DLQ strategy can be implemented with broker policies.
                                logger.exception("failed processing rabbit message")
        except Exception as e:
            logger.warning("RabbitMQ unavailable (degraded)", extra={"error": str(e)})
            await asyncio.sleep(backoff)
