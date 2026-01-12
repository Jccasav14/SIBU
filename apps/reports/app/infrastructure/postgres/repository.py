from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import Any, Iterable

from sqlalchemy import and_, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    actor_metrics,
    appointments_metrics,
    cases_metrics,
    daily_metrics,
    export_jobs,
    security_metrics,
)


def _utc_day(ts: datetime | None) -> date:
    if ts is None:
        ts = datetime.now(timezone.utc)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc).date()


async def _upsert_increment(
    session: AsyncSession,
    table,
    conflict_cols: list[str],
    insert_values: dict[str, Any],
    inc_col: str,
    inc_by: int = 1,
) -> None:
    dialect = session.bind.dialect.name if session.bind is not None else "postgresql"

    if dialect == "postgresql":
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        stmt = pg_insert(table).values(**insert_values)
        stmt = stmt.on_conflict_do_update(
            index_elements=[getattr(table.c, c) for c in conflict_cols],
            set_={inc_col: getattr(table.c, inc_col) + inc_by},
        )
        await session.execute(stmt)
        return

    # SQLite fallback (tests): select then update, else insert.
    where = and_(*[getattr(table.c, c) == insert_values[c] for c in conflict_cols])
    row = (await session.execute(select(table).where(where))).first()
    if row:
        await session.execute(
            update(table).where(where).values({inc_col: getattr(table.c, inc_col) + inc_by})
        )
    else:
        await session.execute(insert(table).values(**insert_values))


class ReportsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def record_event(
        self,
        *,
        ts: datetime | None,
        service: str,
        event_type: str,
        severity: str,
        actor: str | None,
        role: str | None,
    ) -> None:
        d = _utc_day(ts)
        await _upsert_increment(
            self.session,
            daily_metrics,
            ["day", "service", "event_type", "severity", "role"],
            {
                "day": d,
                "service": service,
                "event_type": event_type,
                "severity": severity,
                "role": role,
                "count": 1,
            },
            "count",
            1,
        )
        if actor:
            await _upsert_increment(
                self.session,
                actor_metrics,
                ["day", "actor", "role"],
                {"day": d, "actor": actor, "role": role, "count": 1},
                "count",
                1,
            )

    async def record_case_signal(self, *, ts: datetime | None, signal: str) -> None:
        d = _utc_day(ts)
        col = {"created": "created", "shared": "shared", "closed": "closed"}.get(signal)
        if not col:
            return
        dialect = self.session.bind.dialect.name if self.session.bind is not None else "postgresql"
        if dialect == "postgresql":
            from sqlalchemy.dialects.postgresql import insert as pg_insert
            stmt = pg_insert(cases_metrics).values(day=d, created=0, shared=0, closed=0)
            stmt = stmt.on_conflict_do_update(
                index_elements=[cases_metrics.c.day],
                set_={col: getattr(cases_metrics.c, col) + 1},
            )
            await self.session.execute(stmt)
        else:
            row = (await self.session.execute(select(cases_metrics).where(cases_metrics.c.day == d))).first()
            if row:
                await self.session.execute(
                    update(cases_metrics).where(cases_metrics.c.day == d).values({col: getattr(cases_metrics.c, col) + 1})
                )
            else:
                await self.session.execute(insert(cases_metrics).values(day=d, created=0, shared=0, closed=0))
                await self.session.execute(
                    update(cases_metrics).where(cases_metrics.c.day == d).values({col: getattr(cases_metrics.c, col) + 1})
                )

    async def record_appointment_signal(self, *, ts: datetime | None, signal: str) -> None:
        d = _utc_day(ts)
        col = {"created": "created", "canceled": "canceled", "completed": "completed"}.get(signal)
        if not col:
            return
        dialect = self.session.bind.dialect.name if self.session.bind is not None else "postgresql"
        if dialect == "postgresql":
            from sqlalchemy.dialects.postgresql import insert as pg_insert
            stmt = pg_insert(appointments_metrics).values(day=d, created=0, canceled=0, completed=0)
            stmt = stmt.on_conflict_do_update(
                index_elements=[appointments_metrics.c.day],
                set_={col: getattr(appointments_metrics.c, col) + 1},
            )
            await self.session.execute(stmt)
        else:
            row = (await self.session.execute(select(appointments_metrics).where(appointments_metrics.c.day == d))).first()
            if row:
                await self.session.execute(
                    update(appointments_metrics).where(appointments_metrics.c.day == d).values({col: getattr(appointments_metrics.c, col) + 1})
                )
            else:
                await self.session.execute(insert(appointments_metrics).values(day=d, created=0, canceled=0, completed=0))
                await self.session.execute(
                    update(appointments_metrics).where(appointments_metrics.c.day == d).values({col: getattr(appointments_metrics.c, col) + 1})
                )

    async def record_security_signal(self, *, ts: datetime | None, signal: str) -> None:
        d = _utc_day(ts)
        col = {"login_failed": "login_failed", "access_denied": "access_denied", "suspicious_activity": "suspicious_activity"}.get(signal)
        if not col:
            return
        dialect = self.session.bind.dialect.name if self.session.bind is not None else "postgresql"
        if dialect == "postgresql":
            from sqlalchemy.dialects.postgresql import insert as pg_insert
            stmt = pg_insert(security_metrics).values(day=d, login_failed=0, access_denied=0, suspicious_activity=0)
            stmt = stmt.on_conflict_do_update(
                index_elements=[security_metrics.c.day],
                set_={col: getattr(security_metrics.c, col) + 1},
            )
            await self.session.execute(stmt)
        else:
            row = (await self.session.execute(select(security_metrics).where(security_metrics.c.day == d))).first()
            if row:
                await self.session.execute(
                    update(security_metrics).where(security_metrics.c.day == d).values({col: getattr(security_metrics.c, col) + 1})
                )
            else:
                await self.session.execute(insert(security_metrics).values(day=d, login_failed=0, access_denied=0, suspicious_activity=0))
                await self.session.execute(
                    update(security_metrics).where(security_metrics.c.day == d).values({col: getattr(security_metrics.c, col) + 1})
                )

    async def create_export_job(self, *, job_id: str, type_: str, params: dict[str, Any]) -> None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        await self.session.execute(
            insert(export_jobs).values(
                job_id=job_id,
                status="pending",
                type=type_,
                params_json=json.dumps(params),
                file_path=None,
                error=None,
                created_at=now,
                updated_at=now,
            )
        )

    async def set_export_job_status(self, *, job_id: str, status: str, file_path: str | None = None, error: str | None = None) -> None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        await self.session.execute(
            update(export_jobs)
            .where(export_jobs.c.job_id == job_id)
            .values(status=status, file_path=file_path, error=error, updated_at=now)
        )

    async def get_export_job(self, job_id: str) -> dict[str, Any] | None:
        row = (await self.session.execute(select(export_jobs).where(export_jobs.c.job_id == job_id))).mappings().first()
        return dict(row) if row else None

    async def query_daily_activity(
        self,
        *,
        from_day: date,
        to_day: date,
        service: str | None,
        event_type: str | None,
        severity: str | None,
        role: str | None,
    ) -> list[dict[str, Any]]:
        stmt = select(
            daily_metrics.c.day,
            daily_metrics.c.service,
            daily_metrics.c.event_type,
            daily_metrics.c.severity,
            daily_metrics.c.role,
            daily_metrics.c.count,
        ).where(and_(daily_metrics.c.day >= from_day, daily_metrics.c.day <= to_day))
        if service:
            stmt = stmt.where(daily_metrics.c.service == service)
        if event_type:
            stmt = stmt.where(daily_metrics.c.event_type == event_type)
        if severity:
            stmt = stmt.where(daily_metrics.c.severity == severity)
        if role:
            stmt = stmt.where(daily_metrics.c.role == role)

        stmt = stmt.order_by(daily_metrics.c.day.asc())
        rows = (await self.session.execute(stmt)).mappings().all()
        return [dict(r) for r in rows]

    async def query_cases(self, *, from_day: date, to_day: date) -> list[dict[str, Any]]:
        stmt = select(cases_metrics).where(and_(cases_metrics.c.day >= from_day, cases_metrics.c.day <= to_day)).order_by(cases_metrics.c.day.asc())
        rows = (await self.session.execute(stmt)).mappings().all()
        return [dict(r) for r in rows]

    async def query_appointments(self, *, from_day: date, to_day: date) -> list[dict[str, Any]]:
        stmt = select(appointments_metrics).where(and_(appointments_metrics.c.day >= from_day, appointments_metrics.c.day <= to_day)).order_by(appointments_metrics.c.day.asc())
        rows = (await self.session.execute(stmt)).mappings().all()
        return [dict(r) for r in rows]

    async def query_security(self, *, from_day: date, to_day: date) -> list[dict[str, Any]]:
        stmt = select(security_metrics).where(and_(security_metrics.c.day >= from_day, security_metrics.c.day <= to_day)).order_by(security_metrics.c.day.asc())
        rows = (await self.session.execute(stmt)).mappings().all()
        return [dict(r) for r in rows]

    async def top_actors(self, *, from_day: date, to_day: date, limit: int) -> list[dict[str, Any]]:
        stmt = (
            select(actor_metrics.c.actor, func.coalesce(func.nullif(actor_metrics.c.role, ''), 'unknown').label('role'), func.sum(actor_metrics.c.count).label('count'))
            .where(and_(actor_metrics.c.day >= from_day, actor_metrics.c.day <= to_day))
            .group_by(actor_metrics.c.actor, 'role')
            .order_by(func.sum(actor_metrics.c.count).desc())
            .limit(limit)
        )
        rows = (await self.session.execute(stmt)).mappings().all()
        return [dict(r) for r in rows]

    async def totals_by_service(self, *, from_day: date, to_day: date) -> list[dict[str, Any]]:
        stmt = (
            select(func.coalesce(func.nullif(daily_metrics.c.service, ''), 'unknown').label('service'), func.sum(daily_metrics.c.count).label('count'))
            .where(and_(daily_metrics.c.day >= from_day, daily_metrics.c.day <= to_day))
            .group_by('service')
            .order_by(func.sum(daily_metrics.c.count).desc())
        )
        rows = (await self.session.execute(stmt)).mappings().all()
        return [dict(r) for r in rows]
