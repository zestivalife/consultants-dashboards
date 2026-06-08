import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user_profile import UserProfile


class UserProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, profile: UserProfile) -> UserProfile:
        self._session.add(profile)
        await self._session.flush()
        return profile

    async def get_by_user_id(self, user_id: uuid.UUID) -> UserProfile | None:
        stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, profile: UserProfile) -> UserProfile:
        await self._session.flush()
        return profile
