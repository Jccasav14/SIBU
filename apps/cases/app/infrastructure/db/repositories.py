from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Case, CaseTimelineEvent, CaseAccess, CaseNote
from ...domain.enums import CaseStatus, CasePriority, AccessPermission


class CaseRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, obj: Case) -> Case:
        self.db.add(obj)
        self.db.flush()
        return obj

    def get(self, case_id: str) -> Optional[Case]:
        return self.db.get(Case, case_id)

    def list(
        self,
        *,
        created_by_user_id: Optional[str] = None,
        assigned_professional_id: Optional[str] = None,
        student_id: Optional[str] = None,
        status: Optional[CaseStatus] = None,
        priority: Optional[CasePriority] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[Case]:
        stmt = select(Case)

        if created_by_user_id:
            stmt = stmt.where(Case.created_by_user_id == created_by_user_id)
        if assigned_professional_id:
            stmt = stmt.where(Case.assigned_professional_id == assigned_professional_id)
        if student_id:
            stmt = stmt.where(Case.student_id == student_id)
        if status:
            stmt = stmt.where(Case.status == status)
        if priority:
            stmt = stmt.where(Case.priority == priority)

        stmt = stmt.order_by(Case.created_at.desc()).limit(limit).offset(offset)
        return self.db.execute(stmt).scalars().all()

    def save(self, obj: Case) -> Case:
        self.db.add(obj)
        self.db.flush()
        return obj


class TimelineRepository:
    def __init__(self, db: Session):
        self.db = db

    def add_event(self, event: CaseTimelineEvent) -> CaseTimelineEvent:
        self.db.add(event)
        self.db.flush()
        return event

    def list_by_case(self, case_id: str, limit: int = 200, offset: int = 0) -> list[CaseTimelineEvent]:
        stmt = (
            select(CaseTimelineEvent)
            .where(CaseTimelineEvent.case_id == case_id)
            .order_by(CaseTimelineEvent.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.execute(stmt).scalars().all())


class AccessRepository:
    def __init__(self, db: Session):
        self.db = db

    def grant(self, access: CaseAccess) -> CaseAccess:
        self.db.add(access)
        self.db.flush()
        return access

    def list_for_case(self, case_id: str) -> list[CaseAccess]:
        stmt = select(CaseAccess).where(CaseAccess.case_id == case_id)
        return list(self.db.execute(stmt).scalars().all())

    def has_user_access(self, case_id: str, user_id: str, *, require_write: bool = False) -> bool:
        stmt = select(CaseAccess).where(
            CaseAccess.case_id == case_id,
            CaseAccess.grantee_type == "USER",
            CaseAccess.grantee_id == user_id,
        )
        rows = list(self.db.execute(stmt).scalars().all())
        if not rows:
            return False
        if not require_write:
            return True
        return any(r.permission == AccessPermission.WRITE for r in rows)

    def has_area_access(self, case_id: str, area: str, *, require_write: bool = False) -> bool:
        stmt = select(CaseAccess).where(
            CaseAccess.case_id == case_id,
            CaseAccess.grantee_type == "AREA",
            CaseAccess.grantee_id == area,
        )
        rows = list(self.db.execute(stmt).scalars().all())
        if not rows:
            return False
        if not require_write:
            return True
        return any(r.permission == AccessPermission.WRITE for r in rows)


class NotesRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, note: CaseNote) -> CaseNote:
        self.db.add(note)
        self.db.flush()
        return note

    def list_by_case(self, case_id: str, limit: int = 200, offset: int = 0) -> list[CaseNote]:
        stmt = (
            select(CaseNote)
            .where(CaseNote.case_id == case_id)
            .order_by(CaseNote.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.execute(stmt).scalars().all())
