import uuid
from datetime import datetime

from pydantic import BaseModel


class ScoreMetadata(BaseModel):
    score_version: str
    algorithm_version: str
    computed_at: datetime
    model_config = {"from_attributes": True}


class HealthScoreResponse(BaseModel):
    bmi_score: float | None = None
    whr_score: float | None = None
    muscle_score: float | None = None
    stress_score: float | None = None
    lifestyle_score: float | None = None
    total_health_score: float | None = None
    score_version: str | None = None
    algorithm_version: str | None = None
    computed_at: datetime | None = None
    model_config = {"from_attributes": True}


class PhysicalEaseScoreResponse(BaseModel):
    score: float | None = None
    interpretation: str | None = None
    score_version: str | None = None
    algorithm_version: str | None = None
    computed_at: datetime | None = None
    model_config = {"from_attributes": True}


class ActivePerformanceScoreResponse(BaseModel):
    energy_balance: float | None = None
    body_support: float | None = None
    nourishment: float | None = None
    recovery: float | None = None
    active_performance_score: float | None = None
    score_version: str | None = None
    algorithm_version: str | None = None
    computed_at: datetime | None = None
    model_config = {"from_attributes": True}


class MedicalIndexScoreResponse(BaseModel):
    vitamin_d: float | None = None
    hba1c: float | None = None
    thyroid: float | None = None
    b12: float | None = None
    lipid_profile: float | None = None
    ferritin: float | None = None
    hemoglobin: float | None = None
    crp: float | None = None
    medical_index: float | None = None
    score_version: str | None = None
    algorithm_version: str | None = None
    computed_at: datetime | None = None
    model_config = {"from_attributes": True}


class ComputeResult(BaseModel):
    health: HealthScoreResponse
    physical_ease: PhysicalEaseScoreResponse
    active_performance: ActivePerformanceScoreResponse
    medical_index: MedicalIndexScoreResponse
    recomputed: bool = True


class LatestScoresResponse(BaseModel):
    health: HealthScoreResponse | None = None
    physical_ease: PhysicalEaseScoreResponse | None = None
    active_performance: ActivePerformanceScoreResponse | None = None
    medical_index: MedicalIndexScoreResponse | None = None


class TimelineEntry(BaseModel):
    created_at: datetime
    total_health_score: float | None = None
    active_performance_score: float | None = None
    medical_index: float | None = None
    physical_ease_score: float | None = None
    score_version: str | None = None
    algorithm_version: str | None = None


class TimelineResponse(BaseModel):
    entries: list[TimelineEntry]
