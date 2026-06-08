import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.health_report import HealthReport


class HealthReportRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, report: HealthReport) -> HealthReport:
        self._session.add(report)
        await self._session.flush()
        return report

    async def get_by_user(self, user_id: uuid.UUID) -> list[HealthReport]:
        result = await self._session.execute(
            select(HealthReport)
            .where(HealthReport.user_id == user_id)
            .order_by(HealthReport.uploaded_at.desc())
        )
        return list(result.scalars().all())
