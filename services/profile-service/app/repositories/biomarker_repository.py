import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.biomarker import Biomarker


class BiomarkerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, record: Biomarker) -> Biomarker:
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_by_user_id(self, user_id: uuid.UUID) -> Biomarker | None:
        stmt = select(Biomarker).where(Biomarker.user_id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, record: Biomarker) -> Biomarker:
        await self._session.flush()
        return record
