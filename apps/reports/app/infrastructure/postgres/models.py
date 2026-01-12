from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
)

from .db import metadata


daily_metrics = Table(
    "daily_metrics",
    metadata,
    Column("day", Date, nullable=False),
    Column("service", String(64), nullable=False),
    Column("event_type", String(128), nullable=False),
    Column("severity", String(32), nullable=False),
    Column("role", String(32), nullable=True),
    Column("count", Integer, nullable=False, server_default="0"),
    UniqueConstraint("day", "service", "event_type", "severity", "role", name="uq_daily_metrics"),
)

cases_metrics = Table(
    "cases_metrics",
    metadata,
    Column("day", Date, primary_key=True),
    Column("created", Integer, nullable=False, server_default="0"),
    Column("shared", Integer, nullable=False, server_default="0"),
    Column("closed", Integer, nullable=False, server_default="0"),
)

appointments_metrics = Table(
    "appointments_metrics",
    metadata,
    Column("day", Date, primary_key=True),
    Column("created", Integer, nullable=False, server_default="0"),
    Column("canceled", Integer, nullable=False, server_default="0"),
    Column("completed", Integer, nullable=False, server_default="0"),
)

security_metrics = Table(
    "security_metrics",
    metadata,
    Column("day", Date, primary_key=True),
    Column("login_failed", Integer, nullable=False, server_default="0"),
    Column("access_denied", Integer, nullable=False, server_default="0"),
    Column("suspicious_activity", Integer, nullable=False, server_default="0"),
)

actor_metrics = Table(
    "actor_metrics",
    metadata,
    Column("day", Date, nullable=False),
    Column("actor", String(256), nullable=False),
    Column("role", String(32), nullable=True),
    Column("count", Integer, nullable=False, server_default="0"),
    UniqueConstraint("day", "actor", "role", name="uq_actor_metrics"),
)

export_jobs = Table(
    "export_jobs",
    metadata,
    Column("job_id", String(64), primary_key=True),
    Column("status", String(32), nullable=False),
    Column("type", String(32), nullable=False),
    Column("params_json", Text, nullable=False),
    Column("file_path", Text, nullable=True),
    Column("error", Text, nullable=True),
    Column("created_at", DateTime, nullable=False),
    Column("updated_at", DateTime, nullable=False),
)
