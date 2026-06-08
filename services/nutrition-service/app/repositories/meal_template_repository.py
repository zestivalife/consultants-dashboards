import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.meal_template import MealTemplate


class MealTemplateRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, meal: MealTemplate) -> MealTemplate:
        self._session.add(meal)
        await self._session.flush()
        return meal

    async def create_many(self, meals: list[MealTemplate]) -> list[MealTemplate]:
        self._session.add_all(meals)
        await self._session.flush()
        return meals

    async def get_by_plan(self, diet_plan_id: uuid.UUID) -> list[MealTemplate]:
        result = await self._session.execute(
            select(MealTemplate).where(MealTemplate.diet_plan_id == diet_plan_id)
        )
        return list(result.scalars().all())
