import uuid

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.response import success_response, error_response
from app.db.session import get_db
from app.api.v1.dependencies import get_user_id
from app.schemas.profile import FullProfileCreate, FullProfileUpdate
from app.services import profile_service

router = APIRouter(tags=["profile"])


@router.post("")
async def create_profile(
    body: FullProfileCreate,
    user_id: uuid.UUID = Depends(get_user_id),
    session: AsyncSession = Depends(get_db),
):
    result = await profile_service.create_profile(session, user_id, body)
    return success_response(
        data=result.model_dump(mode="json"),
        message="Profile created",
        status_code=201,
    )


@router.get("/me")
async def get_my_profile(
    user_id: uuid.UUID = Depends(get_user_id),
    session: AsyncSession = Depends(get_db),
):
    result = await profile_service.get_profile(session, user_id)
    return success_response(data=result.model_dump(mode="json"))


@router.put("/me")
async def update_my_profile(
    body: FullProfileUpdate,
    user_id: uuid.UUID = Depends(get_user_id),
    session: AsyncSession = Depends(get_db),
):
    result = await profile_service.update_profile(session, user_id, body)
    return success_response(
        data=result.model_dump(mode="json"),
        message="Profile updated",
    )


@router.get("/onboarding-status")
async def get_onboarding_status(
    user_id: uuid.UUID = Depends(get_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Check whether the user has completed the onboarding questionnaire."""
    result = await profile_service.get_onboarding_status(session, user_id)
    return success_response(data=result.model_dump(mode="json"))


@router.post("/upload-report")
async def upload_health_report(
    file: UploadFile = File(...),
    user_id: uuid.UUID = Depends(get_user_id),
    session: AsyncSession = Depends(get_db),
):
    try:
        result = await profile_service.process_health_report(session, user_id, file)
        return success_response(
            data=result.model_dump(mode="json"),
            message="Health report uploaded and biomarkers extracted successfully",
            status_code=201
        )
    except Exception as exc:
        return error_response(message=str(exc), status_code=400)
