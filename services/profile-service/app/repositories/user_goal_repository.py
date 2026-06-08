import uuid
from typing import Sequence

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user_goal import UserGoal


class UserGoalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, record: UserGoal) -> UserGoal:
        self._session.add(record)
        await self._session.flush()
        return record

    async def create_many(self, records: list[UserGoal]) -> list[UserGoal]:
        self._session.add_all(records)
        await self._session.flush()
        return records

    async def get_by_user_id(self, user_id: uuid.UUID) -> Sequence[UserGoal]:
        stmt = select(UserGoal).where(UserGoal.user_id == user_id)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def delete_by_user_id(self, user_id: uuid.UUID) -> None:
        stmt = delete(UserGoal).where(UserGoal.user_id == user_id)
        await self._session.execute(stmt)
        await self._session.flush()
