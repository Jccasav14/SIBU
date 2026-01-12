from __future__ import annotations

from ..settings import settings


class Mongo:
    def __init__(self) -> None:
        self.client = None

    def connect(self) -> None:
        if self.client:
            return
        # Lazy import so tests can run without Mongo deps.
        from motor.motor_asyncio import AsyncIOMotorClient  # type: ignore

        self.client = AsyncIOMotorClient(settings.MONGO_URI)

    async def close(self) -> None:
        if self.client:
            self.client.close()
            self.client = None

    @property
    def db(self):
        if not self.client:
            raise RuntimeError("Mongo client not initialized")
        return self.client[settings.MONGO_DB]


mongo = Mongo()
