import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ── Meal Template ──────────────────────────────────────
class MealTemplateCreate(BaseModel):
    meal_type: str = Field(..., pattern="^(breakfast|lunch|dinner|snack)$")
    meal_name: str = Field(..., max_length=200)
    calories: float | None = None
    protein: float | None = None
    carbs: float | None = None
    fats: float | None = None


class MealTemplateResponse(BaseModel):
    id: uuid.UUID
    meal_type: str
    meal_name: str
    calories: float | None = None
    protein: float | None = None
    carbs: float | None = None
    fats: float | None = None
    model_config = {"from_attributes": True}


# ── Diet Plan ──────────────────────────────────────────
class DietPlanCreate(BaseModel):
    name: str = Field(..., max_length=200)
    description: str | None = None
    calorie_target: float | None = None
    protein_target: float | None = None
    fat_target: float | None = None
    carb_target: float | None = None
    meals: list[MealTemplateCreate] = []


class DietPlanResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    calorie_target: float | None = None
    protein_target: float | None = None
    fat_target: float | None = None
    carb_target: float | None = None
    created_at: datetime
    meals: list[MealTemplateResponse] = []
    model_config = {"from_attributes": True}


class DietPlanSummary(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    calorie_target: float | None = None
    protein_target: float | None = None
    fat_target: float | None = None
    carb_target: float | None = None
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Assignment ─────────────────────────────────────────
class AssignDietPlanRequest(BaseModel):
    user_id: uuid.UUID
    diet_plan_id: uuid.UUID


class UserDietPlanResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    diet_plan_id: uuid.UUID
    assigned_by: uuid.UUID | None = None
    assigned_at: datetime
    diet_plan: DietPlanResponse | None = None
    model_config = {"from_attributes": True}


# ── Health Report ──────────────────────────────────────
class HealthReportResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    file_url: str
    uploaded_at: datetime
    model_config = {"from_attributes": True}
