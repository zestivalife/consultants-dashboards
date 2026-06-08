import uuid
from datetime import datetime, timezone
from typing import TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

T = TypeVar("T", bound=Base)

SCORE_VERSION = "v1"
ALGORITHM_VERSION = "2026-03"


class ScoreRepository:
    def __init__(self, session: AsyncSession, model: type[T]) -> None:
        self._session = session
        self._model = model

    async def create(self, record: T) -> T:
        if not getattr(record, "score_version", None):
            record.score_version = SCORE_VERSION
        if not getattr(record, "algorithm_version", None):
            record.algorithm_version = ALGORITHM_VERSION
        if not getattr(record, "computed_at", None):
            record.computed_at = datetime.now(timezone.utc)

        self._session.add(record)
        await self._session.flush()
        return record

    async def get_latest(self, user_id: uuid.UUID) -> T | None:
        stmt = (
            select(self._model)
            .where(self._model.user_id == user_id)
            .order_by(self._model.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_timeline(self, user_id: uuid.UUID, limit: int = 30) -> list[T]:
        stmt = (
            select(self._model)
            .where(self._model.user_id == user_id)
            .order_by(self._model.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
