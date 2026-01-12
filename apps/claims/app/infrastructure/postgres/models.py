from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class ClaimType(str, enum.Enum):
    ACCIDENT = "ACCIDENT"
    ILLNESS = "ILLNESS"
    FAMILY_DEATH = "FAMILY_DEATH"
    OTHER = "OTHER"


class ClaimStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CLOSED = "CLOSED"


class PaymentStatus(str, enum.Enum):
    NONE = "NONE"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAID = "PAID"


class ClaimEventType(str, enum.Enum):
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    SUBMITTED = "SUBMITTED"
    DOCUMENT_ADDED = "DOCUMENT_ADDED"
    REVIEWED = "REVIEWED"
    PAID = "PAID"
    CLOSED = "CLOSED"


class DocumentType(str, enum.Enum):
    invoice = "invoice"
    medical_report = "medical_report"
    death_certificate = "death_certificate"
    other = "other"


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    student_id: Mapped[str] = mapped_column(String(64), index=True)
    claim_type: Mapped[ClaimType] = mapped_column(Enum(ClaimType, name="claim_type"))
    status: Mapped[ClaimStatus] = mapped_column(Enum(ClaimStatus, name="claim_status"), default=ClaimStatus.DRAFT)

    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    description: Mapped[str] = mapped_column(Text)

    requested_amount: Mapped[float] = mapped_column(Numeric(12, 2))
    coverage_cap: Mapped[float] = mapped_column(Numeric(12, 2))
    approved_amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)

    payment_status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus, name="payment_status"), default=PaymentStatus.NONE)
    paid_amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payment_method: Mapped[str | None] = mapped_column(String(32), nullable=True)
    payment_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    documents: Mapped[list["ClaimDocument"]] = relationship(back_populates="claim", cascade="all, delete-orphan")
    events: Mapped[list["ClaimEvent"]] = relationship(back_populates="claim", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_claims_status_type", "status", "claim_type"),
    )


class ClaimDocument(Base):
    __tablename__ = "claim_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), index=True)

    doc_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType, name="doc_type"))
    file_url: Mapped[str] = mapped_column(String(512))
    file_hash: Mapped[str] = mapped_column(String(128))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    claim: Mapped[Claim] = relationship(back_populates="documents")

    __table_args__ = (
        UniqueConstraint("claim_id", "file_hash", name="uq_claim_documents_claim_hash"),
    )


class ClaimEvent(Base):
    __tablename__ = "claim_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), index=True)

    actor: Mapped[str] = mapped_column(String(255))
    event_type: Mapped[ClaimEventType] = mapped_column(Enum(ClaimEventType, name="claim_event_type"))
    payload_json: Mapped[str] = mapped_column(Text, default="{}")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    claim: Mapped[Claim] = relationship(back_populates="events")


