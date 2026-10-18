from __future__ import annotations
try:
    from enum import StrEnum
except ImportError:  # Python 3.10 test/runtime compatibility; native in Python 3.11+
    from enum import Enum
    class StrEnum(str, Enum):
        pass
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
    allow_resource_access: bool = True
    allow_homework_checkin: bool = True


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


class BillableServiceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=240)
    description: str | None = Field(default=None, max_length=4000)
    category: str | None = Field(default=None, max_length=120)
    default_price_minor: int = Field(ge=0)
    currency: str = Field(default="INR", pattern=r"^[A-Z]{3}$")
    default_tax_type: Literal["NO_TAX","CGST_SGST","IGST","CUSTOM_TAX"] = "NO_TAX"
    default_tax_rate_bps: int = Field(default=0, ge=0, le=10000)
    active: bool = True


class BillableServiceUpdate(BillableServiceCreate):
    pass


class InvoiceLineInput(BaseModel):
    service_id: UUID | None = None
    description: str = Field(min_length=1, max_length=500)
    quantity: int = Field(default=1, ge=1, le=10000)
    unit_price_minor: int = Field(ge=0)
    discount_type: Literal["NONE","FIXED","PERCENTAGE"] = "NONE"
    discount_value: int = Field(default=0, ge=0)
    tax_type: Literal["NO_TAX","CGST_SGST","IGST","CUSTOM_TAX"] = "NO_TAX"
    tax_rate_bps: int = Field(default=0, ge=0, le=10000)


class InvoiceCreate(BaseModel):
    client_id: str = Field(min_length=1, max_length=120)
    currency: str = Field(default="INR", pattern=r"^[A-Z]{3}$")
    issue_date: date | None = None
    due_date: date | None = None
    client_package_id: UUID | None = None
    appointment_id: UUID | None = None
    notes: str | None = Field(default=None, max_length=4000)
    terms: str | None = Field(default=None, max_length=4000)
    items: list[InvoiceLineInput] = Field(min_length=1, max_length=100)


class InvoiceUpdate(InvoiceCreate):
    pass


class PaymentCreate(BaseModel):
    amount_minor: int = Field(gt=0)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    method: Literal["CASH","BANK_TRANSFER","UPI","CARD_EXTERNAL","PAYMENT_GATEWAY","CHEQUE","OTHER"]
    provenance: Literal["MANUAL_RECORDED","PROVIDER_CONFIRMED"] = "MANUAL_RECORDED"
    reference_number: str | None = Field(default=None, max_length=160)
    provider_name: str | None = Field(default=None, max_length=120)
    provider_reference: str | None = Field(default=None, max_length=160)
    payment_date: date
    notes: str | None = Field(default=None, max_length=4000)


class ProfessionalResourceCreate(BaseModel):
    scope: Literal["PRACTICE","PRACTITIONER"] = "PRACTICE"
    profession_code: str | None = Field(default=None, max_length=80)
    title: str = Field(min_length=1, max_length=240)
    description: str | None = Field(default=None, max_length=4000)
    resource_type: Literal["PDF","DOCUMENT","VIDEO_LINK","ARTICLE_LINK","WORKSHEET","EXERCISE","INSTRUCTION","CHECKLIST","AUDIO_LINK","FORM_LINK"]
    content_reference: str = Field(min_length=1, max_length=4000)
    media_type: str | None = Field(default=None, max_length=120)
    duration_minutes: int | None = Field(default=None, gt=0, le=1440)
    instructions: str | None = Field(default=None, max_length=4000)
    tags: list[str] = Field(default_factory=list, max_length=50)
    capability_required: str | None = Field(default=None, max_length=80)


class ProfessionalResourceUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    description: str | None = Field(default=None, max_length=4000)
    content_reference: str = Field(min_length=1, max_length=4000)
    media_type: str | None = Field(default=None, max_length=120)
    duration_minutes: int | None = Field(default=None, gt=0, le=1440)
    instructions: str | None = Field(default=None, max_length=4000)
    tags: list[str] = Field(default_factory=list, max_length=50)
    capability_required: str | None = Field(default=None, max_length=80)


class ResourceAssignmentCreate(BaseModel):
    resource_id: UUID
    context_type: Literal["CLIENT","SESSION","PLAN","TASK","HOMEWORK","FOLLOWUP"] = "CLIENT"
    context_id: str | None = Field(default=None, max_length=120)
    due_at: datetime | None = None
    instructions: str | None = Field(default=None, max_length=4000)
    required: bool = False


class HomeworkCreate(BaseModel):
    profession_code: str | None = Field(default=None, max_length=80)
    title: str = Field(min_length=1, max_length=240)
    description: str | None = Field(default=None, max_length=4000)
    homework_type: Literal["CHECKLIST","REFLECTION","JOURNAL","EXERCISE","HABIT","OBSERVATION_LOG","EDUCATION_TASK","PRACTICE_ACTIVITY","CUSTOM"]
    instructions: str | None = Field(default=None, max_length=4000)
    start_date: date
    due_date: date | None = None
    cadence: Literal["ONE_TIME","DAILY","WEEKLY","CUSTOM_INTERVAL"] = "ONE_TIME"
    every_n_days: int | None = Field(default=None, gt=0, le=365)
    target_count: int | None = Field(default=None, gt=0, le=10000)
    resource_assignment_id: UUID | None = None
    goal_id: str | None = Field(default=None, max_length=120)
    plan_id: UUID | None = None
    session_id: str | None = Field(default=None, max_length=120)


class HomeworkStatusUpdate(BaseModel):
    status: Literal["IN_PROGRESS","COMPLETED","MISSED","CANCELLED"]


class HomeworkCheckinCreate(BaseModel):
    done: bool | None = None
    completion_count: int | None = Field(default=None, ge=0, le=10000)
    numeric_adherence: float | None = Field(default=None, ge=0, le=100)
    reflection_text: str | None = Field(default=None, max_length=10000)
    note: str | None = Field(default=None, max_length=4000)
    difficulty_rating: int | None = Field(default=None, ge=1, le=5)


class AutomationConditionInput(BaseModel):
    field_key: Literal["CLIENT.status","APPOINTMENT.status","PACKAGE.sessions_remaining","INVOICE.balance_due","HOMEWORK.status","GOAL.status","profession_code","client_id"]
    operator: Literal["EQUALS","NOT_EQUALS","GREATER_THAN","GREATER_OR_EQUAL","LESS_THAN","LESS_OR_EQUAL","IN","NOT_IN","EXISTS","NOT_EXISTS"]
    expected_value: Any = None


class AutomationActionInput(BaseModel):
    action_type: Literal["CREATE_TASK","CREATE_FOLLOWUP","ASSIGN_ASSESSMENT","PREPARE_MESSAGE","CREATE_PLAN_REVIEW","CREATE_RENEWAL_TASK","CREATE_INVOICE_REMINDER","CREATE_HOMEWORK_REVIEW","ADD_WAITLIST_ACTION","CREATE_APPOINTMENT_REMINDER","CREATE_RESOURCE_ASSIGNMENT","CREATE_CLIENT_CHECKIN"]
    configuration: dict[str, Any] = Field(default_factory=dict)
    confirmation_required: bool = False


class AutomationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=240)
    description: str | None = Field(default=None, max_length=4000)
    profession_code: str | None = Field(default=None, max_length=80)
    capability_required: str | None = Field(default=None, max_length=80)
    trigger_type: Literal["CLIENT_CREATED","ONBOARDING_COMPLETED","ASSESSMENT_COMPLETED","SESSION_COMPLETED","APPOINTMENT_CREATED","APPOINTMENT_RESCHEDULED","APPOINTMENT_CANCELLED","NO_SHOW","TASK_OVERDUE","HOMEWORK_COMPLETED","HOMEWORK_OVERDUE","GOAL_DUE","PLAN_PUBLISHED","PLAN_REVIEW_DUE","PACKAGE_ENDING_SOON","SESSIONS_LOW","RENEWAL_DUE","INVOICE_ISSUED","INVOICE_OVERDUE","PAYMENT_RECORDED","CLIENT_INACTIVE","FOLLOWUP_COMPLETED"]
    requires_confirmation: bool = False
    max_retries: int = Field(default=3, ge=0, le=10)
    cooldown_minutes: int | None = Field(default=None, ge=1, le=525600)
    active_from: datetime | None = None
    active_until: datetime | None = None
    conditions: list[AutomationConditionInput] = Field(default_factory=list, max_length=20)
    actions: list[AutomationActionInput] = Field(min_length=1, max_length=20)


class AutomationStateUpdate(BaseModel):
    enabled: bool


class AutomationDryRun(BaseModel):
    event_type: str = Field(min_length=1, max_length=80)
    sample_payload: dict[str, Any] = Field(default_factory=dict)


class AutomationActionDecision(BaseModel):
    decision: Literal["APPROVE","DISMISS"]
    configuration: dict[str, Any] | None = None


class TeamInvitationCreate(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    name: str = Field(min_length=1, max_length=240)
    role: Literal["PRACTICE_ADMIN", "PRACTITIONER", "ASSISTANT", "RECEPTIONIST"]
    profession_code: str | None = Field(default=None, max_length=80)
    specialisation: str | None = Field(default=None, max_length=160)
    location_code: str | None = Field(default=None, max_length=120)
    permission_grants: list[str] = Field(default_factory=list, max_length=64)
    permission_restrictions: list[str] = Field(default_factory=list, max_length=64)
    expires_in_hours: int = Field(default=168, ge=1, le=720)


class TeamInvitationAccept(BaseModel):
    token: str = Field(min_length=24, max_length=500)


class TeamMemberUpdate(BaseModel):
    role: Literal["PRACTICE_ADMIN", "PRACTITIONER", "ASSISTANT", "RECEPTIONIST"]
    profession_code: str | None = Field(default=None, max_length=80)
    specialisation: str | None = Field(default=None, max_length=160)
    location_code: str | None = Field(default=None, max_length=120)
    permission_grants: list[str] = Field(default_factory=list, max_length=64)
    permission_restrictions: list[str] = Field(default_factory=list, max_length=64)
    practice_wide_client_access: bool = False


class ClientTeamAssignmentCreate(BaseModel):
    user_id: str = Field(min_length=1, max_length=120)
    assignment_role: Literal["PRIMARY_PRACTITIONER", "SECONDARY_PRACTITIONER", "CARE_TEAM_MEMBER"]
    reason: str | None = Field(default=None, max_length=500)


class ClientTeamAssignmentUpdate(BaseModel):
    assignment_role: Literal["PRIMARY_PRACTITIONER", "SECONDARY_PRACTITIONER", "CARE_TEAM_MEMBER"]
    reason: str | None = Field(default=None, max_length=500)


class ReferralCreate(BaseModel):
    client_id: str = Field(min_length=1,max_length=120)
    receiving_practitioner_id: str | None = Field(default=None,max_length=120)
    receiving_tenant_id: str | None = Field(default=None,max_length=80)
    receiving_profession_code: str = Field(min_length=1,max_length=80)
    destination_name: str | None = Field(default=None,max_length=240)
    destination_contact: str | None = Field(default=None,max_length=320)
    reason: str = Field(min_length=1,max_length=4000)
    data_scopes: list[str] = Field(default_factory=list,max_length=16)
    consent_version: str = Field(default="P19_V1",max_length=40)


class ReferralAction(BaseModel):
    action: Literal["REQUEST_CONSENT","SEND","ACCEPT","DECLINE","COMPLETE","CANCEL","REQUEST_CLARIFICATION"]
    message: str | None = Field(default=None,max_length=4000)


class ReferralConsentDecision(BaseModel):
    decision: Literal["GRANT","DECLINE"]
    allowed_data_scopes: list[str] = Field(default_factory=list,max_length=16)
    consent_version: str = Field(default="P19_V1",max_length=40)


class ProgressReportCreate(BaseModel):
    client_id: str = Field(min_length=1,max_length=120)
    profession_code: str = Field(min_length=1,max_length=80)
    report_type: Literal["CLIENT_PROGRESS_REPORT","PROGRAMME_COMPLETION_REPORT","ASSESSMENT_PROGRESS_REPORT","REHAB_PROGRESS_REPORT","COACHING_PROGRESS_REPORT","WELLNESS_PROGRESS_REPORT","THERAPY_PROGRESS_REPORT","BEHAVIOUR_PROGRESS_REPORT","DIABETES_EDUCATION_PROGRESS_REPORT","OT_PROGRESS_REPORT"]
    title: str = Field(min_length=1,max_length=240)
    period_start: date
    period_end: date
    included_sections: list[str] = Field(min_length=1,max_length=30)
    consultant_summary: str | None = Field(default=None,max_length=10000)


class ProgressReportUpdate(BaseModel):
    included_sections: list[str] = Field(min_length=1,max_length=30)
    consultant_summary: str | None = Field(default=None,max_length=10000)

class FormField(BaseModel):
    key: str = Field(min_length=1,max_length=120)
    label: str = Field(min_length=1,max_length=500)
    field_type: Literal["SHORT_TEXT","LONG_TEXT","NUMBER","DATE","TIME","YES_NO","SINGLE_SELECT","MULTI_SELECT","CHECKBOX","RATING_SCALE","NUMERIC_SCALE","EMAIL","PHONE","FILE_UPLOAD","SECTION_INFO","CONSENT_CHECKBOX","BODY_REGION","REPEAT_GROUP"]
    required: bool = False
    config: dict[str,Any] = Field(default_factory=dict)
    condition: dict[str,Any] | None = None

class FormSection(BaseModel):
    key: str = Field(min_length=1,max_length=120)
    title: str = Field(min_length=1,max_length=240)
    description: str | None = Field(default=None,max_length=2000)
    fields: list[FormField] = Field(default_factory=list,max_length=100)

class FormCreate(BaseModel):
    title: str = Field(min_length=1,max_length=240)
    form_type: Literal["INTAKE","FOLLOW_UP","CHECK_IN","ASSESSMENT","FEEDBACK","CONSENT_PREPARATION","PROGRAMME_QUESTIONNAIRE","CUSTOM"]
    sections: list[FormSection] = Field(min_length=1,max_length=30)
    settings: dict[str,Any] = Field(default_factory=dict)

class FormAssign(BaseModel):
    client_id: str = Field(min_length=1,max_length=120)
    linked_type: str | None = Field(default=None,max_length=40)
    linked_id: str | None = Field(default=None,max_length=120)
    due_at: datetime | None = None
    expires_at: datetime | None = None

class FormResponseSave(BaseModel):
    answers: dict[str,Any] = Field(default_factory=dict)
    submit: bool = False

class ConsentTemplateCreate(BaseModel):
    title: str = Field(min_length=1,max_length=240)
    consent_type: Literal["GENERAL_SERVICE","TELECONSULTATION","DATA_PRIVACY","DOCUMENT_SHARING","REFERRAL","CARE_THERAPY","PROGRAMME","GUARDIAN_DEPENDENT"]
    body: str = Field(min_length=1,max_length=50000)
    scope: list[str] = Field(default_factory=list,max_length=50)
    required_signatories: list[str] = Field(default_factory=lambda:["CLIENT"],max_length=10)
    effective_date: date
    expires_after_days: int | None = Field(default=None,ge=1,le=3650)
    profession_code: str | None = Field(default=None,max_length=80)

class ConsentAssign(BaseModel):
    client_id: str = Field(min_length=1,max_length=120)

class ConsentDecision(BaseModel):
    decision: Literal["ACCEPT","DECLINE"]
    signatory_name: str = Field(min_length=1,max_length=240)
    signatory_type: str = Field(default="CLIENT",max_length=40)
    signature_method: Literal["TYPED","DRAWN","CHECKBOX"]
    signature_evidence: dict[str,Any] = Field(default_factory=dict)

class DocumentCreate(BaseModel):
    client_id: str | None = Field(default=None,max_length=120)
    title: str = Field(min_length=1,max_length=240)
    category: Literal["CONSENT","REFERRAL","PRESCRIPTION_COPY","LAB_REPORT","PROGRESS_REPORT","ASSESSMENT_ATTACHMENT","SESSION_ATTACHMENT","WORKSHEET","EXERCISE_DOCUMENT","CLIENT_UPLOADED","INVOICE","RECEIPT","IDENTITY_DOCUMENT","PROFESSIONAL_DOCUMENT","OTHER"]
    visibility: Literal["CLIENT_VISIBLE","CARE_TEAM_SHARED","PRACTITIONER_PRIVATE","PRACTICE_ADMINISTRATIVE"]
    filename: str = Field(min_length=1,max_length=500)
    content_type: str = Field(min_length=1,max_length=160)
    size_bytes: int = Field(gt=0,le=52428800)
    checksum_sha256: str | None = Field(default=None,min_length=64,max_length=64)
    tags: list[str] = Field(default_factory=list,max_length=30)
    links: list[dict[str,str]] = Field(default_factory=list,max_length=20)
class DocumentUpdate(BaseModel):
    title: str = Field(min_length=1,max_length=240)
    category: str = Field(min_length=1,max_length=60)
    visibility: Literal["CLIENT_VISIBLE","CARE_TEAM_SHARED","PRACTITIONER_PRIVATE","PRACTICE_ADMINISTRATIVE"]
    tags: list[str] = Field(default_factory=list,max_length=30)
class DocumentFinalise(BaseModel):
    version_id: UUID
class DocumentVersionCreate(BaseModel):
    filename: str = Field(min_length=1,max_length=500)
    content_type: str = Field(min_length=1,max_length=160)
    size_bytes: int = Field(gt=0,le=52428800)
    checksum_sha256: str | None = Field(default=None,min_length=64,max_length=64)
