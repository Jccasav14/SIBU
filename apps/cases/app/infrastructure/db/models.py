import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, Enum as SAEnum, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from ...domain.enums import CaseStatus, CasePriority, TimelineEventType, AccessPermission

class Base(DeclarativeBase):
    pass

class Case(Base):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # "Owner" del caso (el estudiante/paciente). Normalmente viene del servicio users.
    student_id: Mapped[str] = mapped_column(String(64), index=True)

    # Área que abrió el caso (PSY, SOCIAL, MEDICAL, etc.)
    owner_area: Mapped[str] = mapped_column(String(32), index=True, default="GENERAL")

    created_by_user_id: Mapped[str] = mapped_column(String(64), index=True)
    assigned_professional_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)

    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)

    status: Mapped[CaseStatus] = mapped_column(SAEnum(CaseStatus), default=CaseStatus.OPEN, index=True)
    priority: Mapped[CasePriority] = mapped_column(SAEnum(CasePriority), default=CasePriority.MEDIUM, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    timeline: Mapped[list["CaseTimelineEvent"]] = relationship(
        back_populates="case", cascade="all, delete-orphan", lazy="selectin"
    )

    access: Mapped[list["CaseAccess"]] = relationship(
        back_populates="case", cascade="all, delete-orphan", lazy="selectin"
    )

    notes: Mapped[list["CaseNote"]] = relationship(
        back_populates="case", cascade="all, delete-orphan", lazy="selectin"
    )

class CaseTimelineEvent(Base):
    __tablename__ = "case_timeline"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id", ondelete="CASCADE"), index=True)

    type: Mapped[TimelineEventType] = mapped_column(SAEnum(TimelineEventType), index=True)
    data: Mapped[dict] = mapped_column(JSON, default=dict)

    actor_user_id: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    case: Mapped["Case"] = relationship(back_populates="timeline")


class CaseAccess(Base):
    __tablename__ = "case_access"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id", ondelete="CASCADE"), index=True)

    # Se puede compartir por usuario o por área
    grantee_type: Mapped[str] = mapped_column(String(16), index=True)  # "USER" | "AREA"
    grantee_id: Mapped[str] = mapped_column(String(64), index=True)    # user_id o código de área

    permission: Mapped[AccessPermission] = mapped_column(SAEnum(AccessPermission), default=AccessPermission.READ)

    granted_by_user_id: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    case: Mapped["Case"] = relationship(back_populates="access")


class CaseNote(Base):
    __tablename__ = "case_notes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id", ondelete="CASCADE"), index=True)

    author_user_id: Mapped[str] = mapped_column(String(64), index=True)
    author_area: Mapped[str] = mapped_column(String(32), index=True, default="GENERAL")

    kind: Mapped[str] = mapped_column(String(32), default="NOTE", index=True)  # OBSERVATION/DIAGNOSIS/PLAN/REFERRAL...
    content: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    case: Mapped["Case"] = relationship(back_populates="notes")
