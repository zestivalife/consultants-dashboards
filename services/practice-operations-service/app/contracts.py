from enum import StrEnum
from datetime import date, datetime
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

class ProfessionPlanItem(BaseModel):
    key: str = Field(min_length=1, max_length=100, pattern=r"^[a-z][a-z0-9_]*$")
    label: str = Field(min_length=1, max_length=240)
    content: dict[str, Any] = Field(default_factory=dict)

class ProfessionPlanSection(BaseModel):
    key: str = Field(min_length=1, max_length=100, pattern=r"^[a-z][a-z0-9_]*$")
    title: str = Field(min_length=1, max_length=240)
    content: dict[str, Any] = Field(default_factory=dict)
    items: list[ProfessionPlanItem] = Field(default_factory=list, max_length=100)

class ProfessionPlanCreate(BaseModel):
    client_id: str
    plan_type: Literal["THERAPY_PLAN","REHAB_PLAN","EXERCISE_PLAN","HABIT_PLAN","WELLNESS_PLAN","BEHAVIOUR_INTERVENTION_PLAN","OT_PLAN","DIABETES_EDUCATION_PLAN","SUPPORT_PLAN"]
    title: str = Field(min_length=1, max_length=240)
    sections: list[ProfessionPlanSection] = Field(default_factory=list, max_length=40)

class ProfessionPlanSave(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    expected_version: int = Field(ge=1)
    sections: list[ProfessionPlanSection] = Field(default_factory=list, max_length=40)

class SessionNoteSection(BaseModel):
    key: str = Field(min_length=1, max_length=100, pattern=r"^[a-z][a-z0-9_]*$")
    title: str = Field(min_length=1, max_length=240)
    content: dict[str, Any] = Field(default_factory=dict)
    visibility: Literal["PRACTITIONER","CLIENT_INSTRUCTION"] = "PRACTITIONER"

class SessionNoteCreate(BaseModel):
    client_id: str
    consultation_id: str | None = None
    note_type: str = Field(min_length=1, max_length=60)
    title: str = Field(min_length=1, max_length=240)
    sections: list[SessionNoteSection] = Field(default_factory=list, max_length=40)

class SessionNoteSave(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    expected_version: int = Field(ge=1)
    sections: list[SessionNoteSection] = Field(default_factory=list, max_length=40)

class SessionNoteAmendment(BaseModel):
    reason: str = Field(min_length=3, max_length=2000)
    title: str = Field(min_length=1, max_length=240)
    sections: list[SessionNoteSection] = Field(default_factory=list, max_length=40)

class PrivateNoteCreate(BaseModel):
    content: str = Field(min_length=1, max_length=20000)

class ProgressMetricCreate(BaseModel):
    code: str = Field(min_length=1, max_length=100, pattern=r"^[a-z][a-z0-9_]*$")
    label: str = Field(min_length=1, max_length=240)
    value_type: Literal["NUMBER","TEXT","SCALE"]
    unit: str | None = Field(default=None, max_length=60)
    direction: Literal["INCREASE","DECREASE","MAINTAIN"] | None = None
    source_type: Literal["MANUAL","ASSESSMENT","BIOMARKER_REFERENCE"] = "MANUAL"

class ProgressObservationCreate(BaseModel):
    metric_definition_id: UUID
    numeric_value: float | None = None
    text_value: str | None = Field(default=None, max_length=4000)
    source_type: Literal["MANUAL","ASSESSMENT","BIOMARKER_REFERENCE"] = "MANUAL"
    source_id: str | None = Field(default=None, max_length=160)
    observed_at: datetime

class ProgressTargetCreate(BaseModel):
    metric_definition_id: UUID
    numeric_target: float | None = None
    text_target: str | None = Field(default=None, max_length=2000)
    target_date: date | None = None

class ProgressMilestoneCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    description: str | None = Field(default=None, max_length=4000)
    target_date: date | None = None

class TemplateItemInput(BaseModel):
    key: str = Field(min_length=1,max_length=100,pattern=r"^[a-z][a-z0-9_]*$")
    label: str = Field(min_length=1,max_length=240)
    item_type: str = Field(min_length=1,max_length=40)
    config: dict[str,Any] = Field(default_factory=dict)

class TemplateSectionInput(BaseModel):
    key: str = Field(min_length=1,max_length=100,pattern=r"^[a-z][a-z0-9_]*$")
    title: str = Field(min_length=1,max_length=240)
    description: str | None = Field(default=None,max_length=2000)
    items: list[TemplateItemInput] = Field(default_factory=list,max_length=100)

class TemplateCreate(BaseModel):
    template_type: Literal["INTAKE","ASSESSMENT","SESSION_NOTE","PLAN","FOLLOWUP","TASK","MESSAGE","PROGRESS_REPORT"]
    scope: Literal["PRACTICE","PRACTITIONER"]
    title: str = Field(min_length=1,max_length=240)
    description: str | None = Field(default=None,max_length=4000)
    sections: list[TemplateSectionInput] = Field(default_factory=list,max_length=40)

class TemplateUpdate(BaseModel):
    expected_version: int = Field(ge=1)
    title: str = Field(min_length=1,max_length=240)
    description: str | None = Field(default=None,max_length=4000)
    sections: list[TemplateSectionInput] = Field(default_factory=list,max_length=40)

class SessionSuggestionGenerate(BaseModel):
    session_note_id: UUID

class SessionSuggestionDecision(BaseModel):
    decision: Literal["ACCEPT","EDIT_AND_ACCEPT","DISMISS"]
    proposed_payload: dict[str,Any] | None = None

class EngagementProjectionRequest(BaseModel):
    client_ids: list[str] = Field(min_length=1,max_length=100)


class ClientPortalInvitationCreate(BaseModel):
    expires_in_hours: int = Field(default=168, ge=1, le=2160)
    allow_task_completion: bool = True
    allow_document_upload: bool = True


class ClientPortalDocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    document_reference: str = Field(min_length=1, max_length=500)
    media_type: Literal["PDF", "DOCUMENT", "IMAGE", "OTHER"]


class ServicePackageCreate(BaseModel):
    name: str = Field(min_length=1, max_length=240)
    profession_code: str | None = Field(default=None, max_length=80)
    capability_code: str | None = Field(default=None, max_length=80)
    description: str | None = Field(default=None, max_length=4000)
    session_allowance: int = Field(ge=1, le=10000)
    duration_days: int = Field(ge=1, le=3650)
    price_minor: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    active: bool = True

    def snapshot(self):
        return self.model_dump(mode="json")


class ServicePackageUpdate(ServicePackageCreate):
    expected_version: int = Field(ge=1)


class ClientPackageAssign(BaseModel):
    client_id: str = Field(min_length=1, max_length=120)
    package_id: UUID
    start_date: date
    end_date: date
    status: Literal["DRAFT","ACTIVE","PAUSED","COMPLETED","EXPIRED","CANCELLED"] = "ACTIVE"
    sessions_total: int | None = Field(default=None, ge=1, le=10000)
    renewal_date: date | None = None
    notes: str | None = Field(default=None, max_length=4000)


class ClientPackageStatusUpdate(BaseModel):
    status: Literal["DRAFT","ACTIVE","PAUSED","COMPLETED","EXPIRED","CANCELLED"]
    renewal_date: date | None = None
    notes: str | None = Field(default=None, max_length=4000)


class PackageSessionUse(BaseModel):
    consultation_id: str | None = Field(default=None, max_length=120)
    occurred_at: datetime
    notes: str | None = Field(default=None, max_length=1000)


class AppointmentTypeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=1000)
    duration_minutes: int = Field(ge=5, le=480)
    buffer_before_minutes: int = Field(default=0, ge=0, le=240)
    buffer_after_minutes: int = Field(default=0, ge=0, le=240)
    location_type: Literal["ONLINE","IN_PERSON","PHONE","OTHER"]
    location_details: str | None = Field(default=None, max_length=500)


class AvailabilityRuleCreate(BaseModel):
    weekday: int = Field(ge=0, le=6)
    start_time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    end_time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    timezone: str = Field(min_length=1, max_length=80)
    effective_from: date | None = None
    effective_until: date | None = None


class BookingLinkCreate(BaseModel):
    appointment_type_id: UUID
    client_id: str | None = Field(default=None, max_length=120)
    label: str | None = Field(default=None, max_length=160)
    expires_at: datetime | None = None


class AppointmentCreate(BaseModel):
    client_id: str = Field(min_length=1, max_length=120)
    appointment_type_id: UUID
    starts_at: datetime


class AppointmentStatusUpdate(BaseModel):
    status: Literal["CONFIRMED","COMPLETED","CANCELLED","NO_SHOW"]
    cancellation_reason: str | None = Field(default=None, max_length=500)


class WaitlistCreate(BaseModel):
    client_id: str = Field(min_length=1, max_length=120)
    appointment_type_id: UUID
    preferred_from: datetime | None = None
    preferred_until: datetime | None = None
    notes: str | None = Field(default=None, max_length=1000)
