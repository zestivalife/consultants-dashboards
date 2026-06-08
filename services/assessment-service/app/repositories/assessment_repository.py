import uuid
from datetime import datetime
from typing import TypeVar

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

T = TypeVar("T", bound=Base)


class AssessmentRepository:
    """Generic repository that works for any assessment response table."""

    def __init__(self, session: AsyncSession, model: type[T]) -> None:
        self._session = session
        self._model = model

    async def bulk_create(self, records: list[T]) -> list[T]:
        self._session.add_all(records)
        await self._session.flush()
        return records

    async def get_by_user(self, user_id: uuid.UUID) -> list[T]:
        stmt = (
            select(self._model)
            .where(self._model.user_id == user_id)
            .order_by(self._model.submitted_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_submission_time(self, user_id: uuid.UUID) -> datetime | None:
        stmt = (
            select(func.max(self._model.submitted_at))
            .where(self._model.user_id == user_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_by_user(self, user_id: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(self._model)
            .where(self._model.user_id == user_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()
