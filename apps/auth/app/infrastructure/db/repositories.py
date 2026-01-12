from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .models import User


class UserRepository:
    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        q = await db.execute(select(User).where(User.email == email))
        return q.scalar_one_or_none()

    async def create(
        self,
        db: AsyncSession,
        *,
        email: str,
        password_hash: str,
        role: str,
        must_change_password: bool = False,
    ) -> User:
        user = User(
            email=email,
            password_hash=password_hash,
            role=role,
            is_active=True,
            must_change_password=must_change_password,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def list_all(self, db: AsyncSession) -> list[User]:
        q = await db.execute(select(User))
        return list(q.scalars().all())

    # 🔹 AGREGA ESTO
    async def save(self, db: AsyncSession, user: User) -> User:
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
