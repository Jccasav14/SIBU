import os

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..infrastructure.messaging import state as kafka_state
from .schemas import (
    CaseCreate,
    CaseOut,
    CaseUpdate,
    CaseAssign,
    CaseStatusChange,
    CaseShare,
    CaseNoteCreate,
    CaseNoteOut,
    TimelineEventOut,
)
from ..domain.enums import CaseStatus, CasePriority
from ..domain.exceptions import NotFoundError, ForbiddenError, BadRequestError
from ..infrastructure.db.session import get_db
from ..application.services.case_service import CaseService
from ..security.deps import get_current_user
from ..security.jwt import CurrentUser

router = APIRouter(prefix="/cases", tags=["cases"])

# Topic de eventos para Event-Driven (Kafka)
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC_CASE_EVENTS", "sibu.case.events")



from uuid import uuid4
from datetime import datetime, timezone


def _audit_event(*, event_type: str, service: str, user: CurrentUser, entity_type: str | None, entity_id: str | None,
                 payload: dict, severity: str = "INFO", source: str = "kafka") -> dict:
    return {
        "event_id": str(uuid4()),
        "source": source,
        "event_type": event_type,
        "service": service,
        "actor": user.user_id,
        "actor_role": (user.roles[0] if user.roles else "unknown"),
        "entity_type": entity_type,
        "entity_id": entity_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "severity": severity,
        "correlation_id": str(uuid4()),
        "payload": payload,
    }

def _service(db: Session) -> CaseService:
    return CaseService(db)


@router.post("", response_model=CaseOut, status_code=201)
async def create_case(
    payload: CaseCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    created = _service(db).create_case(
        student_id=payload.student_id,
        owner_area=payload.owner_area,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        user=user,
    )

    # 🔔 Event: case.created
    if kafka_state.producer is not None:
        await kafka_state.producer.send_and_wait(
            KAFKA_TOPIC,
            _audit_event(
                    event_type="case.created",
                    service="cases",
                    user=user,
                    entity_type="case",
                    entity_id=created.id,
                    severity="INFO",
                    payload={
                        "case_id": created.id,
                        "student_id": created.student_id,
                        "owner_area": created.owner_area,
                        "title": created.title,
                        "priority": str(created.priority),
                        "status": str(created.status),
                        "created_by": created.created_by_user_id,
                    },
                ),
        )

    return created


@router.get("", response_model=list[CaseOut])
def list_cases(
    status: CaseStatus | None = Query(default=None),
    priority: CasePriority | None = Query(default=None),
    mine: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    return _service(db).list_cases(status=status, priority=priority, mine=mine, user=user, limit=limit, offset=offset)


@router.get("/by-student/{student_id}", response_model=list[CaseOut])
def list_cases_by_student(
    student_id: str,
    status: CaseStatus | None = Query(default=None),
    priority: CasePriority | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Historial del estudiante/paciente.

    IMPORTANTE: Este endpoint NO rompe privacidad.
    Devuelve únicamente casos que el usuario actual puede ver (admin, área dueña, compartidos, creador/asignado).
    """
    try:
        return _service(db).list_cases_by_student(
            student_id=student_id,
            status=status,
            priority=priority,
            user=user,
            limit=limit,
            offset=offset,
        )
    except ForbiddenError as e:
        raise HTTPException(403, str(e))


@router.get("/{case_id}", response_model=CaseOut)
def get_case(case_id: str, db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    try:
        return _service(db).get_case(case_id, user)
    except NotFoundError as e:
        raise HTTPException(404, str(e))
    except ForbiddenError as e:
        raise HTTPException(403, str(e))


@router.patch("/{case_id}", response_model=CaseOut)
def update_case(case_id: str, payload: CaseUpdate, db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    try:
        return _service(db).update_case(
            case_id,
            title=payload.title,
            description=payload.description,
            priority=payload.priority,
            user=user,
        )
    except NotFoundError as e:
        raise HTTPException(404, str(e))
    except ForbiddenError as e:
        raise HTTPException(403, str(e))
    except BadRequestError as e:
        raise HTTPException(400, str(e))


@router.post("/{case_id}/assign", response_model=CaseOut)
def assign_case(case_id: str, payload: CaseAssign, db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    try:
        return _service(db).assign(case_id, payload.professional_id, user)
    except NotFoundError as e:
        raise HTTPException(404, str(e))
    except ForbiddenError as e:
        raise HTTPException(403, str(e))


@router.post("/{case_id}/status", response_model=CaseOut)
async def change_status(
    case_id: str,
    payload: CaseStatusChange,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    try:
        current = _service(db).get_case(case_id, user)
        old_status = current.status

        updated = _service(db).change_status(case_id, payload.status, user)

        # 🔔 Event: case.status_changed
        if kafka_state.producer is not None:
            await kafka_state.producer.send_and_wait(
                KAFKA_TOPIC,
                _audit_event(
                    event_type="case.status_changed",
                    service="cases",
                    user=user,
                    entity_type="case",
                    entity_id=updated.id,
                    severity="INFO",
                    payload={
                        "case_id": updated.id,
                        "old_status": str(old_status),
                        "new_status": str(updated.status),
                        "changed_by": user.user_id,
                    },
                ),
            )

        return updated
    except NotFoundError as e:
        raise HTTPException(404, str(e))
    except ForbiddenError as e:
        raise HTTPException(403, str(e))
    except BadRequestError as e:
        raise HTTPException(400, str(e))


@router.post("/{case_id}/share", response_model=CaseOut)
async def share_case(
    case_id: str,
    payload: CaseShare,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    try:
        updated = _service(db).share(
            case_id,
            user_id=payload.user_id,
            area=payload.area,
            permission=payload.permission,
            user=user,
        )

        # 🔔 Event: case.shared
        if kafka_state.producer is not None:
            await kafka_state.producer.send_and_wait(
                KAFKA_TOPIC,
                _audit_event(
                    event_type="case.shared",
                    service="cases",
                    user=user,
                    entity_type="case",
                    entity_id=updated.id,
                    severity="INFO",
                    payload={
                        "case_id": updated.id,
                        "shared_by": user.user_id,
                        "user_id": payload.user_id,
                        "area": payload.area,
                        "permission": str(payload.permission),
                    },
                ),
            )

        return updated
    except NotFoundError as e:
        raise HTTPException(404, str(e))
    except ForbiddenError as e:
        raise HTTPException(403, str(e))


@router.post("/{case_id}/notes", response_model=CaseNoteOut, status_code=201)
async def add_note(
    case_id: str,
    payload: CaseNoteCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    try:
        note = _service(db).add_note(case_id, kind=payload.kind, content=payload.content, user=user)

        # 🔔 Event: case.note_added
        if kafka_state.producer is not None:
            await kafka_state.producer.send_and_wait(
                KAFKA_TOPIC,
                _audit_event(
                    event_type="case.note_added",
                    service="cases",
                    user=user,
                    entity_type="case",
                    entity_id=case_id,
                    severity="INFO",
                    payload={
                        "case_id": case_id,
                        "note_id": note.id,
                        "kind": note.kind,
                        "author": note.author_user_id,
                    },
                ),
            )

        return note
    except NotFoundError as e:
        raise HTTPException(404, str(e))
    except ForbiddenError as e:
        raise HTTPException(403, str(e))


@router.get("/{case_id}/notes", response_model=list[CaseNoteOut])
def list_notes(
    case_id: str,
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    try:
        return _service(db).list_notes(case_id, user, limit=limit, offset=offset)
    except NotFoundError as e:
        raise HTTPException(404, str(e))
    except ForbiddenError as e:
        raise HTTPException(403, str(e))


@router.get("/{case_id}/timeline", response_model=list[TimelineEventOut])
def get_timeline(
    case_id: str,
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    try:
        return _service(db).timeline_for_case(case_id, user, limit=limit, offset=offset)
    except NotFoundError as e:
        raise HTTPException(404, str(e))
    except ForbiddenError as e:
        raise HTTPException(403, str(e))
