from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.postgres import get_db
from libs.security.jwt import get_current_user, require_role

from .schemas import ProfileOut, ProfileUpdate, StatusUpdateIn, StatusUpdateOut
from ..application.services.profile_service import ProfileService

router = APIRouter()

import os
import httpx
from fastapi import Header

from .schemas import AdminUserCreateIn, AdminUserCreateOut
from libs.security.jwt import require_role, get_current_user

AUTH_URL = os.getenv("AUTH_URL", "http://localhost:8000")  # ajusta tu puerto real de auth

@router.post(
    "/users",
    response_model=AdminUserCreateOut,
    dependencies=[Depends(require_role("admin"))],
)
async def admin_create_user(
    data: AdminUserCreateIn,
    authorization: str = Header(...), 
    db: AsyncSession = Depends(get_db),
):
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(
            f"{AUTH_URL}/auth/admin/users",
            json={"email": data.email, "role": data.role},
            headers={"Authorization": authorization},
        )

    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)

    auth_payload = r.json()
    temp_password = auth_payload["temp_password"]

    svc = ProfileService(db)

    prof = await svc.get_by_email(data.email)
    if not prof:
        prof = await svc.repo.create(email=data.email, is_active=True)


    update_data = {
        "full_name": data.full_name,
        "phone": data.phone,
        "career": data.career,
        "bio": data.bio,
        "area": data.area,
    }
    update_data = {k: v for k, v in update_data.items() if v is not None}
    if update_data:
        prof = await svc.update_me(data.email, update_data)

    return {"email": data.email, "role": data.role, "temp_password": temp_password}

@router.get("/users/me", response_model=ProfileOut)
async def get_me(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = ProfileService(db)
    return await svc.get_or_create_me(user["email"])


@router.put(
    "/users/me",
    response_model=ProfileOut,
    dependencies=[Depends(require_role("student", "professional", "admin"))],
)
async def update_me(
    data: ProfileUpdate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = ProfileService(db)
    return await svc.update_me(user["email"], data.model_dump(exclude_unset=True))


@router.get(
    "/users/{email}",
    response_model=ProfileOut,
    dependencies=[Depends(require_role("admin"))],
)
async def get_by_email(email: str, db: AsyncSession = Depends(get_db)):
    svc = ProfileService(db)
    prof = await svc.get_by_email(email)
    if not prof:
        raise HTTPException(404, "Perfil no encontrado")
    return prof


@router.patch(
    "/users/{email}/active",
    dependencies=[Depends(require_role("admin"))],
)
async def set_active(email: str, active: bool, db: AsyncSession = Depends(get_db)):
    svc = ProfileService(db)
    prof = await svc.set_active(email, active)
    return {"email": prof.email, "is_active": prof.is_active}

@router.patch(
    "/users/{email}/status",
    response_model=StatusUpdateOut,
    dependencies=[Depends(require_role("admin"))],
)
async def set_user_status(email: str, body: StatusUpdateIn, db: AsyncSession = Depends(get_db)):
    """Backoffice: activa/desactiva un usuario por email.
    status=active -> is_active=True
    status=disabled -> is_active=False
    """
    svc = ProfileService(db)
    active = body.status == "active"
    prof = await svc.set_active(email, active)
    return StatusUpdateOut(email=prof.email, status="active" if prof.is_active else "disabled")


@router.patch(
    "/professionals/{email}/status",
    response_model=StatusUpdateOut,
    dependencies=[Depends(require_role("admin"))],
)
async def set_professional_status(email: str, body: StatusUpdateIn, db: AsyncSession = Depends(get_db)):
    """Backoffice: cambia status de un profesional por email.
    (Se usa la misma bandera is_active por ahora.)
    """
    svc = ProfileService(db)
    active = body.status == "active"
    prof = await svc.set_active(email, active)
    return StatusUpdateOut(email=prof.email, status="active" if prof.is_active else "disabled")

