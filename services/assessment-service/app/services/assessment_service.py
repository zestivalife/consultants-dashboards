import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.base import Base
from app.db.models.brain_state_response import BrainStateResponse
from app.db.models.focus_mode_response import FocusModeResponse
from app.db.models.physical_ease_response import PhysicalEaseResponse
from app.db.models.pss10_response import PSS10Response
from app.repositories.assessment_repository import AssessmentRepository
from app.schemas.assessment import (
    AnswerItem,
    AnswerResponse,
    HistoryEntry,
    HistoryResponse,
    SubmissionResponse,
)

logger = get_logger(__name__)

ASSESSMENT_MODELS: dict[str, type[Base]] = {
    "brain_state": BrainStateResponse,
    "focus_mode": FocusModeResponse,
    "pss10": PSS10Response,
    "physical_ease": PhysicalEaseResponse,
}


async def submit(
    session: AsyncSession,
    user_id: uuid.UUID,
    assessment_type: str,
    answers: list[AnswerItem],
) -> SubmissionResponse:
    model_cls = ASSESSMENT_MODELS[assessment_type]
    repo = AssessmentRepository(session, model_cls)

    now = datetime.now(timezone.utc)
    records = [
        model_cls(
            user_id=user_id,
            question_id=a.question_id,
            response_value=a.response_value,
            submitted_at=now,
        )
        for a in answers
    ]
    await repo.bulk_create(records)

    logger.info(
        "assessment_submitted",
        user_id=str(user_id),
        type=assessment_type,
        count=len(records),
    )

    return SubmissionResponse(
        assessment_type=assessment_type,
        count=len(records),
        answers=[AnswerResponse.model_validate(r) for r in records],
    )


async def get_history(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> HistoryResponse:
    entries: list[HistoryEntry] = []

    for atype, model_cls in ASSESSMENT_MODELS.items():
        repo = AssessmentRepository(session, model_cls)
        count = await repo.count_by_user(user_id)
        if count == 0:
            continue
        latest = await repo.get_latest_submission_time(user_id)
        entries.append(
            HistoryEntry(
                assessment_type=atype,
                submitted_at=latest or datetime.now(timezone.utc),
                count=count,
            )
        )

    entries.sort(key=lambda e: e.submitted_at, reverse=True)
    return HistoryResponse(submissions=entries)
