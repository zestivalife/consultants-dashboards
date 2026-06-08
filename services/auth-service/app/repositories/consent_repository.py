import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.consent import Consent


class ConsentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, consent: Consent) -> Consent:
        self._session.add(consent)
        await self._session.flush()
        return consent

    async def get_by_user(self, user_id: uuid.UUID) -> list[Consent]:
        stmt = select(Consent).where(Consent.user_id == user_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
