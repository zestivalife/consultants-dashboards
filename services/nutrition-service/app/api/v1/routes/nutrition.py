import uuid

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.response import success_response, error_response
from app.db.session import get_db
from app.api.v1.dependencies import get_user_id
from app.schemas.nutrition import AssignDietPlanRequest, DietPlanCreate
from app.services import nutrition_service

router = APIRouter(tags=["nutrition"])


@router.post("/diet-plan")
async def create_diet_plan(
    payload: DietPlanCreate,
    session: AsyncSession = Depends(get_db),
):
    result = await nutrition_service.create_diet_plan(session, payload)
    return success_response(data=result.model_dump(mode="json"), status_code=201)


@router.get("/templates")
async def list_templates(
    session: AsyncSession = Depends(get_db),
):
    plans = await nutrition_service.list_diet_plans(session)
    return success_response(data=[p.model_dump(mode="json") for p in plans])


@router.post("/assign")
async def assign_plan(
    payload: AssignDietPlanRequest,
    user_id: uuid.UUID = Depends(get_user_id),
    session: AsyncSession = Depends(get_db),
):
    result = await nutrition_service.assign_diet_plan(session, payload, assigned_by=user_id)
    return success_response(data=result.model_dump(mode="json"), status_code=201)


@router.get("/my-plan")
async def my_plan(
    user_id: uuid.UUID = Depends(get_user_id),
    session: AsyncSession = Depends(get_db),
):
    result = await nutrition_service.get_user_plan(session, user_id)
    return success_response(data=result.model_dump(mode="json"))


@router.post("/upload-report")
async def upload_report(
    file: UploadFile = File(...),
    user_id: uuid.UUID = Depends(get_user_id),
    session: AsyncSession = Depends(get_db),
):
    try:
        result = await nutrition_service.upload_health_report(session, user_id, file)
    except ValueError as exc:
        return error_response(message=str(exc), status_code=400)
    return success_response(data=result.model_dump(mode="json"), status_code=201)
