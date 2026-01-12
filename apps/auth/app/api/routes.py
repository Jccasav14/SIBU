from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import UserRegister, UserLogin, Token
from ..application.services.auth_service import AuthService
from ..infrastructure.db.session import get_db
import secrets
from .schemas import ChangePasswordIn
from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import AdminCreateUser
from ..application.services.auth_service import AuthService
from ..infrastructure.db.session import get_db
from libs.security.jwt import require_role
from libs.security.jwt import require_role, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/change-password")
async def change_password(
    data: ChangePasswordIn,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService()
    return await service.change_password(
        db,
        email=user["email"],
        current_password=data.current_password,
        new_password=data.new_password,
    )

@router.post("/register")
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    service = AuthService()
    return await service.register(db, email=data.email, password=data.password, role=data.role)


@router.post("/login", response_model=Token)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    service = AuthService()
    return await service.login(db, email=data.email, password=data.password)


@router.get("/me")
def me(user=Depends(get_current_user)):
    return {"email": user["email"], "role": user["role"]}


@router.get("/users", dependencies=[Depends(require_role("admin"))])
async def list_users(db: AsyncSession = Depends(get_db)):
    service = AuthService()
    return await service.list_users(db)

@router.post("/admin/users", dependencies=[Depends(require_role("admin"))])
async def admin_create_user(data: AdminCreateUser, db: AsyncSession = Depends(get_db)):
    temp_password = data.password or secrets.token_urlsafe(10)

    service = AuthService()

    await service.register(
        db,
        email=data.email,
        password=temp_password,
        role=data.role,
        must_change_password=True,
    )

    return {
        "email": data.email,
        "role": data.role,
        "temp_password": temp_password
    }