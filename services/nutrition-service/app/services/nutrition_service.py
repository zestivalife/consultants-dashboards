import uuid

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.core.logging import get_logger
from app.core.storage import save_upload
from app.db.models.diet_plan import DietPlan
from app.db.models.health_report import HealthReport
from app.db.models.meal_template import MealTemplate
from app.db.models.user_diet_plan import UserDietPlan
from app.repositories.diet_plan_repository import DietPlanRepository
from app.repositories.health_report_repository import HealthReportRepository
from app.repositories.meal_template_repository import MealTemplateRepository
from app.repositories.user_diet_plan_repository import UserDietPlanRepository
from app.schemas.nutrition import (
    AssignDietPlanRequest,
    DietPlanCreate,
    DietPlanResponse,
    DietPlanSummary,
    HealthReportResponse,
    UserDietPlanResponse,
)

logger = get_logger(__name__)


async def create_diet_plan(
    session: AsyncSession,
    payload: DietPlanCreate,
) -> DietPlanResponse:
    plan_repo = DietPlanRepository(session)
    meal_repo = MealTemplateRepository(session)

    plan = DietPlan(
        name=payload.name,
        description=payload.description,
        calorie_target=payload.calorie_target,
        protein_target=payload.protein_target,
        fat_target=payload.fat_target,
        carb_target=payload.carb_target,
    )
    await plan_repo.create(plan)

    if payload.meals:
        meals = [
            MealTemplate(
                diet_plan_id=plan.id,
                meal_type=m.meal_type,
                meal_name=m.meal_name,
                calories=m.calories,
                protein=m.protein,
                carbs=m.carbs,
                fats=m.fats,
            )
            for m in payload.meals
        ]
        await meal_repo.create_many(meals)

    logger.info("diet_plan_created", plan_id=str(plan.id), name=plan.name)
    await session.commit()
    return DietPlanResponse.model_validate(plan)


async def list_diet_plans(session: AsyncSession) -> list[DietPlanSummary]:
    repo = DietPlanRepository(session)
    plans = await repo.list_all()
    return [DietPlanSummary.model_validate(p) for p in plans]


async def assign_diet_plan(
    session: AsyncSession,
    payload: AssignDietPlanRequest,
    assigned_by: uuid.UUID,
) -> UserDietPlanResponse:
    plan_repo = DietPlanRepository(session)
    plan = await plan_repo.get_by_id(payload.diet_plan_id)
    if plan is None:
        raise NotFoundException("Diet plan not found")

    assignment = UserDietPlan(
        user_id=payload.user_id,
        diet_plan_id=payload.diet_plan_id,
        assigned_by=assigned_by,
    )
    udp_repo = UserDietPlanRepository(session)
    await udp_repo.create(assignment)

    logger.info(
        "diet_plan_assigned",
        user_id=str(payload.user_id),
        plan_id=str(payload.diet_plan_id),
        assigned_by=str(assigned_by),
    )
    return UserDietPlanResponse.model_validate(assignment)


async def get_user_plan(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> UserDietPlanResponse:
    repo = UserDietPlanRepository(session)
    assignment = await repo.get_latest_for_user(user_id)
    if assignment is None:
        raise NotFoundException("No diet plan assigned to this user")
    return UserDietPlanResponse.model_validate(assignment)


async def upload_health_report(
    session: AsyncSession,
    user_id: uuid.UUID,
    file: UploadFile,
) -> HealthReportResponse:
    file_url = await save_upload(file, user_id)

    report = HealthReport(user_id=user_id, file_url=file_url)
    repo = HealthReportRepository(session)
    await repo.create(report)

    logger.info("health_report_uploaded", user_id=str(user_id), file_url=file_url)
    return HealthReportResponse.model_validate(report)
