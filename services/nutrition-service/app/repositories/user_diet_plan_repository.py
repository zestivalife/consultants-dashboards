import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user_diet_plan import UserDietPlan


class UserDietPlanRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, assignment: UserDietPlan) -> UserDietPlan:
        self._session.add(assignment)
        await self._session.flush()
        return assignment

    async def get_latest_for_user(self, user_id: uuid.UUID) -> UserDietPlan | None:
        result = await self._session.execute(
            select(UserDietPlan)
            .where(UserDietPlan.user_id == user_id)
            .order_by(UserDietPlan.assigned_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
