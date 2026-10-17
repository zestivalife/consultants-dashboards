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
        "WELLNESS_CONSULTANT", "BEHAVIOURAL_THERAPIST", "OCCUPATIONAL_THERAPIST",
        "MENTAL_WELLNESS_THERAPIST", "OTHER",
    ]
    capabilities: list[str] = Field(default_factory=list, max_length=64)
    profile: dict[str, Any] = Field(default_factory=dict)


class CommunicationTemplateCreate(BaseModel):
    code: str = Field(min_length=2, max_length=80, pattern=r"^[A-Z0-9_]+$")
    label: str = Field(min_length=1, max_length=120)
    body: str = Field(min_length=1, max_length=2000)


class WhatsAppOpenCreate(BaseModel):
    client_id: str
    intent: Literal[
        "GENERAL_MESSAGE", "SHARE_ONBOARDING_LINK", "SHARE_PUBLISHED_PLAN",
        "APPOINTMENT_REMINDER", "FOLLOW_UP_REMINDER", "ASSESSMENT_LINK",
        "PROGRESS_UPDATE", "CUSTOM_MESSAGE",
    ] = "CUSTOM_MESSAGE"
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


class ProfessionIntakeInvitationCreate(BaseModel):
    expires_in_hours: int = Field(default=168, ge=1, le=720)


class ProfessionTemplateQuestion(BaseModel):
    key: str = Field(min_length=1, max_length=100, pattern=r"^[a-z][a-z0-9_]*$")
    prompt: str = Field(min_length=1, max_length=1000)
    type: Literal["TEXT", "TEXTAREA", "NUMBER", "DATE", "BOOLEAN", "SINGLE_SELECT", "MULTI_SELECT"]
    required: bool = False
    options: list[str] = Field(default_factory=list, max_length=100)


class ProfessionTemplateSection(BaseModel):
    key: str = Field(min_length=1, max_length=80, pattern=r"^[a-z][a-z0-9_]*$")
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    questions: list[ProfessionTemplateQuestion] = Field(min_length=1, max_length=100)


class ProfessionTemplatePublish(BaseModel):
    profession_code: str = Field(min_length=2, max_length=80)
    title: str = Field(min_length=1, max_length=200)
    sections: list[ProfessionTemplateSection] = Field(min_length=1, max_length=30)


class ProfessionIntakeAnswerSave(BaseModel):
    answers: dict[str, Any] = Field(default_factory=dict)


class ProfessionIntakeSubmit(BaseModel):
    consent_accepted: Literal[True]
    consent_version: str = Field(min_length=1, max_length=80)


class ProfessionCustomQuestionCreate(ProfessionTemplateQuestion):
    pass


class ProfessionIntakeReviewCreate(BaseModel):
    event_type: Literal["REVIEW_STARTED", "APPROVED", "CHANGES_REQUESTED"]
    notes: str | None = Field(default=None, max_length=4000)

class AssessmentAssign(BaseModel):
    definition_id: UUID
    due_at: datetime | None = None

class AssessmentAnswerSave(BaseModel):
    answers: dict[str, Any] = Field(default_factory=dict)

class AssessmentComplete(AssessmentAnswerSave):
    review_notes: str | None = Field(default=None, max_length=4000)
