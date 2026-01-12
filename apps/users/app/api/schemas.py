from pydantic import BaseModel, EmailStr
from typing import Optional
from pydantic import BaseModel, EmailStr
from typing import Optional

class AdminUserCreateIn(BaseModel):
    email: EmailStr
    role: str
    area: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    career: Optional[str] = None
    bio: Optional[str] = None

class AdminUserCreateOut(BaseModel):
    email: EmailStr
    role: str
    temp_password: str


class ProfileOut(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None
    career: Optional[str] = None
    bio: Optional[str] = None
    area: Optional[str] = None 
    is_active: bool = True

    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    career: Optional[str] = None
    bio: Optional[str] = None


from pydantic import BaseModel
from typing import Literal

class StatusUpdateIn(BaseModel):
    status: Literal["active", "disabled"]

class StatusUpdateOut(BaseModel):
    email: str
    status: Literal["active", "disabled"]

