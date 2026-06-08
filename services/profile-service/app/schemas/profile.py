import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ── User Profile ──────────────────────────────────────

class UserProfileBase(BaseModel):
    age: int | None = None
    sex: str | None = Field(None, max_length=20)
    height: float | None = None
    weight: float | None = None
    body_fat_percent: float | None = None
    calculated_body_fat: float | None = None


class UserProfileCreate(UserProfileBase):
    pass


class UserProfileUpdate(UserProfileBase):
    pass


class UserProfileResponse(UserProfileBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


# ── Body Measurements ────────────────────────────────

class BodyMeasurementBase(BaseModel):
    arm_circumference: float | None = None
    thigh_circumference: float | None = None
    calf_circumference: float | None = None


class BodyMeasurementCreate(BodyMeasurementBase):
    pass


class BodyMeasurementUpdate(BodyMeasurementBase):
    pass


class BodyMeasurementResponse(BodyMeasurementBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


# ── Biomarkers ───────────────────────────────────────

class BiomarkerBase(BaseModel):
    vitamin_d: float | None = None
    hba1c: float | None = None
    tsh: float | None = None
    b12: float | None = None
    hdl: float | None = None
    ldl: float | None = None
    triglycerides: float | None = None
    ferritin: float | None = None
    hemoglobin: float | None = None
    crp: float | None = None


class BiomarkerCreate(BiomarkerBase):
    pass


class BiomarkerUpdate(BiomarkerBase):
    pass


class BiomarkerResponse(BiomarkerBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


# ── Lifestyle Baseline ───────────────────────────────

class LifestyleBaselineBase(BaseModel):
    activity_level: str | None = Field(None, max_length=50)
    exercise_frequency: int | None = None
    daily_steps: int | None = None
    sleep_duration: float | None = None
    sleep_consistency: int | None = Field(None, ge=1, le=10)
    stress_level: int | None = Field(None, ge=1, le=10)
    water_intake: float | None = None
    food_type: str | None = Field(None, max_length=50)


class LifestyleBaselineCreate(LifestyleBaselineBase):
    pass


class LifestyleBaselineUpdate(LifestyleBaselineBase):
    pass


class LifestyleBaselineResponse(LifestyleBaselineBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


# ── Nutrition Baseline ───────────────────────────────

class NutritionBaselineBase(BaseModel):
    meal_frequency: int | None = None
    protein_intake: str | None = Field(None, max_length=50)
    water_intake: float | None = None
    food_source: str | None = Field(None, max_length=50)
    target_protein: int | None = None
    target_fat: int | None = None
    target_carbs: int | None = None
    target_calories: int | None = None


class NutritionBaselineCreate(NutritionBaselineBase):
    pass


class NutritionBaselineUpdate(NutritionBaselineBase):
    pass


class NutritionBaselineResponse(NutritionBaselineBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


# ── User Goals ───────────────────────────────────────

class UserGoalBase(BaseModel):
    goal_type: str = Field(..., max_length=50)
    is_primary: bool = False


class UserGoalCreate(UserGoalBase):
    pass


class UserGoalResponse(UserGoalBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


# ── Composite (Onboarding) ──────────────────────────

class FullProfileCreate(BaseModel):
    profile: UserProfileCreate
    measurements: BodyMeasurementCreate | None = None
    biomarkers: BiomarkerCreate | None = None
    lifestyle: LifestyleBaselineCreate | None = None
    nutrition: NutritionBaselineCreate | None = None
    goals: list[UserGoalCreate] | None = None


class FullProfileUpdate(BaseModel):
    profile: UserProfileUpdate | None = None
    measurements: BodyMeasurementUpdate | None = None
    biomarkers: BiomarkerUpdate | None = None
    lifestyle: LifestyleBaselineUpdate | None = None
    nutrition: NutritionBaselineUpdate | None = None
    goals: list[UserGoalCreate] | None = None


class FullProfileResponse(BaseModel):
    profile: UserProfileResponse
    measurements: BodyMeasurementResponse | None = None
    biomarkers: BiomarkerResponse | None = None
    lifestyle: LifestyleBaselineResponse | None = None
    nutrition: NutritionBaselineResponse | None = None
    goals: list[UserGoalResponse] | None = None


# ── Onboarding Status ────────────────────────────────

class OnboardingStatusResponse(BaseModel):
    onboarded: bool
    completed_sections: list[str] = []
