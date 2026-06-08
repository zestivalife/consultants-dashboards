import uuid

from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.response import success_response
from app.db.session import get_db
from app.api.v1.dependencies import get_user_id
from app.services import scoring_service

router = APIRouter(tags=["scoring"])


@router.post("/compute")
async def compute_scores(
    request: Request,
    user_id: uuid.UUID = Depends(get_user_id),
    session: AsyncSession = Depends(get_db),
    force: bool = Query(default=False),
):
    request_id = getattr(request.state, "request_id", None)
    result = await scoring_service.compute_scores(session, user_id, request_id, force=force)
    status = 201 if result.recomputed else 200
    message = "Scores computed" if result.recomputed else "Recent scores returned"
    return success_response(
        data=result.model_dump(mode="json"),
        message=message,
        status_code=status,
    )


@router.get("/me")
async def get_latest_scores(
    user_id: uuid.UUID = Depends(get_user_id),
    session: AsyncSession = Depends(get_db),
):
    result = await scoring_service.get_latest(session, user_id)
    return success_response(data=result.model_dump())


@router.get("/timeline")
async def get_score_timeline(
    user_id: uuid.UUID = Depends(get_user_id),
    session: AsyncSession = Depends(get_db),
    limit: int = Query(default=30, ge=1, le=100),
):
    result = await scoring_service.get_timeline(session, user_id, limit)
    return success_response(data=result.model_dump(mode="json"))
