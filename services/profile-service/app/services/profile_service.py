import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.core.logging import get_logger
from app.db.models.biomarker import Biomarker
from app.db.models.body_measurement import BodyMeasurement
from app.db.models.lifestyle_baseline import LifestyleBaseline
from app.db.models.nutrition_baseline import NutritionBaseline
from app.db.models.user_goal import UserGoal
from app.db.models.user_profile import UserProfile
from app.repositories.biomarker_repository import BiomarkerRepository
from app.repositories.body_measurement_repository import BodyMeasurementRepository
from app.repositories.lifestyle_baseline_repository import LifestyleBaselineRepository
from app.repositories.nutrition_baseline_repository import NutritionBaselineRepository
from app.repositories.user_goal_repository import UserGoalRepository
from app.repositories.user_profile_repository import UserProfileRepository
from app.schemas.profile import (
    BiomarkerResponse,
    BodyMeasurementResponse,
    FullProfileCreate,
    FullProfileResponse,
    FullProfileUpdate,
    LifestyleBaselineResponse,
    NutritionBaselineResponse,
    OnboardingStatusResponse,
    UserGoalResponse,
    UserProfileResponse,
)

logger = get_logger(__name__)


def _profile_resp(p: UserProfile) -> UserProfileResponse:
    return UserProfileResponse.model_validate(p)


def _measurement_resp(m: BodyMeasurement | None) -> BodyMeasurementResponse | None:
    return BodyMeasurementResponse.model_validate(m) if m else None


def _biomarker_resp(b: Biomarker | None) -> BiomarkerResponse | None:
    return BiomarkerResponse.model_validate(b) if b else None


def _lifestyle_resp(l: LifestyleBaseline | None) -> LifestyleBaselineResponse | None:
    return LifestyleBaselineResponse.model_validate(l) if l else None


def _nutrition_resp(n: NutritionBaseline | None) -> NutritionBaselineResponse | None:
    return NutritionBaselineResponse.model_validate(n) if n else None


def _goals_resp(goals: list) -> list[UserGoalResponse] | None:
    if not goals:
        return None
    return [UserGoalResponse.model_validate(g) for g in goals]


async def create_profile(
    session: AsyncSession,
    user_id: uuid.UUID,
    data: FullProfileCreate,
) -> FullProfileResponse:
    profile_repo = UserProfileRepository(session)
    meas_repo = BodyMeasurementRepository(session)
    bio_repo = BiomarkerRepository(session)
    life_repo = LifestyleBaselineRepository(session)
    nutr_repo = NutritionBaselineRepository(session)
    goal_repo = UserGoalRepository(session)

    existing = await profile_repo.get_by_user_id(user_id)
    if existing:
        raise ConflictException("Profile already exists for this user")

    profile = UserProfile(user_id=user_id, **data.profile.model_dump())
    await profile_repo.create(profile)

    measurement = None
    if data.measurements:
        measurement = BodyMeasurement(user_id=user_id, **data.measurements.model_dump())
        await meas_repo.create(measurement)

    biomarker = None
    if data.biomarkers:
        biomarker = Biomarker(user_id=user_id, **data.biomarkers.model_dump())
        await bio_repo.create(biomarker)

    lifestyle = None
    if data.lifestyle:
        lifestyle = LifestyleBaseline(user_id=user_id, **data.lifestyle.model_dump())
        await life_repo.create(lifestyle)

    nutrition = None
    if data.nutrition:
        nutrition = NutritionBaseline(user_id=user_id, **data.nutrition.model_dump())
        await nutr_repo.create(nutrition)

    goals = []
    if data.goals:
        goal_records = [
            UserGoal(user_id=user_id, **g.model_dump()) for g in data.goals
        ]
        goals = await goal_repo.create_many(goal_records)

    logger.info("profile_created", user_id=str(user_id))

    return FullProfileResponse(
        profile=_profile_resp(profile),
        measurements=_measurement_resp(measurement),
        biomarkers=_biomarker_resp(biomarker),
        lifestyle=_lifestyle_resp(lifestyle),
        nutrition=_nutrition_resp(nutrition),
        goals=_goals_resp(goals),
    )


async def get_profile(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> FullProfileResponse:
    profile_repo = UserProfileRepository(session)
    meas_repo = BodyMeasurementRepository(session)
    bio_repo = BiomarkerRepository(session)
    life_repo = LifestyleBaselineRepository(session)
    nutr_repo = NutritionBaselineRepository(session)
    goal_repo = UserGoalRepository(session)

    profile = await profile_repo.get_by_user_id(user_id)
    if profile is None:
        raise NotFoundException("Profile not found")

    measurement = await meas_repo.get_by_user_id(user_id)
    biomarker = await bio_repo.get_by_user_id(user_id)
    lifestyle = await life_repo.get_by_user_id(user_id)
    nutrition = await nutr_repo.get_by_user_id(user_id)
    goals = await goal_repo.get_by_user_id(user_id)

    return FullProfileResponse(
        profile=_profile_resp(profile),
        measurements=_measurement_resp(measurement),
        biomarkers=_biomarker_resp(biomarker),
        lifestyle=_lifestyle_resp(lifestyle),
        nutrition=_nutrition_resp(nutrition),
        goals=_goals_resp(list(goals)),
    )


async def update_profile(
    session: AsyncSession,
    user_id: uuid.UUID,
    data: FullProfileUpdate,
) -> FullProfileResponse:
    profile_repo = UserProfileRepository(session)
    meas_repo = BodyMeasurementRepository(session)
    bio_repo = BiomarkerRepository(session)
    life_repo = LifestyleBaselineRepository(session)
    nutr_repo = NutritionBaselineRepository(session)
    goal_repo = UserGoalRepository(session)

    profile = await profile_repo.get_by_user_id(user_id)
    if profile is None:
        raise NotFoundException("Profile not found")

    if data.profile:
        updates = data.profile.model_dump(exclude_unset=True)
        for key, value in updates.items():
            setattr(profile, key, value)
        profile.updated_at = datetime.now(timezone.utc)
        await profile_repo.update(profile)

    measurement = await meas_repo.get_by_user_id(user_id)
    if data.measurements:
        updates = data.measurements.model_dump(exclude_unset=True)
        if measurement is None:
            measurement = BodyMeasurement(user_id=user_id, **updates)
            await meas_repo.create(measurement)
        else:
            for key, value in updates.items():
                setattr(measurement, key, value)
            measurement.updated_at = datetime.now(timezone.utc)
            await meas_repo.update(measurement)

    biomarker = await bio_repo.get_by_user_id(user_id)
    if data.biomarkers:
        updates = data.biomarkers.model_dump(exclude_unset=True)
        if biomarker is None:
            biomarker = Biomarker(user_id=user_id, **updates)
            await bio_repo.create(biomarker)
        else:
            for key, value in updates.items():
                setattr(biomarker, key, value)
            biomarker.updated_at = datetime.now(timezone.utc)
            await bio_repo.update(biomarker)

    lifestyle = await life_repo.get_by_user_id(user_id)
    if data.lifestyle:
        updates = data.lifestyle.model_dump(exclude_unset=True)
        if lifestyle is None:
            lifestyle = LifestyleBaseline(user_id=user_id, **updates)
            await life_repo.create(lifestyle)
        else:
            for key, value in updates.items():
                setattr(lifestyle, key, value)
            lifestyle.updated_at = datetime.now(timezone.utc)
            await life_repo.update(lifestyle)

    nutrition = await nutr_repo.get_by_user_id(user_id)
    if data.nutrition:
        updates = data.nutrition.model_dump(exclude_unset=True)
        if nutrition is None:
            nutrition = NutritionBaseline(user_id=user_id, **updates)
            await nutr_repo.create(nutrition)
        else:
            for key, value in updates.items():
                setattr(nutrition, key, value)
            nutrition.updated_at = datetime.now(timezone.utc)
            await nutr_repo.update(nutrition)

    if data.goals is not None:
        await goal_repo.delete_by_user_id(user_id)
        goal_records = [
            UserGoal(user_id=user_id, **g.model_dump()) for g in data.goals
        ]
        goals = await goal_repo.create_many(goal_records) if goal_records else []
    else:
        goals = list(await goal_repo.get_by_user_id(user_id))

    logger.info("profile_updated", user_id=str(user_id))

    return FullProfileResponse(
        profile=_profile_resp(profile),
        measurements=_measurement_resp(measurement),
        biomarkers=_biomarker_resp(biomarker),
        lifestyle=_lifestyle_resp(lifestyle),
        nutrition=_nutrition_resp(nutrition),
        goals=_goals_resp(goals),
    )


async def get_onboarding_status(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> OnboardingStatusResponse:
    """Check if user has completed onboarding (i.e., has a profile record)."""
    profile_repo = UserProfileRepository(session)
    meas_repo = BodyMeasurementRepository(session)
    bio_repo = BiomarkerRepository(session)
    life_repo = LifestyleBaselineRepository(session)
    nutr_repo = NutritionBaselineRepository(session)
    goal_repo = UserGoalRepository(session)

    completed = []

    profile = await profile_repo.get_by_user_id(user_id)
    if profile:
        completed.append("basic_profile")

    measurement = await meas_repo.get_by_user_id(user_id)
    if measurement:
        completed.append("body_measurements")

    biomarker = await bio_repo.get_by_user_id(user_id)
    if biomarker:
        completed.append("biomarkers")

    lifestyle = await life_repo.get_by_user_id(user_id)
    if lifestyle:
        completed.append("lifestyle")

    nutrition = await nutr_repo.get_by_user_id(user_id)
    if nutrition:
        completed.append("nutrition")

    goals = await goal_repo.get_by_user_id(user_id)
    if goals:
        completed.append("goals")

    # User is considered onboarded if they have at least the basic profile
    return OnboardingStatusResponse(
        onboarded=profile is not None,
        completed_sections=completed,
    )


async def process_health_report(
    session: AsyncSession,
    user_id: uuid.UUID,
    file,
) -> BiomarkerResponse:
    """
    Simulates parsing an uploaded health report (PDF/Image) using OCR/LLM
    and extracting biomarker data. In production, this would integrate
    with a medical document parsing pipeline.
    """
    import random
    
    # Mocking realistic biomarker values
    extracted_data = {
        "vitamin_d": round(random.uniform(15.0, 50.0), 1),
        "hba1c": round(random.uniform(4.8, 7.5), 1),
        "tsh": round(random.uniform(0.5, 6.0), 2),
        "b12": round(random.uniform(150, 600), 0),
        "hdl": round(random.uniform(35, 70), 0),
        "ldl": round(random.uniform(70, 160), 0),
        "triglycerides": round(random.uniform(80, 250), 0),
        "ferritin": round(random.uniform(20, 250), 0),
        "hemoglobin": round(random.uniform(10.5, 16.5), 1),
        "crp": round(random.uniform(0.1, 8.0), 2),
    }

    bio_repo = BiomarkerRepository(session)
    biomarker = await bio_repo.get_by_user_id(user_id)
    
    if biomarker is None:
        biomarker = Biomarker(user_id=user_id, **extracted_data)
        await bio_repo.create(biomarker)
    else:
        for key, value in extracted_data.items():
            setattr(biomarker, key, value)
        biomarker.updated_at = datetime.now(timezone.utc)
        await bio_repo.update(biomarker)

    logger.info("health_report_processed", user_id=str(user_id))
    return BiomarkerResponse.model_validate(biomarker)
