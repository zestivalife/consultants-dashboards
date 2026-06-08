import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.diet_plan import DietPlan


class DietPlanRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, plan: DietPlan) -> DietPlan:
        self._session.add(plan)
        await self._session.flush()
        await self._session.refresh(plan, ["meals"])
        return plan

    async def get_by_id(self, plan_id: uuid.UUID) -> DietPlan | None:
        return await self._session.get(DietPlan, plan_id)

    async def list_all(self) -> list[DietPlan]:
        result = await self._session.execute(
            select(DietPlan).order_by(DietPlan.created_at.desc())
        )
        return list(result.scalars().all())
