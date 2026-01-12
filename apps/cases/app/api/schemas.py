from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field, model_validator

from ..domain.enums import CaseStatus, CasePriority, TimelineEventType, AccessPermission


class CaseCreate(BaseModel):
    # Caso siempre pertenece a un estudiante/paciente
    student_id: str = Field(min_length=1, max_length=64)

    # Área que abre el caso (PSY, SOCIAL, MEDICAL...)
    owner_area: str = Field(default="GENERAL", min_length=1, max_length=32)

    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=3, max_length=5000)
    priority: CasePriority = CasePriority.MEDIUM


class CaseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, min_length=3, max_length=5000)
    priority: CasePriority | None = None


class CaseAssign(BaseModel):
    professional_id: str = Field(min_length=1, max_length=64)


class CaseStatusChange(BaseModel):
    status: CaseStatus


class CaseShare(BaseModel):
    # compartir a un usuario específico o a un área completa
    user_id: str | None = Field(default=None, min_length=1, max_length=64)
    area: str | None = Field(default=None, min_length=1, max_length=32)
    permission: AccessPermission = AccessPermission.READ

    @model_validator(mode="after")
    def _check_target(self):
        if not self.user_id and not self.area:
            raise ValueError("Debes enviar user_id o area")
        return self


class CaseNoteCreate(BaseModel):
    kind: str = Field(default="NOTE", min_length=1, max_length=32)
    content: str = Field(min_length=1, max_length=8000)


class CaseNoteOut(BaseModel):
    id: str
    case_id: str
    author_user_id: str
    author_area: str
    kind: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class CaseOut(BaseModel):
    id: str
    student_id: str
    owner_area: str
    created_by_user_id: str
    assigned_professional_id: str | None
    title: str
    description: str
    status: CaseStatus
    priority: CasePriority
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TimelineEventOut(BaseModel):
    id: str
    case_id: str
    type: TimelineEventType
    data: dict
    actor_user_id: str
    created_at: datetime

    class Config:
        from_attributes = True
