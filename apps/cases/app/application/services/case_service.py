from __future__ import annotations

from sqlalchemy.orm import Session

from ...domain.enums import CaseStatus, TimelineEventType, AccessPermission
from ...domain.exceptions import NotFoundError, ForbiddenError, BadRequestError
from ...infrastructure.db.models import Case, CaseTimelineEvent, CaseAccess, CaseNote
from ...infrastructure.db.repositories import CaseRepository, TimelineRepository, AccessRepository, NotesRepository
from ...security.jwt import CurrentUser

# reglas simples de transición (puedes endurecerlas luego)
_ALLOWED_TRANSITIONS: dict[CaseStatus, set[CaseStatus]] = {
    CaseStatus.OPEN: {CaseStatus.IN_PROGRESS, CaseStatus.CLOSED},
    CaseStatus.IN_PROGRESS: {CaseStatus.RESOLVED, CaseStatus.CLOSED},
    CaseStatus.RESOLVED: {CaseStatus.CLOSED, CaseStatus.IN_PROGRESS},
    CaseStatus.CLOSED: set(),
}


def _is_admin(user: CurrentUser) -> bool:
    return "admin" in user.roles


def _is_professional(user: CurrentUser) -> bool:
    # puedes mapear roles reales luego (psychologist/social_worker/etc)
    return "professional" in user.roles or any(r in user.roles for r in ["psychologist", "doctor", "social_worker"])


def _is_student(user: CurrentUser) -> bool:
    return "student" in user.roles


class CaseService:
    def __init__(self, db: Session):
        self.db = db
        self.cases = CaseRepository(db)
        self.timeline = TimelineRepository(db)
        self.access = AccessRepository(db)
        self.notes = NotesRepository(db)

    def _can_view(self, c: Case, user: CurrentUser) -> bool:
        if _is_admin(user):
            return True

        # el estudiante ve sus propios casos
        if _is_student(user) and c.student_id == user.user_id:
            return True

        # profesionales: creador / asignado
        if c.created_by_user_id == user.user_id:
            return True
        if c.assigned_professional_id and c.assigned_professional_id == user.user_id:
            return True

        # acceso explícito (por usuario o por área)
        if self.access.has_user_access(c.id, user.user_id):
            return True
        if user.area and self.access.has_area_access(c.id, user.area):
            return True

        # acceso por área dueña (si el profesional pertenece a esa área)
        if user.area and c.owner_area == user.area:
            return True

        return False

    def _can_write(self, c: Case, user: CurrentUser) -> bool:
        if _is_admin(user):
            return True

        # el estudiante no escribe historia clínica aquí (eso lo decide tu política)
        if _is_student(user):
            return False

        # creador puede editar campos mientras no esté CLOSED
        if c.created_by_user_id == user.user_id and c.status != CaseStatus.CLOSED:
            return True

        # asignado puede trabajar el caso
        if c.assigned_professional_id and c.assigned_professional_id == user.user_id:
            return True

        # permisos explícitos
        if self.access.has_user_access(c.id, user.user_id, require_write=True):
            return True
        if user.area and self.access.has_area_access(c.id, user.area, require_write=True):
            return True

        return False

    def create_case(
        self,
        *,
        student_id: str,
        owner_area: str,
        title: str,
        description: str,
        priority,
        user: CurrentUser,
    ) -> Case:
        if not (_is_admin(user) or _is_professional(user)):
            raise ForbiddenError("Solo un profesional o admin puede crear casos")

        c = Case(
            student_id=student_id,
            owner_area=owner_area,
            created_by_user_id=user.user_id,
            title=title,
            description=description,
            priority=priority,
            status=CaseStatus.OPEN,
        )
        self.cases.create(c)
        self.timeline.add_event(
            CaseTimelineEvent(
                case_id=c.id,
                type=TimelineEventType.CREATED,
                data={"title": title, "priority": str(priority), "student_id": student_id, "owner_area": owner_area},
                actor_user_id=user.user_id,
            )
        )
        self.db.commit()
        self.db.refresh(c)
        return c

    def get_case(self, case_id: str, user: CurrentUser) -> Case:
        c = self.cases.get(case_id)
        if not c:
            raise NotFoundError("Case no existe")
        if not self._can_view(c, user):
            raise ForbiddenError("No puedes ver este case")
        return c

    def list_cases(self, *, status=None, priority=None, mine: bool = False, user: CurrentUser, limit: int = 50, offset: int = 0):
        # Admin ve todo
        if _is_admin(user):
            return self.cases.list(status=status, priority=priority, limit=limit, offset=offset)

        # Estudiante ve solo sus casos
        if _is_student(user):
            return self.cases.list(student_id=user.user_id, status=status, priority=priority, limit=limit, offset=offset)

        # Profesionales: (mine=true) mis creados/asignados; si no, todo accesible (filtrado en memoria)
        if mine:
            rows = self.cases.list(created_by_user_id=user.user_id, status=status, priority=priority, limit=limit, offset=offset)
            # también incluir asignados
            rows2 = self.cases.list(assigned_professional_id=user.user_id, status=status, priority=priority, limit=limit, offset=offset)
            # dedup
            by_id = {c.id: c for c in list(rows) + list(rows2)}
            return list(by_id.values())

        # accesibles: en MVP filtramos en memoria
        rows = self.cases.list(status=status, priority=priority, limit=limit, offset=offset)
        return [c for c in rows if self._can_view(c, user)]

    def list_cases_by_student(
        self,
        *,
        student_id: str,
        status=None,
        priority=None,
        user: CurrentUser,
        limit: int = 50,
        offset: int = 0,
    ):
        """Lista el historial (casos) de un estudiante/paciente.

        Regla MVP:
        - Admin: ve todo.
        - Estudiante: solo su propio historial.
        - Profesional: solo lo que puede ver por reglas de área/owner + share + asignación.
        """

        if _is_admin(user):
            return self.cases.list(student_id=student_id, status=status, priority=priority, limit=limit, offset=offset)

        if _is_student(user):
            if user.user_id != student_id:
                raise ForbiddenError("No puedes ver el historial de otro estudiante")
            return self.cases.list(student_id=student_id, status=status, priority=priority, limit=limit, offset=offset)

        rows = self.cases.list(student_id=student_id, status=status, priority=priority, limit=limit, offset=offset)
        return [c for c in rows if self._can_view(c, user)]

    def update_case(self, case_id: str, *, title=None, description=None, priority=None, user: CurrentUser) -> Case:
        c = self.get_case(case_id, user)
        if not self._can_write(c, user):
            raise ForbiddenError("No puedes modificar este case")

        changed = {}
        if title is not None:
            c.title = title
            changed["title"] = title
        if description is not None:
            c.description = description
            changed["description"] = "updated"
        if priority is not None:
            c.priority = priority
            changed["priority"] = str(priority)

        if not changed:
            raise BadRequestError("Nada que actualizar")

        self.cases.save(c)
        self.timeline.add_event(
            CaseTimelineEvent(
                case_id=c.id,
                type=TimelineEventType.UPDATED,
                data=changed,
                actor_user_id=user.user_id,
            )
        )
        self.db.commit()
        self.db.refresh(c)
        return c

    def assign(self, case_id: str, professional_id: str, user: CurrentUser) -> Case:
        c = self.get_case(case_id, user)
        if not (_is_admin(user) or c.created_by_user_id == user.user_id):
            raise ForbiddenError("Solo admin o creador puede asignar")

        c.assigned_professional_id = professional_id
        self.cases.save(c)
        self.timeline.add_event(
            CaseTimelineEvent(
                case_id=c.id,
                type=TimelineEventType.ASSIGNED,
                data={"professional_id": professional_id},
                actor_user_id=user.user_id,
            )
        )
        self.db.commit()
        self.db.refresh(c)
        return c

    def change_status(self, case_id: str, new_status: CaseStatus, user: CurrentUser) -> Case:
        c = self.get_case(case_id, user)
        if not self._can_write(c, user):
            raise ForbiddenError("No puedes cambiar estado")

        allowed = _ALLOWED_TRANSITIONS.get(c.status, set())
        if new_status not in allowed:
            raise BadRequestError(f"Transición no permitida: {c.status} -> {new_status}")

        old = c.status
        c.status = new_status
        self.cases.save(c)
        self.timeline.add_event(
            CaseTimelineEvent(
                case_id=c.id,
                type=TimelineEventType.STATUS_CHANGED,
                data={"from": str(old), "to": str(new_status)},
                actor_user_id=user.user_id,
            )
        )
        self.db.commit()
        self.db.refresh(c)
        return c

    def share(self, case_id: str, *, user_id: str | None, area: str | None, permission: AccessPermission, user: CurrentUser) -> Case:
        c = self.get_case(case_id, user)
        if not self._can_write(c, user):
            raise ForbiddenError("No puedes compartir este case")

        if user_id:
            access = CaseAccess(
                case_id=c.id,
                grantee_type="USER",
                grantee_id=user_id,
                permission=permission,
                granted_by_user_id=user.user_id,
            )
            self.access.grant(access)
        if area:
            access = CaseAccess(
                case_id=c.id,
                grantee_type="AREA",
                grantee_id=area,
                permission=permission,
                granted_by_user_id=user.user_id,
            )
            self.access.grant(access)

        self.timeline.add_event(
            CaseTimelineEvent(
                case_id=c.id,
                type=TimelineEventType.SHARED,
                data={"user_id": user_id, "area": area, "permission": str(permission)},
                actor_user_id=user.user_id,
            )
        )
        self.db.commit()
        self.db.refresh(c)
        return c

    def add_note(self, case_id: str, *, kind: str, content: str, user: CurrentUser) -> CaseNote:
        c = self.get_case(case_id, user)
        if not self._can_write(c, user):
            raise ForbiddenError("No puedes agregar notas a este case")

        note = CaseNote(
            case_id=c.id,
            author_user_id=user.user_id,
            author_area=user.area or c.owner_area,
            kind=kind,
            content=content,
        )
        self.notes.add(note)
        self.timeline.add_event(
            CaseTimelineEvent(
                case_id=c.id,
                type=TimelineEventType.NOTE_ADDED,
                data={"note_id": note.id, "kind": kind},
                actor_user_id=user.user_id,
            )
        )
        self.db.commit()
        self.db.refresh(note)
        return note

    def list_notes(self, case_id: str, user: CurrentUser, limit: int = 200, offset: int = 0) -> list[CaseNote]:
        c = self.get_case(case_id, user)
        return self.notes.list_by_case(c.id, limit=limit, offset=offset)

    def timeline_for_case(self, case_id: str, user: CurrentUser, limit: int = 200, offset: int = 0):
        c = self.get_case(case_id, user)
        return self.timeline.list_by_case(c.id, limit=limit, offset=offset)
