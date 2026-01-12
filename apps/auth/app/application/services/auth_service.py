import os

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...infrastructure.db.repositories import UserRepository
from ...infrastructure.security.password import hash_password, verify_password
from ...api.schemas import Token

from libs.security.jwt import create_token
from libs.messaging.kafka import get_producer


class AuthService:
    def __init__(self, user_repo: UserRepository | None = None):
        self.user_repo = user_repo or UserRepository()

    async def register(
        self,
        db: AsyncSession,
        *,
        email: str,
        password: str,
        role: str,
        must_change_password: bool = False,
    ) -> dict:
        existing = await self.user_repo.get_by_email(db, email)
        if existing:
            raise HTTPException(status_code=400, detail="Usuario ya existe")

        user = await self.user_repo.create(
            db,
            email=email,
            password_hash=hash_password(password),
            role=role,
            must_change_password=must_change_password,
        )

        await self._publish_user_created(email=user.email, role=user.role)
        return {"msg": "Usuario creado en Postgres", "email": user.email, "role": user.role}

    async def login(self, db: AsyncSession, *, email: str, password: str) -> Token:
        user = await self.user_repo.get_by_email(db, email)
        if not user or not verify_password(password, user.password_hash):
            # Emit audit event (Kafka) - degraded mode if Kafka down
            await self._publish_login_failed(email=email, reason="invalid_credentials")
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Usuario inactivo")

        token = create_token({"email": user.email, "role": user.role})
        # Emit audit event (Kafka) - degraded mode if Kafka down
        await self._publish_login_success(email=user.email, role=user.role)
        # Include a hint for the client to force a password change after a temp password.
        return Token(access_token=token, must_change_password=getattr(user, "must_change_password", False))

    async def list_users(self, db: AsyncSession) -> list[dict]:
        users = await self.user_repo.list_all(db)
        return [{"email": u.email, "role": u.role, "is_active": u.is_active} for u in users]

    async def _publish_user_created(self, *, email: str, role: str) -> None:
        topic = os.getenv("KAFKA_TOPIC_USER_EVENTS", "sibu.user.events")
        try:
            producer = await get_producer()
            try:
                await producer.send_and_wait(
                    topic,
                    {"type": "user.created", "email": email, "role": role},
                )
            finally:
                await producer.stop()
        except Exception as e:
            print(f"[WARN] Kafka publish failed: {e}")

    async def _publish_login_failed(self, *, email: str, reason: str = "invalid_credentials") -> None:
        topic = os.getenv("KAFKA_TOPIC_USER_EVENTS", "sibu.user.events")
        try:
            producer = await get_producer()
            try:
                await producer.send_and_wait(
                    topic,
                    {"type": "auth.login_failed", "email": email, "reason": reason},
                )
            finally:
                await producer.stop()
        except Exception as e:
            print(f"[WARN] Kafka publish failed: {e}")

    async def _publish_login_success(self, *, email: str, role: str) -> None:
        topic = os.getenv("KAFKA_TOPIC_USER_EVENTS", "sibu.user.events")
        try:
            producer = await get_producer()
            try:
                await producer.send_and_wait(
                    topic,
                    {"type": "auth.login_success", "email": email, "role": role},
                )
            finally:
                await producer.stop()
        except Exception as e:
            print(f"[WARN] Kafka publish failed: {e}")


    async def change_password(self, db, *, email, current_password, new_password):
        user = await self.user_repo.get_by_email(db, email)

        if not user or not verify_password(current_password, user.password_hash):
            raise HTTPException(status_code=401, detail="Contraseña actual incorrecta")

        user.password_hash = hash_password(new_password)

        if hasattr(user, "must_change_password"):
            user.must_change_password = False

        await self.user_repo.save(db, user)
        return {"msg": "Contraseña actualizada"}