from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .models import UserProfile


class UserProfileRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> UserProfile | None:
        q = await self.db.execute(select(UserProfile).where(UserProfile.email == email))
        return q.scalar_one_or_none()

    async def create(self, email: str, is_active: bool = True) -> UserProfile:
        prof = UserProfile(email=email, is_active=is_active)
        self.db.add(prof)
        await self.db.commit()
        await self.db.refresh(prof)
        return prof

    async def save(self, prof: UserProfile) -> UserProfile:
        self.db.add(prof)
        await self.db.commit()
        await self.db.refresh(prof)
        return prof
