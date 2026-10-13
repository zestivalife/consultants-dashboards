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
