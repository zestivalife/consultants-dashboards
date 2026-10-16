from enum import StrEnum
from datetime import datetime
from typing import Any, Literal
from uuid import UUID
from pydantic import BaseModel, Field


class ConsultationStatus(StrEnum):
    SCHEDULED="SCHEDULED"; IN_PROGRESS="IN_PROGRESS"; COMPLETED="COMPLETED"; CANCELLED="CANCELLED"; NO_SHOW="NO_SHOW"


class WorkStatus(StrEnum):
    TODO="TODO"; IN_PROGRESS="IN_PROGRESS"; COMPLETED="COMPLETED"; OVERDUE="OVERDUE"; CANCELLED="CANCELLED"


class ResourceCreate(BaseModel):
    client_id: str
    type: str
    title: str = Field(min_length=1, max_length=240)
    status: str
    due_at: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class ResourceUpdate(BaseModel):
    version: int = Field(ge=1)
    status: str | None = None
    title: str | None = Field(default=None, min_length=1, max_length=240)
    due_at: str | None = None
    payload: dict[str, Any] | None = None


class Page(BaseModel):
    items: list[dict[str, Any]]
    next_cursor: UUID | None = None


class ConsultationTransition(BaseModel):
    version: int = Field(ge=1)
    action: Literal["RESCHEDULE", "START", "COMPLETE", "CANCEL", "MARK_NO_SHOW"]
    scheduled_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=5, le=480)
    outcome: str | None = Field(default=None, max_length=4000)
    next_followup_at: datetime | None = None


class GoalProgressCreate(BaseModel):
    recorded_at: datetime
    value: float
    unit: str = Field(min_length=1, max_length=32)
    note: str | None = Field(default=None, max_length=1000)


class MediaReferenceCreate(BaseModel):
    client_id: str
    captured_at: datetime
    media_type: Literal["MEAL_PHOTO", "PROGRESS_PHOTO", "WEIGHT_SCREENSHOT", "OTHER_CHECKIN_MEDIA"]
    document_reference: str = Field(min_length=1, max_length=500)
    meal: str | None = Field(default=None, max_length=120)
    note: str | None = Field(default=None, max_length=1000)


class OutboxDelivery(BaseModel):
    consumer_name: str = Field(min_length=1, max_length=120)
    event_id: UUID


class PracticeConfigurationUpdate(BaseModel):
    profession: Literal[
        "DIETITIAN", "NUTRITIONIST", "PSYCHOLOGIST", "COUNSELLOR",
        "PHYSIOTHERAPIST", "HEALTH_COACH", "DIABETES_EDUCATOR",
        "WELLNESS_CONSULTANT", "OTHER",
    ]
    capabilities: list[str] = Field(default_factory=list, max_length=64)
    profile: dict[str, Any] = Field(default_factory=dict)


class CommunicationTemplateCreate(BaseModel):
    code: str = Field(min_length=2, max_length=80, pattern=r"^[A-Z0-9_]+$")
    label: str = Field(min_length=1, max_length=120)
    body: str = Field(min_length=1, max_length=2000)


class WhatsAppOpenCreate(BaseModel):
    client_id: str
    template_code: str | None = Field(default=None, max_length=80)
    purpose: str = Field(min_length=1, max_length=120)
    phone: str = Field(min_length=8, max_length=24)
    message: str = Field(min_length=1, max_length=2000)
    shareable_type: str | None = Field(default=None, max_length=80)
    shareable_id: str | None = Field(default=None, max_length=160)


class OnboardingCompletedCreate(BaseModel):
    client_id: str
    client_name: str = Field(min_length=1, max_length=200)
    completed_at: datetime
