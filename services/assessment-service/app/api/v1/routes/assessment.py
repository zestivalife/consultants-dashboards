import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.response import success_response
from app.db.session import get_db
from app.api.v1.dependencies import get_user_id
from app.schemas.assessment import SubmissionRequest
from app.services import assessment_service

router = APIRouter(tags=["assessments"])


@router.post("/brain-state")
async def submit_brain_state(
    body: SubmissionRequest,
    user_id: uuid.UUID = Depends(get_user_id),
    session: AsyncSession = Depends(get_db),
):
    result = await assessment_service.submit(session, user_id, "brain_state", body.answers)
    return success_response(data=result.model_dump(mode="json"), message="Brain state assessment submitted", status_code=201)


@router.post("/focus-mode")
async def submit_focus_mode(
    body: SubmissionRequest,
    user_id: uuid.UUID = Depends(get_user_id),
    session: AsyncSession = Depends(get_db),
):
    result = await assessment_service.submit(session, user_id, "focus_mode", body.answers)
    return success_response(data=result.model_dump(mode="json"), message="Focus mode assessment submitted", status_code=201)


@router.post("/pss10")
async def submit_pss10(
    body: SubmissionRequest,
    user_id: uuid.UUID = Depends(get_user_id),
    session: AsyncSession = Depends(get_db),
):
    result = await assessment_service.submit(session, user_id, "pss10", body.answers)
    return success_response(data=result.model_dump(mode="json"), message="PSS-10 assessment submitted", status_code=201)


@router.post("/physical-ease")
async def submit_physical_ease(
    body: SubmissionRequest,
    user_id: uuid.UUID = Depends(get_user_id),
    session: AsyncSession = Depends(get_db),
):
    result = await assessment_service.submit(session, user_id, "physical_ease", body.answers)
    return success_response(data=result.model_dump(mode="json"), message="Physical ease assessment submitted", status_code=201)


@router.get("/history")
async def get_history(
    user_id: uuid.UUID = Depends(get_user_id),
    session: AsyncSession = Depends(get_db),
):
    result = await assessment_service.get_history(session, user_id)
    return success_response(data=result.model_dump(mode="json"))
