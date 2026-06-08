import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core import cache
from app.core.http_client import fetch_assessment_history, fetch_profile
from app.core.logging import get_logger
from app.db.models.active_performance_score import ActivePerformanceScore
from app.db.models.health_score import HealthScore
from app.db.models.medical_index_score import MedicalIndexScore
from app.db.models.physical_ease_score import PhysicalEaseScore
from app.repositories.score_repository import ScoreRepository
from app.schemas.scoring import (
    ActivePerformanceScoreResponse,
    ComputeResult,
    HealthScoreResponse,
    LatestScoresResponse,
    MedicalIndexScoreResponse,
    PhysicalEaseScoreResponse,
    TimelineEntry,
    TimelineResponse,
)
from app.services.formulas import (
    active_performance_score as ap_formula,
    health_score as hs_formula,
    medical_index_score as mi_formula,
    physical_ease_score as pe_formula,
)

logger = get_logger(__name__)


def _idempotency_window() -> timedelta:
    return timedelta(minutes=get_settings().scoring_idempotency_minutes)


async def _resolve_profile(user_id: uuid.UUID, request_id: str | None) -> dict:
    profile = await cache.get_cached_profile(user_id)
    if not profile:
        profile = await fetch_profile(user_id, request_id)
        if profile:
            await cache.set_cached_profile(user_id, profile)
    return profile or {}


async def _resolve_assessments(user_id: uuid.UUID, request_id: str | None) -> list[dict]:
    assessments = await cache.get_cached_assessments(user_id)
    if assessments is None:
        assessments = await fetch_assessment_history(user_id, request_id)
        await cache.set_cached_assessments(user_id, assessments)
    return assessments


def _filter_assessments(submissions: list[dict], assessment_type: str) -> list[dict]:
    return [s for s in submissions if s.get("assessment_type") == assessment_type]


async def _get_recent_scores(session: AsyncSession, user_id: uuid.UUID) -> ComputeResult | None:
    hs = await ScoreRepository(session, HealthScore).get_latest(user_id)
    if hs is None or hs.computed_at is None:
        return None

    computed = hs.computed_at if hs.computed_at.tzinfo else hs.computed_at.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) - computed >= _idempotency_window():
        return None

    pe = await ScoreRepository(session, PhysicalEaseScore).get_latest(user_id)
    ap = await ScoreRepository(session, ActivePerformanceScore).get_latest(user_id)
    mi = await ScoreRepository(session, MedicalIndexScore).get_latest(user_id)

    return ComputeResult(
        health=HealthScoreResponse.model_validate(hs),
        physical_ease=PhysicalEaseScoreResponse.model_validate(pe) if pe else PhysicalEaseScoreResponse(),
        active_performance=ActivePerformanceScoreResponse.model_validate(ap) if ap else ActivePerformanceScoreResponse(),
        medical_index=MedicalIndexScoreResponse.model_validate(mi) if mi else MedicalIndexScoreResponse(),
        recomputed=False,
    )


async def compute_scores(
    session: AsyncSession,
    user_id: uuid.UUID,
    request_id: str | None = None,
    force: bool = False,
) -> ComputeResult:
    if not force:
        existing = await _get_recent_scores(session, user_id)
        if existing is not None:
            logger.info("scores_idempotent_hit", user_id=str(user_id))
            return existing

    locked = await cache.acquire_scoring_lock(user_id)
    if not locked:
        logger.info("scores_lock_contention", user_id=str(user_id))
        existing = await _get_recent_scores(session, user_id)
        if existing is not None:
            return existing
        return await _build_latest_or_empty(session, user_id)

    try:
        return await _compute_and_store(session, user_id, request_id)
    finally:
        await cache.release_scoring_lock(user_id)


async def _build_latest_or_empty(session: AsyncSession, user_id: uuid.UUID) -> ComputeResult:
    hs = await ScoreRepository(session, HealthScore).get_latest(user_id)
    pe = await ScoreRepository(session, PhysicalEaseScore).get_latest(user_id)
    ap = await ScoreRepository(session, ActivePerformanceScore).get_latest(user_id)
    mi = await ScoreRepository(session, MedicalIndexScore).get_latest(user_id)

    return ComputeResult(
        health=HealthScoreResponse.model_validate(hs) if hs else HealthScoreResponse(),
        physical_ease=PhysicalEaseScoreResponse.model_validate(pe) if pe else PhysicalEaseScoreResponse(),
        active_performance=ActivePerformanceScoreResponse.model_validate(ap) if ap else ActivePerformanceScoreResponse(),
        medical_index=MedicalIndexScoreResponse.model_validate(mi) if mi else MedicalIndexScoreResponse(),
        recomputed=False,
    )


async def _compute_and_store(
    session: AsyncSession,
    user_id: uuid.UUID,
    request_id: str | None,
) -> ComputeResult:
    profile_data = await _resolve_profile(user_id, request_id)
    all_assessments = await _resolve_assessments(user_id, request_id)

    pss_data = _filter_assessments(all_assessments, "pss10")
    pe_data = _filter_assessments(all_assessments, "physical_ease")

    async with session.begin():
        hs_repo = ScoreRepository(session, HealthScore)
        hs_values = hs_formula.compute(profile_data, has_pss=len(pss_data) > 0)
        hs_record = await hs_repo.create(HealthScore(user_id=user_id, **hs_values))

        pe_repo = ScoreRepository(session, PhysicalEaseScore)
        pe_count = pe_data[0].get("count", 0) if pe_data else 0
        pe_values = pe_formula.compute(has_physical_ease=len(pe_data) > 0, response_count=pe_count)
        pe_record = await pe_repo.create(PhysicalEaseScore(user_id=user_id, **pe_values))

        ap_repo = ScoreRepository(session, ActivePerformanceScore)
        ap_values = ap_formula.compute(profile_data)
        ap_record = await ap_repo.create(ActivePerformanceScore(user_id=user_id, **ap_values))

        mi_repo = ScoreRepository(session, MedicalIndexScore)
        biomarkers = profile_data.get("biomarkers") if profile_data else None
        mi_values = mi_formula.compute(biomarkers)
        mi_record = await mi_repo.create(MedicalIndexScore(user_id=user_id, **mi_values))

    logger.info(
        "scores_computed",
        user_id=str(user_id),
        score_version=hs_record.score_version,
        algorithm_version=hs_record.algorithm_version,
    )

    return ComputeResult(
        health=HealthScoreResponse.model_validate(hs_record),
        physical_ease=PhysicalEaseScoreResponse.model_validate(pe_record),
        active_performance=ActivePerformanceScoreResponse.model_validate(ap_record),
        medical_index=MedicalIndexScoreResponse.model_validate(mi_record),
    )


async def get_latest(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> LatestScoresResponse:
    hs = await ScoreRepository(session, HealthScore).get_latest(user_id)
    pe = await ScoreRepository(session, PhysicalEaseScore).get_latest(user_id)
    ap = await ScoreRepository(session, ActivePerformanceScore).get_latest(user_id)
    mi = await ScoreRepository(session, MedicalIndexScore).get_latest(user_id)

    return LatestScoresResponse(
        health=HealthScoreResponse.model_validate(hs) if hs else None,
        physical_ease=PhysicalEaseScoreResponse.model_validate(pe) if pe else None,
        active_performance=ActivePerformanceScoreResponse.model_validate(ap) if ap else None,
        medical_index=MedicalIndexScoreResponse.model_validate(mi) if mi else None,
    )


async def get_timeline(
    session: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 30,
) -> TimelineResponse:
    hs_list = await ScoreRepository(session, HealthScore).get_timeline(user_id, limit)
    ap_list = await ScoreRepository(session, ActivePerformanceScore).get_timeline(user_id, limit)
    mi_list = await ScoreRepository(session, MedicalIndexScore).get_timeline(user_id, limit)
    pe_list = await ScoreRepository(session, PhysicalEaseScore).get_timeline(user_id, limit)

    by_date: dict[str, TimelineEntry] = {}

    for hs in hs_list:
        key = hs.created_at.isoformat()
        by_date.setdefault(key, TimelineEntry(created_at=hs.created_at))
        by_date[key].total_health_score = hs.total_health_score
        by_date[key].score_version = hs.score_version
        by_date[key].algorithm_version = hs.algorithm_version

    for ap in ap_list:
        key = ap.created_at.isoformat()
        by_date.setdefault(key, TimelineEntry(created_at=ap.created_at))
        by_date[key].active_performance_score = ap.active_performance_score

    for mi in mi_list:
        key = mi.created_at.isoformat()
        by_date.setdefault(key, TimelineEntry(created_at=mi.created_at))
        by_date[key].medical_index = mi.medical_index

    for pe in pe_list:
        key = pe.created_at.isoformat()
        by_date.setdefault(key, TimelineEntry(created_at=pe.created_at))
        by_date[key].physical_ease_score = pe.score

    entries = sorted(by_date.values(), key=lambda e: e.created_at, reverse=True)
    return TimelineResponse(entries=entries[:limit])
