from __future__ import annotations

from typing import Optional, Set

from pydantic import BaseModel, EmailStr, field_validator

# NOTE: SIBU roles for this project (student removed, insurance added)
ALLOWED_ROLES: Set[str] = {"insurance", "professional", "admin"}


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    role: str  # insurance | professional | admin

    @field_validator("password")
    @classmethod
    def password_rules(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La contraseña debe tener mínimo 8 caracteres.")
        if len(v) > 128:
            raise ValueError("La contraseña es demasiado larga (máx 128 caracteres).")
        return v

    @field_validator("role")
    @classmethod
    def role_rules(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in ALLOWED_ROLES:
            raise ValueError("Rol inválido. Usa: insurance, professional, admin.")
        return v


class AdminCreateUser(BaseModel):
    email: EmailStr
    role: str
    password: Optional[str] = None

    @field_validator("role")
    @classmethod
    def role_rules(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in ALLOWED_ROLES:
            raise ValueError("Rol inválido. Usa: insurance, professional, admin.")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    must_change_password: bool = False


class UserJWT(BaseModel):
    email: EmailStr
    role: str
