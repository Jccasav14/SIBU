from sqlalchemy.ext.asyncio import AsyncSession

from ...infrastructure.db.repositories import UserProfileRepository
from ...infrastructure.db.models import UserProfile


class ProfileService:
    def __init__(self, db: AsyncSession):
        self.repo = UserProfileRepository(db)

    async def get_or_create_me(self, email: str) -> UserProfile:
        prof = await self.repo.get_by_email(email)
        if prof:
            return prof
        return await self.repo.create(email=email, is_active=True)

    async def update_me(self, email: str, data: dict) -> UserProfile:
        prof = await self.repo.get_by_email(email)
        if not prof:
            prof = UserProfile(email=email, is_active=True)

        for k, v in data.items():
            setattr(prof, k, v)

        return await self.repo.save(prof)

    async def get_by_email(self, email: str) -> UserProfile | None:
        return await self.repo.get_by_email(email)

    async def set_active(self, email: str, active: bool) -> UserProfile:
        prof = await self.repo.get_by_email(email)
        if not prof:
            return await self.repo.create(email=email, is_active=active)
        prof.is_active = active
        return await self.repo.save(prof)
