from contextlib import asynccontextmanager
from datetime import date, datetime, timezone, timedelta
from uuid import UUID, uuid4
import json
import base64
import hashlib
import re
import secrets
import structlog
import httpx
import phonenumbers
from urllib.parse import urlparse
from cryptography.fernet import Fernet
from fastapi import Depends, FastAPI, Header, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from app.contracts import (ConsultationTransition, GoalProgressCreate,
                           MediaReferenceCreate, OutboxDelivery, ResourceCreate,
                           ResourceUpdate, PracticeConfigurationUpdate,
                           CommunicationTemplateCreate, WhatsAppOpenCreate,
                           OnboardingCompletedCreate, ProfessionIntakeInvitationCreate,
                           ProfessionIntakeAnswerSave, ProfessionIntakeSubmit,
                           ProfessionTemplatePublish, ProfessionCustomQuestionCreate,
                           ProfessionIntakeReviewCreate, AssessmentAssign,
                           AssessmentAnswerSave, AssessmentComplete,
                           ProfessionPlanCreate, ProfessionPlanSave,
                           DietPlanCreate, DietPlanSave, DietPlanReviewAction)
from app.contracts import SessionNoteCreate, SessionNoteSave, SessionNoteAmendment, PrivateNoteCreate
from app.contracts import ProgressMetricCreate, ProgressObservationCreate, ProgressTargetCreate, ProgressMilestoneCreate
from app.contracts import TemplateCreate, TemplateUpdate, SessionSuggestionGenerate, SessionSuggestionDecision, EngagementProjectionRequest, PostSessionStart, PostSessionActionComplete, FeedbackRequestCreate, FeedbackSubmit, FeedbackAction, TeleconsultConfigure, TeleconsultTransition, SecureConversationCreate, SecureMessageCreate, CalendarConnectionPrepare, CalendarBusyBlockImport, CalendarExternalChange, MarketplaceCommissionRuleCreate, MarketplacePayoutUpdate, RefundCreate, RefundTransition, SupportTicketCreate, SupportTicketUpdate
from app.contracts import ClientPortalInvitationCreate, ClientPortalDocumentCreate, PreConsultationInvite
from app.contracts import (ServicePackageCreate, ServicePackageUpdate,
                           ClientPackageAssign, ClientPackageStatusUpdate,
                           PackageSessionUse)
from app.contracts import (AppointmentTypeCreate, AvailabilityRuleCreate, BookingLinkCreate,
                           AppointmentCreate, AppointmentStatusUpdate, WaitlistCreate)
from app.contracts import (BillableServiceCreate, BillableServiceUpdate, InvoiceCreate,
                           InvoiceUpdate, PaymentCreate)
from app.contracts import (ProfessionalResourceCreate, ProfessionalResourceUpdate,
                           ResourceAssignmentCreate, HomeworkCreate,
                           HomeworkStatusUpdate, HomeworkCheckinCreate)
from app.contracts import (AutomationCreate, AutomationStateUpdate,
                           AutomationDryRun, AutomationActionDecision)
from app.contracts import (TeamInvitationCreate, TeamInvitationAccept, TeamMemberUpdate,
                           ClientTeamAssignmentCreate, ClientTeamAssignmentUpdate)
from app.contracts import ReferralCreate, ReferralAction, ReferralConsentDecision
from app.contracts import ProgressReportCreate, ProgressReportUpdate
from app.contracts import FormCreate, FormAssign, FormResponseSave
from app.contracts import ConsentTemplateCreate, ConsentAssign, ConsentDecision
from app.contracts import DocumentCreate, DocumentUpdate, DocumentFinalise, DocumentVersionCreate
from app.contracts import LeadCreate, LeadStageUpdate, LeadFollowUpCreate, LeadConvert
from app.contracts import CommunicationPreparationCreate, CommunicationReminderCreate
from app.contracts import PracticeLocationCreate, LocationResourceAssign
from app.contracts import PaymentOrderCreate, PaymentVerification
from app.contracts import AiDraftRequest
from app.contracts import (ClientExportRequest, ExternalClientProfileEnrichmentUpdate,
                           ExternalMeasurementCorrection, ExternalMeasurementCreate,
                           InternalClientProfileEnrichmentUpdate)
from app.internal_client_profile import merge_enrichment, projection as internal_profile_projection, validate_enrichment
from app.external_client_profile import merge_external_enrichment, projection as external_profile_projection, validate_external_enrichment
from app.external_measurements import calculated_health_parameters, validated_measurement
from app.measurement_context import assessment_measurement_sources, resolve_latest_measurements
from app.nutrition_foundation import (AssessmentReview, AssessmentSource, AssessmentStale,
                                      ClinicalDocumentLink, DietPlanAssessmentBind,
                                      NutritionAssessmentCreate, NutritionAssessmentSave,
                                      NutritionAssessmentTransition, NutritionProfile,
                                      assessment_fingerprint,
                                      diet_plan_readiness,
                                      measurement_calculations,
                                      source_manifest,
                                      CALCULATION_VERSIONS)
from app.smart_intake import (FIELD_REGISTRY, FIELD_SCHEMA_VERSION, InformationRequestCreate,
                              InformationRequestPatch, InformationRequestReview,
                              resolve_assessment, resolve_completeness, scoped_patch)
from app.document_storage import (StorageUnavailable, InvalidDocument, new_object_key, new_credential_evidence_key,
                                  signed_upload, signed_download, signed_view, validate_document,
                                  upload_object, verify_uploaded_object, verify_jpeg_object)
from app.billing import calculate_line
from app.p15 import adherence_summary, homework_transition
from app.p16 import (ACTION_TYPES, CONFIRMATION_ACTIONS, SAFE_ACTIONS,
                     assert_chain_depth, evaluate_condition, idempotency_key)
from app.p17 import PERMISSIONS, ROLE_PERMISSIONS, can_manage_role, resolve_permissions
from app.p18 import MIN_COHORT_SIZE, analytics_window, cohort_result, rate
from app.p19 import ALLOWED_SCOPES, referral_transition, validate_scopes
from app.p20 import build_docx, build_pdf, checksum
from app.p24 import assert_transition as assert_lead_transition, normal_email, normal_phone
from app.p26 import validate_resource_type
from app.p28 import PaymentProviderNotConfigured, canonical_payload_hash, verify_razorpay_payment, verify_razorpay_webhook
from app.p29 import classify_output, validate_ai_request
from app.p30 import EXCLUDED_BY_DEFAULT, export_checksum, validate_export_sections
from app.command_centre import next_action, operational_priority, section as command_section, sort_work
from app.p37 import project_readiness, resolve_requirements
from app.p38 import project_post_session, resolve_post_session_actions
from app.p39 import experience_label, public_review_eligible, validate_ratings
from app.p40 import join_allowed, provider_status, validate_external_meeting_url
from app.p41 import validate_message
from app.p42 import external_change_action, project_busy_block, provider_state
from app.p43 import assert_paid_evidence
from app.p44 import downgrade_policy, provider_status as subscription_provider_status
from app.p45 import discount_minor, validate_rule
from app.p46 import refund_transition
from app.p47 import safe_context
from app.p48 import category as notification_category, digest_mode
from app.p49 import resolve_command
from app.marketplace import (ADMIN_ACTIONS,REASON_REQUIRED,AdminDecision,BookingManagementAction,ConsultantContactSave,EnrolmentAction,EnrolmentCreate,PublicBookingCreate,PublicWaitlistCreate,ProfilePhotoFinalise,ProfilePhotoPrepare,QualificationEvidencePrepare,QualificationEvidenceFinalise,PromotionQuote,HomepageFeatureDecision,MarketplaceComparisonEvent,MarketplaceEventCreate,ProfileSave,
                             QualificationCreate,QualificationDecision,ReviewCreate,ReviewReport,assert_transition,
                             can_publish,completeness,dedupe_key,privacy_safe_name,public_projection,
                             publicly_visible,slug_base)
from app.finder import FINDER_EVENTS,SUPPORT_TAXONOMY,FinderEvent,FinderRequest,explain_and_score
from app.client_portal import PortalTokenError, issue_portal_token, portal_token_hash, validate_portal_token
from app.communications import InvalidPhone, normalize_phone
from app.diet_plan_policy import can_publish_independently
from app.domain import calendar_window, consultation_transition, factual_summary
from app.db import get_db, engine
from app.profession_intake import (FROZEN_PROFESSIONS, SUPPORTED_PROFESSIONS,
                                   IntakeTokenError, issue_token, token_hash,
                                   validate_token)
from app.qa_delegation import QaDelegation, QaDelegationError, require_qa_delegation

logger = structlog.get_logger(__name__)
RESOURCE_TABLES = {
    "consultations": "practice_consultations",
    "follow-ups": "practice_follow_ups",
    "goals": "practice_goals",
    "tasks": "practice_tasks",
    "check-ins": "practice_checkins",
    "adherence": "practice_adherence_entries",
    "notes": "practice_client_notes",
}
NOTIFICATION_EVENTS = {
    "CONSULTATION_SCHEDULED", "CONSULTATION_COMPLETED", "FOLLOWUP_CREATED",
    "FOLLOWUP_DUE", "FOLLOWUP_COMPLETED", "TASK_CREATED", "TASK_DUE",
    "TASK_COMPLETED", "CHECKIN_SUBMITTED", "REPORT_PROCESSED",
    "DIET_PLAN_PUBLISHED",
}
CREATE_EVENTS = {"consultations": "CONSULTATION_SCHEDULED", "follow-ups": "FOLLOWUP_CREATED", "tasks": "TASK_CREATED", "check-ins": "CHECKIN_SUBMITTED"}
COMPLETE_EVENTS = {"consultations": "CONSULTATION_COMPLETED", "follow-ups": "FOLLOWUP_COMPLETED", "tasks": "TASK_COMPLETED"}

ALL_CAPABILITIES = {
    "CLIENT_CRM", "CLIENT_ONBOARDING", "CONSULTATIONS", "SESSION_NOTES", "PRIVATE_NOTES",
    "FOLLOW_UPS", "GOALS_PROGRESS", "TASKS", "CALENDAR", "COMMUNICATION",
    "WHATSAPP_SHARING", "ASSESSMENTS", "FORM_BUILDER", "DIET_PLAN",
    "CARE_PLAN", "THERAPY_PLAN", "BEHAVIOURAL_PLAN", "EXERCISE_PLAN",
    "REHAB_PLAN", "HABIT_PLAN", "LAB_ANALYSIS", "BIOMARKERS", "MEASUREMENTS",
    "TEMPLATES", "PROGRESS_REPORTS", "PRACTICE_TEAM", "PACKAGES", "BILLING",
    "RENEWALS", "ANALYTICS", "CLIENT_PORTAL", "RESOURCE_LIBRARY", "HOMEWORK", "ADHERENCE", "AUTOMATIONS",
}
RESOURCE_CAPABILITY = {"consultations":"CONSULTATIONS", "follow-ups":"FOLLOW_UPS", "goals":"GOALS_PROGRESS", "tasks":"TASKS"}
PROFESSION_DEFAULTS = {
    "DIETITIAN": {"CONSULTATIONS","SESSION_NOTES","FOLLOW_UPS","GOALS_PROGRESS","TASKS","CALENDAR","COMMUNICATION","WHATSAPP_SHARING","DIET_PLAN","LAB_ANALYSIS","BIOMARKERS","MEASUREMENTS","TEMPLATES","CLIENT_CRM","CLIENT_ONBOARDING"},
    "NUTRITIONIST": {"CONSULTATIONS","SESSION_NOTES","FOLLOW_UPS","GOALS_PROGRESS","TASKS","CALENDAR","COMMUNICATION","WHATSAPP_SHARING","DIET_PLAN","LAB_ANALYSIS","BIOMARKERS","MEASUREMENTS","TEMPLATES","CLIENT_CRM","CLIENT_ONBOARDING"},
    "CLINICAL_NUTRITIONIST": {"CONSULTATIONS","SESSION_NOTES","FOLLOW_UPS","GOALS_PROGRESS","TASKS","CALENDAR","COMMUNICATION","WHATSAPP_SHARING","DIET_PLAN","LAB_ANALYSIS","BIOMARKERS","MEASUREMENTS","TEMPLATES","CLIENT_CRM","CLIENT_ONBOARDING"},
    "SPORTS_NUTRITIONIST": {"CONSULTATIONS","SESSION_NOTES","FOLLOW_UPS","GOALS_PROGRESS","TASKS","CALENDAR","COMMUNICATION","WHATSAPP_SHARING","DIET_PLAN","LAB_ANALYSIS","BIOMARKERS","MEASUREMENTS","TEMPLATES","CLIENT_CRM","CLIENT_ONBOARDING"},
    "PSYCHOLOGIST": {"CONSULTATIONS","SESSION_NOTES","PRIVATE_NOTES","FOLLOW_UPS","GOALS_PROGRESS","TASKS","CALENDAR","COMMUNICATION","WHATSAPP_SHARING","THERAPY_PLAN","ASSESSMENTS","TEMPLATES","CLIENT_CRM","CLIENT_ONBOARDING"},
    "COUNSELLOR": {"CONSULTATIONS","SESSION_NOTES","FOLLOW_UPS","GOALS_PROGRESS","TASKS","CALENDAR","COMMUNICATION","WHATSAPP_SHARING","THERAPY_PLAN","ASSESSMENTS","TEMPLATES","CLIENT_CRM","CLIENT_ONBOARDING"},
    "PHYSIOTHERAPIST": {"CONSULTATIONS","SESSION_NOTES","FOLLOW_UPS","GOALS_PROGRESS","TASKS","CALENDAR","COMMUNICATION","WHATSAPP_SHARING","REHAB_PLAN","EXERCISE_PLAN","ASSESSMENTS","TEMPLATES","CLIENT_CRM","CLIENT_ONBOARDING"},
    "HEALTH_COACH": {"CONSULTATIONS","SESSION_NOTES","FOLLOW_UPS","GOALS_PROGRESS","TASKS","CALENDAR","COMMUNICATION","WHATSAPP_SHARING","HABIT_PLAN","TEMPLATES","CLIENT_CRM","CLIENT_ONBOARDING"},
    "DIABETES_EDUCATOR": {"CONSULTATIONS","SESSION_NOTES","FOLLOW_UPS","GOALS_PROGRESS","TASKS","CALENDAR","COMMUNICATION","WHATSAPP_SHARING","CARE_PLAN","ASSESSMENTS","MEASUREMENTS","TEMPLATES","CLIENT_CRM","CLIENT_ONBOARDING"},
    "WELLNESS_CONSULTANT": {"CONSULTATIONS","SESSION_NOTES","FOLLOW_UPS","GOALS_PROGRESS","TASKS","CALENDAR","COMMUNICATION","WHATSAPP_SHARING","CARE_PLAN","HABIT_PLAN","ASSESSMENTS","TEMPLATES","CLIENT_CRM","CLIENT_ONBOARDING"},
    "BEHAVIOURAL_THERAPIST": {"CONSULTATIONS","SESSION_NOTES","PRIVATE_NOTES","FOLLOW_UPS","GOALS_PROGRESS","TASKS","CALENDAR","COMMUNICATION","WHATSAPP_SHARING","BEHAVIOURAL_PLAN","ASSESSMENTS","TEMPLATES","CLIENT_CRM","CLIENT_ONBOARDING"},
    "OCCUPATIONAL_THERAPIST": {"CONSULTATIONS","SESSION_NOTES","FOLLOW_UPS","GOALS_PROGRESS","TASKS","CALENDAR","COMMUNICATION","WHATSAPP_SHARING","THERAPY_PLAN","ASSESSMENTS","TEMPLATES","CLIENT_CRM","CLIENT_ONBOARDING"},
    "MENTAL_WELLNESS_THERAPIST": {"CONSULTATIONS","SESSION_NOTES","PRIVATE_NOTES","FOLLOW_UPS","GOALS_PROGRESS","TASKS","CALENDAR","COMMUNICATION","WHATSAPP_SHARING","THERAPY_PLAN","ASSESSMENTS","TEMPLATES","CLIENT_CRM","CLIENT_ONBOARDING"},
}
for _profession, _profession_capabilities in PROFESSION_DEFAULTS.items():
    _profession_capabilities.update({"RESOURCE_LIBRARY", "HOMEWORK", "ADHERENCE"})
    if _profession not in FROZEN_PROFESSIONS:
        _profession_capabilities.add("AUTOMATIONS")
TERMINOLOGY = {
    "DIETITIAN":{"consultation":"Consultation","plan":"Diet Plan","goal":"Nutrition Goal"},
    "NUTRITIONIST":{"consultation":"Consultation","plan":"Nutrition Plan","goal":"Nutrition Goal"},
    "CLINICAL_NUTRITIONIST":{"consultation":"Consultation","plan":"Clinical Nutrition Plan","goal":"Nutrition Goal"},
    "SPORTS_NUTRITIONIST":{"consultation":"Consultation","plan":"Sports Nutrition Plan","goal":"Performance Nutrition Goal"},
    "PSYCHOLOGIST":{"consultation":"Session","plan":"Therapy Plan","goal":"Therapy Goal"},
    "COUNSELLOR":{"consultation":"Session","plan":"Care Plan","goal":"Therapy Goal"},
    "PHYSIOTHERAPIST":{"consultation":"Assessment","plan":"Rehab Plan","goal":"Exercise Goal"},
    "HEALTH_COACH":{"consultation":"Coaching Session","plan":"Habit Plan","goal":"Lifestyle Goal"},
    "DIABETES_EDUCATOR":{"consultation":"Education Session","plan":"Care Plan","goal":"Self-management Goal"},
    "WELLNESS_CONSULTANT":{"consultation":"Wellness Session","plan":"Wellness Plan","goal":"Wellness Goal"},
    "BEHAVIOURAL_THERAPIST":{"consultation":"Therapy Session","plan":"Behavioural Plan","goal":"Behavioural Goal"},
    "OCCUPATIONAL_THERAPIST":{"consultation":"Assessment","plan":"Therapy Plan","goal":"Functional Goal"},
    "MENTAL_WELLNESS_THERAPIST":{"consultation":"Therapy Session","plan":"Wellness Plan","goal":"Wellness Goal"},
}

PROFESSION_ALIASES = {
    "DIETITIAN": "DIETITIAN",
    "DIETICIAN": "DIETITIAN",
    "REGISTERED_DIETITIAN": "DIETITIAN",
    "CLINICAL_DIETITIAN": "CLINICAL_NUTRITIONIST",
    "NUTRITIONIST": "NUTRITIONIST",
    "NUTRITION_CONSULTANT": "NUTRITIONIST",
    "NUTRITION_CONSULTANT_DIETITIAN": "DIETITIAN",
    "DIETITIAN_NUTRITIONIST": "DIETITIAN",
    "CLINICAL_NUTRITIONIST": "CLINICAL_NUTRITIONIST",
    "SPORTS_NUTRITIONIST": "SPORTS_NUTRITIONIST",
}


def canonical_profession(value: str | None) -> str:
    token = re.sub(r"[^A-Z0-9]+", "_", str(value or "").strip().upper()).strip("_")
    return PROFESSION_ALIASES.get(token, token if token in PROFESSION_DEFAULTS else "OTHER")

PROFESSION_CLIENT360_SECTIONS = {
    "PSYCHOLOGIST": [("Assessments", "assessments"), ("Sessions", "consultations"), ("Therapy Goals", "goals"), ("Notes", "notes"), ("Progress", "tasks")],
    "PHYSIOTHERAPIST": [("Pain & Function", "assessments"), ("Physical Assessments", "assessments"), ("Rehab", "goals"), ("Exercise", "tasks"), ("Progress", "follow-ups")],
    "DIABETES_EDUCATOR": [("Metabolic Profile", "assessments"), ("Biomarkers", "biomarkers"), ("Education", "consultations"), ("Lifestyle", "goals"), ("Progress", "follow-ups")],
    "HEALTH_COACH": [("Coaching Profile", "assessments"), ("Check-ins", "follow-ups"), ("Habits", "tasks"), ("Goals", "goals"), ("Progress", "consultations")],
    "WELLNESS_CONSULTANT": [("Wellness Profile", "assessments"), ("Habits", "tasks"), ("Wellness Plan", "goals"), ("Progress", "follow-ups")],
    "BEHAVIOURAL_THERAPIST": [("Behaviour Profile", "assessments"), ("Behaviour Logs", "notes"), ("Intervention Plan", "goals"), ("Progress", "follow-ups")],
    "OCCUPATIONAL_THERAPIST": [("Functional Profile", "assessments"), ("ADL", "assessments"), ("Activities", "tasks"), ("OT Plan", "goals"), ("Progress", "follow-ups")],
    "MENTAL_WELLNESS_THERAPIST": [("Wellbeing", "assessments"), ("Sessions", "consultations"), ("Goals", "goals"), ("Support Plan", "tasks"), ("Progress", "follow-ups")],
}

PLAN_CAPABILITIES = {
    "THERAPY_PLAN":"THERAPY_PLAN", "REHAB_PLAN":"REHAB_PLAN", "EXERCISE_PLAN":"EXERCISE_PLAN",
    "HABIT_PLAN":"HABIT_PLAN", "WELLNESS_PLAN":"CARE_PLAN", "BEHAVIOUR_INTERVENTION_PLAN":"BEHAVIOURAL_PLAN",
    "OT_PLAN":"THERAPY_PLAN", "DIABETES_EDUCATION_PLAN":"CARE_PLAN", "SUPPORT_PLAN":"THERAPY_PLAN",
}

DIET_PLAN_REVIEW_ROLES = {"SENIOR_CONSULTANT", "PRACTICE_ADMIN", "PRACTICE_OWNER", "SUPER_ADMIN", "SUPERUSER", "PLATFORM_OWNER"}

def _diet_plan_actor_clause(ctx):
    if ctx.get("role") in DIET_PLAN_REVIEW_ROLES:
        return "", {}
    return " AND authorised_consultant_id=:actor", {"actor": ctx["user_id"]}


async def configuration(db: AsyncSession, ctx):
    row = (await db.execute(text("SELECT profession,capabilities,terminology,profile,version FROM practice_tenant_configuration WHERE tenant_id=:tenant_id"), {"tenant_id":ctx["tenant_id"]})).mappings().first()
    if row: return dict(row)
    profession = canonical_profession(ctx.get("profession_code"))
    if profession in PROFESSION_DEFAULTS:
        return {"profession":profession,"capabilities":sorted(PROFESSION_DEFAULTS[profession]),"terminology":TERMINOLOGY[profession],"profile":{},"version":0}
    return {"profession":"OTHER","capabilities":["CLIENT_CRM","CLIENT_ONBOARDING","CONSULTATIONS","FOLLOW_UPS","GOALS_PROGRESS","TASKS","CALENDAR","COMMUNICATION","WHATSAPP_SHARING","TEMPLATES"],"terminology":{"consultation":"Consultation","plan":"Care Plan","goal":"Goal"},"profile":{},"version":0}


async def require_capability(request: Request, db: AsyncSession, ctx, capability: str):
    config = await configuration(db, ctx)
    if capability not in set(config["capabilities"]):
        return error(request, 403, "CAPABILITY_NOT_ENABLED", f"{capability.replace('_',' ').title()} is not enabled for this practice")
    return None


def error(request: Request, status: int, code: str, message: str, retryable: bool = False):
    return JSONResponse(status_code=status, content={"success": False, "error": {"code": code, "safe_message": message, "correlation_id": getattr(request.state, "correlation_id", None), "retryable": retryable}})


def context(x_user_id: str | None = Header(None), x_tenant_id: str | None = Header(None), x_user_role: str | None = Header(None), x_tenant_type: str | None = Header(None), x_user_email: str | None = Header(None), x_profession_code: str | None = Header(None), x_user_permissions: str | None = Header(None)):
    role=(x_user_role or "member").upper()
    if not x_user_id:
        return None
    if not x_tenant_id and role not in {"SUPER_ADMIN","SUPERUSER","PLATFORM_OWNER"}:
        return None
    return {"user_id": x_user_id, "tenant_id": x_tenant_id, "role": role, "tenant_type": x_tenant_type, "email": (x_user_email or "").lower(), "profession_code": x_profession_code, "permissions": {item.strip() for item in (x_user_permissions or "").split(",") if item.strip()}}


def external_only(request: Request, ctx):
    if not ctx:
        return error(request, 401, "AUTHENTICATION_REQUIRED", "Authentication is required")
    if ctx.get("tenant_type") not in {"INDEPENDENT_CONSULTANT", "PRACTICE", "CLINIC"}:
        return error(request, 403, "EXTERNAL_PRACTICE_SCOPE_REQUIRED", "External practice access is required")
    return None


def internal_profile_only(request: Request, ctx, *, write: bool = False):
    if not ctx:
        return error(request, 401, "AUTHENTICATION_REQUIRED", "Authentication is required")
    if ctx.get("tenant_type") != "ZESTIVA_INTERNAL" or not ctx.get("tenant_id"):
        return error(request, 403, "INTERNAL_PROFILE_SCOPE_REQUIRED", "Internal client profile access is required")
    permissions = ctx.get("permissions", set())
    read_allowed = bool(permissions & {"client_read", "internal.operations.manage"})
    write_allowed = bool(permissions & {"plan_review", "internal.operations.manage"})
    if not read_allowed or (write and not write_allowed):
        return error(request, 403, "INTERNAL_CLIENT_PERMISSION_REQUIRED", "You do not have permission to access Internal client profiles")
    return None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("service_starting", service=get_settings().app_name)
    yield
    await engine().dispose()


app = FastAPI(title="Practice Operations Service", version=get_settings().app_version, lifespan=lifespan)


@app.get("/api/v1/practice-operations/clients/{client_id}/profile-enrichment")
async def get_external_client_profile_enrichment(request: Request, client_id: str, ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied = external_only(request, ctx)
    if denied: return denied
    row = (await db.execute(text("""SELECT values,version,schema_version,provenance,updated_at,updated_by
      FROM external_client_profile_enrichments WHERE tenant_id=:tenant AND client_id=:client"""),
      {"tenant":ctx["tenant_id"],"client":client_id})).mappings().first()
    if not row:
        return {"success":True,"data":external_profile_projection({},0,{"source":"EXTERNAL_CLIENT360_ENRICHMENT","tenant_id":ctx["tenant_id"],"client_id":client_id}),"error":None,"request_id":request.state.correlation_id}
    provenance={**dict(row["provenance"] or {}),"source":"EXTERNAL_CLIENT360_ENRICHMENT","tenant_id":ctx["tenant_id"],"client_id":client_id,"updated_at":row["updated_at"].isoformat(),"updated_by":row["updated_by"]}
    return {"success":True,"data":external_profile_projection(dict(row["values"] or {}),row["version"],provenance),"error":None,"request_id":request.state.correlation_id}


@app.put("/api/v1/practice-operations/clients/{client_id}/profile-enrichment")
async def update_external_client_profile_enrichment(request: Request, client_id: str, body: ExternalClientProfileEnrichmentUpdate, ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied = external_only(request, ctx)
    if denied: return denied
    try: values = validate_external_enrichment(body.values)
    except (TypeError, ValueError) as exc: return error(request,422,"INVALID_EXTERNAL_PROFILE_ENRICHMENT",str(exc))
    now=datetime.now(timezone.utc)
    event={"event":"EXTERNAL_CLIENT_PROFILE_ENRICHMENT_UPDATED","actor_id":ctx["user_id"],"timestamp":now.isoformat(),"expected_version":body.expected_version,"changed_fields":sorted(values)}
    if body.expected_version == 0:
        try:
            row=(await db.execute(text("""INSERT INTO external_client_profile_enrichments
              (tenant_id,client_id,values,version,schema_version,provenance,audit_history,created_by,updated_by,created_at,updated_at)
              VALUES (:tenant,:client,CAST(:values AS jsonb),1,1,CAST(:provenance AS jsonb),CAST(:audit AS jsonb),:actor,:actor,:now,:now)
              RETURNING values,version,provenance,updated_at"""),{"tenant":ctx["tenant_id"],"client":client_id,"values":json.dumps(values),"provenance":json.dumps({"source":"EXTERNAL_CLIENT360_ENRICHMENT"}),"audit":json.dumps([event]),"actor":ctx["user_id"],"now":now})).mappings().one()
        except IntegrityError:
            await db.rollback();return error(request,409,"STALE_WRITE","The client profile changed in another session. Refresh and try again")
    else:
        current=(await db.execute(text("SELECT values FROM external_client_profile_enrichments WHERE tenant_id=:tenant AND client_id=:client AND version=:version"),{"tenant":ctx["tenant_id"],"client":client_id,"version":body.expected_version})).mappings().first()
        if not current:return error(request,409,"STALE_WRITE","The client profile changed in another session. Refresh and try again")
        merged_values=merge_external_enrichment(dict(current["values"] or {}),values)
        row=(await db.execute(text("""UPDATE external_client_profile_enrichments SET
          values=CAST(:values AS jsonb),version=version+1,updated_by=:actor,updated_at=:now,
          provenance=provenance || CAST(:provenance AS jsonb),audit_history=audit_history || CAST(:audit AS jsonb)
          WHERE tenant_id=:tenant AND client_id=:client AND version=:version RETURNING values,version,provenance,updated_at"""),{"tenant":ctx["tenant_id"],"client":client_id,"values":json.dumps(merged_values),"provenance":json.dumps({"source":"EXTERNAL_CLIENT360_ENRICHMENT","last_actor_id":ctx["user_id"]}),"audit":json.dumps([event]),"actor":ctx["user_id"],"now":now,"version":body.expected_version})).mappings().first()
        if not row:
            await db.rollback();return error(request,409,"STALE_WRITE","The client profile changed in another session. Refresh and try again")
    await db.commit()
    provenance={**dict(row["provenance"] or {}),"source":"EXTERNAL_CLIENT360_ENRICHMENT","tenant_id":ctx["tenant_id"],"client_id":client_id,"updated_at":row["updated_at"].isoformat(),"updated_by":ctx["user_id"]}
    return {"success":True,"data":external_profile_projection(dict(row["values"] or {}),row["version"],provenance),"error":None,"request_id":request.state.correlation_id}


def _measurement_row(row):
    value = dict(row)
    for key in ("id", "series_id", "supersedes_id"):
        if value.get(key) is not None:
            value[key] = str(value[key])
    value["value"] = float(value["value"])
    for key in ("measured_at", "created_at"):
        value[key] = value[key].isoformat()
    return value


async def _measurement_projection(db, tenant_id: str, client_id: str):
    rows = (await db.execute(text("""SELECT id,series_id,measurement_type,value,unit,measured_at,source,
      recorded_by,created_at,version,supersedes_id,correction_reason
      FROM external_client_measurements WHERE tenant_id=:tenant AND client_id=:client
      ORDER BY measured_at DESC,created_at DESC,version DESC"""),
      {"tenant":tenant_id,"client":client_id})).mappings().all()
    projected = [_measurement_row(row) for row in rows]
    latest_series = {}
    for row in projected:
        current = latest_series.get(row["series_id"])
        if current is None or row["version"] > current["version"]:
            latest_series[row["series_id"]] = row
    current_rows = sorted(latest_series.values(), key=lambda row:(row["measured_at"],row["created_at"]), reverse=True)
    legacy_row=(await db.execute(text("""SELECT values,version,updated_at FROM external_client_profile_enrichments
      WHERE tenant_id=:tenant AND client_id=:client"""),{"tenant":tenant_id,"client":client_id})).mappings().first()
    legacy=dict((legacy_row or {}).get("values") or {}).get("measurements") or {}
    resolved=resolve_latest_measurements(projected,legacy)
    return {"latest":resolved["latest"],"eligible_latest":resolved["eligible_latest"],"history":projected,
            "calculations":resolved["calculations"],"rejected":resolved["rejected"],
            "measurement_context_fingerprint":resolved["fingerprint"],
            "source_measurement_ids":resolved["source_measurement_ids"],
            "requires_professional_confirmation":resolved["requires_professional_confirmation"],
            "resolver_version":resolved["resolver_version"],
            "methodology_versions":["bmi.metric.v1","whr.metric.v1","whtr.metric.v1",
                                    "weight-change.metric.v1","weight-change-percent.metric.v1",
                                    "weight-trend.dated-observations.v1"]}


async def _mark_measurement_context_changed(db, tenant_id: str, client_id: str, actor_id: str, now: datetime):
    assessment=(await db.execute(text("""SELECT id,current_version,status FROM external_nutrition_assessments
      WHERE tenant_id=:tenant AND client_id=:client ORDER BY updated_at DESC LIMIT 1 FOR UPDATE"""),
      {"tenant":tenant_id,"client":client_id})).mappings().first()
    if not assessment:return
    await db.execute(text("""UPDATE external_nutrition_assessments SET stale=TRUE,
      stale_reason='MEASUREMENT_CONTEXT_CHANGED',readiness_status='BLOCKED',updated_at=:now
      WHERE id=:id AND tenant_id=:tenant"""),{"now":now,"id":assessment["id"],"tenant":tenant_id})
    await _nutrition_event(db,assessment_id=assessment["id"],tenant_id=tenant_id,client_id=client_id,
      version=assessment["current_version"],event_type="MEASUREMENT_CONTEXT_CHANGED",
      from_status=assessment["status"],to_status=assessment["status"],actor_id=actor_id,now=now,
      notes="A persisted measurement changed; professional reassessment is required before publication")


@app.get("/api/v1/practice-operations/clients/{client_id}/measurements")
async def list_external_client_measurements(request: Request, client_id: str, ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    data=await _measurement_projection(db,ctx["tenant_id"],client_id)
    return {"success":True,"data":data,"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/clients/{client_id}/measurements",status_code=201)
async def create_external_client_measurements(request: Request, client_id: str, body: ExternalMeasurementCreate, ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    now=datetime.now(timezone.utc);seen=set()
    try:
        validated=[validated_measurement(item.measurement_type,item.value,item.unit) for item in body.measurements]
    except ValueError as exc:return error(request,422,"INVALID_EXTERNAL_MEASUREMENT",str(exc))
    if any(kind in seen or seen.add(kind) for kind,_,_ in validated):
        return error(request,422,"DUPLICATE_MEASUREMENT_TYPE","Each measurement type may appear once per entry")
    for kind,value,unit in validated:
        record_id=uuid4()
        await db.execute(text("""INSERT INTO external_client_measurements
          (id,series_id,tenant_id,client_id,measurement_type,value,unit,measured_at,source,recorded_by,created_at,version)
          VALUES (:id,:id,:tenant,:client,:kind,:value,:unit,:measured,:source,:actor,:now,1)"""),
          {"id":record_id,"tenant":ctx["tenant_id"],"client":client_id,"kind":kind,"value":value,
           "unit":unit,"measured":body.measured_at,"source":body.source,"actor":ctx["user_id"],"now":now})
    await _mark_measurement_context_changed(db,ctx["tenant_id"],client_id,ctx["user_id"],now)
    await db.commit();data=await _measurement_projection(db,ctx["tenant_id"],client_id)
    return {"success":True,"data":data,"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/clients/{client_id}/measurements/{measurement_id}/corrections",status_code=201)
async def correct_external_client_measurement(request: Request, client_id: str, measurement_id: UUID, body: ExternalMeasurementCorrection, ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    row=(await db.execute(text("""SELECT m.* FROM external_client_measurements m
      WHERE m.id=:id AND m.tenant_id=:tenant AND m.client_id=:client FOR UPDATE"""),
      {"id":measurement_id,"tenant":ctx["tenant_id"],"client":client_id})).mappings().first()
    if not row:return error(request,404,"MEASUREMENT_NOT_FOUND","Measurement was not found")
    maximum=(await db.execute(text("SELECT max(version) FROM external_client_measurements WHERE tenant_id=:tenant AND client_id=:client AND series_id=:series"),
      {"tenant":ctx["tenant_id"],"client":client_id,"series":row["series_id"]})).scalar_one()
    if row["version"] != maximum:return error(request,409,"STALE_MEASUREMENT_VERSION","Refresh before correcting this measurement")
    try:kind,value,unit=validated_measurement(row["measurement_type"],body.value,body.unit)
    except ValueError as exc:return error(request,422,"INVALID_EXTERNAL_MEASUREMENT",str(exc))
    now=datetime.now(timezone.utc);new_id=uuid4()
    await db.execute(text("""INSERT INTO external_client_measurements
      (id,series_id,tenant_id,client_id,measurement_type,value,unit,measured_at,source,recorded_by,
       created_at,version,supersedes_id,correction_reason)
      VALUES (:id,:series,:tenant,:client,:kind,:value,:unit,:measured,'PROFESSIONALLY_RECORDED',:actor,
              :now,:version,:prior,:reason)"""),
      {"id":new_id,"series":row["series_id"],"tenant":ctx["tenant_id"],"client":client_id,"kind":kind,
       "value":value,"unit":unit,"measured":body.measured_at,"actor":ctx["user_id"],"now":now,
       "version":row["version"]+1,"prior":row["id"],"reason":body.reason})
    await _mark_measurement_context_changed(db,ctx["tenant_id"],client_id,ctx["user_id"],now)
    await db.commit();data=await _measurement_projection(db,ctx["tenant_id"],client_id)
    return {"success":True,"data":data,"error":None,"request_id":request.state.correlation_id}


def _nutrition_assessment_projection(row):
    value=dict(row)
    for key in ("id","assessment_id"):
        if value.get(key) is not None:value[key]=str(value[key])
    return value


async def _nutrition_event(db, *, assessment_id, tenant_id, client_id, version, event_type,
                           from_status, to_status, actor_id, now, notes=None):
    await db.execute(text("""INSERT INTO external_nutrition_assessment_events
      (id,assessment_id,tenant_id,client_id,assessment_version,event_type,from_status,to_status,notes,actor_id,created_at)
      VALUES (:id,:assessment,:tenant,:client,:version,:event,:before,:after,:notes,:actor,:now)"""),
      {"id":uuid4(),"assessment":assessment_id,"tenant":tenant_id,"client":client_id,"version":version,
       "event":event_type,"before":from_status,"after":to_status,"notes":notes,"actor":actor_id,"now":now})


async def _information_audit(db,row,event_type,actor_type,actor_id,now,metadata=None):
    await db.execute(text("""INSERT INTO external_client_information_request_audit
      (id,request_id,tenant_id,client_id,event_type,actor_type,actor_id,metadata,created_at)
      VALUES (:id,:request,:tenant,:client,:event,:actor_type,:actor,CAST(:metadata AS jsonb),:now)"""),
      {"id":uuid4(),"request":row["id"],"tenant":row["tenant_id"],"client":row["client_id"],"event":event_type,
       "actor_type":actor_type,"actor":actor_id,"metadata":json.dumps(metadata or {}),"now":now})


async def _canonical_intake(db,tenant_id,client_id):
    row=(await db.execute(text("SELECT values,updated_at FROM external_client_profile_enrichments WHERE tenant_id=:tenant AND client_id=:client"),
      {"tenant":tenant_id,"client":client_id})).mappings().first()
    return (dict(row["values"] or {}),row["updated_at"]) if row else ({},None)


@app.get("/api/v1/practice-operations/clients/{client_id}/information-completeness")
async def client_information_completeness(request:Request,client_id:str,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=await _nutrition_scope(request,db,ctx)
    if denied:return denied
    values,updated_at=await _canonical_intake(db,ctx["tenant_id"],client_id)
    request_rows=(await db.execute(text("""SELECT field_ids,status FROM external_client_information_requests WHERE tenant_id=:tenant AND client_id=:client
      AND status IN ('CREATED','SENT','OPENED','PARTIALLY_COMPLETED','SUBMITTED','COMPLETED')"""),{"tenant":ctx["tenant_id"],"client":client_id})).mappings().all()
    pending={field for row in request_rows if row["status"] in {'CREATED','SENT','OPENED','PARTIALLY_COMPLETED'} for field in (row["field_ids"] or [])}
    review={field for row in request_rows if row["status"]=='SUBMITTED' for field in (row["field_ids"] or [])}
    confirmed={field for row in request_rows if row["status"]=='COMPLETED' for field in (row["field_ids"] or [])}
    return {"success":True,"data":resolve_completeness(values,pending_fields=pending,review_fields=review,confirmed_fields=confirmed,updated_at=updated_at),"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/clients/{client_id}/information-requests",status_code=201)
async def create_information_request(request:Request,client_id:str,body:InformationRequestCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=await _nutrition_scope(request,db,ctx)
    if denied:return denied
    values,updated_at=await _canonical_intake(db,ctx["tenant_id"],client_id);resolved=resolve_completeness(values,updated_at=updated_at)
    requestable={row["field_id"] for row in resolved["fields"] if row["client_can_provide"] and row["status"] in {"MISSING","INVALID","REQUIRES_CONFIRMATION"}}
    if not set(body.field_ids)<=requestable:return error(request,409,"INFORMATION_FIELDS_NOT_REQUESTABLE","A field is already complete or is not client-answerable")
    existing=(await db.execute(text("""SELECT id FROM external_client_information_requests WHERE tenant_id=:tenant AND client_id=:client
      AND field_ids=CAST(:fields AS jsonb) AND status IN ('CREATED','SENT','OPENED','PARTIALLY_COMPLETED') LIMIT 1"""),
      {"tenant":ctx["tenant_id"],"client":client_id,"fields":json.dumps(body.field_ids)})).first()
    if existing:return error(request,409,"EQUIVALENT_INFORMATION_REQUEST_ACTIVE","An equivalent request is already active")
    token=secrets.token_urlsafe(32);now=datetime.now(timezone.utc);row={"id":uuid4(),"tenant_id":ctx["tenant_id"],"client_id":client_id}
    state="SENT" if body.delivery_channel in {"EMAIL","WHATSAPP"} else "CREATED";delivery={"COPY_LINK":"LINK_COPIED","EMAIL":"QUEUED","WHATSAPP":"LINK_COPIED"}[body.delivery_channel]
    await db.execute(text("""INSERT INTO external_client_information_requests
      (id,tenant_id,client_id,consultant_id,token_hash_sha256,field_ids,field_schema_version,status,delivery_state,version,expires_at,created_at,updated_at,audit_metadata)
      VALUES (:id,:tenant,:client,:actor,:token,CAST(:fields AS jsonb),:schema,:status,:delivery,1,:expires,:now,:now,CAST(:audit AS jsonb))"""),
      {"id":row["id"],"tenant":row["tenant_id"],"client":client_id,"actor":ctx["user_id"],"token":hashlib.sha256(token.encode()).hexdigest(),"fields":json.dumps(body.field_ids),"schema":FIELD_SCHEMA_VERSION,"status":state,"delivery":delivery,"expires":now+timedelta(hours=body.expires_in_hours),"now":now,"audit":json.dumps({"created_by":ctx["user_id"]})})
    await _information_audit(db,row,"REQUEST_CREATED","CONSULTANT",ctx["user_id"],now,{"field_ids":body.field_ids,"delivery_channel":body.delivery_channel});await db.commit()
    return {"success":True,"data":{"id":str(row["id"]),"status":state,"delivery_state":delivery,"token":token,"field_ids":body.field_ids,"expires_at":(now+timedelta(hours=body.expires_in_hours)).isoformat()},"error":None,"request_id":request.state.correlation_id}


@app.get("/api/v1/practice-operations/clients/{client_id}/information-requests")
async def list_information_requests(request:Request,client_id:str,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=await _nutrition_scope(request,db,ctx)
    if denied:return denied
    rows=(await db.execute(text("""SELECT r.id,r.field_ids,r.status,r.delivery_state,r.version,r.created_at,r.expires_at,
      s.patch,s.provenance,s.submitted_at,s.review_decisions,s.review_notes FROM external_client_information_requests r
      LEFT JOIN LATERAL (SELECT patch,provenance,submitted_at,review_decisions,review_notes FROM external_client_information_request_submissions WHERE request_id=r.id ORDER BY version DESC LIMIT 1) s ON TRUE
      WHERE r.tenant_id=:tenant AND r.client_id=:client ORDER BY r.created_at DESC"""),{"tenant":ctx["tenant_id"],"client":client_id})).mappings().all()
    items=[]
    for row in rows:
        item=dict(row);item["id"]=str(item["id"]);items.append(item)
    return {"success":True,"data":{"items":items},"error":None,"request_id":request.state.correlation_id}


async def _client_information_scope(db,token,for_update=False):
    row=(await db.execute(text("""SELECT id,tenant_id,client_id,consultant_id,field_ids,field_schema_version,status,
      delivery_state,version,expires_at,opened_at,submitted_at,reviewed_at,revoked_at,created_at,updated_at
      FROM external_client_information_requests WHERE token_hash_sha256=:hash"""+(" FOR UPDATE" if for_update else "")),{"hash":hashlib.sha256(token.encode()).hexdigest()})).mappings().first()
    if not row:return None,"INVALID"
    if row["revoked_at"] or row["status"]=="REVOKED":return row,"REVOKED"
    if row["expires_at"]<=datetime.now(timezone.utc):return row,"EXPIRED"
    if row["status"] in {"COMPLETED","SUPERSEDED"}:return row,row["status"]
    return row,None


@app.get("/api/v1/client-information/{token}")
async def open_client_information_request(request:Request,token:str,db:AsyncSession=Depends(get_db)):
    row,state=await _client_information_scope(db,token,True)
    if not row:return error(request,404,"INFORMATION_REQUEST_INVALID","This secure update link is invalid")
    if state:return error(request,410,f"INFORMATION_REQUEST_{state}","This secure update link is no longer active")
    values,_=await _canonical_intake(db,row["tenant_id"],row["client_id"]);by_id={item["field_id"]:item for item in resolve_completeness(values)["fields"]}
    fields=[{**by_id[field],"kind":FIELD_REGISTRY[field]["kind"],"options":FIELD_REGISTRY[field].get("options",[])} for field in row["field_ids"] if by_id[field]["status"] not in {"CAPTURED","CONFIRMED","NOT_APPLICABLE"}]
    draft=(await db.execute(text("""SELECT patch FROM external_client_information_request_submissions
      WHERE request_id=:id AND status='DRAFT' ORDER BY version DESC LIMIT 1"""),{"id":row["id"]})).scalar_one_or_none() or {}
    now=datetime.now(timezone.utc)
    if row["status"] in {"CREATED","SENT"}:
        await db.execute(text("UPDATE external_client_information_requests SET status='OPENED',opened_at=COALESCE(opened_at,:now),updated_at=:now WHERE id=:id"),{"now":now,"id":row["id"]});await _information_audit(db,row,"REQUEST_OPENED","CLIENT",None,now);await db.commit()
    return {"success":True,"data":{"request_id":str(row["id"]),"version":row["version"],"status":"OPENED","fields":fields,"initial_values":{key:value for key,value in dict(draft).items() if key in {field["field_id"] for field in fields}},"all_complete":not fields,"expires_at":row["expires_at"].isoformat()},"error":None,"request_id":request.state.correlation_id}


@app.patch("/api/v1/client-information/{token}")
async def save_client_information_request(request:Request,token:str,body:InformationRequestPatch,db:AsyncSession=Depends(get_db)):
    row,state=await _client_information_scope(db,token,True)
    if not row:return error(request,404,"INFORMATION_REQUEST_INVALID","This secure update link is invalid")
    if state:return error(request,410,f"INFORMATION_REQUEST_{state}","This secure update link is no longer active")
    if row["version"]!=body.expected_version:return error(request,409,"STALE_INFORMATION_REQUEST","Refresh before saving")
    if not set(body.values)<=set(row["field_ids"]):return error(request,422,"INFORMATION_FIELD_OUT_OF_SCOPE","A submitted field was not requested")
    now=datetime.now(timezone.utc);version=int(row["version"])+1
    await db.execute(text("""INSERT INTO external_client_information_request_submissions
      (id,request_id,tenant_id,client_id,version,patch,provenance,status,submitted_at) VALUES
      (:id,:request,:tenant,:client,:version,CAST(:patch AS jsonb),CAST(:provenance AS jsonb),'DRAFT',:now)"""),
      {"id":uuid4(),"request":row["id"],"tenant":row["tenant_id"],"client":row["client_id"],"version":version,"patch":json.dumps(body.values),"provenance":json.dumps({"source":"CLIENT_FOLLOW_UP","request_id":str(row["id"])}),"now":now})
    await db.execute(text("UPDATE external_client_information_requests SET status='PARTIALLY_COMPLETED',version=:version,updated_at=:now WHERE id=:id"),{"version":version,"now":now,"id":row["id"]});await _information_audit(db,row,"DRAFT_SAVED","CLIENT",None,now,{"fields":sorted(body.values)});await db.commit()
    return {"success":True,"data":{"version":version,"status":"PARTIALLY_COMPLETED"},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/client-information/{token}/submit")
async def submit_client_information_request(request:Request,token:str,body:InformationRequestPatch,db:AsyncSession=Depends(get_db)):
    row,state=await _client_information_scope(db,token,True)
    if not row:return error(request,404,"INFORMATION_REQUEST_INVALID","This secure update link is invalid")
    if state:return error(request,410,f"INFORMATION_REQUEST_{state}","This secure update link is no longer active")
    if row["status"]=="SUBMITTED":
        prior=(await db.execute(text("""SELECT patch FROM external_client_information_request_submissions
          WHERE request_id=:id AND status='PENDING_CONSULTANT_REVIEW' ORDER BY version DESC LIMIT 1"""),{"id":row["id"]})).scalar_one_or_none()
        if dict(prior or {})==body.values:
            return {"success":True,"data":{"version":row["version"],"status":"SUBMITTED","professional_review_required":True,"idempotent":True},"error":None,"request_id":request.state.correlation_id}
        return error(request,409,"INFORMATION_REQUEST_ALREADY_SUBMITTED","This request is awaiting consultant review")
    if row["version"]!=body.expected_version:return error(request,409,"STALE_INFORMATION_REQUEST","Refresh before submitting")
    values,_=await _canonical_intake(db,row["tenant_id"],row["client_id"])
    draft=(await db.execute(text("""SELECT patch FROM external_client_information_request_submissions
      WHERE request_id=:id AND status='DRAFT' ORDER BY version DESC LIMIT 1"""),{"id":row["id"]})).scalar_one_or_none() or {}
    submitted={**dict(draft),**body.values}
    if not submitted or not set(submitted)<=set(row["field_ids"]):return error(request,422,"INFORMATION_REQUEST_INCOMPLETE","Submit every applicable field still requested")
    try:merged=scoped_patch(values,submitted,set(row["field_ids"]))
    except ValueError as exc:return error(request,422,"INVALID_INFORMATION_RESPONSE",str(exc))
    after={item["field_id"]:item for item in resolve_completeness(merged)["fields"]}
    unresolved={field for field in row["field_ids"] if after[field]["status"] not in {"CAPTURED","CONFIRMED","NOT_APPLICABLE"}}
    if unresolved:return error(request,422,"INFORMATION_REQUEST_INCOMPLETE","Submit every applicable field still requested")
    now=datetime.now(timezone.utc);version=int(row["version"])+1;audit={"event":"CLIENT_INFORMATION_SUBMITTED","request_id":str(row["id"]),"fields":sorted(submitted),"at":now.isoformat()}
    exists=(await db.execute(text("SELECT version FROM external_client_profile_enrichments WHERE tenant_id=:tenant AND client_id=:client FOR UPDATE"),{"tenant":row["tenant_id"],"client":row["client_id"]})).scalar_one_or_none()
    if exists:
        await db.execute(text("""UPDATE external_client_profile_enrichments SET values=CAST(:values AS jsonb),version=version+1,provenance=provenance||CAST(:provenance AS jsonb),audit_history=audit_history||CAST(:audit AS jsonb),updated_by='CLIENT_FOLLOW_UP',updated_at=:now WHERE tenant_id=:tenant AND client_id=:client"""),{"values":json.dumps(merged),"provenance":json.dumps({"client_follow_up":audit}),"audit":json.dumps([audit]),"now":now,"tenant":row["tenant_id"],"client":row["client_id"]})
    else:
        await db.execute(text("""INSERT INTO external_client_profile_enrichments (tenant_id,client_id,values,version,schema_version,provenance,audit_history,created_by,updated_by,created_at,updated_at) VALUES (:tenant,:client,CAST(:values AS jsonb),1,1,CAST(:provenance AS jsonb),CAST(:audit AS jsonb),'CLIENT_FOLLOW_UP','CLIENT_FOLLOW_UP',:now,:now)"""),{"tenant":row["tenant_id"],"client":row["client_id"],"values":json.dumps(merged),"provenance":json.dumps({"client_follow_up":audit}),"audit":json.dumps([audit]),"now":now})
    await db.execute(text("""UPDATE external_nutrition_assessments SET stale=TRUE,stale_reason='CLIENT_INFORMATION_UPDATED',
      readiness_status='BLOCKED',updated_at=:now WHERE tenant_id=:tenant AND client_id=:client"""),
      {"now":now,"tenant":row["tenant_id"],"client":row["client_id"]})
    await db.execute(text("""INSERT INTO external_client_information_request_submissions (id,request_id,tenant_id,client_id,version,patch,provenance,status,submitted_at) VALUES (:id,:request,:tenant,:client,:version,CAST(:patch AS jsonb),CAST(:provenance AS jsonb),'PENDING_CONSULTANT_REVIEW',:now)"""),{"id":uuid4(),"request":row["id"],"tenant":row["tenant_id"],"client":row["client_id"],"version":version,"patch":json.dumps(submitted),"provenance":json.dumps(audit),"now":now})
    await db.execute(text("UPDATE external_client_information_requests SET status='SUBMITTED',version=:version,submitted_at=:now,updated_at=:now WHERE id=:id"),{"version":version,"now":now,"id":row["id"]});await _information_audit(db,row,"REQUEST_SUBMITTED","CLIENT",None,now,{"fields":sorted(submitted)});await db.commit()
    return {"success":True,"data":{"version":version,"status":"SUBMITTED","professional_review_required":True},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/information-requests/{request_id}/review")
async def review_client_information_request(request:Request,request_id:UUID,body:InformationRequestReview,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=await _nutrition_scope(request,db,ctx)
    if denied:return denied
    row=(await db.execute(text("""SELECT id,tenant_id,client_id,consultant_id,field_ids,status,version,expires_at,revoked_at
      FROM external_client_information_requests WHERE id=:id AND tenant_id=:tenant FOR UPDATE"""),{"id":request_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not row:return error(request,404,"INFORMATION_REQUEST_NOT_FOUND","Client information request not found")
    if row["status"]!="SUBMITTED" or row["version"]!=body.expected_version:return error(request,409,"STALE_INFORMATION_REVIEW","Refresh before review")
    submitted_patch=(await db.execute(text("""SELECT patch FROM external_client_information_request_submissions
      WHERE request_id=:id AND version=:version AND status='PENDING_CONSULTANT_REVIEW'"""),{"id":request_id,"version":body.expected_version})).scalar_one_or_none() or {}
    if set(body.decisions)!=set(submitted_patch):return error(request,422,"REVIEW_SCOPE_INCOMPLETE","Review every submitted field without expanding the request scope")
    clarification=any(value=="REQUEST_CLARIFICATION" for value in body.decisions.values());now=datetime.now(timezone.utc);status="PARTIALLY_COMPLETED" if clarification else "COMPLETED"
    await db.execute(text("""UPDATE external_client_information_request_submissions SET status=:submission,reviewed_by=:actor,reviewed_at=:now,review_decisions=CAST(:decisions AS jsonb),review_notes=:notes WHERE request_id=:id AND version=:version"""),{"submission":"CLARIFICATION_REQUESTED" if clarification else "CONFIRMED","actor":ctx["user_id"],"now":now,"decisions":json.dumps(body.decisions),"notes":body.notes,"id":request_id,"version":body.expected_version})
    await db.execute(text("UPDATE external_client_information_requests SET status=:status,reviewed_at=:now,updated_at=:now,version=version+1 WHERE id=:id"),{"status":status,"now":now,"id":request_id});await _information_audit(db,row,"CLARIFICATION_REQUESTED" if clarification else "REQUEST_COMPLETED","CONSULTANT",ctx["user_id"],now,{"decisions":body.decisions});await db.commit()
    return {"success":True,"data":{"status":status,"version":body.expected_version+1},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/information-requests/{request_id}/revoke")
async def revoke_client_information_request(request:Request,request_id:UUID,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=await _nutrition_scope(request,db,ctx)
    if denied:return denied
    now=datetime.now(timezone.utc);row=(await db.execute(text("""UPDATE external_client_information_requests SET status='REVOKED',revoked_at=:now,updated_at=:now,version=version+1 WHERE id=:id AND tenant_id=:tenant AND status IN ('CREATED','SENT','OPENED','PARTIALLY_COMPLETED') RETURNING *"""),{"now":now,"id":request_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not row:return error(request,409,"INFORMATION_REQUEST_NOT_ACTIVE","The request is missing or inactive")
    await _information_audit(db,row,"REQUEST_REVOKED","CONSULTANT",ctx["user_id"],now);await db.commit()
    return {"success":True,"data":{"id":str(request_id),"status":"REVOKED"},"error":None,"request_id":request.state.correlation_id}


async def _nutrition_scope(request,db,ctx):
    denied=external_only(request,ctx)
    if denied:return denied
    return await require_capability(request,db,ctx,"DIET_PLAN")


@app.get("/api/v1/practice-operations/clients/{client_id}/nutrition-assessment")
async def get_nutrition_assessment(request:Request,client_id:str,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=await _nutrition_scope(request,db,ctx)
    if denied:return denied
    row=(await db.execute(text("""SELECT a.*,v.id AS assessment_version_id,v.source_manifest,v.calculation_methodologies,
      v.calculations,v.input_completeness,v.clinical_safety_findings,v.nutrition_considerations,v.provenance,
      v.fingerprint_sha256,v.created_at AS version_created_at,v.reviewed_by,v.reviewed_at,v.assessment_data,v.readiness
      FROM external_nutrition_assessments a JOIN external_nutrition_assessment_versions v
      ON v.assessment_id=a.id AND v.version=a.current_version
      WHERE a.tenant_id=:tenant AND a.client_id=:client ORDER BY a.updated_at DESC LIMIT 1"""),
      {"tenant":ctx["tenant_id"],"client":client_id})).mappings().first()
    canonical,intake_updated_at=await _canonical_intake(db,ctx["tenant_id"],client_id)
    if not row:
        measurement_context=await _measurement_projection(db,ctx["tenant_id"],client_id)
        resolved=resolve_assessment(canonical,intake_updated_at=intake_updated_at)
        return {"success":True,"data":{"status":"NOT_STARTED","readiness_status":"NOT_STARTED","version":0,
          **resolved,"readiness":{"outcome":"NOT_STARTED","checklist":{},"outstanding_information":[]},
          "measurement_context":measurement_context,"history":[]},"error":None,"request_id":request.state.correlation_id}
    events=(await db.execute(text("""SELECT event_type,assessment_version,from_status,to_status,notes,actor_id,created_at
      FROM external_nutrition_assessment_events WHERE tenant_id=:tenant AND client_id=:client AND assessment_id=:assessment
      ORDER BY created_at DESC"""),{"tenant":ctx["tenant_id"],"client":client_id,"assessment":row["id"]})).mappings().all()
    data=_nutrition_assessment_projection(row);data["history"]=[{**dict(item),"created_at":item["created_at"].isoformat()} for item in events]
    data.update(resolve_assessment(canonical,dict(row["assessment_data"] or {}),intake_updated_at=intake_updated_at,
      professionally_confirmed=bool(row["reviewed_at"] or row["status"]=="REVIEWED")))
    measurement_context=await _measurement_projection(db,ctx["tenant_id"],client_id)
    saved_ids=sorted(str(item.get("source_id")) for item in (row["source_manifest"] or []) if item.get("source_type")=="MEASUREMENT")
    data["measurement_context"]=measurement_context
    data["measurement_context_changed"]=saved_ids!=measurement_context["source_measurement_ids"]
    if data["measurement_context_changed"]:
        data["stale"]=True;data["readiness_status"]="BLOCKED"
        data["readiness"]={**dict(data.get("readiness") or {}),"outcome":"BLOCKED",
          "outstanding_information":sorted(set(list((data.get("readiness") or {}).get("outstanding_information") or [])+["assessment_sources_changed"]))}
    return {"success":True,"data":data,"error":None,"request_id":request.state.correlation_id}


@app.put("/api/v1/practice-operations/clients/{client_id}/nutrition-assessment")
async def save_nutrition_assessment(request:Request,client_id:str,body:NutritionAssessmentSave,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=await _nutrition_scope(request,db,ctx)
    if denied:return denied
    measurement_context=await _measurement_projection(db,ctx["tenant_id"],client_id)
    submitted_sources=[source for source in body.sources if source.source_type!="MEASUREMENT"]
    canonical_sources=[AssessmentSource.model_validate(source) for source in assessment_measurement_sources(measurement_context)]
    sources=submitted_sources+canonical_sources
    current=(await db.execute(text("""SELECT id,current_version,status,authorised_consultant_id,stale FROM external_nutrition_assessments
      WHERE tenant_id=:tenant AND client_id=:client ORDER BY updated_at DESC LIMIT 1 FOR UPDATE"""),
      {"tenant":ctx["tenant_id"],"client":client_id})).mappings().first()
    if (current and current["current_version"]!=body.expected_version) or (not current and body.expected_version!=0):
        return error(request,409,"STALE_NUTRITION_ASSESSMENT","The Nutrition Assessment changed in another session. Refresh and try again")
    if current and str(current["authorised_consultant_id"])!=str(ctx["user_id"]) and ctx.get("role") not in DIET_PLAN_REVIEW_ROLES:
        return error(request,403,"NUTRITION_ASSESSMENT_ACCESS_DENIED","This Nutrition Assessment is assigned to another practitioner")
    if current and current["status"] not in {"DRAFT","CHANGES_REQUESTED"}:
        return error(request,409,"INVALID_NUTRITION_ASSESSMENT_TRANSITION","Only draft or changes-requested assessments can be edited")
    new_status="SUBMITTED" if body.action=="SUBMIT" else "DRAFT"
    readiness=diet_plan_readiness(body.profile,sources,workflow_status=new_status,
      stale=False,clinical_safety_findings=body.clinical_safety_findings)
    if measurement_context["requires_professional_confirmation"]:
        readiness["outcome"]="BLOCKED"
        readiness["outstanding_information"]=sorted(set(readiness["outstanding_information"]+["legacy_measurements_require_professional_confirmation"]))
    if body.action=="SUBMIT" and readiness["outcome"]=="INCOMPLETE":
        return error(request,409,"NUTRITION_ASSESSMENT_INCOMPLETE","Complete the outstanding information before submitting")
    calculations=measurement_context["calculations"]
    profile_data=body.profile.model_dump(mode="json")
    fingerprint=hashlib.sha256(json.dumps({"client_id":client_id,"profile":profile_data,
      "sources":[item.model_dump(mode="json") for item in sources],"calculations":calculations},sort_keys=True,default=str).encode()).hexdigest()
    duplicate=(await db.execute(text("SELECT assessment_id,version FROM external_nutrition_assessment_versions WHERE tenant_id=:tenant AND client_id=:client AND fingerprint_sha256=:fingerprint"),
      {"tenant":ctx["tenant_id"],"client":client_id,"fingerprint":fingerprint})).first()
    if duplicate:
        if current and duplicate.assessment_id==current["id"] and duplicate.version==current["current_version"]:
            readiness["outcome"]="BLOCKED" if readiness["outcome"]=="BLOCKED" else ("NEEDS_REVIEW" if new_status=="SUBMITTED" else readiness["outcome"])
            now=datetime.now(timezone.utc)
            if current["status"]!=new_status:
                await db.execute(text("""UPDATE external_nutrition_assessments SET status=:status,readiness_status=:readiness,updated_at=:now
                  WHERE id=:id AND tenant_id=:tenant AND current_version=:version"""),{"status":new_status,"readiness":readiness["outcome"],"now":now,"id":current["id"],"tenant":ctx["tenant_id"],"version":current["current_version"]})
                await _nutrition_event(db,assessment_id=current["id"],tenant_id=ctx["tenant_id"],client_id=client_id,version=current["current_version"],event_type=body.action,from_status=current["status"],to_status=new_status,actor_id=ctx["user_id"],now=now)
                await db.commit()
            return {"success":True,"data":{"id":str(current["id"]),"version":current["current_version"],"status":new_status,
              "readiness_status":readiness["outcome"],"assessment_data":profile_data,"readiness":readiness,"idempotent":current["status"]==new_status},"error":None,"request_id":request.state.correlation_id}
        return error(request,409,"ASSESSMENT_INPUTS_UNCHANGED","The saved assessment already represents these inputs")
    now=datetime.now(timezone.utc);assessment_id=current["id"] if current else uuid4();version=body.expected_version+1;version_id=uuid4()
    readiness["outcome"]="BLOCKED" if readiness["outcome"]=="BLOCKED" else ("NEEDS_REVIEW" if new_status=="SUBMITTED" else readiness["outcome"])
    if current:
        await db.execute(text("""UPDATE external_nutrition_assessments SET current_version=:version,status=:status,
          review_state='NOT_REVIEWED',readiness_status=:readiness,stale=FALSE,stale_reason=NULL,updated_at=:now
          WHERE id=:id AND tenant_id=:tenant AND current_version=:expected"""),
          {"version":version,"status":new_status,"readiness":readiness["outcome"],"now":now,"id":assessment_id,"tenant":ctx["tenant_id"],"expected":body.expected_version})
    else:
        await db.execute(text("""INSERT INTO external_nutrition_assessments
          (id,tenant_id,client_id,authorised_consultant_id,status,current_version,review_state,consent_state,stale,readiness_status,created_at,updated_at)
          VALUES (:id,:tenant,:client,:actor,:status,1,'NOT_REVIEWED','CONFIRMED',FALSE,:readiness,:now,:now)"""),
          {"id":assessment_id,"tenant":ctx["tenant_id"],"client":client_id,"actor":ctx["user_id"],"status":new_status,"readiness":readiness["outcome"],"now":now})
    await db.execute(text("""INSERT INTO external_nutrition_assessment_versions
      (id,assessment_id,tenant_id,client_id,version,source_manifest,calculation_methodologies,calculations,input_completeness,
       clinical_safety_findings,nutrition_considerations,provenance,fingerprint_sha256,created_by,created_at,assessment_data,readiness)
      VALUES (:vid,:id,:tenant,:client,:version,CAST(:manifest AS jsonb),CAST(:methods AS jsonb),CAST(:calculations AS jsonb),CAST(:complete AS jsonb),
       CAST(:safety AS jsonb),'[]'::jsonb,CAST(:provenance AS jsonb),:fingerprint,:actor,:now,CAST(:assessment AS jsonb),CAST(:readiness AS jsonb))"""),
      {"vid":version_id,"id":assessment_id,"tenant":ctx["tenant_id"],"client":client_id,"version":version,
       "manifest":json.dumps(source_manifest(sources)),"methods":json.dumps(CALCULATION_VERSIONS),"calculations":json.dumps(calculations),
       "complete":json.dumps({"complete":not readiness["outstanding_information"],"missing":readiness["outstanding_information"]}),
       "safety":json.dumps(body.clinical_safety_findings),"provenance":json.dumps({"owner":"PRACTICE_OPERATIONS","scope":"EXTERNAL_ONLY","measurement_context_fingerprint":measurement_context["measurement_context_fingerprint"]}),
       "fingerprint":fingerprint,"actor":ctx["user_id"],"now":now,"assessment":json.dumps(profile_data),"readiness":json.dumps(readiness)})
    for source in sources:
        await db.execute(text("""INSERT INTO external_nutrition_assessment_inputs
          (id,assessment_version_id,tenant_id,client_id,source_type,source_id,source_version,source_status,observed_at,provenance,created_at)
          VALUES (:id,:assessment_version,:tenant,:client,:type,:source,:source_version,:status,:observed,CAST(:provenance AS jsonb),:now)"""),
          {"id":uuid4(),"assessment_version":version_id,"tenant":ctx["tenant_id"],"client":client_id,"type":source.source_type,
           "source":source.source_id,"source_version":source.source_version,"status":source.status,"observed":source.observed_at,
           "provenance":json.dumps(source.provenance),"now":now})
    await _nutrition_event(db,assessment_id=assessment_id,tenant_id=ctx["tenant_id"],client_id=client_id,version=version,
      event_type=body.action,from_status=current["status"] if current else None,to_status=new_status,actor_id=ctx["user_id"],now=now)
    await db.commit()
    return {"success":True,"data":{"id":str(assessment_id),"version":version,"status":new_status,
      "readiness_status":readiness["outcome"],"assessment_data":profile_data,"readiness":readiness},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/nutrition-assessments/{assessment_id}/transition")
async def transition_nutrition_assessment(request:Request,assessment_id:UUID,body:NutritionAssessmentTransition,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=await _nutrition_scope(request,db,ctx)
    if denied:return denied
    current=(await db.execute(text("""SELECT a.client_id,a.current_version,a.status,a.stale,v.assessment_data,v.source_manifest,v.clinical_safety_findings
      FROM external_nutrition_assessments a JOIN external_nutrition_assessment_versions v ON v.assessment_id=a.id AND v.version=a.current_version
      WHERE a.id=:id AND a.tenant_id=:tenant FOR UPDATE"""),{"id":assessment_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not current:return error(request,404,"NUTRITION_ASSESSMENT_NOT_FOUND","Nutrition Assessment not found")
    if current["current_version"]!=body.expected_version:return error(request,409,"STALE_NUTRITION_ASSESSMENT","Refresh before changing assessment status")
    transitions={("SUBMITTED","START_REVIEW"):"IN_REVIEW",("IN_REVIEW","MARK_REVIEWED"):"REVIEWED",("SUBMITTED","MARK_REVIEWED"):"REVIEWED",
      ("SUBMITTED","REQUEST_CHANGES"):"CHANGES_REQUESTED",("IN_REVIEW","REQUEST_CHANGES"):"CHANGES_REQUESTED"}
    target=transitions.get((current["status"],body.action))
    if not target:return error(request,409,"INVALID_NUTRITION_ASSESSMENT_TRANSITION",f"Cannot {body.action.lower().replace('_',' ')} from {current['status'].lower()}")
    profile=NutritionProfile.model_validate(dict(current["assessment_data"] or {}));readiness=diet_plan_readiness(profile,list(current["source_manifest"] or []),workflow_status=target,stale=current["stale"],clinical_safety_findings=list(current["clinical_safety_findings"] or []))
    if target=="REVIEWED" and readiness["outcome"] not in {"BLOCKED","INCOMPLETE"}:readiness["outcome"]="READY"
    review={"IN_REVIEW":"IN_REVIEW","REVIEWED":"REVIEWED","CHANGES_REQUESTED":"CHANGES_REQUESTED"}[target];now=datetime.now(timezone.utc)
    await db.execute(text("""UPDATE external_nutrition_assessments SET status=:status,review_state=:review,readiness_status=:readiness,updated_at=:now
      WHERE id=:id AND tenant_id=:tenant AND current_version=:version"""),{"status":target,"review":review,"readiness":readiness["outcome"],"now":now,"id":assessment_id,"tenant":ctx["tenant_id"],"version":body.expected_version})
    if target=="REVIEWED":await db.execute(text("UPDATE external_nutrition_assessment_versions SET reviewed_by=:actor,reviewed_at=:now,readiness=CAST(:readiness AS jsonb) WHERE assessment_id=:id AND version=:version"),{"actor":ctx["user_id"],"now":now,"readiness":json.dumps(readiness),"id":assessment_id,"version":body.expected_version})
    await _nutrition_event(db,assessment_id=assessment_id,tenant_id=ctx["tenant_id"],client_id=current["client_id"],version=body.expected_version,event_type=body.action,from_status=current["status"],to_status=target,actor_id=ctx["user_id"],now=now,notes=body.notes)
    await db.commit();return {"success":True,"data":{"id":str(assessment_id),"version":body.expected_version,"status":target,"review_state":review,"readiness_status":readiness["outcome"],"readiness":readiness},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/clients/{client_id}/nutrition-assessments",status_code=201)
async def create_nutrition_assessment(request:Request,client_id:str,body:NutritionAssessmentCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=await _nutrition_scope(request,db,ctx)
    if denied:return denied
    try:
        calculations=measurement_calculations(body.sources)
        fingerprint=assessment_fingerprint(client_id,body.sources,calculations)
    except ValueError as exc:
        return error(request,422,"UNSAFE_NUTRITION_ASSESSMENT_INPUT",str(exc))
    now=datetime.now(timezone.utc);assessment_id=body.assessment_id or uuid4()
    existing=(await db.execute(text("""SELECT id,current_version,authorised_consultant_id FROM external_nutrition_assessments
      WHERE id=:id AND tenant_id=:tenant AND client_id=:client FOR UPDATE"""),{"id":assessment_id,"tenant":ctx["tenant_id"],"client":client_id})).mappings().first()
    if body.assessment_id and not existing:return error(request,404,"NUTRITION_ASSESSMENT_NOT_FOUND","Nutrition Assessment not found")
    if existing and str(existing["authorised_consultant_id"])!=str(ctx["user_id"]) and ctx.get("role") not in DIET_PLAN_REVIEW_ROLES:
        return error(request,403,"NUTRITION_ASSESSMENT_ACCESS_DENIED","This Nutrition Assessment is assigned to another practitioner")
    duplicate=(await db.execute(text("""SELECT assessment_id,version FROM external_nutrition_assessment_versions
      WHERE tenant_id=:tenant AND client_id=:client AND fingerprint_sha256=:fingerprint"""),
      {"tenant":ctx["tenant_id"],"client":client_id,"fingerprint":fingerprint})).mappings().first()
    if duplicate:
        return error(request,409,"ASSESSMENT_INPUTS_UNCHANGED","An immutable assessment version already represents these inputs")
    version=(existing["current_version"]+1) if existing else 1;version_id=uuid4()
    manifest=source_manifest(body.sources)
    completeness={"source_types":sorted({source.source_type for source in body.sources}),"source_count":len(body.sources),"complete":body.consent_state=="CONFIRMED"}
    provenance={"owner":"PRACTICE_OPERATIONS","scope":"EXTERNAL_ONLY","created_by":ctx["user_id"],"immutable":True}
    if existing:
        await db.execute(text("""UPDATE external_nutrition_assessments SET current_version=:version,status='DRAFT',
          review_state=:review,consent_state=:consent,stale=FALSE,stale_reason=NULL,updated_at=:now
          WHERE id=:id AND tenant_id=:tenant AND client_id=:client"""),{"version":version,"review":body.professional_review_state,"consent":body.consent_state,"now":now,"id":assessment_id,"tenant":ctx["tenant_id"],"client":client_id})
    else:
        await db.execute(text("""INSERT INTO external_nutrition_assessments
          (id,tenant_id,client_id,authorised_consultant_id,status,current_version,review_state,consent_state,stale,created_at,updated_at)
          VALUES (:id,:tenant,:client,:actor,'DRAFT',1,:review,:consent,FALSE,:now,:now)"""),{"id":assessment_id,"tenant":ctx["tenant_id"],"client":client_id,"actor":ctx["user_id"],"review":body.professional_review_state,"consent":body.consent_state,"now":now})
    await db.execute(text("""INSERT INTO external_nutrition_assessment_versions
      (id,assessment_id,tenant_id,client_id,version,source_manifest,calculation_methodologies,calculations,input_completeness,
       clinical_safety_findings,nutrition_considerations,provenance,fingerprint_sha256,created_by,created_at)
      VALUES (:vid,:id,:tenant,:client,:version,CAST(:manifest AS jsonb),CAST(:methods AS jsonb),CAST(:calculations AS jsonb),CAST(:completeness AS jsonb),
       CAST(:safety AS jsonb),CAST(:considerations AS jsonb),CAST(:provenance AS jsonb),:fingerprint,:actor,:now)"""),
      {"vid":version_id,"id":assessment_id,"tenant":ctx["tenant_id"],"client":client_id,"version":version,"manifest":json.dumps(manifest),"methods":json.dumps(CALCULATION_VERSIONS),"calculations":json.dumps(calculations),"completeness":json.dumps(completeness),"safety":json.dumps(body.clinical_safety_findings),"considerations":json.dumps([item.model_dump() for item in body.nutrition_considerations]),"provenance":json.dumps(provenance),"fingerprint":fingerprint,"actor":ctx["user_id"],"now":now})
    for source in body.sources:
        await db.execute(text("""INSERT INTO external_nutrition_assessment_inputs
          (id,assessment_version_id,tenant_id,client_id,source_type,source_id,source_version,source_status,observed_at,provenance,created_at)
          VALUES (:id,:version,:tenant,:client,:type,:source,:source_version,:status,:observed,CAST(:provenance AS jsonb),:now)"""),
          {"id":uuid4(),"version":version_id,"tenant":ctx["tenant_id"],"client":client_id,"type":source.source_type,"source":source.source_id,"source_version":source.source_version,"status":source.status,"observed":source.observed_at,"provenance":json.dumps(source.provenance),"now":now})
    await db.commit()
    return {"success":True,"data":{"id":str(assessment_id),"version":version,"status":"DRAFT","fingerprint":fingerprint,"calculations":calculations},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/nutrition-assessments/{assessment_id}/review")
async def review_nutrition_assessment(request:Request,assessment_id:UUID,body:AssessmentReview,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=await _nutrition_scope(request,db,ctx)
    if denied:return denied
    if body.decision!="START_REVIEW" and ctx.get("role") not in DIET_PLAN_REVIEW_ROLES:return error(request,403,"NUTRITION_REVIEW_AUTHORITY_REQUIRED","Senior review authority is required")
    states={"START_REVIEW":("IN_REVIEW","IN_REVIEW"),"APPROVE":("REVIEWED","REVIEWED"),"REQUEST_CHANGES":("CHANGES_REQUESTED","CHANGES_REQUESTED")};status,review=states[body.decision];now=datetime.now(timezone.utc)
    row=(await db.execute(text("""UPDATE external_nutrition_assessments SET status=:status,review_state=:review,updated_at=:now
      WHERE id=:id AND tenant_id=:tenant AND current_version=:version RETURNING client_id,current_version"""),{"status":status,"review":review,"now":now,"id":assessment_id,"tenant":ctx["tenant_id"],"version":body.expected_version})).mappings().first()
    if not row:return error(request,409,"STALE_OR_MISSING_ASSESSMENT","Assessment changed or is unavailable")
    if body.decision=="APPROVE":await db.execute(text("UPDATE external_nutrition_assessment_versions SET reviewed_by=:actor,reviewed_at=:now WHERE assessment_id=:id AND tenant_id=:tenant AND version=:version"),{"actor":ctx["user_id"],"now":now,"id":assessment_id,"tenant":ctx["tenant_id"],"version":body.expected_version})
    await db.commit();return {"success":True,"data":{"id":str(assessment_id),"version":body.expected_version,"status":status,"review_state":review},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/nutrition-assessments/{assessment_id}/stale")
async def mark_nutrition_assessment_stale(request:Request,assessment_id:UUID,body:AssessmentStale,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=await _nutrition_scope(request,db,ctx)
    if denied:return denied
    now=datetime.now(timezone.utc);row=(await db.execute(text("""UPDATE external_nutrition_assessments SET stale=TRUE,stale_reason=:reason,updated_at=:now
      WHERE id=:id AND tenant_id=:tenant RETURNING client_id"""),{"reason":body.reason,"now":now,"id":assessment_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not row:return error(request,404,"NUTRITION_ASSESSMENT_NOT_FOUND","Nutrition Assessment not found")
    await db.execute(text("""INSERT INTO external_nutrition_staleness_events
      (id,assessment_id,tenant_id,client_id,source_type,source_id,source_version,reason,created_by,created_at)
      VALUES (:event,:assessment,:tenant,:client,:type,:source,:version,:reason,:actor,:now)"""),{"event":uuid4(),"assessment":assessment_id,"tenant":ctx["tenant_id"],"client":row["client_id"],"type":body.source_type,"source":body.source_id,"version":body.source_version,"reason":body.reason,"actor":ctx["user_id"],"now":now})
    await db.commit();return {"success":True,"data":{"id":str(assessment_id),"stale":True,"reason":body.reason},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/clients/{client_id}/diet-plan-assessment-links",status_code=201)
async def bind_diet_plan_assessment(request:Request,client_id:str,body:DietPlanAssessmentBind,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=await _nutrition_scope(request,db,ctx)
    if denied:return denied
    assessment=(await db.execute(text("""SELECT a.id,a.current_version,a.status,a.stale,v.fingerprint_sha256,v.calculation_methodologies
      FROM external_nutrition_assessments a JOIN external_nutrition_assessment_versions v ON v.assessment_id=a.id AND v.version=:version
      WHERE a.id=:id AND a.tenant_id=:tenant AND a.client_id=:client"""),{"version":body.assessment_version,"id":body.assessment_id,"tenant":ctx["tenant_id"],"client":client_id})).mappings().first()
    if not assessment:return error(request,404,"ASSESSMENT_BINDING_INVALID","Assessment does not belong to this tenant and client")
    if assessment["status"]!="REVIEWED" or assessment["stale"]:return error(request,409,"ASSESSMENT_NOT_READY","A reviewed current assessment is required")
    now=datetime.now(timezone.utc)
    try:await db.execute(text("""INSERT INTO external_diet_plan_assessment_links
      (id,tenant_id,client_id,external_plan_id,external_plan_version,assessment_id,assessment_version,source_fingerprint_sha256,
       calculation_methodologies,plan_state,legacy_lineage_state,created_by,created_at)
      VALUES (:id,:tenant,:client,:plan,:plan_version,:assessment,:assessment_version,:fingerprint,CAST(:methods AS jsonb),:state,'LINKED',:actor,:now)"""),{"id":uuid4(),"tenant":ctx["tenant_id"],"client":client_id,"plan":body.external_plan_id,"plan_version":body.external_plan_version,"assessment":assessment["id"],"assessment_version":body.assessment_version,"fingerprint":assessment["fingerprint_sha256"],"methods":json.dumps(dict(assessment["calculation_methodologies"] or {})),"state":body.plan_state,"actor":ctx["user_id"],"now":now})
    except IntegrityError:await db.rollback();return error(request,409,"PLAN_ASSESSMENT_LINK_EXISTS","This plan version already has assessment lineage")
    await db.commit();return {"success":True,"data":{"client_id":client_id,"external_plan_id":body.external_plan_id,"external_plan_version":body.external_plan_version,"assessment_id":body.assessment_id,"assessment_version":body.assessment_version},"error":None,"request_id":request.state.correlation_id}


@app.put("/api/v1/practice-operations/clients/{client_id}/clinical-document-links/{document_reference}")
async def upsert_clinical_document_link(request:Request,client_id:str,document_reference:str,body:ClinicalDocumentLink,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=await _nutrition_scope(request,db,ctx)
    if denied:return denied
    if body.document_reference!=document_reference:return error(request,422,"DOCUMENT_REFERENCE_MISMATCH","Document reference does not match the route")
    now=datetime.now(timezone.utc)
    await db.execute(text("""INSERT INTO external_clinical_document_links
      (id,tenant_id,client_id,document_reference,health_record_reference,extraction_run_reference,observation_references,source_available,source_status,created_by,created_at,updated_at)
      VALUES (:id,:tenant,:client,:document,:health,:extraction,CAST(:observations AS jsonb),:available,:status,:actor,:now,:now)
      ON CONFLICT(tenant_id,client_id,document_reference) DO UPDATE SET health_record_reference=EXCLUDED.health_record_reference,
      extraction_run_reference=EXCLUDED.extraction_run_reference,observation_references=EXCLUDED.observation_references,
      source_available=EXCLUDED.source_available,source_status=EXCLUDED.source_status,updated_at=EXCLUDED.updated_at"""),{"id":uuid4(),"tenant":ctx["tenant_id"],"client":client_id,"document":document_reference,"health":body.health_record_reference,"extraction":body.extraction_run_reference,"observations":json.dumps(body.observation_references),"available":body.source_available,"status":body.source_status,"actor":ctx["user_id"],"now":now})
    await db.commit();return {"success":True,"data":body.model_dump(),"error":None,"request_id":request.state.correlation_id}


@app.get("/api/v1/practice-operations/clients/{client_id}/clinical-document-links")
async def list_clinical_document_links(request:Request,client_id:str,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=await _nutrition_scope(request,db,ctx)
    if denied:return denied
    rows=(await db.execute(text("""SELECT document_reference,health_record_reference,extraction_run_reference,
      observation_references,source_available,source_status,created_at,updated_at
      FROM external_clinical_document_links WHERE tenant_id=:tenant AND client_id=:client ORDER BY updated_at DESC"""),
      {"tenant":ctx["tenant_id"],"client":client_id})).mappings().all()
    return {"success":True,"data":{"items":[dict(row) for row in rows]},"error":None,"request_id":request.state.correlation_id}


@app.get("/api/v1/practice-operations/internal-client-profiles/{client_id}")
async def get_internal_client_profile_enrichment(request: Request, client_id: str, ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied = internal_profile_only(request, ctx)
    if denied: return denied
    row = (await db.execute(text("""SELECT values,version,schema_version,provenance,updated_at,updated_by
      FROM internal_client_profile_enrichments WHERE tenant_id=:tenant AND client_id=:client"""),
      {"tenant":ctx["tenant_id"],"client":client_id})).mappings().first()
    if not row:
        return {"success":True,"data":internal_profile_projection({},0,{"source":"INTERNAL_ENRICHMENT","tenant_id":ctx["tenant_id"],"client_id":client_id}),"error":None,"request_id":request.state.correlation_id}
    provenance={**dict(row["provenance"] or {}),"source":"INTERNAL_ENRICHMENT","tenant_id":ctx["tenant_id"],"client_id":client_id,"updated_at":row["updated_at"].isoformat(),"updated_by":row["updated_by"]}
    return {"success":True,"data":internal_profile_projection(dict(row["values"] or {}),row["version"],provenance),"error":None,"request_id":request.state.correlation_id}


@app.put("/api/v1/practice-operations/internal-client-profiles/{client_id}")
async def update_internal_client_profile_enrichment(request: Request, client_id: str, body: InternalClientProfileEnrichmentUpdate, ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied = internal_profile_only(request, ctx, write=True)
    if denied: return denied
    try: values = validate_enrichment(body.values)
    except (TypeError, ValueError) as exc: return error(request,422,"INVALID_INTERNAL_PROFILE_ENRICHMENT",str(exc))
    now=datetime.now(timezone.utc)
    event={"event":"INTERNAL_CLIENT_PROFILE_ENRICHMENT_UPDATED","actor_id":ctx["user_id"],"timestamp":now.isoformat(),"expected_version":body.expected_version,"changed_fields":sorted(values)}
    if body.expected_version == 0:
        try:
            row=(await db.execute(text("""INSERT INTO internal_client_profile_enrichments
              (tenant_id,client_id,values,version,schema_version,provenance,audit_history,created_by,updated_by,created_at,updated_at)
              VALUES (:tenant,:client,CAST(:values AS jsonb),1,1,CAST(:provenance AS jsonb),CAST(:audit AS jsonb),:actor,:actor,:now,:now)
              RETURNING values,version,provenance,updated_at"""),{"tenant":ctx["tenant_id"],"client":client_id,"values":json.dumps(values),"provenance":json.dumps({"source":"INTERNAL_ENRICHMENT"}),"audit":json.dumps([event]),"actor":ctx["user_id"],"now":now})).mappings().one()
        except IntegrityError:
            await db.rollback();return error(request,409,"STALE_WRITE","The profile changed in another session. Refresh and try again")
    else:
        current=(await db.execute(text("SELECT values FROM internal_client_profile_enrichments WHERE tenant_id=:tenant AND client_id=:client AND version=:version"),{"tenant":ctx["tenant_id"],"client":client_id,"version":body.expected_version})).mappings().first()
        if not current:
            return error(request,409,"STALE_WRITE","The profile changed in another session. Refresh and try again")
        merged_values=merge_enrichment(dict(current["values"] or {}),values)
        row=(await db.execute(text("""UPDATE internal_client_profile_enrichments SET
          values=CAST(:values AS jsonb),version=version+1,updated_by=:actor,updated_at=:now,
          provenance=provenance || CAST(:provenance AS jsonb),audit_history=audit_history || CAST(:audit AS jsonb)
          WHERE tenant_id=:tenant AND client_id=:client AND version=:version RETURNING values,version,provenance,updated_at"""),{"tenant":ctx["tenant_id"],"client":client_id,"values":json.dumps(merged_values),"provenance":json.dumps({"source":"INTERNAL_ENRICHMENT","last_actor_id":ctx["user_id"]}),"audit":json.dumps([event]),"actor":ctx["user_id"],"now":now,"version":body.expected_version})).mappings().first()
        if not row:
            await db.rollback();return error(request,409,"STALE_WRITE","The profile changed in another session. Refresh and try again")
    await db.commit()
    provenance={**dict(row["provenance"] or {}),"source":"INTERNAL_ENRICHMENT","tenant_id":ctx["tenant_id"],"client_id":client_id,"updated_at":row["updated_at"].isoformat(),"updated_by":ctx["user_id"]}
    return {"success":True,"data":internal_profile_projection(dict(row["values"] or {}),row["version"],provenance),"error":None,"request_id":request.state.correlation_id}


@app.exception_handler(QaDelegationError)
async def qa_delegation_error(_request: Request, exc: QaDelegationError):
    return JSONResponse(status_code=403, content={"success": False, "error": {"code": "QA_DELEGATION_DENIED", "safe_message": str(exc)}})


@app.put("/internal/qa/external-practice/configuration")
async def configure_external_qa_practice(request: Request, body: PracticeConfigurationUpdate,
    authority: QaDelegation = Depends(require_qa_delegation), db: AsyncSession = Depends(get_db)):
    if body.profession != authority.profession_code or body.profession not in SUPPORTED_PROFESSIONS:
        return error(request, 422, "QA_PROFESSION_SCOPE_MISMATCH", "The signed profession scope does not match the request")
    requested = set(body.capabilities) or PROFESSION_DEFAULTS[body.profession]
    if requested - ALL_CAPABILITIES:
        return error(request, 400, "UNKNOWN_CAPABILITY", "One or more capabilities are not recognised")
    terminology, now = TERMINOLOGY[body.profession], datetime.now(timezone.utc)
    row = (await db.execute(text("""INSERT INTO practice_tenant_configuration
      (tenant_id,profession,capabilities,terminology,profile,version,updated_by,updated_at)
      VALUES (:tenant,:profession,CAST(:capabilities AS jsonb),CAST(:terminology AS jsonb),CAST(:profile AS jsonb),1,:actor,:now)
      ON CONFLICT (tenant_id) DO UPDATE SET profession=EXCLUDED.profession,capabilities=EXCLUDED.capabilities,
      terminology=EXCLUDED.terminology,profile=EXCLUDED.profile,version=practice_tenant_configuration.version+1,
      updated_by=EXCLUDED.updated_by,updated_at=EXCLUDED.updated_at
      RETURNING profession,capabilities,terminology,profile,version"""), {
        "tenant": authority.tenant_id, "profession": body.profession, "capabilities": json.dumps(sorted(requested)),
        "terminology": json.dumps(terminology), "profile": json.dumps(body.profile), "actor": authority.actor_id, "now": now,
    })).mappings().one()
    profile_id = (await db.execute(text("""INSERT INTO external_profession_profiles
      (id,tenant_id,profession_code,display_name,terminology,active,version,created_by,created_at,updated_at)
      VALUES (:id,:tenant,:profession,:display,CAST(:terminology AS jsonb),TRUE,1,:actor,:now,:now)
      ON CONFLICT (tenant_id,profession_code) DO UPDATE SET terminology=EXCLUDED.terminology,active=TRUE,
      version=external_profession_profiles.version+1,updated_at=EXCLUDED.updated_at RETURNING id"""), {
        "id": uuid4(), "tenant": authority.tenant_id, "profession": body.profession,
        "display": body.profession.replace("_", " ").title(), "terminology": json.dumps(terminology),
        "actor": authority.actor_id, "now": now,
    })).scalar_one()
    await db.execute(text("DELETE FROM external_profession_capability_profiles WHERE tenant_id=:tenant AND profession_profile_id=:profile"), {"tenant": authority.tenant_id, "profile": profile_id})
    for capability in sorted(requested):
        await db.execute(text("""INSERT INTO external_profession_capability_profiles
          (id,profession_profile_id,tenant_id,capability_code,enabled,created_at)
          VALUES (:id,:profile,:tenant,:capability,TRUE,:now)"""), {
            "id": uuid4(), "profile": profile_id, "tenant": authority.tenant_id, "capability": capability, "now": now,
        })
    await db.commit()
    return {"success": True, "data": dict(row), "error": None, "request_id": request.state.correlation_id}


def _profession_token_error(request: Request, exc: Exception):
    message = str(exc)
    code = "PROFESSION_INTAKE_TOKEN_EXPIRED" if "expired" in message.lower() else "INVALID_PROFESSION_INTAKE_TOKEN"
    return error(request, 401, code, "This profession intake link is invalid or has expired")


async def _profession_token_scope(request: Request, token: str, action: str, db: AsyncSession):
    try:
        claims = validate_token(token, secret=get_settings().profession_intake_secret, required_action=action)
    except IntakeTokenError as exc:
        return None, _profession_token_error(request, exc)
    row = (await db.execute(text("""SELECT id,tenant_id,client_id,profession_code,template_version_id,status,
      completion_percent,review_state,token_version,token_expires_at FROM external_client_intake_instances
      WHERE id=CAST(:id AS uuid) AND tenant_id=:tenant_id AND client_id=:client_id
        AND profession_code=:profession_code AND template_version_id=CAST(:template_version_id AS uuid)
        AND token_hash=:token_hash AND token_version=:token_version"""), {
        "id": claims.intake_instance_id, "tenant_id": claims.tenant_id, "client_id": claims.client_id,
        "profession_code": claims.profession_code, "template_version_id": claims.template_version_id,
        "token_hash": token_hash(token), "token_version": claims.token_version,
    })).mappings().first()
    now = datetime.now(timezone.utc)
    if not row or row["status"] in {"REVOKED", "EXPIRED"} or row["token_expires_at"] <= now:
        return None, error(request, 401, "INVALID_PROFESSION_INTAKE_SCOPE", "This profession intake link is invalid or has expired")
    return dict(row), None


@app.middleware("http")
async def correlation(request: Request, call_next):
    request.state.correlation_id = request.headers.get("X-Request-Id") or str(uuid4())
    response = await call_next(request)
    response.headers["X-Request-Id"] = request.state.correlation_id
    return response


@app.get("/health")
async def health(): return {"status": "ok", "service": get_settings().app_name}


@app.get("/readiness")
async def readiness(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1")); return {"status": "ready"}


@app.get("/version")
async def version():
    settings=get_settings(); return {"service": settings.app_name, "version": settings.app_version, "commit_sha": settings.app_commit_sha}


# Keep the literal collection route ahead of the generic ``/{resource}``
# routes below. FastAPI resolves equal-method routes in registration order;
# without this guard, ``GET /templates`` and ``POST /templates`` are consumed
# by the generic practice-resource handlers and return RESOURCE_NOT_FOUND (or
# validate against the wrong request contract) before the template library can
# run. The implementation functions are resolved when the request is handled.
@app.get("/api/v1/practice-operations/templates")
async def template_collection_route(request:Request,scope:str|None=None,template_type:str|None=None,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    return await list_templates(request,scope,template_type,ctx,db)


@app.post("/api/v1/practice-operations/templates",status_code=201)
async def template_collection_create_route(request:Request,body:TemplateCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    return await create_template(request,body,ctx,db)


# Keep the P23 literal collection route ahead of the legacy one-segment
# resource route for the same Starlette registration-order reason.
@app.get("/api/v1/practice-operations/documents")
async def document_collection_route(request:Request,client_id:str|None=None,category:str|None=None,status:str|None=None,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    return await list_documents(request,client_id,category,status,ctx,db)


@app.post("/api/v1/practice-operations/documents",status_code=201)
async def document_collection_create_route(request:Request,body:DocumentCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    return await create_document(request,body,ctx,db)


@app.get("/api/v1/practice-operations/{resource}")
async def list_resources(request: Request, resource: str, client_id: str | None = None, status: str | None = None, cursor: UUID | None = None, limit: int = Query(25, ge=1, le=100), ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied: return denied
    if resource == "configuration":
        return {"success":True,"data":await configuration(db,ctx),"error":None,"request_id":request.state.correlation_id}
    table=RESOURCE_TABLES.get(resource)
    if not table: return error(request, 404, "RESOURCE_NOT_FOUND", "Practice resource not found")
    capability = RESOURCE_CAPABILITY.get(resource)
    if capability:
        capability_denied = await require_capability(request, db, ctx, capability)
        if capability_denied: return capability_denied
    clauses=["tenant_id = :tenant_id"]; params={"tenant_id":ctx["tenant_id"], "limit":limit+1}
    if client_id: clauses.append("client_id = :client_id"); params["client_id"]=client_id
    if status: clauses.append("status = :status"); params["status"]=status
    if cursor: clauses.append("id < :cursor"); params["cursor"]=cursor
    rows=(await db.execute(text(f"SELECT id, tenant_id, client_id, type, title, status, due_at, payload, version, created_at, updated_at FROM {table} WHERE {' AND '.join(clauses)} ORDER BY id DESC LIMIT :limit"), params)).mappings().all()
    more=len(rows)>limit; items=[dict(row) for row in rows[:limit]]
    return {"success":True,"data":{"items":items,"next_cursor":str(items[-1]["id"]) if more else None},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/{resource}", status_code=201)
async def create_resource(request: Request, resource: str, body: ResourceCreate, idempotency_key: str | None=Header(None, alias="Idempotency-Key"), ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied: return denied
    if not idempotency_key: return error(request,400,"IDEMPOTENCY_KEY_REQUIRED","Idempotency-Key is required")
    table=RESOURCE_TABLES.get(resource)
    if not table: return error(request,404,"RESOURCE_NOT_FOUND","Practice resource not found")
    capability = RESOURCE_CAPABILITY.get(resource)
    if capability:
        capability_denied = await require_capability(request, db, ctx, capability)
        if capability_denied: return capability_denied
    existing=(await db.execute(text(f"SELECT * FROM {table} WHERE tenant_id=:tenant_id AND idempotency_key=:key"),{"tenant_id":ctx["tenant_id"],"key":idempotency_key})).mappings().first()
    if existing: return {"success":True,"data":dict(existing),"error":None,"request_id":request.state.correlation_id}
    item_id=uuid4(); event_id=uuid4(); now=datetime.now(timezone.utc); event_type=CREATE_EVENTS.get(resource, f"{resource.rstrip('s').replace('-','_').upper()}_CREATED")
    params={"id":item_id,"tenant_id":ctx["tenant_id"],"client_id":body.client_id,"type":body.type,"title":body.title,"status":body.status,"due_at":body.due_at,"payload":json.dumps(body.payload),"actor":ctx["user_id"],"key":idempotency_key,"now":now}
    await db.execute(text(f"INSERT INTO {table} (id,tenant_id,client_id,type,title,status,due_at,payload,version,created_by,idempotency_key,created_at,updated_at) VALUES (:id,:tenant_id,:client_id,:type,:title,:status,:due_at,CAST(:payload AS jsonb),1,:actor,:key,:now,:now)"),params)
    await db.execute(text("INSERT INTO service_outbox_events (id,tenant_id,event_type,aggregate_type,aggregate_id,payload,status,created_at) VALUES (:id,:tenant_id,:event_type,:aggregate_type,:aggregate_id,CAST(:payload AS jsonb),'PENDING',:now)"),{"id":event_id,"tenant_id":ctx["tenant_id"],"event_type":event_type,"aggregate_type":resource,"aggregate_id":item_id,"payload":json.dumps({"client_id":body.client_id}),"now":now})
    await db.execute(text("""INSERT INTO practice_timeline_events
      (id,tenant_id,client_id,event_type,source_type,source_id,summary,metadata,occurred_at)
      VALUES (:timeline_id,:tenant_id,:client_id,:event_type,:source_type,:source_id,:summary,CAST(:metadata AS jsonb),:now)
      ON CONFLICT (tenant_id,event_type,source_type,source_id) DO NOTHING"""), {"timeline_id":uuid4(),"tenant_id":ctx["tenant_id"],"client_id":body.client_id,"event_type":event_type,"source_type":resource.upper(),"source_id":str(item_id),"summary":body.title,"metadata":json.dumps({"status":body.status}),"now":now})
    return {"success":True,"data":{"id":str(item_id),**body.model_dump(),"version":1},"error":None,"request_id":request.state.correlation_id}


@app.patch("/api/v1/practice-operations/{resource}/{item_id}")
async def update_resource(request: Request, resource: str, item_id: UUID, body: ResourceUpdate, ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied: return denied
    table=RESOURCE_TABLES.get(resource)
    if not table: return error(request,404,"RESOURCE_NOT_FOUND","Practice resource not found")
    capability = RESOURCE_CAPABILITY.get(resource)
    if capability:
        capability_denied = await require_capability(request, db, ctx, capability)
        if capability_denied: return capability_denied
    values=body.model_dump(exclude_none=True); expected=values.pop("version"); values["updated_at"]=datetime.now(timezone.utc)
    if "payload" in values: values["payload"]=json.dumps(values["payload"])
    assignments=[]
    for key in values: assignments.append(f"{key} = CAST(:{key} AS jsonb)" if key=="payload" else f"{key} = :{key}")
    assignments.append("version = version + 1")
    result=await db.execute(text(f"UPDATE {table} SET {', '.join(assignments)} WHERE id=:id AND tenant_id=:tenant_id AND version=:version RETURNING id, version, status, updated_at"),{"id":item_id,"tenant_id":ctx["tenant_id"],"version":expected,**values})
    row=result.mappings().first()
    if not row: return error(request,409,"STALE_WRITE","This record changed. Refresh and retry")
    event_type = COMPLETE_EVENTS.get(resource) if row["status"] == "COMPLETED" else None
    if event_type:
        await db.execute(text("INSERT INTO service_outbox_events (id,tenant_id,event_type,aggregate_type,aggregate_id,payload,status,created_at) VALUES (:event_id,:tenant_id,:event_type,:aggregate_type,:aggregate_id,CAST(:payload AS jsonb),'PENDING',:now)"), {"event_id": uuid4(), "tenant_id": ctx["tenant_id"], "event_type": event_type, "aggregate_type": resource, "aggregate_id": item_id, "payload": json.dumps({"status": row["status"]}), "now": datetime.now(timezone.utc)})
        source = (await db.execute(text(f"SELECT client_id,title FROM {table} WHERE id=:id AND tenant_id=:tenant_id"), {"id":item_id,"tenant_id":ctx["tenant_id"]})).mappings().first()
        if source:
            await db.execute(text("""INSERT INTO practice_timeline_events
              (id,tenant_id,client_id,event_type,source_type,source_id,summary,metadata,occurred_at)
              VALUES (:timeline_id,:tenant_id,:client_id,:event_type,:source_type,:source_id,:summary,CAST(:metadata AS jsonb),:now)
              ON CONFLICT (tenant_id,event_type,source_type,source_id) DO NOTHING"""), {"timeline_id":uuid4(),"tenant_id":ctx["tenant_id"],"client_id":source["client_id"],"event_type":event_type,"source_type":resource.upper(),"source_id":f"{item_id}:completed","summary":source["title"],"metadata":json.dumps({"status":row["status"]}),"now":datetime.now(timezone.utc)})
    return {"success":True,"data":dict(row),"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/consultations/{item_id}/transition")
async def transition_consultation(request: Request, item_id: UUID, body: ConsultationTransition, ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied = external_only(request, ctx)
    if denied: return denied
    row = (await db.execute(text("SELECT status,payload FROM practice_consultations WHERE id=:id AND tenant_id=:tenant_id"), {"id": item_id, "tenant_id": ctx["tenant_id"]})).mappings().first()
    if not row: return error(request, 404, "CONSULTATION_NOT_FOUND", "Consultation not found")
    try: target = consultation_transition(row["status"], body.action)
    except ValueError as exc: return error(request, 409, "INVALID_CONSULTATION_TRANSITION", str(exc))
    payload = dict(row["payload"] or {})
    for key in ("scheduled_at", "duration_minutes", "outcome", "next_followup_at"):
        value = getattr(body, key)
        if value is not None: payload[key] = value.isoformat() if isinstance(value, datetime) else value
    now = datetime.now(timezone.utc)
    changed = (await db.execute(text("""UPDATE practice_consultations SET status=:status,payload=CAST(:payload AS jsonb),version=version+1,updated_at=:now
      WHERE id=:id AND tenant_id=:tenant_id AND version=:version RETURNING id,status,version,payload,updated_at"""),
      {"status": target, "payload": json.dumps(payload), "now": now, "id": item_id, "tenant_id": ctx["tenant_id"], "version": body.version})).mappings().first()
    if not changed: return error(request, 409, "STALE_WRITE", "This record changed. Refresh and retry")
    event_type = "CONSULTATION_COMPLETED" if target == "COMPLETED" else ("CONSULTATION_SCHEDULED" if body.action == "RESCHEDULE" else f"CONSULTATION_{target}")
    await db.execute(text("INSERT INTO service_outbox_events (id,tenant_id,event_type,aggregate_type,aggregate_id,payload,status,created_at) VALUES (:event_id,:tenant_id,:event_type,'consultation',:id,CAST(:payload AS jsonb),'PENDING',:now)"),
                     {"event_id": uuid4(), "tenant_id": ctx["tenant_id"], "event_type": event_type, "id": item_id, "payload": json.dumps({"status": target}), "now": now})
    return {"success": True, "data": dict(changed), "error": None, "request_id": request.state.correlation_id}


@app.post("/api/v1/practice-operations/goals/{goal_id}/progress", status_code=201)
async def append_goal_progress(request: Request, goal_id: UUID, body: GoalProgressCreate, idempotency_key: str | None=Header(None, alias="Idempotency-Key"), ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied = external_only(request, ctx)
    if denied: return denied
    if not idempotency_key: return error(request, 400, "IDEMPOTENCY_KEY_REQUIRED", "Idempotency-Key is required")
    goal = (await db.execute(text("SELECT client_id FROM practice_goals WHERE id=:id AND tenant_id=:tenant_id"), {"id": goal_id, "tenant_id": ctx["tenant_id"]})).mappings().first()
    if not goal: return error(request, 404, "GOAL_NOT_FOUND", "Goal not found")
    existing = (await db.execute(text("SELECT id,goal_id,recorded_at,value,unit,note FROM practice_goal_progress_entries WHERE tenant_id=:tenant_id AND idempotency_key=:key"), {"tenant_id": ctx["tenant_id"], "key": idempotency_key})).mappings().first()
    if existing: return {"success": True, "data": dict(existing), "error": None, "request_id": request.state.correlation_id}
    progress_id, now = uuid4(), datetime.now(timezone.utc)
    row = (await db.execute(text("""INSERT INTO practice_goal_progress_entries
      (id,tenant_id,goal_id,client_id,recorded_at,value,unit,note,created_by,idempotency_key,created_at)
      VALUES (:id,:tenant_id,:goal_id,:client_id,:recorded_at,:value,:unit,:note,:actor,:key,:now)
      RETURNING id,goal_id,recorded_at,value,unit,note"""), {"id": progress_id, "tenant_id": ctx["tenant_id"], "goal_id": goal_id, "client_id": goal["client_id"], "recorded_at": body.recorded_at, "value": body.value, "unit": body.unit, "note": body.note, "actor": ctx["user_id"], "key": idempotency_key, "now": now})).mappings().one()
    return {"success": True, "data": dict(row), "error": None, "request_id": request.state.correlation_id}


@app.get("/api/v1/practice-operations/goals/{goal_id}/progress")
async def goal_progress_history(request: Request, goal_id: UUID, ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied = external_only(request, ctx)
    if denied: return denied
    rows = (await db.execute(text("SELECT id,recorded_at,value,unit,note,created_at FROM practice_goal_progress_entries WHERE tenant_id=:tenant_id AND goal_id=:goal_id ORDER BY recorded_at DESC,id DESC"), {"tenant_id": ctx["tenant_id"], "goal_id": goal_id})).mappings().all()
    return {"success": True, "data": {"items": [dict(row) for row in rows]}, "error": None, "request_id": request.state.correlation_id}


@app.post("/api/v1/practice-operations/media-references", status_code=201)
async def create_media_reference(request: Request, body: MediaReferenceCreate, idempotency_key: str | None=Header(None, alias="Idempotency-Key"), ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied = external_only(request, ctx)
    if denied: return denied
    if not idempotency_key: return error(request, 400, "IDEMPOTENCY_KEY_REQUIRED", "Idempotency-Key is required")
    item_id, now = uuid4(), datetime.now(timezone.utc)
    row = (await db.execute(text("""INSERT INTO practice_media_references
      (id,tenant_id,client_id,captured_at,media_type,document_reference,meal,note,created_by,idempotency_key,created_at)
      VALUES (:id,:tenant_id,:client_id,:captured_at,:media_type,:document_reference,:meal,:note,:actor,:key,:now)
      ON CONFLICT (tenant_id,idempotency_key) DO UPDATE SET idempotency_key=EXCLUDED.idempotency_key
      RETURNING id,client_id,captured_at,media_type,document_reference,meal,note"""), {"id": item_id, "tenant_id": ctx["tenant_id"], **body.model_dump(), "actor": ctx["user_id"], "key": idempotency_key, "now": now})).mappings().one()
    return {"success": True, "data": dict(row), "error": None, "request_id": request.state.correlation_id}


@app.get("/api/v1/practice-operations/calendar/events")
async def calendar_projection(request: Request, view: str="AGENDA", anchor: datetime | None=None, client_id: str | None=None, ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied,_ = await _team_guard(request,db,ctx,"CALENDAR_VIEW",client_id)
    if denied: return denied
    try: start, end = calendar_window(view.upper(), anchor or datetime.now(timezone.utc))
    except ValueError: return error(request, 400, "INVALID_CALENDAR_VIEW", "View must be AGENDA, DAY, WEEK, or MONTH")
    params = {"tenant_id": ctx["tenant_id"], "start": start, "end": end, "client_id": client_id}
    rows = (await db.execute(text("""SELECT id,client_id,title,status,due_at AS starts_at,'CONSULTATION' AS source_type FROM practice_consultations WHERE tenant_id=:tenant_id AND due_at>=:start AND due_at<:end AND (CAST(:client_id AS text) IS NULL OR client_id=CAST(:client_id AS text))
      UNION ALL SELECT id,client_id,title,status,due_at,'FOLLOW_UP' FROM practice_follow_ups WHERE tenant_id=:tenant_id AND due_at>=:start AND due_at<:end AND (CAST(:client_id AS text) IS NULL OR client_id=CAST(:client_id AS text))
      UNION ALL SELECT id,client_id,title,status,due_at,'TASK' FROM practice_tasks WHERE tenant_id=:tenant_id AND due_at>=:start AND due_at<:end AND (CAST(:client_id AS text) IS NULL OR client_id=CAST(:client_id AS text))
      UNION ALL SELECT a.id,a.client_id,t.name,a.status,a.starts_at,'APPOINTMENT'
      FROM external_scheduled_appointments a JOIN external_appointment_types t
        ON t.id=a.appointment_type_id AND t.tenant_id=a.tenant_id
      WHERE a.tenant_id=:tenant_id AND a.starts_at>=:start AND a.starts_at<:end
        AND (CAST(:client_id AS varchar) IS NULL OR a.client_id=CAST(:client_id AS varchar))
      ORDER BY starts_at,id"""), params)).mappings().all()
    return {"success": True, "data": {"view": view.upper(), "start": start, "end": end, "items": [dict(row) for row in rows], "external_adapter": None}, "error": None, "request_id": request.state.correlation_id}


@app.get("/api/v1/practice-operations/clients/{client_id}/preconsult-summary")
async def preconsult_summary(request: Request, client_id: str, ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied = external_only(request, ctx)
    if denied: return denied
    params = {"tenant_id": ctx["tenant_id"], "client_id": client_id}
    last = (await db.execute(text("SELECT id,status,due_at,payload FROM practice_consultations WHERE tenant_id=:tenant_id AND client_id=:client_id AND status='COMPLETED' ORDER BY due_at DESC NULLS LAST,id DESC LIMIT 1"), params)).mappings().first()
    async def items(table: str, clause: str="TRUE", limit: int=10):
        return [dict(r) for r in (await db.execute(text(f"SELECT id,status,due_at,payload FROM {table} WHERE tenant_id=:tenant_id AND client_id=:client_id AND {clause} ORDER BY updated_at DESC,id DESC LIMIT {limit}"), params)).mappings().all()]
    parts = {"last_consultation": dict(last) if last else None, "goals": await items("practice_goals", "status NOT IN ('COMPLETED','CANCELLED')"), "checkins": await items("practice_checkins"), "adherence": await items("practice_adherence_entries"), "open_tasks": await items("practice_tasks", "status NOT IN ('COMPLETED','CANCELLED')"), "missed_followups": await items("practice_follow_ups", "status='OVERDUE'")}
    summary = factual_summary(parts)
    summary["unavailable_sources"] = ["latest_measurements", "recent_reports", "biomarker_changes", "latest_diet_plan"]
    return {"success": True, "data": summary, "error": None, "request_id": request.state.correlation_id}


@app.get("/api/v1/practice-operations/configuration")
async def get_configuration(request: Request, ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied = external_only(request, ctx)
    if denied: return denied
    return {"success": True, "data": await configuration(db, ctx), "error": None, "request_id": request.state.correlation_id}


@app.put("/api/v1/practice-operations/configuration")
async def put_configuration(request: Request, body: PracticeConfigurationUpdate, ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied = external_only(request, ctx)
    if denied: return denied
    if (ctx.get("role") or "").upper() not in {"OWNER", "ADMIN", "ORGANISATION_ADMIN"}:
        return error(request, 403, "PRACTICE_ADMIN_REQUIRED", "Practice owner or administrator access is required")
    requested = set(body.capabilities) or PROFESSION_DEFAULTS.get(body.profession, {"CLIENT_CRM","CLIENT_ONBOARDING","CONSULTATIONS","FOLLOW_UPS","GOALS_PROGRESS","TASKS","CALENDAR","COMMUNICATION","WHATSAPP_SHARING","TEMPLATES"})
    unknown = requested - ALL_CAPABILITIES
    if unknown: return error(request, 400, "UNKNOWN_CAPABILITY", "One or more capabilities are not recognised")
    terminology = TERMINOLOGY.get(body.profession, {"consultation":"Consultation","plan":"Care Plan","goal":"Goal"})
    now = datetime.now(timezone.utc)
    row = (await db.execute(text("""INSERT INTO practice_tenant_configuration
      (tenant_id,profession,capabilities,terminology,profile,version,updated_by,updated_at)
      VALUES (:tenant_id,:profession,CAST(:capabilities AS jsonb),CAST(:terminology AS jsonb),CAST(:profile AS jsonb),1,:actor,:now)
      ON CONFLICT (tenant_id) DO UPDATE SET profession=EXCLUDED.profession,capabilities=EXCLUDED.capabilities,
      terminology=EXCLUDED.terminology,profile=EXCLUDED.profile,version=practice_tenant_configuration.version+1,
      updated_by=EXCLUDED.updated_by,updated_at=EXCLUDED.updated_at
      RETURNING profession,capabilities,terminology,profile,version"""), {"tenant_id":ctx["tenant_id"],"profession":body.profession,"capabilities":json.dumps(sorted(requested)),"terminology":json.dumps(terminology),"profile":json.dumps(body.profile),"actor":ctx["user_id"],"now":now})).mappings().one()
    if body.profession in SUPPORTED_PROFESSIONS:
        profession_profile_id = (await db.execute(text("""INSERT INTO external_profession_profiles
          (id,tenant_id,profession_code,display_name,terminology,active,version,created_by,created_at,updated_at)
          VALUES (:id,:tenant,:profession,:display,CAST(:terminology AS jsonb),TRUE,1,:actor,:now,:now)
          ON CONFLICT (tenant_id,profession_code) DO UPDATE SET terminology=EXCLUDED.terminology,active=TRUE,
          version=external_profession_profiles.version+1,updated_at=EXCLUDED.updated_at
          RETURNING id"""), {"id":uuid4(),"tenant":ctx["tenant_id"],"profession":body.profession,"display":body.profession.replace("_"," ").title(),"terminology":json.dumps(terminology),"actor":ctx["user_id"],"now":now})).scalar_one()
        await db.execute(text("DELETE FROM external_profession_capability_profiles WHERE tenant_id=:tenant AND profession_profile_id=:profile"), {"tenant":ctx["tenant_id"],"profile":profession_profile_id})
        for capability in sorted(requested):
            await db.execute(text("""INSERT INTO external_profession_capability_profiles
              (id,profession_profile_id,tenant_id,capability_code,enabled,created_at)
              VALUES (:id,:profile,:tenant,:capability,TRUE,:now)"""), {"id":uuid4(),"profile":profession_profile_id,"tenant":ctx["tenant_id"],"capability":capability,"now":now})
    return {"success": True, "data": dict(row), "error": None, "request_id": request.state.correlation_id}


@app.get("/api/v1/practice-operations/communication/templates")
async def list_templates(request: Request, ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied = external_only(request, ctx)
    if denied: return denied
    capability_denied = await require_capability(request, db, ctx, "COMMUNICATION")
    if capability_denied: return capability_denied
    rows = (await db.execute(text("SELECT id,code,label,body,active,version FROM practice_communication_templates WHERE tenant_id=:tenant_id AND active=TRUE ORDER BY label"), {"tenant_id":ctx["tenant_id"]})).mappings().all()
    return {"success": True, "data": {"items":[dict(row) for row in rows]}, "error": None, "request_id": request.state.correlation_id}


@app.post("/api/v1/practice-operations/communication/templates", status_code=201)
async def create_template(request: Request, body: CommunicationTemplateCreate, ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied = external_only(request, ctx)
    if denied: return denied
    capability_denied = await require_capability(request, db, ctx, "COMMUNICATION")
    if capability_denied: return capability_denied
    item_id, now = uuid4(), datetime.now(timezone.utc)
    row = (await db.execute(text("""INSERT INTO practice_communication_templates
      (id,tenant_id,code,label,body,active,version,created_by,created_at,updated_at)
      VALUES (:id,:tenant_id,:code,:label,:body,TRUE,1,:actor,:now,:now)
      ON CONFLICT (tenant_id,code) DO UPDATE SET label=EXCLUDED.label,body=EXCLUDED.body,active=TRUE,
      version=practice_communication_templates.version+1,updated_at=EXCLUDED.updated_at
      RETURNING id,code,label,body,active,version"""), {"id":item_id,"tenant_id":ctx["tenant_id"],**body.model_dump(),"actor":ctx["user_id"],"now":now})).mappings().one()
    return {"success": True, "data": dict(row), "error": None, "request_id": request.state.correlation_id}


@app.post("/api/v1/practice-operations/communication/whatsapp-opened", status_code=201)
async def whatsapp_opened(request: Request, body: WhatsAppOpenCreate, ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied = external_only(request, ctx)
    if denied: return denied
    capability_denied = await require_capability(request, db, ctx, "WHATSAPP_SHARING")
    if capability_denied: return capability_denied
    try:e164,digits=normalize_phone(body.phone,body.country_iso2)
    except InvalidPhone as exc:return error(request,400,"INVALID_PHONE",str(exc))
    if body.shareable_type == "DIET_PLAN_DRAFT" or (body.intent == "SHARE_PUBLISHED_PLAN" and body.shareable_type != "PUBLISHED_DIET_PLAN"): return error(request, 409, "DRAFT_NOT_SHAREABLE", "Publish the plan before sharing")
    item_id, now = uuid4(), datetime.now(timezone.utc)
    metadata = {"phone_last4":digits[-4:],"intent":body.intent,"shareable_type":body.shareable_type,"shareable_id":body.shareable_id}
    await db.execute(text("""INSERT INTO practice_communication_activity
      (id,tenant_id,client_id,channel,event_type,template_code,purpose,metadata,created_by,created_at)
      VALUES (:id,:tenant_id,:client_id,'WHATSAPP','WHATSAPP_OPENED',:template_code,:purpose,CAST(:metadata AS jsonb),:actor,:now)"""), {"id":item_id,"tenant_id":ctx["tenant_id"],"client_id":body.client_id,"template_code":body.template_code,"purpose":body.purpose,"metadata":json.dumps(metadata),"actor":ctx["user_id"],"now":now})
    await db.execute(text("""INSERT INTO practice_timeline_events
      (id,tenant_id,client_id,event_type,source_type,source_id,summary,metadata,occurred_at)
      VALUES (:id,:tenant_id,:client_id,'WHATSAPP_OPENED','COMMUNICATION',:source_id,:summary,CAST(:metadata AS jsonb),:now)
      ON CONFLICT (tenant_id,event_type,source_type,source_id) DO NOTHING"""), {"id":uuid4(),"tenant_id":ctx["tenant_id"],"client_id":body.client_id,"source_id":str(item_id),"summary":f"WhatsApp opened for {body.purpose}","metadata":json.dumps({"template_code":body.template_code}),"now":now})
    return {"success": True, "data": {"id":str(item_id),"event_type":"WHATSAPP_OPENED","intent":body.intent,"phone":digits,"phone_e164":e164,"message":body.message}, "error": None, "request_id": request.state.correlation_id}


@app.get("/api/v1/practice-operations/communication/activity")
async def communication_activity(request: Request, client_id: str | None=None, ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied = external_only(request, ctx)
    if denied: return denied
    params={"tenant_id":ctx["tenant_id"],"client_id":client_id}
    rows=(await db.execute(text("SELECT id,client_id,channel,event_type,template_code,purpose,metadata,created_at FROM practice_communication_activity WHERE tenant_id=:tenant_id AND (CAST(:client_id AS text) IS NULL OR client_id=CAST(:client_id AS text)) ORDER BY created_at DESC LIMIT 100"),params)).mappings().all()
    return {"success":True,"data":{"items":[dict(row) for row in rows]},"error":None,"request_id":request.state.correlation_id}


@app.get("/api/v1/practice-operations/notifications")
async def notifications(request: Request, unread_only: bool=False, ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied = external_only(request, ctx)
    if denied: return denied
    rows=(await db.execute(text("SELECT id,client_id,event_type,title,payload,read_at,created_at FROM practice_notifications WHERE tenant_id=:tenant_id AND (:unread=FALSE OR read_at IS NULL) ORDER BY created_at DESC LIMIT 100"),{"tenant_id":ctx["tenant_id"],"unread":unread_only})).mappings().all()
    return {"success":True,"data":{"items":[dict(row) for row in rows]},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/events/onboarding-completed", status_code=201)
async def onboarding_completed(request: Request, body: OnboardingCompletedCreate, ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied = external_only(request, ctx)
    if denied: return denied
    row=(await db.execute(text("""INSERT INTO practice_notifications
      (id,tenant_id,client_id,event_type,title,payload,created_at)
      VALUES (:id,:tenant_id,:client_id,'ONBOARDING_COMPLETED',:title,CAST(:payload AS jsonb),:completed_at)
      ON CONFLICT (tenant_id,event_type,client_id) WHERE event_type='ONBOARDING_COMPLETED'
      DO UPDATE SET title=EXCLUDED.title,payload=EXCLUDED.payload,created_at=EXCLUDED.created_at
      RETURNING id,client_id,event_type,title,payload,read_at,created_at"""), {"id":uuid4(),"tenant_id":ctx["tenant_id"],"client_id":body.client_id,"title":f"{body.client_name} completed onboarding","payload":json.dumps({"actions":["VIEW_CLIENT","WHATSAPP"]}),"completed_at":body.completed_at})).mappings().one()
    await db.execute(text("""INSERT INTO practice_timeline_events
      (id,tenant_id,client_id,event_type,source_type,source_id,summary,metadata,occurred_at)
      VALUES (:id,:tenant_id,:client_id,'ONBOARDING_COMPLETED','ONBOARDING',:source_id,:summary,'{}'::jsonb,:occurred_at)
      ON CONFLICT (tenant_id,event_type,source_type,source_id) DO NOTHING"""), {"id":uuid4(),"tenant_id":ctx["tenant_id"],"client_id":body.client_id,"source_id":body.client_id,"summary":f"{body.client_name} completed onboarding","occurred_at":body.completed_at})
    return {"success":True,"data":dict(row),"error":None,"request_id":request.state.correlation_id}


@app.get("/api/v1/practice-operations/clients/{client_id}/timeline")
async def client_timeline(request: Request, client_id: str, ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied = external_only(request, ctx)
    if denied: return denied
    rows=(await db.execute(text("SELECT id,event_type,source_type,source_id,summary,metadata,occurred_at FROM practice_timeline_events WHERE tenant_id=:tenant_id AND client_id=:client_id ORDER BY occurred_at DESC,id DESC LIMIT 100"),{"tenant_id":ctx["tenant_id"],"client_id":client_id})).mappings().all()
    return {"success":True,"data":{"items":[dict(row) for row in rows]},"error":None,"request_id":request.state.correlation_id}


@app.get("/api/v1/practice-operations/outbox/pending")
async def pending_outbox(request: Request, consumer_name: str, limit: int=Query(50, ge=1, le=100), ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied = external_only(request, ctx)
    if denied: return denied
    rows = (await db.execute(text("""SELECT e.id,e.event_type,e.aggregate_type,e.aggregate_id,e.payload,e.created_at
      FROM service_outbox_events e LEFT JOIN service_outbox_deliveries d ON d.event_id=e.id AND d.consumer_name=:consumer
      WHERE e.tenant_id=:tenant_id AND d.event_id IS NULL AND e.event_type IN
      ('CONSULTATION_SCHEDULED','CONSULTATION_COMPLETED','FOLLOWUP_CREATED','FOLLOWUP_DUE','FOLLOWUP_COMPLETED','TASK_CREATED','TASK_DUE','TASK_COMPLETED','CHECKIN_SUBMITTED','REPORT_PROCESSED','DIET_PLAN_PUBLISHED')
      AND (e.available_at IS NULL OR e.available_at<=:now)
      ORDER BY e.created_at,e.id LIMIT :limit"""), {"consumer": consumer_name, "tenant_id": ctx["tenant_id"], "now": datetime.now(timezone.utc), "limit": limit})).mappings().all()
    return {"success": True, "data": {"items": [dict(row) for row in rows]}, "error": None, "request_id": request.state.correlation_id}


@app.post("/api/v1/practice-operations/outbox/deliveries")
async def acknowledge_delivery(request: Request, body: OutboxDelivery, ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied = external_only(request, ctx)
    if denied: return denied
    result = await db.execute(text("""INSERT INTO service_outbox_deliveries (consumer_name,event_id,tenant_id,delivered_at)
      SELECT :consumer,e.id,e.tenant_id,:now FROM service_outbox_events e WHERE e.id=:event_id AND e.tenant_id=:tenant_id
      ON CONFLICT (consumer_name,event_id) DO NOTHING RETURNING event_id"""), {"consumer": body.consumer_name, "event_id": body.event_id, "tenant_id": ctx["tenant_id"], "now": datetime.now(timezone.utc)})
    inserted = result.scalar_one_or_none()
    if inserted is None:
        exists = (await db.execute(text("SELECT 1 FROM service_outbox_events WHERE id=:id AND tenant_id=:tenant_id"), {"id": body.event_id, "tenant_id": ctx["tenant_id"]})).scalar_one_or_none()
        if not exists: return error(request, 404, "OUTBOX_EVENT_NOT_FOUND", "Outbox event not found")
    return {"success": True, "data": {"event_id": str(body.event_id), "delivered": True}, "error": None, "request_id": request.state.correlation_id}


@app.post("/api/v1/practice-operations/profession-intake/templates", status_code=201)
async def publish_profession_template(request: Request, body: ProfessionTemplatePublish, ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied = external_only(request, ctx)
    if denied: return denied
    if (ctx.get("role") or "").upper() not in {"OWNER", "ADMIN", "ORGANISATION_ADMIN"}:
        return error(request, 403, "PRACTICE_ADMIN_REQUIRED", "Practice owner or administrator access is required")
    profession = body.profession_code.upper()
    if profession in FROZEN_PROFESSIONS:
        return error(request, 409, "DIETITIAN_FLOW_FROZEN", "Dietitian and Nutritionist intake remains on the existing accepted flow")
    if profession not in SUPPORTED_PROFESSIONS:
        return error(request, 400, "UNSUPPORTED_PROFESSION", "This profession is not supported")
    duplicate_keys = [section.key for section in body.sections if len({q.key for q in section.questions}) != len(section.questions)]
    if len({section.key for section in body.sections}) != len(body.sections) or duplicate_keys:
        return error(request, 400, "DUPLICATE_TEMPLATE_KEY", "Section and question keys must be unique")
    now, template_id = datetime.now(timezone.utc), uuid4()
    version = (await db.execute(text("SELECT COALESCE(MAX(version),0)+1 FROM external_intake_template_versions WHERE tenant_id=:tenant_id AND profession_code=:profession"), {"tenant_id":ctx["tenant_id"],"profession":profession})).scalar_one()
    await db.execute(text("UPDATE external_intake_template_versions SET status='RETIRED' WHERE tenant_id=:tenant_id AND profession_code=:profession AND status='ACTIVE'"), {"tenant_id":ctx["tenant_id"],"profession":profession})
    await db.execute(text("""INSERT INTO external_intake_template_versions
      (id,tenant_id,profession_code,version,title,status,published_at,created_by,created_at)
      VALUES (:id,:tenant_id,:profession,:version,:title,'ACTIVE',:now,:actor,:now)"""), {"id":template_id,"tenant_id":ctx["tenant_id"],"profession":profession,"version":version,"title":body.title,"actor":ctx["user_id"],"now":now})
    for section_order, section in enumerate(body.sections):
        section_id = uuid4()
        await db.execute(text("""INSERT INTO external_intake_template_sections
          (id,template_version_id,tenant_id,section_key,title,description,sort_order)
          VALUES (:id,:template,:tenant,:key,:title,:description,:sort)"""), {"id":section_id,"template":template_id,"tenant":ctx["tenant_id"],"key":section.key,"title":section.title,"description":section.description,"sort":section_order})
        for question_order, question in enumerate(section.questions):
            await db.execute(text("""INSERT INTO external_intake_template_questions
              (id,section_id,tenant_id,question_key,prompt,question_type,required,options,validation,sort_order)
              VALUES (:id,:section,:tenant,:key,:prompt,:type,:required,CAST(:options AS jsonb),'{}'::jsonb,:sort)"""), {"id":uuid4(),"section":section_id,"tenant":ctx["tenant_id"],"key":question.key,"prompt":question.prompt,"type":question.type,"required":question.required,"options":json.dumps(question.options),"sort":question_order})
    return {"success":True,"data":{"id":str(template_id),"professionCode":profession,"version":version,"status":"ACTIVE"},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/clients/{client_id}/profession-intake-invitations", status_code=201)
async def create_profession_invitation(request: Request, client_id: str, body: ProfessionIntakeInvitationCreate, ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied = external_only(request, ctx)
    if denied: return denied
    config = await configuration(db, ctx)
    profession = str(config.get("profession") or "").upper()
    if profession in FROZEN_PROFESSIONS:
        return error(request, 409, "USE_EXISTING_DIETITIAN_INTAKE", "Use the existing Dietitian or Nutritionist invitation flow")
    if profession not in SUPPORTED_PROFESSIONS:
        return error(request, 400, "UNSUPPORTED_PROFESSION", "Configure a supported profession before inviting this client")
    template = (await db.execute(text("""SELECT id,version FROM external_intake_template_versions
      WHERE tenant_id=:tenant_id AND profession_code=:profession AND status='ACTIVE'"""), {"tenant_id":ctx["tenant_id"],"profession":profession})).mappings().first()
    if not template:
        return error(request, 409, "ACTIVE_TEMPLATE_REQUIRED", "Publish an active profession intake template first")
    now, instance_id = datetime.now(timezone.utc), uuid4()
    expires_at = now + timedelta(hours=body.expires_in_hours)
    token = issue_token(secret=get_settings().profession_intake_secret, tenant_id=ctx["tenant_id"], client_id=client_id,
                        intake_instance_id=str(instance_id), profession_code=profession, template_version_id=str(template["id"]),
                        expires_at=int(expires_at.timestamp()))
    await db.execute(text("""UPDATE external_client_intake_instances SET status='REVOKED',updated_at=:now
      WHERE tenant_id=:tenant_id AND client_id=:client_id AND status IN ('NOT_STARTED','IN_PROGRESS')"""), {"now":now,"tenant_id":ctx["tenant_id"],"client_id":client_id})
    await db.execute(text("""INSERT INTO external_client_intake_instances
      (id,tenant_id,client_id,profession_code,template_version_id,status,completion_percent,token_hash,token_expires_at,token_version,review_state,created_by,created_at,updated_at)
      VALUES (:id,:tenant,:client,:profession,:template,'NOT_STARTED',0,:token_hash,:expires,1,'PENDING',:actor,:now,:now)"""), {"id":instance_id,"tenant":ctx["tenant_id"],"client":client_id,"profession":profession,"template":template["id"],"token_hash":token_hash(token),"expires":expires_at,"actor":ctx["user_id"],"now":now})
    await db.execute(text("""INSERT INTO external_client_intake_audit_events
      (id,intake_instance_id,tenant_id,client_id,event_type,actor_id,metadata,created_at)
      VALUES (:id,:instance,:tenant,:client,'INVITATION_ISSUED',:actor,CAST(:metadata AS jsonb),:now)"""), {"id":uuid4(),"instance":instance_id,"tenant":ctx["tenant_id"],"client":client_id,"actor":ctx["user_id"],"metadata":json.dumps({"profession_code":profession,"template_version":template["version"]}),"now":now})
    base = get_settings().profession_intake_public_url.rstrip("/")
    return {"success":True,"data":{"intakeInstanceId":str(instance_id),"expiresAt":expires_at,"shareUrl":f"{base}/{token}","professionCode":profession},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/clients/{client_id}/profession-intake-invitations/revoke")
async def revoke_profession_invitation(request: Request, client_id: str, ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied = external_only(request, ctx)
    if denied: return denied
    now=datetime.now(timezone.utc)
    row=(await db.execute(text("""UPDATE external_client_intake_instances SET status='REVOKED',token_version=token_version+1,updated_at=:now
      WHERE id=(SELECT id FROM external_client_intake_instances WHERE tenant_id=:tenant AND client_id=:client AND status IN ('NOT_STARTED','IN_PROGRESS') ORDER BY created_at DESC LIMIT 1)
      AND tenant_id=:tenant AND client_id=:client RETURNING id,status"""), {"now":now,"tenant":ctx["tenant_id"],"client":client_id})).mappings().first()
    if not row: return error(request,404,"ACTIVE_PROFESSION_INTAKE_NOT_FOUND","No active profession intake invitation was found")
    await db.execute(text("""INSERT INTO external_client_intake_audit_events
      (id,intake_instance_id,tenant_id,client_id,event_type,actor_id,metadata,created_at)
      VALUES (:id,:instance,:tenant,:client,'INVITATION_REVOKED',:actor,'{}'::jsonb,:now)"""), {"id":uuid4(),"instance":row["id"],"tenant":ctx["tenant_id"],"client":client_id,"actor":ctx["user_id"],"now":now})
    return {"success":True,"data":{"id":str(row["id"]),"status":"REVOKED"},"error":None,"request_id":request.state.correlation_id}


@app.get("/api/v1/practice-operations/clients/{client_id}/profession-intake")
async def profession_intake_projection(request: Request, client_id: str, ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied = external_only(request, ctx)
    if denied: return denied
    row = (await db.execute(text("""SELECT i.id,i.profession_code,i.status,i.completion_percent,i.review_state,i.submitted_at,
      t.id AS template_version_id,t.version AS template_version,t.title
      FROM external_client_intake_instances i JOIN external_intake_template_versions t ON t.id=i.template_version_id
      WHERE i.tenant_id=:tenant AND i.client_id=:client ORDER BY i.created_at DESC LIMIT 1"""), {"tenant":ctx["tenant_id"],"client":client_id})).mappings().first()
    return {"success":True,"data":dict(row) if row else None,"error":None,"request_id":request.state.correlation_id}


@app.get("/api/v1/practice-operations/profession-intake/projections")
async def profession_intake_projections(request: Request, ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied = external_only(request, ctx)
    if denied: return denied
    rows=(await db.execute(text("""SELECT DISTINCT ON (client_id) client_id,profession_code,status,completion_percent,review_state,submitted_at
      FROM external_client_intake_instances WHERE tenant_id=:tenant ORDER BY client_id,created_at DESC"""), {"tenant":ctx["tenant_id"]})).mappings().all()
    return {"success":True,"data":{"items":[dict(row) for row in rows]},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/clients/{client_id}/profession-intake/custom-questions", status_code=201)
async def create_profession_custom_question(request: Request, client_id: str, body: ProfessionCustomQuestionCreate, ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied = external_only(request, ctx)
    if denied: return denied
    instance=(await db.execute(text("""SELECT id,status FROM external_client_intake_instances WHERE tenant_id=:tenant AND client_id=:client
      ORDER BY created_at DESC LIMIT 1"""), {"tenant":ctx["tenant_id"],"client":client_id})).mappings().first()
    if not instance: return error(request,404,"PROFESSION_INTAKE_NOT_FOUND","Profession intake not found")
    if instance["status"] in {"COMPLETED","REVOKED","EXPIRED"}: return error(request,409,"INTAKE_NOT_EDITABLE","Custom questions cannot be added to this intake")
    sort=(await db.execute(text("SELECT COALESCE(MAX(sort_order),-1)+1 FROM external_client_intake_custom_questions WHERE tenant_id=:tenant AND client_id=:client AND intake_instance_id=:instance"), {"tenant":ctx["tenant_id"],"client":client_id,"instance":instance["id"]})).scalar_one()
    item_id=uuid4()
    await db.execute(text("""INSERT INTO external_client_intake_custom_questions
      (id,intake_instance_id,tenant_id,client_id,question_key,prompt,question_type,required,options,sort_order,created_by,created_at)
      VALUES (:id,:instance,:tenant,:client,:key,:prompt,:type,:required,CAST(:options AS jsonb),:sort,:actor,:now)"""), {"id":item_id,"instance":instance["id"],"tenant":ctx["tenant_id"],"client":client_id,"key":body.key,"prompt":body.prompt,"type":body.type,"required":body.required,"options":json.dumps(body.options),"sort":sort,"actor":ctx["user_id"],"now":datetime.now(timezone.utc)})
    return {"success":True,"data":{"id":str(item_id),"key":body.key},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/clients/{client_id}/profession-intake/reviews", status_code=201)
async def review_profession_intake(request: Request, client_id: str, body: ProfessionIntakeReviewCreate, ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied = external_only(request, ctx)
    if denied: return denied
    instance=(await db.execute(text("SELECT id,status FROM external_client_intake_instances WHERE tenant_id=:tenant AND client_id=:client ORDER BY created_at DESC LIMIT 1"), {"tenant":ctx["tenant_id"],"client":client_id})).mappings().first()
    if not instance: return error(request,404,"PROFESSION_INTAKE_NOT_FOUND","Profession intake not found")
    if instance["status"] != "COMPLETED": return error(request,409,"INTAKE_NOT_SUBMITTED","Only a submitted intake can be reviewed")
    review_state={"REVIEW_STARTED":"IN_REVIEW","APPROVED":"APPROVED","CHANGES_REQUESTED":"CHANGES_REQUESTED"}[body.event_type]
    now=datetime.now(timezone.utc)
    await db.execute(text("""INSERT INTO external_client_intake_review_events
      (id,intake_instance_id,tenant_id,client_id,event_type,notes,actor_id,created_at)
      VALUES (:id,:instance,:tenant,:client,:event,:notes,:actor,:now)"""), {"id":uuid4(),"instance":instance["id"],"tenant":ctx["tenant_id"],"client":client_id,"event":body.event_type,"notes":body.notes,"actor":ctx["user_id"],"now":now})
    await db.execute(text("UPDATE external_client_intake_instances SET review_state=:state,updated_at=:now WHERE id=:id AND tenant_id=:tenant AND client_id=:client"), {"state":review_state,"now":now,"id":instance["id"],"tenant":ctx["tenant_id"],"client":client_id})
    return {"success":True,"data":{"reviewState":review_state},"error":None,"request_id":request.state.correlation_id}


async def _assessment_guard(request,db,ctx):
    denied=external_only(request,ctx)
    return denied or await require_capability(request,db,ctx,"ASSESSMENTS")

@app.get("/api/v1/practice-operations/assessments/definitions")
async def assessment_definitions(request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=await _assessment_guard(request,db,ctx)
    if denied:return denied
    config=await configuration(db,ctx)
    rows=(await db.execute(text("""SELECT d.id,d.code,d.title,d.description,d.profession_code,d.scope,v.id version_id,v.version
      FROM external_assessment_definitions d JOIN external_assessment_versions v ON v.definition_id=d.id AND v.status='ACTIVE'
      WHERE d.active=TRUE AND d.profession_code=:profession AND (d.tenant_id IS NULL OR d.tenant_id=:tenant_id)
      ORDER BY d.scope,d.title"""),{"profession":config["profession"],"tenant_id":ctx["tenant_id"]})).mappings().all()
    return {"success":True,"data":{"items":[dict(row) for row in rows]},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/clients/{client_id}/assessments",status_code=201)
async def assign_assessment(request:Request,client_id:str,body:AssessmentAssign,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=await _assessment_guard(request,db,ctx)
    if denied:return denied
    definition=(await db.execute(text("""SELECT d.id,d.profession_code,v.id version_id FROM external_assessment_definitions d
      JOIN external_assessment_versions v ON v.definition_id=d.id AND v.status='ACTIVE'
      WHERE d.id=:id AND d.active=TRUE AND (d.tenant_id IS NULL OR d.tenant_id=:tenant_id)"""),{"id":body.definition_id,"tenant_id":ctx["tenant_id"]})).mappings().first()
    if not definition:return error(request,404,"ASSESSMENT_DEFINITION_NOT_FOUND","Assessment definition not found")
    item_id=uuid4();now=datetime.now(timezone.utc)
    await db.execute(text("""INSERT INTO external_assessment_instances
      (id,tenant_id,client_id,definition_id,version_id,profession_code,status,assigned_by,assigned_at,due_at,updated_at)
      VALUES (:id,:tenant,:client,:definition,:version,:profession,'ASSIGNED',:actor,:now,:due,:now)"""),{"id":item_id,"tenant":ctx["tenant_id"],"client":client_id,"definition":definition["id"],"version":definition["version_id"],"profession":definition["profession_code"],"actor":ctx["user_id"],"now":now,"due":body.due_at})
    await db.commit();return {"success":True,"data":{"id":str(item_id),"status":"ASSIGNED"},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/clients/{client_id}/assessments")
async def client_assessments(request:Request,client_id:str,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=await _assessment_guard(request,db,ctx)
    if denied:return denied
    rows=(await db.execute(text("""SELECT i.id,i.status,i.assigned_at,i.due_at,i.completed_at,d.title,d.code
      FROM external_assessment_instances i JOIN external_assessment_definitions d ON d.id=i.definition_id
      WHERE i.tenant_id=:tenant AND i.client_id=:client ORDER BY i.assigned_at DESC"""),{"tenant":ctx["tenant_id"],"client":client_id})).mappings().all()
    return {"success":True,"data":{"items":[dict(row) for row in rows]},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/assessments/{assessment_id}")
async def assessment_detail(request:Request,assessment_id:UUID,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=await _assessment_guard(request,db,ctx)
    if denied:return denied
    instance=(await db.execute(text("SELECT id,tenant_id,client_id,definition_id,version_id,profession_code,status,assigned_by,assigned_at,due_at,completed_at,updated_at FROM external_assessment_instances WHERE id=:id AND tenant_id=:tenant"),{"id":assessment_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not instance:return error(request,404,"ASSESSMENT_NOT_FOUND","Assessment not found")
    questions=(await db.execute(text("SELECT id,question_key,prompt,question_type,required,options,sort_order FROM external_assessment_questions WHERE version_id=:version ORDER BY sort_order"),{"version":instance["version_id"]})).mappings().all()
    answers=(await db.execute(text("SELECT q.question_key,a.answer FROM external_assessment_answers a JOIN external_assessment_questions q ON q.id=a.question_id WHERE a.assessment_instance_id=:id"),{"id":assessment_id})).mappings().all()
    return {"success":True,"data":{"instance":dict(instance),"questions":[dict(q) for q in questions],"answers":{a["question_key"]:a["answer"] for a in answers}},"error":None,"request_id":request.state.correlation_id}

async def _save_assessment_answers(db,instance,answers,actor):
    now=datetime.now(timezone.utc)
    for key,value in answers.items():
        await db.execute(text("""INSERT INTO external_assessment_answers(id,assessment_instance_id,tenant_id,client_id,question_id,answer,answered_by,answered_at)
          SELECT :id,:instance,:tenant,:client,q.id,CAST(:answer AS jsonb),:actor,:now FROM external_assessment_questions q
          WHERE q.version_id=:version AND q.question_key=:key
          ON CONFLICT(assessment_instance_id,question_id) DO UPDATE SET answer=EXCLUDED.answer,answered_by=EXCLUDED.answered_by,answered_at=EXCLUDED.answered_at"""),{"id":uuid4(),"instance":instance["id"],"tenant":instance["tenant_id"],"client":instance["client_id"],"answer":json.dumps(value),"actor":actor,"now":now,"version":instance["version_id"],"key":key})

@app.patch("/api/v1/practice-operations/assessments/{assessment_id}")
async def save_assessment(request:Request,assessment_id:UUID,body:AssessmentAnswerSave,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=await _assessment_guard(request,db,ctx)
    if denied:return denied
    instance=(await db.execute(text("SELECT id,tenant_id,client_id,definition_id,version_id,profession_code,status,assigned_by,assigned_at,due_at,completed_at,updated_at FROM external_assessment_instances WHERE id=:id AND tenant_id=:tenant"),{"id":assessment_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not instance:return error(request,404,"ASSESSMENT_NOT_FOUND","Assessment not found")
    await _save_assessment_answers(db,instance,body.answers,ctx["user_id"]);await db.execute(text("UPDATE external_assessment_instances SET status='IN_PROGRESS',updated_at=:now WHERE id=:id"),{"id":assessment_id,"now":datetime.now(timezone.utc)});await db.commit()
    return {"success":True,"data":{"id":str(assessment_id),"status":"IN_PROGRESS"},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/assessments/{assessment_id}/complete")
async def complete_assessment(request:Request,assessment_id:UUID,body:AssessmentComplete,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=await _assessment_guard(request,db,ctx)
    if denied:return denied
    instance=(await db.execute(text("SELECT id,tenant_id,client_id,definition_id,version_id,profession_code,status,assigned_by,assigned_at,due_at,completed_at,updated_at FROM external_assessment_instances WHERE id=:id AND tenant_id=:tenant"),{"id":assessment_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not instance:return error(request,404,"ASSESSMENT_NOT_FOUND","Assessment not found")
    await _save_assessment_answers(db,instance,body.answers,ctx["user_id"]);now=datetime.now(timezone.utc)
    missing=(await db.execute(text("""SELECT COUNT(*) FROM external_assessment_questions q LEFT JOIN external_assessment_answers a ON a.question_id=q.id AND a.assessment_instance_id=:id WHERE q.version_id=:version AND q.required=TRUE AND a.id IS NULL"""),{"id":assessment_id,"version":instance["version_id"]})).scalar_one()
    if missing:return error(request,409,"ASSESSMENT_REQUIRED_ANSWERS_MISSING","Complete all required assessment questions")
    await db.execute(text("UPDATE external_assessment_instances SET status='COMPLETED',completed_at=:now,updated_at=:now WHERE id=:id"),{"id":assessment_id,"now":now});await db.execute(text("INSERT INTO external_assessment_review_events(id,assessment_instance_id,tenant_id,client_id,event_type,notes,actor_id,created_at) VALUES (:event,:id,:tenant,:client,'COMPLETED',:notes,:actor,:now)"),{"event":uuid4(),"id":assessment_id,"tenant":ctx["tenant_id"],"client":instance["client_id"],"notes":body.review_notes,"actor":ctx["user_id"],"now":now});await _preconsultation_event_once(db,ctx["tenant_id"],instance["client_id"],"ASSESSMENT_COMPLETED",ctx["user_id"],"PRACTITIONER",{"assessment_id":str(assessment_id)});await _record_preconsultation_readiness(db,ctx["tenant_id"],instance["client_id"]);await db.commit()
    return {"success":True,"data":{"id":str(assessment_id),"status":"COMPLETED"},"error":None,"request_id":request.state.correlation_id}


@app.get("/api/v1/practice-operations/clients/{client_id}/profession-view")
async def profession_client360(request: Request, client_id: str, ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied = external_only(request, ctx)
    if denied: return denied
    config = await configuration(db, ctx)
    profession = config["profession"]
    sections = PROFESSION_CLIENT360_SECTIONS.get(profession, [])
    if not sections:
        return {"success":True,"data":{"profession":profession,"sections":[]},"error":None,"request_id":request.state.correlation_id}
    capabilities = set(config["capabilities"])
    resource_caps = {"consultations":"CONSULTATIONS", "follow-ups":"FOLLOW_UPS", "goals":"GOALS_PROGRESS", "tasks":"TASKS", "notes":"SESSION_NOTES", "assessments":"ASSESSMENTS"}
    records = {}
    for source in {source for _, source in sections if source != "biomarkers"}:
        capability = resource_caps[source]
        if capability not in capabilities:
            records[source] = {"state":"UNAVAILABLE", "items":[], "reason":"CAPABILITY_NOT_ENABLED"}
            continue
        if source == "assessments":
            rows = (await db.execute(text("""SELECT i.id,i.status,i.assigned_at AS occurred_at,i.completed_at,d.title,i.profession_code
              FROM external_assessment_instances i JOIN external_assessment_definitions d ON d.id=i.definition_id
              WHERE i.tenant_id=:tenant AND i.client_id=:client ORDER BY i.assigned_at DESC LIMIT 25"""), {"tenant":ctx["tenant_id"],"client":client_id})).mappings().all()
        else:
            table = RESOURCE_TABLES[source]
            rows = (await db.execute(text(f"SELECT id,title,status,type,due_at,created_at AS occurred_at,updated_at,payload FROM {table} WHERE tenant_id=:tenant AND client_id=:client ORDER BY created_at DESC LIMIT 25"), {"tenant":ctx["tenant_id"],"client":client_id})).mappings().all()
        records[source] = {"state":"READY", "items":[dict(row) for row in rows]}
    projected=[]
    for label,source in sections:
        if source == "biomarkers":
            projected.append({"label":label,"source":source,"state":"EXTERNAL_SOURCE","items":[]})
        else:
            projected.append({"label":label,"source":source,**records[source]})
    return {"success":True,"data":{"profession":profession,"capabilities":config["capabilities"],"terminology":config["terminology"],"sections":projected},"error":None,"request_id":request.state.correlation_id}

async def _write_plan_sections(db, tenant_id, version_id, sections):
    for section_order, section in enumerate(sections, 1):
        section_id=uuid4()
        await db.execute(text("INSERT INTO external_profession_plan_sections(id,plan_version_id,tenant_id,section_key,title,content,sort_order) VALUES (:id,:version,:tenant,:key,:title,CAST(:content AS jsonb),:sort)"),{"id":section_id,"version":version_id,"tenant":tenant_id,"key":section.key,"title":section.title,"content":json.dumps(section.content),"sort":section_order})
        for item_order,item in enumerate(section.items,1):
            await db.execute(text("INSERT INTO external_profession_plan_items(id,plan_section_id,tenant_id,item_key,label,content,sort_order) VALUES (:id,:section,:tenant,:key,:label,CAST(:content AS jsonb),:sort)"),{"id":uuid4(),"section":section_id,"tenant":tenant_id,"key":item.key,"label":item.label,"content":json.dumps(item.content),"sort":item_order})

@app.get("/api/v1/practice-operations/clients/{client_id}/profession-plans")
async def list_profession_plans(request:Request,client_id:str,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    rows=(await db.execute(text("SELECT id,client_id,profession_code,plan_type,title,status,current_version,created_at,updated_at FROM external_profession_plans WHERE tenant_id=:tenant AND client_id=:client ORDER BY updated_at DESC"),{"tenant":ctx["tenant_id"],"client":client_id})).mappings().all()
    return {"success":True,"data":{"items":[dict(row) for row in rows]},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/profession-plans",status_code=201)
async def create_profession_plan(request:Request,body:ProfessionPlanCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    capability_denied=await require_capability(request,db,ctx,PLAN_CAPABILITIES[body.plan_type])
    if capability_denied:return capability_denied
    config=await configuration(db,ctx);plan_id=uuid4();version_id=uuid4();now=datetime.now(timezone.utc)
    await db.execute(text("INSERT INTO external_profession_plans(id,tenant_id,client_id,profession_code,plan_type,title,status,current_version,created_by,created_at,updated_at) VALUES (:id,:tenant,:client,:profession,:type,:title,'DRAFT',1,:actor,:now,:now)"),{"id":plan_id,"tenant":ctx["tenant_id"],"client":body.client_id,"profession":config["profession"],"type":body.plan_type,"title":body.title,"actor":ctx["user_id"],"now":now})
    await db.execute(text("INSERT INTO external_profession_plan_versions(id,plan_id,tenant_id,client_id,version,status,title,created_by,created_at) VALUES (:id,:plan,:tenant,:client,1,'DRAFT',:title,:actor,:now)"),{"id":version_id,"plan":plan_id,"tenant":ctx["tenant_id"],"client":body.client_id,"title":body.title,"actor":ctx["user_id"],"now":now})
    await _write_plan_sections(db,ctx["tenant_id"],version_id,body.sections)
    await db.execute(text("INSERT INTO external_profession_plan_audit_events(id,plan_id,plan_version_id,tenant_id,client_id,event_type,actor_id,metadata,created_at) VALUES (:id,:plan,:version,:tenant,:client,'CREATED',:actor,CAST(:metadata AS jsonb),:now)"),{"id":uuid4(),"plan":plan_id,"version":version_id,"tenant":ctx["tenant_id"],"client":body.client_id,"actor":ctx["user_id"],"metadata":json.dumps({"plan_type":body.plan_type}),"now":now});await db.commit()
    return {"success":True,"data":{"id":str(plan_id),"version_id":str(version_id),"status":"DRAFT","version":1},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/profession-plans/{plan_id}")
async def profession_plan_detail(request:Request,plan_id:UUID,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    plan=(await db.execute(text("SELECT id,client_id,profession_code,plan_type,title,status,current_version,created_at,updated_at FROM external_profession_plans WHERE id=:id AND tenant_id=:tenant"),{"id":plan_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not plan:return error(request,404,"PROFESSION_PLAN_NOT_FOUND","Profession plan not found")
    versions=[dict(row) for row in (await db.execute(text("SELECT id,version,status,title,published_at,created_at FROM external_profession_plan_versions WHERE plan_id=:plan AND tenant_id=:tenant ORDER BY version DESC"),{"plan":plan_id,"tenant":ctx["tenant_id"]})).mappings().all()]
    current=next((version for version in versions if version["version"]==plan["current_version"]),None);sections=[]
    if current:
        rows=(await db.execute(text("SELECT id,section_key,title,content,sort_order FROM external_profession_plan_sections WHERE plan_version_id=:version AND tenant_id=:tenant ORDER BY sort_order"),{"version":current["id"],"tenant":ctx["tenant_id"]})).mappings().all()
        for row in rows:
            section=dict(row);section["items"]=[dict(item) for item in (await db.execute(text("SELECT id,item_key,label,content,sort_order FROM external_profession_plan_items WHERE plan_section_id=:section AND tenant_id=:tenant ORDER BY sort_order"),{"section":row["id"],"tenant":ctx["tenant_id"]})).mappings().all()];sections.append(section)
    return {"success":True,"data":{"plan":dict(plan),"versions":versions,"sections":sections},"error":None,"request_id":request.state.correlation_id}

@app.patch("/api/v1/practice-operations/profession-plans/{plan_id}")
async def save_profession_plan(request:Request,plan_id:UUID,body:ProfessionPlanSave,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    plan=(await db.execute(text("SELECT id,client_id,status,current_version FROM external_profession_plans WHERE id=:id AND tenant_id=:tenant"),{"id":plan_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not plan:return error(request,404,"PROFESSION_PLAN_NOT_FOUND","Profession plan not found")
    if plan["status"] in {"PUBLISHED","SUPERSEDED"}:return error(request,409,"PUBLISHED_PLAN_IMMUTABLE","Published profession plans are immutable")
    if plan["current_version"]!=body.expected_version:return error(request,409,"STALE_WRITE","This plan changed. Refresh and retry")
    version=(await db.execute(text("SELECT id FROM external_profession_plan_versions WHERE plan_id=:plan AND tenant_id=:tenant AND version=:version"),{"plan":plan_id,"tenant":ctx["tenant_id"],"version":plan["current_version"]})).scalar_one()
    await db.execute(text("DELETE FROM external_profession_plan_sections WHERE plan_version_id=:version AND tenant_id=:tenant"),{"version":version,"tenant":ctx["tenant_id"]});await _write_plan_sections(db,ctx["tenant_id"],version,body.sections);now=datetime.now(timezone.utc)
    await db.execute(text("UPDATE external_profession_plan_versions SET status='SAVED',title=:title WHERE id=:version AND tenant_id=:tenant"),{"title":body.title,"version":version,"tenant":ctx["tenant_id"]})
    await db.execute(text("UPDATE external_profession_plans SET status='SAVED',title=:title,updated_at=:now WHERE id=:plan AND tenant_id=:tenant"),{"title":body.title,"now":now,"plan":plan_id,"tenant":ctx["tenant_id"]})
    await db.execute(text("INSERT INTO external_profession_plan_audit_events(id,plan_id,plan_version_id,tenant_id,client_id,event_type,actor_id,created_at) VALUES (:id,:plan,:version,:tenant,:client,'SAVED',:actor,:now)"),{"id":uuid4(),"plan":plan_id,"version":version,"tenant":ctx["tenant_id"],"client":plan["client_id"],"actor":ctx["user_id"],"now":now});await db.commit()
    return {"success":True,"data":{"id":str(plan_id),"status":"SAVED","version":plan["current_version"]},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/profession-plans/{plan_id}/publish")
async def publish_profession_plan(request:Request,plan_id:UUID,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    plan=(await db.execute(text("SELECT id,client_id,status,current_version FROM external_profession_plans WHERE id=:id AND tenant_id=:tenant"),{"id":plan_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not plan:return error(request,404,"PROFESSION_PLAN_NOT_FOUND","Profession plan not found")
    if plan["status"]=="PUBLISHED":return error(request,409,"PUBLISHED_PLAN_IMMUTABLE","Published profession plans are immutable")
    now=datetime.now(timezone.utc);version=(await db.execute(text("UPDATE external_profession_plan_versions SET status='PUBLISHED',published_at=:now WHERE plan_id=:plan AND tenant_id=:tenant AND version=:version RETURNING id"),{"now":now,"plan":plan_id,"tenant":ctx["tenant_id"],"version":plan["current_version"]})).scalar_one()
    await db.execute(text("UPDATE external_profession_plans SET status='PUBLISHED',updated_at=:now WHERE id=:plan AND tenant_id=:tenant"),{"now":now,"plan":plan_id,"tenant":ctx["tenant_id"]})
    await db.execute(text("INSERT INTO external_profession_plan_audit_events(id,plan_id,plan_version_id,tenant_id,client_id,event_type,actor_id,created_at) VALUES (:id,:plan,:version,:tenant,:client,'PUBLISHED',:actor,:now)"),{"id":uuid4(),"plan":plan_id,"version":version,"tenant":ctx["tenant_id"],"client":plan["client_id"],"actor":ctx["user_id"],"now":now});await db.commit()
    return {"success":True,"data":{"id":str(plan_id),"status":"PUBLISHED","version":plan["current_version"]},"error":None,"request_id":request.state.correlation_id}

async def _diet_plan_row(request, db, ctx, plan_id):
    actor_clause, actor_params = _diet_plan_actor_clause(ctx)
    row=(await db.execute(text(f"""SELECT id,tenant_id,client_id,profession_code,plan_type,title,status,current_version,
      daily_calories_target,daily_protein_target_g,authorised_consultant_id,created_at,updated_at
      FROM external_profession_plans WHERE id=:id AND tenant_id=:tenant AND plan_type='DIET_PLAN'{actor_clause}"""),
      {"id":plan_id,"tenant":ctx["tenant_id"],**actor_params})).mappings().first()
    return row

async def _diet_plan_publication_eligibility(db,ctx,consultant_id):
    row=(await db.execute(text("""SELECT p.approval_valid,p.approved_version,v.projection
      FROM external_consultant_public_profiles p
      LEFT JOIN external_consultant_public_profile_versions v ON v.profile_id=p.id AND v.version=p.approved_version
      WHERE p.tenant_id=:tenant AND p.consultant_user_id=:consultant"""),
      {"tenant":ctx["tenant_id"],"consultant":consultant_id})).mappings().first()
    if not row or not row["approval_valid"] or row["approved_version"] is None:return {"state":"UNVERIFIED","experience_years":None,"independent":False}
    years=int((row["projection"] or {}).get("experience_years") or 0)
    return {"state":"VERIFIED","experience_years":years,"independent":years>=1}

async def _current_diet_plan_readiness(db,ctx,client_id):
    row=(await db.execute(text("""SELECT id,current_version,status,readiness_status,stale
      FROM external_nutrition_assessments
      WHERE tenant_id=:tenant AND client_id=:client ORDER BY updated_at DESC LIMIT 1"""),
      {"tenant":ctx["tenant_id"],"client":client_id})).mappings().first()
    if not row:return {"outcome":"NOT_STARTED","assessment_id":None,"assessment_version":None}
    outcome="BLOCKED" if row["stale"] else str(row["readiness_status"] or "INCOMPLETE")
    if row["status"]!="REVIEWED" and outcome=="READY":outcome="NEEDS_REVIEW"
    return {"outcome":outcome,"assessment_id":str(row["id"]),"assessment_version":row["current_version"]}

async def _diet_plan_health_context(db,ctx,client_id):
    measurement=await _measurement_projection(db,ctx["tenant_id"],client_id)
    assessment=(await db.execute(text("""SELECT a.id,a.current_version,a.status,a.readiness_status,a.stale,
      v.source_manifest,v.assessment_data,v.calculations,v.reviewed_by,v.reviewed_at
      FROM external_nutrition_assessments a JOIN external_nutrition_assessment_versions v
      ON v.assessment_id=a.id AND v.version=a.current_version
      WHERE a.tenant_id=:tenant AND a.client_id=:client ORDER BY a.updated_at DESC LIMIT 1"""),
      {"tenant":ctx["tenant_id"],"client":client_id})).mappings().first()
    saved_ids=sorted(str(item.get("source_id")) for item in ((assessment or {}).get("source_manifest") or []) if item.get("source_type")=="MEASUREMENT")
    changed=bool(assessment) and saved_ids!=measurement["source_measurement_ids"]
    readiness="NOT_STARTED" if not assessment else ("BLOCKED" if assessment["stale"] or changed else str(assessment["readiness_status"] or "INCOMPLETE"))
    profile=dict((assessment or {}).get("assessment_data") or {})
    return {
      "measurement_context":measurement,
      "assessment":{"id":str(assessment["id"]) if assessment else None,"version":assessment["current_version"] if assessment else None,
        "status":assessment["status"] if assessment else "NOT_STARTED","readiness":readiness,
        "reviewed_by":str(assessment["reviewed_by"]) if assessment and assessment["reviewed_by"] else None,
        "reviewed_at":assessment["reviewed_at"].isoformat() if assessment and assessment["reviewed_at"] else None,
        "measurement_context_changed":changed},
      "profile":{"dietary_preference":profile.get("dietary_preference"),"allergies_intolerances":profile.get("allergies_intolerances") or [],
        "food_restrictions":profile.get("food_restrictions") or [],"weight_management_goals":profile.get("weight_management_goals") or [],
        "recovery_disease_management_goals":profile.get("recovery_disease_management_goals") or []},
      "target_policy":{"methodology":"PROFESSIONAL_JUDGEMENT","automatic_calorie_prescription":False,
        "professional_confirmation_required":True},
    }


@app.get("/api/v1/practice-operations/clients/{client_id}/diet-plan-context")
async def get_diet_plan_health_context(request:Request,client_id:str,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    capability_denied=await require_capability(request,db,ctx,"DIET_PLAN")
    if capability_denied:return capability_denied
    return {"success":True,"data":await _diet_plan_health_context(db,ctx,client_id),"error":None,"request_id":request.state.correlation_id}

def _diet_plan_readiness_error(request,readiness):
    return error(request,409,"DIET_PLAN_READINESS_REQUIRED",
      f"Nutrition Assessment readiness is {readiness['outcome']}. Complete and review the assessment before authoring or publishing a Diet Plan")

async def _diet_plan_projection(db, plan):
    versions=[dict(row) for row in (await db.execute(text("""SELECT id,version,status,title,nutrition_snapshot,published_at,created_at
      FROM external_profession_plan_versions WHERE plan_id=:plan AND tenant_id=:tenant ORDER BY version DESC"""),
      {"plan":plan["id"],"tenant":plan["tenant_id"]})).mappings().all()]
    current=next((row for row in versions if row["version"]==plan["current_version"]),None)
    options=[]
    if current:
        section=(await db.execute(text("""SELECT id FROM external_profession_plan_sections
          WHERE plan_version_id=:version AND tenant_id=:tenant AND section_key='meal_options'"""),
          {"version":current["id"],"tenant":plan["tenant_id"]})).scalar_one_or_none()
        if section:
            items=(await db.execute(text("""SELECT content FROM external_profession_plan_items
              WHERE plan_section_id=:section AND tenant_id=:tenant ORDER BY sort_order"""),
              {"section":section,"tenant":plan["tenant_id"]})).scalars().all()
            options=[dict(item or {}) for item in items]
    value=dict(plan);value["id"]=str(value["id"]);value["daily_protein_target_g"]=float(value["daily_protein_target_g"] or 0)
    context=await _measurement_projection(db,plan["tenant_id"],plan["client_id"])
    for version in versions:
        version["id"]=str(version["id"])
        snapshot=dict(version.get("nutrition_snapshot") or {})
        version["measurement_context_changed"]=bool(snapshot.get("measurement_context_fingerprint")) and snapshot.get("measurement_context_fingerprint")!=context["measurement_context_fingerprint"]
    return {"plan":value,"versions":versions,"current_version":current,"options":options}

@app.get("/api/v1/practice-operations/clients/{client_id}/diet-plans")
async def list_diet_plans(request:Request,client_id:str,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    capability_denied=await require_capability(request,db,ctx,"DIET_PLAN")
    if capability_denied:return capability_denied
    actor_clause,actor_params=_diet_plan_actor_clause(ctx)
    rows=(await db.execute(text(f"""SELECT id,tenant_id,client_id,profession_code,plan_type,title,status,current_version,
      daily_calories_target,daily_protein_target_g,authorised_consultant_id,created_at,updated_at
      FROM external_profession_plans WHERE tenant_id=:tenant AND client_id=:client AND plan_type='DIET_PLAN'{actor_clause}
      ORDER BY updated_at DESC"""),{"tenant":ctx["tenant_id"],"client":client_id,**actor_params})).mappings().all()
    return {"success":True,"data":{"items":[dict(row) for row in rows]},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/diet-plans",status_code=201)
async def create_diet_plan(request:Request,body:DietPlanCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    capability_denied=await require_capability(request,db,ctx,"DIET_PLAN")
    if capability_denied:return capability_denied
    readiness=await _current_diet_plan_readiness(db,ctx,body.client_id)
    health_context=await _diet_plan_health_context(db,ctx,body.client_id)
    config=await configuration(db,ctx);now=datetime.now(timezone.utc);plan_id=uuid4();version_id=uuid4()
    await db.execute(text("""INSERT INTO external_profession_plans
      (id,tenant_id,client_id,profession_code,plan_type,title,status,current_version,created_by,authorised_consultant_id,daily_calories_target,daily_protein_target_g,created_at,updated_at)
      VALUES (:id,:tenant,:client,:profession,'DIET_PLAN',:title,'DRAFT',1,:actor,:actor,:calories,:protein,:now,:now)"""),
      {"id":plan_id,"tenant":ctx["tenant_id"],"client":body.client_id,"profession":config["profession"],"title":body.name,"actor":ctx["user_id"],"calories":body.daily_calories_target,"protein":body.daily_protein_target_g,"now":now})
    measurement=health_context["measurement_context"]
    snapshot={"daily_calories_target":body.daily_calories_target,"daily_protein_target_g":body.daily_protein_target_g,"health_goals":body.health_goals,"actual_calories":0,"actual_protein_g":0,"source":"CONSULTANT_AUTHORED",
      "target_methodology":"PROFESSIONAL_JUDGEMENT","target_reviewed_by":ctx["user_id"],
      "measurement_context_fingerprint":measurement["measurement_context_fingerprint"],
      "measurement_source_ids":measurement["source_measurement_ids"],"measurement_snapshot":measurement["eligible_latest"],
      "measurement_calculations":measurement["calculations"],"assessment_id":readiness["assessment_id"],
      "assessment_version":readiness["assessment_version"]}
    await db.execute(text("""INSERT INTO external_profession_plan_versions
      (id,plan_id,tenant_id,client_id,version,status,title,nutrition_snapshot,created_by,created_at)
      VALUES (:id,:plan,:tenant,:client,1,'DRAFT',:title,CAST(:snapshot AS jsonb),:actor,:now)"""),
      {"id":version_id,"plan":plan_id,"tenant":ctx["tenant_id"],"client":body.client_id,"title":body.name,"snapshot":json.dumps(snapshot),"actor":ctx["user_id"],"now":now})
    await db.execute(text("""INSERT INTO external_profession_plan_audit_events
      (id,plan_id,plan_version_id,tenant_id,client_id,event_type,actor_id,metadata,created_at)
      VALUES (:id,:plan,:version,:tenant,:client,'CREATED',:actor,CAST(:metadata AS jsonb),:now)"""),
      {"id":uuid4(),"plan":plan_id,"version":version_id,"tenant":ctx["tenant_id"],"client":body.client_id,"actor":ctx["user_id"],"metadata":json.dumps(snapshot),"now":now})
    await db.commit()
    return {"success":True,"data":{"id":str(plan_id),"version_id":str(version_id),"status":"DRAFT","version":1},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/diet-plans/{plan_id}")
async def get_diet_plan(request:Request,plan_id:UUID,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    plan=await _diet_plan_row(request,db,ctx,plan_id)
    if not plan:return error(request,404,"DIET_PLAN_NOT_FOUND","Diet Plan not found")
    return {"success":True,"data":await _diet_plan_projection(db,plan),"error":None,"request_id":request.state.correlation_id}

@app.put("/api/v1/practice-operations/diet-plans/{plan_id}/draft")
async def save_diet_plan(request:Request,plan_id:UUID,body:DietPlanSave,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    plan=await _diet_plan_row(request,db,ctx,plan_id)
    if not plan:return error(request,404,"DIET_PLAN_NOT_FOUND","Diet Plan not found")
    if plan["status"] in {"APPROVED","PUBLISHED","ARCHIVED"}:return error(request,409,"DIET_PLAN_IMMUTABLE","Approved and published Diet Plans are immutable")
    if plan["current_version"]!=body.expected_version:return error(request,409,"STALE_WRITE","This Diet Plan changed. Refresh and retry")
    readiness=await _current_diet_plan_readiness(db,ctx,plan["client_id"])
    health_context=await _diet_plan_health_context(db,ctx,plan["client_id"])
    now=datetime.now(timezone.utc);next_version=plan["current_version"]+1;version_id=uuid4()
    actual_calories=sum(float((item.get("nutrition") or {}).get("kcal") or 0) for item in body.options if item.get("selected",True))
    actual_protein=sum(float((item.get("nutrition") or {}).get("protein") or 0) for item in body.options if item.get("selected",True))
    measurement=health_context["measurement_context"]
    snapshot={"daily_calories_target":plan["daily_calories_target"],"daily_protein_target_g":float(plan["daily_protein_target_g"] or 0),"actual_calories":round(actual_calories,2),"actual_protein_g":round(actual_protein,2),"option_count":len(body.options),
      "target_methodology":"PROFESSIONAL_JUDGEMENT","target_reviewed_by":ctx["user_id"],
      "measurement_context_fingerprint":measurement["measurement_context_fingerprint"],
      "measurement_source_ids":measurement["source_measurement_ids"],"measurement_snapshot":measurement["eligible_latest"],
      "measurement_calculations":measurement["calculations"],"assessment_id":readiness["assessment_id"],
      "assessment_version":readiness["assessment_version"]}
    await db.execute(text("""INSERT INTO external_profession_plan_versions
      (id,plan_id,tenant_id,client_id,version,status,title,nutrition_snapshot,created_by,created_at)
      VALUES (:id,:plan,:tenant,:client,:version,'SAVED',:title,CAST(:snapshot AS jsonb),:actor,:now)"""),
      {"id":version_id,"plan":plan_id,"tenant":ctx["tenant_id"],"client":plan["client_id"],"version":next_version,"title":plan["title"],"snapshot":json.dumps(snapshot),"actor":ctx["user_id"],"now":now})
    section_id=uuid4();await db.execute(text("""INSERT INTO external_profession_plan_sections
      (id,plan_version_id,tenant_id,section_key,title,content,sort_order) VALUES (:id,:version,:tenant,'meal_options','Meal options',CAST(:content AS jsonb),1)"""),
      {"id":section_id,"version":version_id,"tenant":ctx["tenant_id"],"content":json.dumps(snapshot)})
    for index,item in enumerate(body.options):
        await db.execute(text("""INSERT INTO external_profession_plan_items
          (id,plan_section_id,tenant_id,item_key,label,content,sort_order) VALUES (:id,:section,:tenant,:key,:label,CAST(:content AS jsonb),:sort)"""),
          {"id":uuid4(),"section":section_id,"tenant":ctx["tenant_id"],"key":f"option_{index+1}","label":str(item.get("mealHead") or "Meal option"),"content":json.dumps(item),"sort":index+1})
    await db.execute(text("UPDATE external_profession_plans SET status='SAVED',current_version=:version,updated_at=:now WHERE id=:plan AND tenant_id=:tenant"),{"version":next_version,"now":now,"plan":plan_id,"tenant":ctx["tenant_id"]})
    await db.execute(text("""INSERT INTO external_profession_plan_audit_events
      (id,plan_id,plan_version_id,tenant_id,client_id,event_type,actor_id,metadata,created_at)
      VALUES (:id,:plan,:version,:tenant,:client,'SAVED',:actor,CAST(:metadata AS jsonb),:now)"""),
      {"id":uuid4(),"plan":plan_id,"version":version_id,"tenant":ctx["tenant_id"],"client":plan["client_id"],"actor":ctx["user_id"],"metadata":json.dumps(snapshot),"now":now})
    await db.commit()
    return {"success":True,"data":{"id":str(plan_id),"version_id":str(version_id),"status":"SAVED","version":next_version,"nutrition":snapshot},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/diet-plans/{plan_id}/review")
async def review_diet_plan(request:Request,plan_id:UUID,body:DietPlanReviewAction,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    plan=await _diet_plan_row(request,db,ctx,plan_id)
    if not plan:return error(request,404,"DIET_PLAN_NOT_FOUND","Diet Plan not found")
    if plan["current_version"]!=body.expected_version:return error(request,409,"STALE_WRITE","This Diet Plan changed. Refresh and retry")
    transitions={"SUBMIT":({"DRAFT","SAVED","CHANGES_REQUESTED"},"SUBMITTED"),"START_REVIEW":({"SUBMITTED"},"UNDER_REVIEW"),"REQUEST_CHANGES":({"SUBMITTED","UNDER_REVIEW"},"CHANGES_REQUESTED"),"APPROVE":({"UNDER_REVIEW"},"APPROVED")}
    allowed,target=transitions[body.action]
    if plan["status"] not in allowed:return error(request,409,"INVALID_DIET_PLAN_TRANSITION",f"Cannot {body.action.lower().replace('_',' ')} a {plan['status'].lower()} Diet Plan")
    if body.action!="SUBMIT" and ctx.get("role") not in DIET_PLAN_REVIEW_ROLES:return error(request,403,"SENIOR_REVIEW_REQUIRED","Senior Consultant or administrator authority is required")
    now=datetime.now(timezone.utc);version_id=(await db.execute(text("SELECT id FROM external_profession_plan_versions WHERE plan_id=:plan AND tenant_id=:tenant AND version=:version"),{"plan":plan_id,"tenant":ctx["tenant_id"],"version":plan["current_version"]})).scalar_one()
    await db.execute(text("UPDATE external_profession_plans SET status=:status,updated_at=:now WHERE id=:plan AND tenant_id=:tenant"),{"status":target,"now":now,"plan":plan_id,"tenant":ctx["tenant_id"]})
    await db.execute(text("UPDATE external_profession_plan_versions SET status=:status WHERE id=:version AND tenant_id=:tenant"),{"status":target,"version":version_id,"tenant":ctx["tenant_id"]})
    await db.execute(text("""INSERT INTO external_profession_plan_audit_events
      (id,plan_id,plan_version_id,tenant_id,client_id,event_type,actor_id,metadata,created_at)
      VALUES (:id,:plan,:version,:tenant,:client,:event,:actor,CAST(:metadata AS jsonb),:now)"""),
      {"id":uuid4(),"plan":plan_id,"version":version_id,"tenant":ctx["tenant_id"],"client":plan["client_id"],"event":target,"actor":ctx["user_id"],"metadata":json.dumps({"reason":body.reason,"version":body.expected_version}),"now":now})
    await db.commit()
    return {"success":True,"data":{"id":str(plan_id),"status":target,"version":body.expected_version},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/diet-plans/{plan_id}/publish")
async def publish_diet_plan(request:Request,plan_id:UUID,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    plan=await _diet_plan_row(request,db,ctx,plan_id)
    if not plan:return error(request,404,"DIET_PLAN_NOT_FOUND","Diet Plan not found")
    readiness=await _current_diet_plan_readiness(db,ctx,plan["client_id"])
    if readiness["outcome"]!="READY":return _diet_plan_readiness_error(request,readiness)
    eligibility=await _diet_plan_publication_eligibility(db,ctx,plan["authorised_consultant_id"])
    independently_publishable=can_publish_independently(verification_state=eligibility["state"],experience_years=eligibility["experience_years"],plan_status=plan["status"],actor_is_author=str(ctx["user_id"])==str(plan["authorised_consultant_id"]))
    if plan["status"]!="APPROVED" and not independently_publishable:
        code="PROFESSIONAL_EXPERIENCE_UNVERIFIED" if eligibility["state"]=="UNVERIFIED" else "DIET_PLAN_APPROVAL_REQUIRED"
        message="Verified professional experience is required for independent publication" if eligibility["state"]=="UNVERIFIED" else "Senior review is required when verified experience is under one year"
        return error(request,409,code,message)
    version_row=(await db.execute(text("""SELECT id,nutrition_snapshot FROM external_profession_plan_versions
      WHERE plan_id=:plan AND tenant_id=:tenant AND version=:version"""),{"plan":plan_id,"tenant":ctx["tenant_id"],"version":plan["current_version"]})).mappings().one()
    option_count=int((version_row["nutrition_snapshot"] or {}).get("option_count") or 0)
    if option_count<1:return error(request,409,"DIET_PLAN_CONTENT_REQUIRED","Add and save governed meal options before publication")
    current_context=await _measurement_projection(db,ctx["tenant_id"],plan["client_id"])
    if (version_row["nutrition_snapshot"] or {}).get("measurement_context_fingerprint")!=current_context["measurement_context_fingerprint"]:
        return error(request,409,"DIET_PLAN_MEASUREMENT_CONTEXT_STALE","Measurements changed after this draft was saved. Review the assessment and save a new plan version")
    lineage=(await db.execute(text("""SELECT assessment_id,assessment_version FROM external_diet_plan_assessment_links
      WHERE tenant_id=:tenant AND client_id=:client AND external_plan_id=:plan AND external_plan_version=:version
      AND legacy_lineage_state='LINKED'"""),{"tenant":ctx["tenant_id"],"client":plan["client_id"],"plan":str(plan_id),"version":str(plan["current_version"])})).mappings().first()
    if not lineage:return error(request,409,"NUTRITION_ASSESSMENT_REQUIRED","Bind an approved current Nutrition Assessment before publication")
    now=datetime.now(timezone.utc);version_id=(await db.execute(text("UPDATE external_profession_plan_versions SET status='PUBLISHED',published_at=:now WHERE plan_id=:plan AND tenant_id=:tenant AND version=:version RETURNING id"),{"now":now,"plan":plan_id,"tenant":ctx["tenant_id"],"version":plan["current_version"]})).scalar_one()
    await db.execute(text("UPDATE external_profession_plans SET status='PUBLISHED',updated_at=:now WHERE id=:plan AND tenant_id=:tenant"),{"now":now,"plan":plan_id,"tenant":ctx["tenant_id"]})
    await db.execute(text("INSERT INTO external_profession_plan_audit_events(id,plan_id,plan_version_id,tenant_id,client_id,event_type,actor_id,created_at) VALUES (:id,:plan,:version,:tenant,:client,'PUBLISHED',:actor,:now)"),{"id":uuid4(),"plan":plan_id,"version":version_id,"tenant":ctx["tenant_id"],"client":plan["client_id"],"actor":ctx["user_id"],"now":now});await db.commit()
    return {"success":True,"data":{"id":str(plan_id),"status":"PUBLISHED","version":plan["current_version"],"publication_basis":"INDEPENDENT_VERIFIED_EXPERIENCE" if independently_publishable else "SENIOR_APPROVED"},"error":None,"request_id":request.state.correlation_id}

async def _write_note_sections(db,tenant,version_id,sections):
    for order,section in enumerate(sections,1):
        await db.execute(text("INSERT INTO external_session_note_sections(id,note_version_id,tenant_id,section_key,title,content,visibility,sort_order) VALUES (:id,:version,:tenant,:key,:title,CAST(:content AS jsonb),:visibility,:sort)"),{"id":uuid4(),"version":version_id,"tenant":tenant,"key":section.key,"title":section.title,"content":json.dumps(section.content),"visibility":section.visibility,"sort":order})

def _private_note_cipher():
    secret=get_settings().private_notes_encryption_key.encode()
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(secret).digest()))

@app.get("/api/v1/practice-operations/clients/{client_id}/session-notes")
async def list_session_notes(request:Request,client_id:str,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx) or await require_capability(request,db,ctx,"SESSION_NOTES")
    if not denied:denied,_=await _team_guard(request,db,ctx,"PROFESSIONAL_NOTE_VIEW",client_id)
    if denied:return denied
    rows=(await db.execute(text("SELECT id,consultation_id,note_type,title,status,current_version,created_at,updated_at FROM external_session_notes WHERE tenant_id=:tenant AND client_id=:client ORDER BY updated_at DESC"),{"tenant":ctx["tenant_id"],"client":client_id})).mappings().all()
    return {"success":True,"data":{"items":[dict(row) for row in rows]},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/session-notes",status_code=201)
async def create_session_note(request:Request,body:SessionNoteCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx) or await require_capability(request,db,ctx,"SESSION_NOTES")
    if not denied:denied,_=await _team_guard(request,db,ctx,"PROFESSIONAL_NOTE_CREATE",body.client_id)
    if denied:return denied
    config=await configuration(db,ctx);note_id=uuid4();version_id=uuid4();now=datetime.now(timezone.utc)
    await db.execute(text("INSERT INTO external_session_notes(id,tenant_id,client_id,profession_code,consultation_id,note_type,title,status,current_version,created_by,created_at,updated_at) VALUES (:id,:tenant,:client,:profession,:consultation,:type,:title,'DRAFT',1,:actor,:now,:now)"),{"id":note_id,"tenant":ctx["tenant_id"],"client":body.client_id,"profession":config["profession"],"consultation":body.consultation_id,"type":body.note_type,"title":body.title,"actor":ctx["user_id"],"now":now})
    await db.execute(text("INSERT INTO external_session_note_versions(id,note_id,tenant_id,client_id,version,status,title,created_by,created_at) VALUES (:id,:note,:tenant,:client,1,'DRAFT',:title,:actor,:now)"),{"id":version_id,"note":note_id,"tenant":ctx["tenant_id"],"client":body.client_id,"title":body.title,"actor":ctx["user_id"],"now":now});await _write_note_sections(db,ctx["tenant_id"],version_id,body.sections);await db.commit()
    return {"success":True,"data":{"id":str(note_id),"status":"DRAFT","version":1},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/session-notes/{note_id}")
async def session_note_detail(request:Request,note_id:UUID,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx) or await require_capability(request,db,ctx,"SESSION_NOTES")
    if denied:return denied
    note=(await db.execute(text("SELECT id,client_id,consultation_id,note_type,title,status,current_version,created_at,updated_at FROM external_session_notes WHERE id=:id AND tenant_id=:tenant"),{"id":note_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not note:return error(request,404,"SESSION_NOTE_NOT_FOUND","Session note not found")
    versions=[dict(row) for row in (await db.execute(text("SELECT id,version,status,title,amendment_reason,created_at,finalised_at FROM external_session_note_versions WHERE note_id=:note AND tenant_id=:tenant ORDER BY version DESC"),{"note":note_id,"tenant":ctx["tenant_id"]})).mappings().all()];current=next(row for row in versions if row["version"]==note["current_version"])
    sections=[dict(row) for row in (await db.execute(text("SELECT id,section_key,title,content,visibility,sort_order FROM external_session_note_sections WHERE note_version_id=:version AND tenant_id=:tenant ORDER BY sort_order"),{"version":current["id"],"tenant":ctx["tenant_id"]})).mappings().all()]
    return {"success":True,"data":{"note":dict(note),"versions":versions,"sections":sections},"error":None,"request_id":request.state.correlation_id}

@app.patch("/api/v1/practice-operations/session-notes/{note_id}")
async def save_session_note(request:Request,note_id:UUID,body:SessionNoteSave,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx) or await require_capability(request,db,ctx,"SESSION_NOTES")
    if denied:return denied
    note=(await db.execute(text("SELECT id,client_id,status,current_version FROM external_session_notes WHERE id=:id AND tenant_id=:tenant"),{"id":note_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not note:return error(request,404,"SESSION_NOTE_NOT_FOUND","Session note not found")
    if note["status"] in {"FINALISED","AMENDED"}:return error(request,409,"FINALISED_NOTE_IMMUTABLE","Finalised note versions are immutable; create an amendment")
    if note["current_version"]!=body.expected_version:return error(request,409,"STALE_WRITE","This note changed. Refresh and retry")
    version=(await db.execute(text("SELECT id FROM external_session_note_versions WHERE note_id=:note AND tenant_id=:tenant AND version=:version"),{"note":note_id,"tenant":ctx["tenant_id"],"version":note["current_version"]})).scalar_one();await db.execute(text("DELETE FROM external_session_note_sections WHERE note_version_id=:version AND tenant_id=:tenant"),{"version":version,"tenant":ctx["tenant_id"]});await _write_note_sections(db,ctx["tenant_id"],version,body.sections);now=datetime.now(timezone.utc)
    await db.execute(text("UPDATE external_session_note_versions SET status='SAVED',title=:title WHERE id=:version"),{"title":body.title,"version":version});await db.execute(text("UPDATE external_session_notes SET status='SAVED',title=:title,updated_at=:now WHERE id=:note AND tenant_id=:tenant"),{"title":body.title,"now":now,"note":note_id,"tenant":ctx["tenant_id"]});await db.commit()
    return {"success":True,"data":{"id":str(note_id),"status":"SAVED","version":note["current_version"]},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/session-notes/{note_id}/finalise")
async def finalise_session_note(request:Request,note_id:UUID,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx) or await require_capability(request,db,ctx,"SESSION_NOTES")
    if denied:return denied
    now=datetime.now(timezone.utc);row=(await db.execute(text("UPDATE external_session_notes SET status='FINALISED',updated_at=:now WHERE id=:id AND tenant_id=:tenant AND status IN ('DRAFT','SAVED') RETURNING current_version"),{"now":now,"id":note_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not row:return error(request,409,"NOTE_NOT_FINALISABLE","This note cannot be finalised")
    await db.execute(text("UPDATE external_session_note_versions SET status='FINALISED',finalised_at=:now WHERE note_id=:note AND tenant_id=:tenant AND version=:version"),{"now":now,"note":note_id,"tenant":ctx["tenant_id"],"version":row["current_version"]});await db.commit();return {"success":True,"data":{"id":str(note_id),"status":"FINALISED"},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/session-notes/{note_id}/amendments",status_code=201)
async def amend_session_note(request:Request,note_id:UUID,body:SessionNoteAmendment,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx) or await require_capability(request,db,ctx,"SESSION_NOTES")
    if denied:return denied
    note=(await db.execute(text("SELECT client_id,status,current_version FROM external_session_notes WHERE id=:id AND tenant_id=:tenant"),{"id":note_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not note or note["status"] not in {"FINALISED","AMENDED"}:return error(request,409,"AMENDMENT_REQUIRES_FINALISED_NOTE","Only a finalised note can be amended")
    version_number=note["current_version"]+1;version_id=uuid4();now=datetime.now(timezone.utc)
    await db.execute(text("INSERT INTO external_session_note_versions(id,note_id,tenant_id,client_id,version,status,title,amendment_reason,created_by,created_at,finalised_at) VALUES (:id,:note,:tenant,:client,:version,'AMENDED',:title,:reason,:actor,:now,:now)"),{"id":version_id,"note":note_id,"tenant":ctx["tenant_id"],"client":note["client_id"],"version":version_number,"title":body.title,"reason":body.reason,"actor":ctx["user_id"],"now":now});await _write_note_sections(db,ctx["tenant_id"],version_id,body.sections)
    await db.execute(text("UPDATE external_session_notes SET status='AMENDED',title=:title,current_version=:version,updated_at=:now WHERE id=:note AND tenant_id=:tenant"),{"title":body.title,"version":version_number,"now":now,"note":note_id,"tenant":ctx["tenant_id"]});await db.commit();return {"success":True,"data":{"id":str(note_id),"status":"AMENDED","version":version_number},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/session-notes/{note_id}/private")
async def list_private_notes(request:Request,note_id:UUID,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx) or await require_capability(request,db,ctx,"PRIVATE_NOTES")
    if denied:return denied
    note=(await db.execute(text("SELECT client_id FROM external_session_notes WHERE id=:id AND tenant_id=:tenant"),{"id":note_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not note:return error(request,404,"SESSION_NOTE_NOT_FOUND","Session note not found")
    denied,_=await _team_guard(request,db,ctx,"PRIVATE_NOTE_VIEW",note["client_id"])
    if denied:return denied
    rows=(await db.execute(text("SELECT id,encrypted_content,created_by,created_at,updated_at FROM external_session_private_notes WHERE note_id=:note AND tenant_id=:tenant AND created_by=:actor ORDER BY created_at DESC"),{"note":note_id,"tenant":ctx["tenant_id"],"actor":ctx["user_id"]})).mappings().all();cipher=_private_note_cipher()
    return {"success":True,"data":{"items":[{"id":row["id"],"content":cipher.decrypt(row["encrypted_content"].encode()).decode(),"created_by":row["created_by"],"created_at":row["created_at"],"updated_at":row["updated_at"]} for row in rows]},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/session-notes/{note_id}/private",status_code=201)
async def create_private_note(request:Request,note_id:UUID,body:PrivateNoteCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx) or await require_capability(request,db,ctx,"PRIVATE_NOTES")
    if denied:return denied
    note=(await db.execute(text("SELECT client_id FROM external_session_notes WHERE id=:id AND tenant_id=:tenant"),{"id":note_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not note:return error(request,404,"SESSION_NOTE_NOT_FOUND","Session note not found")
    denied,_=await _team_guard(request,db,ctx,"PRIVATE_NOTE_CREATE",note["client_id"])
    if denied:return denied
    item_id=uuid4();now=datetime.now(timezone.utc);encrypted=_private_note_cipher().encrypt(body.content.encode()).decode()
    await db.execute(text("INSERT INTO external_session_private_notes(id,note_id,tenant_id,client_id,encrypted_content,created_by,created_at,updated_at) VALUES (:id,:note,:tenant,:client,:content,:actor,:now,:now)"),{"id":item_id,"note":note_id,"tenant":ctx["tenant_id"],"client":note["client_id"],"content":encrypted,"actor":ctx["user_id"],"now":now});await db.commit();return {"success":True,"data":{"id":str(item_id)},"error":None,"request_id":request.state.correlation_id}

async def _progress_guard(request,db,ctx):
    return external_only(request,ctx) or await require_capability(request,db,ctx,"GOALS_PROGRESS")

PROFESSION_SIGNAL_CODES={
 "DIABETES_EDUCATOR":{"assessment":"ASSESSMENT_REVIEW_PENDING","followup":"EDUCATION_FOLLOWUP_DUE","goal":"LIFESTYLE_GOAL_REVIEW","plan":"EDUCATION_PLAN_REVIEW_DUE","task":"SELF_MANAGEMENT_REVIEW_DUE"},
 "PSYCHOLOGIST":{"assessment":"ASSESSMENT_REVIEW_PENDING","followup":"SESSION_FOLLOWUP_DUE","goal":"THERAPY_GOAL_REVIEW","plan":"THERAPY_PLAN_REVIEW","task":"HOMEWORK_REVIEW_DUE","missed":"MISSED_SESSION"},
 "WELLNESS_CONSULTANT":{"assessment":"ASSESSMENT_REVIEW_PENDING","followup":"WELLNESS_CHECKIN_DUE","goal":"WELLNESS_GOAL_REVIEW","plan":"WELLNESS_PLAN_REVIEW","task":"HABIT_REVIEW_DUE"},
 "HEALTH_COACH":{"followup":"CHECKIN_OVERDUE","goal":"GOAL_STAGNATION","plan":"COACHING_PLAN_REVIEW","task":"ACCOUNTABILITY_TASK_DUE"},
 "BEHAVIOURAL_THERAPIST":{"assessment":"ASSESSMENT_REVIEW_PENDING","followup":"BEHAVIOUR_REVIEW_DUE","goal":"TARGET_BEHAVIOUR_DATA_INCOMPLETE","plan":"INTERVENTION_PLAN_REVIEW","task":"CAREGIVER_TASK_DUE"},
 "OCCUPATIONAL_THERAPIST":{"assessment":"FUNCTION_REASSESSMENT_DUE","followup":"FOLLOWUP_DUE","goal":"ADL_GOAL_REVIEW","plan":"OT_PLAN_REVIEW","task":"ACTIVITY_ADHERENCE_REVIEW"},
 "PHYSIOTHERAPIST":{"assessment":"FUNCTION_REASSESSMENT_DUE","followup":"FOLLOWUP_OVERDUE","goal":"REHAB_MILESTONE_DUE","plan":"REHAB_PLAN_REVIEW","task":"EXERCISE_ADHERENCE_REVIEW"},
 "MENTAL_WELLNESS_THERAPIST":{"assessment":"MOOD_REVIEW_DUE","followup":"SESSION_FOLLOWUP_DUE","goal":"GOAL_REVIEW","plan":"SUPPORT_PLAN_REVIEW","task":"STRESS_REVIEW_DUE"},
}

@app.get("/api/v1/practice-operations/intelligence/signals")
async def profession_intelligence_signals(request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    config=await configuration(db,ctx);profession=config["profession"];codes=PROFESSION_SIGNAL_CODES.get(profession,{})
    tenant=ctx["tenant_id"];now=datetime.now(timezone.utc);items=[]
    def add(kind,row,reason,target):
        code=codes.get(kind)
        if not code:return
        source={"assessment":"external_assessment_instances","followup":"practice_follow_ups","goal":"practice_goals","plan":"external_profession_plans","task":"practice_tasks","missed":"practice_consultations"}[kind]
        items.append({"signal_code":code,"profession_code":profession,"tenant_id":tenant,"client_id":row["client_id"],"source_domain":source,"source_record_id":str(row["id"]),"reason":reason,"occurred_at":row.get("updated_at") or row.get("created_at"),"due_at":row.get("due_at"),"priority":"P3_MEDIUM" if kind in {"assessment","followup","missed"} else "P4_LOW","cta":{"label":"Review","target":target},"provenance":{"table":source,"record_id":str(row["id"])},"resolution_state":"ACTIVE"})
    assessments=(await db.execute(text("SELECT id,client_id,status,due_at,updated_at FROM external_assessment_instances WHERE tenant_id=:tenant AND status IN ('ASSIGNED','IN_PROGRESS','COMPLETED') AND (status='COMPLETED' OR due_at<:now)"),{"tenant":tenant,"now":now})).mappings().all()
    for row in assessments:add("assessment",row,"Assessment is ready or due for practitioner review.","assessments")
    for kind,table,target,label in (("followup","practice_follow_ups","followups","Follow-up is due for review."),("task","practice_tasks","tasks","Practice task is due for review.")):
        rows=(await db.execute(text(f"SELECT id,client_id,due_at,updated_at FROM {table} WHERE tenant_id=:tenant AND due_at<:now AND status NOT IN ('COMPLETED','CANCELLED','ARCHIVED')"),{"tenant":tenant,"now":now})).mappings().all()
        for row in rows:add(kind,row,label,target)
    goals=(await db.execute(text("SELECT id,client_id,updated_at,due_at FROM practice_goals WHERE tenant_id=:tenant AND status NOT IN ('COMPLETED','CANCELLED','ARCHIVED') AND updated_at<:stale"),{"tenant":tenant,"stale":now-timedelta(days=30)})).mappings().all()
    for row in goals:add("goal",row,"Goal has not been updated in 30 days and needs workflow review.","goals")
    plans=(await db.execute(text("SELECT id,client_id,updated_at,NULL::timestamptz AS due_at FROM external_profession_plans WHERE tenant_id=:tenant AND status IN ('DRAFT','SAVED','PUBLISHED') AND updated_at<:stale"),{"tenant":tenant,"stale":now-timedelta(days=30)})).mappings().all()
    for row in plans:add("plan",row,"Profession plan has reached its operational review interval.","client")
    missed=(await db.execute(text("SELECT id,client_id,updated_at,due_at FROM practice_consultations WHERE tenant_id=:tenant AND status='MISSED'"),{"tenant":tenant})).mappings().all()
    for row in missed:add("missed",row,"A recorded session was missed and needs follow-up.","consultations")
    if "BILLING" in set(config["capabilities"]):
        billing_rows=(await db.execute(text("""SELECT id,client_id,status,due_date,updated_at,balance_due_minor,
          CASE WHEN due_date<CURRENT_DATE THEN 'INVOICE_OVERDUE'
               WHEN status='PART_PAID' THEN 'PART_PAYMENT_OUTSTANDING'
               ELSE 'PAYMENT_DUE_SOON' END AS signal_code
          FROM external_invoices WHERE tenant_id=:tenant AND status IN ('ISSUED','PART_PAID','OVERDUE')
          AND balance_due_minor>0 AND (due_date<=CURRENT_DATE+INTERVAL '7 days' OR status='PART_PAID')"""),
          {"tenant":tenant})).mappings().all()
        for row in billing_rows:
            items.append({"signal_code":row["signal_code"],"profession_code":profession,"tenant_id":tenant,
              "client_id":row["client_id"],"source_domain":"external_invoices","source_record_id":str(row["id"]),
              "reason":"An issued invoice has an outstanding recorded balance.","occurred_at":row["updated_at"],
              "due_at":row["due_date"],"priority":"P3_MEDIUM" if row["signal_code"]=="INVOICE_OVERDUE" else "P4_LOW",
              "cta":{"label":"Open Invoice","target":"billing"},
              "provenance":{"table":"external_invoices","record_id":str(row["id"])},"resolution_state":"ACTIVE"})
    if "HOMEWORK" in set(config["capabilities"]):
        homework_rows=(await db.execute(text("""SELECT id,client_id,status,due_date,updated_at,
          CASE WHEN status='MISSED' THEN 'HOMEWORK_MISSED'
               WHEN due_date<CURRENT_DATE THEN 'HOMEWORK_OVERDUE' ELSE 'HOMEWORK_DUE' END AS signal_code
          FROM external_homework_assignments WHERE tenant_id=:tenant
          AND status IN ('NOT_STARTED','IN_PROGRESS','MISSED')
          AND (status='MISSED' OR due_date<=CURRENT_DATE+INTERVAL '3 days')"""),{"tenant":tenant})).mappings().all()
        for row in homework_rows:
            items.append({"signal_code":row["signal_code"],"profession_code":profession,"tenant_id":tenant,
              "client_id":row["client_id"],"source_domain":"external_homework_assignments","source_record_id":str(row["id"]),
              "reason":"Client homework is due or has a recorded missed status.","occurred_at":row["updated_at"],
              "due_at":row["due_date"],"priority":"P3_MEDIUM" if row["signal_code"]!="HOMEWORK_DUE" else "P4_LOW",
              "cta":{"label":"Review Homework","target":"client"},
              "provenance":{"table":"external_homework_assignments","record_id":str(row["id"])},"resolution_state":"ACTIVE"})
        unopened=(await db.execute(text("""SELECT id,client_id,assigned_at FROM external_resource_assignments
          WHERE tenant_id=:tenant AND status='ASSIGNED' AND assigned_at<:cutoff"""),
          {"tenant":tenant,"cutoff":now-timedelta(days=7)})).mappings().all()
        for row in unopened:
            items.append({"signal_code":"RESOURCE_ASSIGNED_NOT_OPENED","profession_code":profession,"tenant_id":tenant,
              "client_id":row["client_id"],"source_domain":"external_resource_assignments","source_record_id":str(row["id"]),
              "reason":"An assigned resource has no explicit open event after seven days.","occurred_at":row["assigned_at"],
              "due_at":None,"priority":"P4_LOW","cta":{"label":"Review Resource","target":"client"},
              "provenance":{"table":"external_resource_assignments","record_id":str(row["id"])},"resolution_state":"ACTIVE"})
        adherence_rows=(await db.execute(text("""SELECT client_id,MAX(updated_at) AS updated_at,
          COUNT(*)::int AS assigned_count,COUNT(*) FILTER (WHERE status='COMPLETED')::int AS completed_count
          FROM external_homework_assignments WHERE tenant_id=:tenant AND start_date>=CURRENT_DATE-INTERVAL '29 days'
          GROUP BY client_id HAVING COUNT(*)>=2 AND
          (COUNT(*) FILTER (WHERE status='COMPLETED')::numeric/COUNT(*))<0.5"""),{"tenant":tenant})).mappings().all()
        for row in adherence_rows:
            items.append({"signal_code":"ADHERENCE_NEEDS_ATTENTION","profession_code":profession,"tenant_id":tenant,
              "client_id":row["client_id"],"source_domain":"external_homework_assignments","source_record_id":row["client_id"],
              "reason":f"{row['completed_count']} of {row['assigned_count']} assigned activities were completed in the last 30 days.",
              "occurred_at":row["updated_at"],"due_at":None,"priority":"P3_MEDIUM",
              "cta":{"label":"Review Adherence","target":"client"},
              "provenance":{"table":"external_homework_assignments","client_id":row["client_id"],"window":"30_DAY"},"resolution_state":"ACTIVE"})
    items.sort(key=lambda item:(item["priority"],str(item.get("due_at") or item.get("occurred_at") or "")))
    return {"success":True,"data":{"profession_code":profession,"items":items},"error":None,"request_id":request.state.correlation_id}

async def _write_template_sections(db,tenant,version_id,sections):
    for section_index,section in enumerate(sections):
        section_id=uuid4();await db.execute(text("INSERT INTO external_template_sections(id,template_version_id,tenant_id,section_key,title,description,sort_order) VALUES (:id,:version,:tenant,:key,:title,:description,:sort)"),{"id":section_id,"version":version_id,"tenant":tenant,"key":section.key,"title":section.title,"description":section.description,"sort":section_index})
        for item_index,item in enumerate(section.items):await db.execute(text("INSERT INTO external_template_items(id,section_id,tenant_id,item_key,label,item_type,config,sort_order) VALUES (:id,:section,:tenant,:key,:label,:type,CAST(:config AS jsonb),:sort)"),{"id":uuid4(),"section":section_id,"tenant":tenant,"key":item.key,"label":item.label,"type":item.item_type,"config":json.dumps(item.config),"sort":item_index})

@app.get("/api/v1/practice-operations/templates")
async def list_templates(request:Request,scope:str|None=None,template_type:str|None=None,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    config=await configuration(db,ctx);rows=(await db.execute(text("SELECT id,profession_code,template_type,scope,owner_id,title,description,active,current_version,updated_at FROM external_template_definitions WHERE active=TRUE AND profession_code=:profession AND (scope='SYSTEM' OR tenant_id=:tenant) AND (CAST(:scope AS text) IS NULL OR scope=CAST(:scope AS text)) AND (CAST(:type AS text) IS NULL OR template_type=CAST(:type AS text)) ORDER BY scope,title"),{"profession":config["profession"],"tenant":ctx["tenant_id"],"scope":scope,"type":template_type})).mappings().all()
    return {"success":True,"data":{"items":[dict(row) for row in rows]},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/templates",status_code=201)
async def create_template(request:Request,body:TemplateCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    if body.scope=="PRACTICE" and (ctx.get("role") or "").upper() not in {"OWNER","ADMIN","ORGANISATION_ADMIN"}:return error(request,403,"PRACTICE_ADMIN_REQUIRED","Practice template creation requires owner or administrator access")
    config=await configuration(db,ctx);definition_id=uuid4();version_id=uuid4();now=datetime.now(timezone.utc);tenant=ctx["tenant_id"]
    await db.execute(text("INSERT INTO external_template_definitions(id,tenant_id,profession_code,template_type,scope,owner_id,title,description,active,current_version,created_by,created_at,updated_at) VALUES (:id,:tenant,:profession,:type,:scope,:owner,:title,:description,TRUE,1,:actor,:now,:now)"),{"id":definition_id,"tenant":tenant,"profession":config["profession"],"type":body.template_type,"scope":body.scope,"owner":ctx["user_id"] if body.scope=="PRACTITIONER" else None,"title":body.title,"description":body.description,"actor":ctx["user_id"],"now":now})
    await db.execute(text("INSERT INTO external_template_versions(id,definition_id,tenant_id,version,title,description,status,created_by,created_at) VALUES (:id,:definition,:tenant,1,:title,:description,'ACTIVE',:actor,:now)"),{"id":version_id,"definition":definition_id,"tenant":tenant,"title":body.title,"description":body.description,"actor":ctx["user_id"],"now":now});await _write_template_sections(db,tenant,version_id,body.sections);await db.execute(text("INSERT INTO external_template_audit_events(id,definition_id,template_version_id,tenant_id,event_type,actor_id,created_at) VALUES (:id,:definition,:version,:tenant,'CREATED',:actor,:now)"),{"id":uuid4(),"definition":definition_id,"version":version_id,"tenant":tenant,"actor":ctx["user_id"],"now":now});await db.commit();return {"success":True,"data":{"id":str(definition_id),"version":1},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/templates/{template_id}")
async def get_template(request:Request,template_id:UUID,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    row=(await db.execute(text("SELECT id,tenant_id,profession_code,template_type,scope,owner_id,title,description,active,current_version,created_by,created_at,updated_at FROM external_template_definitions WHERE id=:id AND (scope='SYSTEM' OR tenant_id=:tenant)"),{"id":template_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not row:return error(request,404,"TEMPLATE_NOT_FOUND","Template not found")
    version=(await db.execute(text("SELECT id,definition_id,tenant_id,version,title,description,status,created_by,created_at FROM external_template_versions WHERE definition_id=:id AND version=:version"),{"id":template_id,"version":row["current_version"]})).mappings().one();sections=[dict(item) for item in (await db.execute(text("SELECT id,template_version_id,tenant_id,section_key,title,description,sort_order FROM external_template_sections WHERE template_version_id=:version ORDER BY sort_order"),{"version":version["id"]})).mappings().all()];items=[dict(item) for item in (await db.execute(text("SELECT i.id,i.section_id,i.tenant_id,i.item_key,i.label,i.item_type,i.config,i.sort_order FROM external_template_items i JOIN external_template_sections s ON s.id=i.section_id WHERE s.template_version_id=:version ORDER BY s.sort_order,i.sort_order"),{"version":version["id"]})).mappings().all()]
    for section in sections:section["items"]=[item for item in items if item["section_id"]==section["id"]]
    return {"success":True,"data":{"definition":dict(row),"version":dict(version),"sections":sections,"locked":row["scope"]=="SYSTEM"},"error":None,"request_id":request.state.correlation_id}

@app.patch("/api/v1/practice-operations/templates/{template_id}")
async def update_template(request:Request,template_id:UUID,body:TemplateUpdate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    row=(await db.execute(text("SELECT scope,owner_id,current_version FROM external_template_definitions WHERE id=:id AND tenant_id=:tenant AND active=TRUE"),{"id":template_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not row:return error(request,404,"TEMPLATE_NOT_FOUND","Editable template not found")
    if row["scope"]=="SYSTEM":return error(request,409,"SYSTEM_TEMPLATE_IMMUTABLE","System templates require a new governed version")
    if row["scope"]=="PRACTITIONER" and row["owner_id"]!=ctx["user_id"]:return error(request,403,"TEMPLATE_OWNER_REQUIRED","Only the owning practitioner may edit this template")
    if row["current_version"]!=body.expected_version:return error(request,409,"TEMPLATE_VERSION_CONFLICT","Template has changed; reload before editing")
    version_number=row["current_version"]+1;version_id=uuid4();now=datetime.now(timezone.utc);tenant=ctx["tenant_id"]
    await db.execute(text("UPDATE external_template_versions SET status='SUPERSEDED' WHERE definition_id=:id AND status='ACTIVE'"),{"id":template_id});await db.execute(text("INSERT INTO external_template_versions(id,definition_id,tenant_id,version,title,description,status,created_by,created_at) VALUES (:id,:definition,:tenant,:version,:title,:description,'ACTIVE',:actor,:now)"),{"id":version_id,"definition":template_id,"tenant":tenant,"version":version_number,"title":body.title,"description":body.description,"actor":ctx["user_id"],"now":now});await _write_template_sections(db,tenant,version_id,body.sections);await db.execute(text("UPDATE external_template_definitions SET title=:title,description=:description,current_version=:version,updated_at=:now WHERE id=:id"),{"title":body.title,"description":body.description,"version":version_number,"now":now,"id":template_id});await db.execute(text("INSERT INTO external_template_audit_events(id,definition_id,template_version_id,tenant_id,event_type,actor_id,created_at) VALUES (:event,:definition,:version,:tenant,'VERSION_CREATED',:actor,:now)"),{"event":uuid4(),"definition":template_id,"version":version_id,"tenant":tenant,"actor":ctx["user_id"],"now":now});await db.commit();return {"success":True,"data":{"id":str(template_id),"version":version_number},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/templates/{template_id}/duplicate",status_code=201)
async def duplicate_template(request:Request,template_id:UUID,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    source=(await db.execute(text("SELECT template_type,title,description FROM external_template_definitions WHERE id=:id AND (scope='SYSTEM' OR tenant_id=:tenant) AND active=TRUE"),{"id":template_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not source:return error(request,404,"TEMPLATE_NOT_FOUND","Template not found")
    detail=await get_template(request,template_id,ctx,db);payload=detail["data"];body=TemplateCreate(template_type=source["template_type"],scope="PRACTITIONER",title=f'{source["title"]} copy',description=source["description"],sections=[{"key":section["section_key"],"title":section["title"],"description":section["description"],"items":[{"key":item["item_key"],"label":item["label"],"item_type":item["item_type"],"config":item["config"]} for item in section["items"]]} for section in payload["sections"]]);return await create_template(request,body,ctx,db)

@app.post("/api/v1/practice-operations/templates/{template_id}/archive")
async def archive_template(request:Request,template_id:UUID,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    result=await db.execute(text("UPDATE external_template_definitions SET active=FALSE,updated_at=:now WHERE id=:id AND tenant_id=:tenant AND scope<>'SYSTEM' AND (scope='PRACTICE' OR owner_id=:actor)"),{"now":datetime.now(timezone.utc),"id":template_id,"tenant":ctx["tenant_id"],"actor":ctx["user_id"]})
    if result.rowcount!=1:return error(request,404,"EDITABLE_TEMPLATE_NOT_FOUND","Editable custom template not found")
    await db.commit();return {"success":True,"data":{"id":str(template_id),"archived":True},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/clients/{client_id}/session-briefing")
async def session_briefing(request:Request,client_id:str,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    tenant=ctx["tenant_id"];params={"tenant":tenant,"client":client_id};summary=[];changed=[];outstanding=[];progress=[];refs=[]
    async def latest(query):return (await db.execute(text(query),params)).mappings().first()
    last_note=await latest("SELECT id,title,status,updated_at FROM external_session_notes WHERE tenant_id=:tenant AND client_id=:client AND status IN ('FINALISED','AMENDED') ORDER BY updated_at DESC LIMIT 1")
    if last_note:summary.append({"text":f'Last completed session: {last_note["title"]}',"source_ref":f'session-note:{last_note["id"]}'});refs.append({"domain":"external_session_notes","id":str(last_note["id"])})
    assessment=await latest("SELECT id,status,completed_at,updated_at FROM external_assessment_instances WHERE tenant_id=:tenant AND client_id=:client ORDER BY updated_at DESC LIMIT 1")
    if assessment:changed.append({"text":f'Latest assessment status: {assessment["status"].replace("_"," ").lower()}',"source_ref":f'assessment:{assessment["id"]}'});refs.append({"domain":"external_assessment_instances","id":str(assessment["id"])})
    for domain,table,label,target in (("task","practice_tasks","Open task","outstanding"),("followup","practice_follow_ups","Open follow-up","outstanding"),("goal","practice_goals","Active goal","progress")):
        rows=(await db.execute(text(f"SELECT id,title,status,due_at,updated_at FROM {table} WHERE tenant_id=:tenant AND client_id=:client AND status NOT IN ('COMPLETED','CANCELLED','ARCHIVED') ORDER BY updated_at DESC LIMIT 5"),params)).mappings().all()
        for row in rows:
            item={"text":f'{label}: {row["title"]}',"source_ref":f'{domain}:{row["id"]}',"due_at":row["due_at"]};(outstanding if target=="outstanding" else progress).append(item);refs.append({"domain":table,"id":str(row["id"])})
    plan=await latest("SELECT id,title,status,updated_at FROM external_profession_plans WHERE tenant_id=:tenant AND client_id=:client ORDER BY updated_at DESC LIMIT 1")
    if plan:changed.append({"text":f'Latest plan: {plan["title"]} ({plan["status"].lower()})',"source_ref":f'profession-plan:{plan["id"]}'});refs.append({"domain":"external_profession_plans","id":str(plan["id"])})
    observations=(await db.execute(text("SELECT id,numeric_value,text_value,observed_at FROM external_progress_observations WHERE tenant_id=:tenant AND client_id=:client ORDER BY observed_at DESC LIMIT 5"),params)).mappings().all()
    for row in observations:progress.append({"text":f'Progress observation recorded: {row["numeric_value"] if row["numeric_value"] is not None else row["text_value"]}',"source_ref":f'progress:{row["id"]}'});refs.append({"domain":"external_progress_observations","id":str(row["id"])})
    communication=await latest("SELECT id,purpose,created_at FROM practice_communication_activity WHERE tenant_id=:tenant AND client_id=:client ORDER BY created_at DESC LIMIT 1")
    if communication:changed.append({"text":f'Latest communication: {communication["purpose"]}',"source_ref":f'communication:{communication["id"]}'});refs.append({"domain":"practice_communication_activity","id":str(communication["id"])})
    return {"success":True,"data":{"client_summary":summary,"since_last_session":changed,"items_to_review":outstanding+progress,"outstanding_actions":outstanding,"recent_progress":progress,"source_refs":refs,"partial_data":not bool(last_note)},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/session-assistant/suggestions",status_code=201)
async def generate_session_suggestions(request:Request,body:SessionSuggestionGenerate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    note=(await db.execute(text("SELECT id,client_id,title,status,current_version FROM external_session_notes WHERE id=:id AND tenant_id=:tenant"),{"id":body.session_note_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not note:return error(request,404,"SESSION_NOTE_NOT_FOUND","Session note not found")
    if note["status"] not in {"FINALISED","AMENDED"}:return error(request,409,"COMPLETED_SESSION_REQUIRED","Post-session suggestions require a finalised structured session")
    now=datetime.now(timezone.utc);suggestions=[("CREATE_FOLLOWUP","A finalised session is available for practitioner follow-up.",{"title":f'Follow up: {note["title"]}'}),("PREPARE_MESSAGE","Client communication may be prepared from the completed session.",{"purpose":"Post-session follow-up"})]
    for suggestion_type,reason,payload in suggestions:await db.execute(text("INSERT INTO external_session_action_suggestions(id,tenant_id,client_id,session_note_id,suggestion_type,reason,source,proposed_payload,confidence,status,practitioner_id,created_at,updated_at) VALUES (:id,:tenant,:client,:note,:type,:reason,CAST(:source AS jsonb),CAST(:payload AS jsonb),'ELIGIBLE','PROPOSED',:actor,:now,:now) ON CONFLICT (tenant_id,session_note_id,suggestion_type) DO NOTHING"),{"id":uuid4(),"tenant":ctx["tenant_id"],"client":note["client_id"],"note":note["id"],"type":suggestion_type,"reason":reason,"source":json.dumps({"domain":"external_session_notes","id":str(note["id"]),"version":note["current_version"]}),"payload":json.dumps(payload),"actor":ctx["user_id"],"now":now})
    await db.commit();return await list_session_suggestions(request,note["client_id"],ctx,db)

@app.get("/api/v1/practice-operations/clients/{client_id}/session-assistant/suggestions")
async def list_session_suggestions(request:Request,client_id:str,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    rows=(await db.execute(text("SELECT id,session_note_id,suggestion_type,reason,source,proposed_payload,confidence,status,confirmed_by,confirmed_at,created_at FROM external_session_action_suggestions WHERE tenant_id=:tenant AND client_id=:client ORDER BY created_at DESC"),{"tenant":ctx["tenant_id"],"client":client_id})).mappings().all();return {"success":True,"data":{"items":[dict(row) for row in rows]},"error":None,"request_id":request.state.correlation_id}

@app.patch("/api/v1/practice-operations/session-assistant/suggestions/{suggestion_id}")
async def decide_session_suggestion(request:Request,suggestion_id:UUID,body:SessionSuggestionDecision,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    row=(await db.execute(text("SELECT status,proposed_payload FROM external_session_action_suggestions WHERE id=:id AND tenant_id=:tenant"),{"id":suggestion_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not row:return error(request,404,"SUGGESTION_NOT_FOUND","Suggestion not found")
    if row["status"]!="PROPOSED":return error(request,409,"SUGGESTION_ALREADY_DECIDED","Suggestion has already been decided")
    status={"ACCEPT":"ACCEPTED","EDIT_AND_ACCEPT":"EDITED_ACCEPTED","DISMISS":"DISMISSED"}[body.decision];payload=body.proposed_payload if body.decision=="EDIT_AND_ACCEPT" else row["proposed_payload"];now=datetime.now(timezone.utc)
    await db.execute(text("UPDATE external_session_action_suggestions SET status=:status,proposed_payload=CAST(:payload AS jsonb),confirmed_by=:actor,confirmed_at=:now,updated_at=:now WHERE id=:id AND tenant_id=:tenant"),{"status":status,"payload":json.dumps(payload),"actor":ctx["user_id"],"now":now,"id":suggestion_id,"tenant":ctx["tenant_id"]});await db.commit();return {"success":True,"data":{"id":str(suggestion_id),"status":status,"action_executed":False},"error":None,"request_id":request.state.correlation_id}

async def _post_session_projection(db,tenant,checklist):
    params={"tenant":tenant,"client":checklist["client_id"],"consultation":checklist["consultation_id"],"started":checklist["started_at"],"now":datetime.now(timezone.utc)}
    evidence={}
    queries={
      "SESSION_NOTE":"SELECT id FROM external_session_notes WHERE tenant_id=:tenant AND client_id=:client AND consultation_id=:consultation AND status IN ('FINALISED','AMENDED') LIMIT 1",
      "HOMEWORK":"SELECT id FROM external_homework_assignments WHERE tenant_id=:tenant AND client_id=:client AND session_id=:consultation AND status<>'CANCELLED' LIMIT 1",
      "RESOURCE":"SELECT id FROM external_resource_assignments WHERE tenant_id=:tenant AND client_id=:client AND context_type='SESSION' AND context_id=:consultation AND status<>'CANCELLED' LIMIT 1",
      "GOAL":"SELECT id FROM practice_goals WHERE tenant_id=:tenant AND client_id=:client AND updated_at>=:started LIMIT 1",
      "FOLLOWUP":"SELECT id FROM practice_follow_ups WHERE tenant_id=:tenant AND client_id=:client AND created_at>=:started AND status<>'CANCELLED' LIMIT 1",
      "NEXT_APPOINTMENT":"SELECT id FROM practice_consultations WHERE tenant_id=:tenant AND client_id=:client AND due_at>:now AND status NOT IN ('CANCELLED','COMPLETED','NO_SHOW','MISSED') LIMIT 1",
      "PLAN_REVIEW":"SELECT id FROM external_profession_plans WHERE tenant_id=:tenant AND client_id=:client AND updated_at>=:started LIMIT 1",
      "REPORT":"SELECT id FROM external_progress_reports WHERE tenant_id=:tenant AND client_id=:client AND created_at>=:started AND status<>'REVOKED' LIMIT 1",
      "BILLING":"SELECT id FROM external_invoices WHERE tenant_id=:tenant AND client_id=:client AND created_at>=:started LIMIT 1",
    }
    for key,query in queries.items():
        try:evidence[key]="COMPLETE" if (await db.execute(text(query),params)).first() else "PENDING"
        except Exception:evidence[key]="FAILED"
    completed=(await db.execute(text("SELECT action_key FROM external_post_session_events WHERE tenant_id=:tenant AND checklist_id=:id AND event_type IN ('POST_SESSION_ACTION_COMPLETED','RENEWAL_PREPARED')"),{"tenant":tenant,"id":checklist["id"]})).scalars().all()
    for key in completed:evidence[key]="COMPLETE"
    projection=project_post_session(list(checklist["action_requirements"] or []),evidence)
    package=None
    if checklist.get("client_package_id"):
        package=(await db.execute(text("""SELECT q.id,q.sessions_total,q.end_date,q.renewal_date,q.status,
          (q.sessions_total-COUNT(s.id))::int sessions_remaining FROM external_client_packages q
          LEFT JOIN external_client_package_sessions s ON s.client_package_id=q.id AND s.tenant_id=q.tenant_id
          WHERE q.id=:package AND q.tenant_id=:tenant GROUP BY q.id"""),{"package":checklist["client_package_id"],"tenant":tenant})).mappings().first()
    projection.update({"id":str(checklist["id"]),"clientId":checklist["client_id"],"consultationId":checklist["consultation_id"],"professionCode":checklist["profession_code"],"lifecycleState":checklist["lifecycle_state"],"package":dict(package) if package else None,"autoRenew":False,"autoMessageSend":False,"autonomousClinicalAction":None})
    return projection

@app.post("/api/v1/practice-operations/clients/{client_id}/post-session",status_code=201)
async def start_post_session(request:Request,client_id:str,body:PostSessionStart,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"SESSION_EDIT")
    if denied:return denied
    tenant=ctx["tenant_id"]
    session=(await db.execute(text("SELECT id,client_id,status FROM practice_consultations WHERE id=CAST(:id AS uuid) AND tenant_id=:tenant AND client_id=:client"),{"id":body.consultation_id,"tenant":tenant,"client":client_id})).mappings().first()
    if not session:return error(request,404,"COMPLETED_SESSION_NOT_FOUND","Completed session was not found")
    if session["status"]!="COMPLETED":return error(request,409,"COMPLETED_SESSION_REQUIRED","Post-session flow applies only to completed sessions")
    existing=(await db.execute(text("SELECT id,tenant_id,client_id,consultation_id,session_note_id,profession_code,service_id,client_package_id,lifecycle_state,action_requirements,started_at,operationally_closed_at,created_by,created_at,updated_at FROM external_post_session_checklists WHERE tenant_id=:tenant AND consultation_id=:session"),{"tenant":tenant,"session":body.consultation_id})).mappings().first()
    if existing:return {"success":True,"data":await _post_session_projection(db,tenant,existing),"error":None,"request_id":request.state.correlation_id}
    profession=str(ctx.get("profession_code") or "GENERAL")
    package_low=False;milestone_due=False;report_due=False
    if body.client_package_id:
        used=(await db.execute(text("SELECT COUNT(*) FROM external_client_package_sessions WHERE tenant_id=:tenant AND client_package_id=:package"),{"tenant":tenant,"package":body.client_package_id})).scalar_one()
        package=(await db.execute(text("SELECT sessions_total,end_date FROM external_client_packages WHERE id=:package AND tenant_id=:tenant AND client_id=:client"),{"package":body.client_package_id,"tenant":tenant,"client":client_id})).mappings().first()
        if not package:return error(request,404,"CLIENT_PACKAGE_NOT_FOUND","Client package was not found")
        package_low=package["sessions_total"]-used<=2
        milestone_due=bool((await db.execute(text("SELECT id FROM external_programme_milestones WHERE tenant_id=:tenant AND client_id=:client AND client_package_id=:package AND status='PENDING' AND (due_date IS NULL OR due_date<=CURRENT_DATE) LIMIT 1"),{"tenant":tenant,"client":client_id,"package":body.client_package_id})).first())
    actions=resolve_post_session_actions(profession,capabilities=body.capabilities,package_low=package_low,milestone_due=milestone_due,report_due=report_due)
    now=datetime.now(timezone.utc);checklist_id=uuid4()
    await db.execute(text("""INSERT INTO external_post_session_checklists(id,tenant_id,client_id,consultation_id,session_note_id,profession_code,service_id,client_package_id,lifecycle_state,action_requirements,started_at,created_by,created_at,updated_at)
      VALUES (:id,:tenant,:client,:session,:note,:profession,:service,:package,'POST_SESSION_STARTED',CAST(:actions AS jsonb),:now,:actor,:now,:now)"""),{"id":checklist_id,"tenant":tenant,"client":client_id,"session":body.consultation_id,"note":body.session_note_id,"profession":profession,"service":body.service_id,"package":body.client_package_id,"actions":json.dumps(actions),"now":now,"actor":ctx["user_id"]})
    await db.execute(text("INSERT INTO external_post_session_events(id,checklist_id,tenant_id,client_id,consultation_id,event_type,actor_id,actor_type,metadata,created_at) VALUES (:event,:id,:tenant,:client,:session,'POST_SESSION_STARTED',:actor,'PRACTITIONER','{}'::jsonb,:now)"),{"event":uuid4(),"id":checklist_id,"tenant":tenant,"client":client_id,"session":body.consultation_id,"actor":ctx["user_id"],"now":now})
    await db.commit()
    row={"id":checklist_id,"client_id":client_id,"consultation_id":body.consultation_id,"session_note_id":body.session_note_id,"profession_code":profession,"service_id":body.service_id,"client_package_id":body.client_package_id,"lifecycle_state":"POST_SESSION_STARTED","action_requirements":actions,"started_at":now}
    return {"success":True,"data":await _post_session_projection(db,tenant,row),"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/clients/{client_id}/post-session/{consultation_id}")
async def get_post_session(request:Request,client_id:str,consultation_id:str,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"SESSION_VIEW")
    if denied:return denied
    row=(await db.execute(text("SELECT id,tenant_id,client_id,consultation_id,session_note_id,profession_code,service_id,client_package_id,lifecycle_state,action_requirements,started_at,operationally_closed_at,created_by,created_at,updated_at FROM external_post_session_checklists WHERE tenant_id=:tenant AND client_id=:client AND consultation_id=:session"),{"tenant":ctx["tenant_id"],"client":client_id,"session":consultation_id})).mappings().first()
    if not row:return {"success":True,"data":{"state":"CONFIRMED_EMPTY","checklist":None},"error":None,"request_id":request.state.correlation_id}
    return {"success":True,"data":await _post_session_projection(db,ctx["tenant_id"],row),"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/post-session/{checklist_id}/actions/complete")
async def complete_post_session_action(request:Request,checklist_id:UUID,body:PostSessionActionComplete,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"SESSION_EDIT")
    if denied:return denied
    row=(await db.execute(text("SELECT id,tenant_id,client_id,consultation_id,session_note_id,profession_code,service_id,client_package_id,lifecycle_state,action_requirements,started_at,operationally_closed_at,created_by,created_at,updated_at FROM external_post_session_checklists WHERE id=:id AND tenant_id=:tenant FOR UPDATE"),{"id":checklist_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not row:return error(request,404,"POST_SESSION_NOT_FOUND","Post-session checklist was not found")
    event_type={"FOLLOWUP":"FOLLOWUP_CREATED","HOMEWORK":"HOMEWORK_ASSIGNED","RESOURCE":"RESOURCE_ASSIGNED","NEXT_APPOINTMENT":"NEXT_SESSION_BOOKED","GOAL":"PROGRESS_REVIEW_CREATED","REPORT":"PROGRESS_REVIEW_CREATED","RENEWAL":"RENEWAL_PREPARED"}.get(body.action_key,"POST_SESSION_ACTION_COMPLETED")
    now=datetime.now(timezone.utc)
    await db.execute(text("INSERT INTO external_post_session_events(id,checklist_id,tenant_id,client_id,consultation_id,event_type,action_key,actor_id,actor_type,metadata,created_at) VALUES (:event,:id,:tenant,:client,:session,:type,:action,:actor,'PRACTITIONER',CAST(:metadata AS jsonb),:now)"),{"event":uuid4(),"id":row["id"],"tenant":ctx["tenant_id"],"client":row["client_id"],"session":row["consultation_id"],"type":event_type,"action":body.action_key,"actor":ctx["user_id"],"metadata":json.dumps({"source_record_id":body.source_record_id}),"now":now})
    await db.execute(text("UPDATE external_post_session_checklists SET lifecycle_state='IN_PROGRESS',updated_at=:now WHERE id=:id"),{"now":now,"id":row["id"]});await db.commit()
    updated={**dict(row),"lifecycle_state":"IN_PROGRESS"};projection=await _post_session_projection(db,ctx["tenant_id"],updated)
    if projection["sessionOperationallyClosed"]:
        await db.execute(text("UPDATE external_post_session_checklists SET lifecycle_state='SESSION_OPERATIONALLY_CLOSED',operationally_closed_at=:now,updated_at=:now WHERE id=:id"),{"now":now,"id":row["id"]})
        await db.execute(text("INSERT INTO external_post_session_events(id,checklist_id,tenant_id,client_id,consultation_id,event_type,actor_id,actor_type,metadata,created_at) VALUES (:event,:id,:tenant,:client,:session,'SESSION_OPERATIONALLY_CLOSED',:actor,'SYSTEM','{}'::jsonb,:now)"),{"event":uuid4(),"id":row["id"],"tenant":ctx["tenant_id"],"client":row["client_id"],"session":row["consultation_id"],"actor":ctx["user_id"],"now":now});await db.commit();projection["lifecycleState"]="SESSION_OPERATIONALLY_CLOSED"
    return {"success":True,"data":projection,"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/post-session/analytics")
async def post_session_analytics(request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"ANALYTICS_VIEW")
    if denied:return denied
    rows=[dict(row) for row in (await db.execute(text("SELECT id,tenant_id,client_id,consultation_id,session_note_id,profession_code,service_id,client_package_id,lifecycle_state,action_requirements,started_at,operationally_closed_at,created_by,created_at,updated_at FROM external_post_session_checklists WHERE tenant_id=:tenant"),{"tenant":ctx["tenant_id"]})).mappings().all()]
    projections=[await _post_session_projection(db,ctx["tenant_id"],row) for row in rows]
    return {"success":True,"data":{"state":"READY" if rows else "CONFIRMED_EMPTY","sessionCount":len(rows),"operationallyClosed":sum(1 for item in projections if item["sessionOperationallyClosed"]),"noFutureSession":sum(1 for item in projections if next((x for x in item["items"] if x["key"]=="NEXT_APPOINTMENT"),{}).get("status")=="PENDING"),"metrics":["FOLLOWUP_COMPLETION_RATE","NEXT_SESSION_BOOKING_RATE","PACKAGE_RENEWAL_RATE","PROGRAMME_CONTINUATION_RATE","AVERAGE_DAYS_TO_NEXT_SESSION","PROGRESS_REVIEW_COMPLETION","REPORT_COMPLETION"]},"error":None,"request_id":request.state.correlation_id}

async def _engagement_projection(db,tenant,client_id):
    now=datetime.now(timezone.utc);params={"tenant":tenant,"client":client_id,"now":now,"inactive":now-timedelta(days=21),"stale":now-timedelta(days=30),"plan_stale":now-timedelta(days=60)};reasons=[];indicators=[]
    future=(await db.execute(text("SELECT id,due_at FROM practice_consultations WHERE tenant_id=:tenant AND client_id=:client AND due_at>=:now AND status NOT IN ('CANCELLED','COMPLETED','NO_SHOW','MISSED') ORDER BY due_at LIMIT 1"),params)).mappings().first()
    if not future:reasons.append({"code":"NO_FUTURE_SESSION","reason":"No future session is currently scheduled.","source":"practice_consultations"})
    missed=(await db.execute(text("SELECT COUNT(*) FROM practice_consultations WHERE tenant_id=:tenant AND client_id=:client AND status IN ('NO_SHOW','MISSED')"),params)).scalar_one()
    if missed>=2:reasons.append({"code":"MULTIPLE_MISSED_SESSIONS","reason":f'{missed} sessions are recorded as missed.',"source":"practice_consultations"})
    overdue_checkin=(await db.execute(text("SELECT id,due_at FROM practice_checkins WHERE tenant_id=:tenant AND client_id=:client AND due_at<:now AND status NOT IN ('COMPLETED','CANCELLED','ARCHIVED') ORDER BY due_at LIMIT 1"),params)).mappings().first()
    if overdue_checkin:reasons.append({"code":"CHECKIN_OVERDUE","reason":"A check-in is overdue.","source":f'practice_checkins:{overdue_checkin["id"]}'})
    stale_goal=(await db.execute(text("SELECT id,updated_at FROM practice_goals WHERE tenant_id=:tenant AND client_id=:client AND status NOT IN ('COMPLETED','CANCELLED','ARCHIVED') AND updated_at<:stale ORDER BY updated_at LIMIT 1"),params)).mappings().first()
    if stale_goal:reasons.append({"code":"GOAL_NOT_UPDATED","reason":"An active goal has not been updated for 30 days.","source":f'practice_goals:{stale_goal["id"]}'})
    stale_plan=(await db.execute(text("SELECT id,updated_at FROM external_profession_plans WHERE tenant_id=:tenant AND client_id=:client AND status='PUBLISHED' AND updated_at<:plan_stale ORDER BY updated_at LIMIT 1"),params)).mappings().first()
    if stale_plan:reasons.append({"code":"PLAN_REVIEW_OVERDUE","reason":"The published profession plan is due for operational review.","source":f'external_profession_plans:{stale_plan["id"]}'})
    activity=(await db.execute(text("""SELECT MAX(value) FROM (SELECT MAX(updated_at) value FROM practice_consultations WHERE tenant_id=:tenant AND client_id=:client UNION ALL SELECT MAX(updated_at) FROM practice_checkins WHERE tenant_id=:tenant AND client_id=:client UNION ALL SELECT MAX(updated_at) FROM practice_tasks WHERE tenant_id=:tenant AND client_id=:client UNION ALL SELECT MAX(updated_at) FROM practice_goals WHERE tenant_id=:tenant AND client_id=:client UNION ALL SELECT MAX(created_at) FROM practice_communication_activity WHERE tenant_id=:tenant AND client_id=:client) activity"""),params)).scalar_one_or_none()
    if activity and activity<params["inactive"]:reasons.append({"code":"CLIENT_INACTIVE","reason":"No meaningful practice activity is recorded for 21 days.","source":"practice activity timeline"})
    if future:indicators.append({"reason":"A future session is scheduled.","source":f'practice_consultations:{future["id"]}'})
    state="INSUFFICIENT_DATA" if not activity else "NEEDS_ATTENTION" if len(reasons)>=2 else "MODERATE" if reasons else "HIGH"
    return {"client_id":client_id,"state":state,"reasons":reasons,"positive_indicators":indicators,"last_meaningful_activity":activity,"cta":{"label":"Open client","target":"client"},"explanation":"Operational engagement only; not a clinical risk assessment."}

@app.post("/api/v1/practice-operations/engagement/projections")
async def engagement_projections(request:Request,body:EngagementProjectionRequest,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    items=[await _engagement_projection(db,ctx["tenant_id"],client_id) for client_id in dict.fromkeys(body.client_ids)]
    return {"success":True,"data":{"items":items},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/clients/{client_id}/engagement")
async def client_engagement(request:Request,client_id:str,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    return {"success":True,"data":await _engagement_projection(db,ctx["tenant_id"],client_id),"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/clients/{client_id}/progress")
async def client_progress(request:Request,client_id:str,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=await _progress_guard(request,db,ctx)
    if denied:return denied
    metrics=[dict(row) for row in (await db.execute(text("SELECT id,code,label,value_type,unit,direction,source_type,active FROM external_progress_metric_definitions WHERE tenant_id=:tenant AND active=TRUE ORDER BY label"),{"tenant":ctx["tenant_id"]})).mappings().all()]
    observations=[dict(row) for row in (await db.execute(text("SELECT o.id,o.metric_definition_id,o.numeric_value,o.text_value,o.source_type,o.source_id,o.observed_at,m.label,m.unit FROM external_progress_observations o JOIN external_progress_metric_definitions m ON m.id=o.metric_definition_id WHERE o.tenant_id=:tenant AND o.client_id=:client ORDER BY o.observed_at DESC LIMIT 200"),{"tenant":ctx["tenant_id"],"client":client_id})).mappings().all()]
    targets=[dict(row) for row in (await db.execute(text("SELECT t.id,t.metric_definition_id,t.numeric_target,t.text_target,t.target_date,t.status,m.label,m.unit FROM external_progress_targets t JOIN external_progress_metric_definitions m ON m.id=t.metric_definition_id WHERE t.tenant_id=:tenant AND t.client_id=:client ORDER BY t.created_at DESC"),{"tenant":ctx["tenant_id"],"client":client_id})).mappings().all()]
    milestones=[dict(row) for row in (await db.execute(text("SELECT id,title,description,status,target_date,achieved_at,created_at FROM external_progress_milestones WHERE tenant_id=:tenant AND client_id=:client ORDER BY created_at DESC"),{"tenant":ctx["tenant_id"],"client":client_id})).mappings().all()]
    return {"success":True,"data":{"metrics":metrics,"observations":observations,"targets":targets,"milestones":milestones,"biomarker_history_source":"EXISTING_EXTERNAL_BIOMARKER_HISTORY"},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/progress/metrics",status_code=201)
async def create_progress_metric(request:Request,body:ProgressMetricCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=await _progress_guard(request,db,ctx)
    if denied:return denied
    config=await configuration(db,ctx);item_id=uuid4();now=datetime.now(timezone.utc)
    await db.execute(text("INSERT INTO external_progress_metric_definitions(id,tenant_id,profession_code,code,label,value_type,unit,direction,source_type,created_by,created_at) VALUES (:id,:tenant,:profession,:code,:label,:type,:unit,:direction,:source,:actor,:now)"),{"id":item_id,"tenant":ctx["tenant_id"],"profession":config["profession"],"code":body.code,"label":body.label,"type":body.value_type,"unit":body.unit,"direction":body.direction,"source":body.source_type,"actor":ctx["user_id"],"now":now});await db.commit()
    return {"success":True,"data":{"id":str(item_id)},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/clients/{client_id}/progress/observations",status_code=201)
async def create_progress_observation(request:Request,client_id:str,body:ProgressObservationCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=await _progress_guard(request,db,ctx)
    if denied:return denied
    if body.source_type=="BIOMARKER_REFERENCE" and (not body.source_id or body.numeric_value is not None or body.text_value is not None):return error(request,400,"BIOMARKER_REFERENCE_ONLY","Biomarker progress must reference existing history without copying its value")
    metric=(await db.execute(text("SELECT id FROM external_progress_metric_definitions WHERE id=:id AND tenant_id=:tenant AND active=TRUE"),{"id":body.metric_definition_id,"tenant":ctx["tenant_id"]})).scalar_one_or_none()
    if not metric:return error(request,404,"PROGRESS_METRIC_NOT_FOUND","Progress metric not found")
    item_id=uuid4();now=datetime.now(timezone.utc);await db.execute(text("INSERT INTO external_progress_observations(id,tenant_id,client_id,metric_definition_id,numeric_value,text_value,source_type,source_id,observed_at,recorded_by,created_at) VALUES (:id,:tenant,:client,:metric,:numeric,:text,:source,:source_id,:observed,:actor,:now)"),{"id":item_id,"tenant":ctx["tenant_id"],"client":client_id,"metric":metric,"numeric":body.numeric_value,"text":body.text_value,"source":body.source_type,"source_id":body.source_id,"observed":body.observed_at,"actor":ctx["user_id"],"now":now});await db.commit()
    return {"success":True,"data":{"id":str(item_id)},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/clients/{client_id}/progress/targets",status_code=201)
async def create_progress_target(request:Request,client_id:str,body:ProgressTargetCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=await _progress_guard(request,db,ctx)
    if denied:return denied
    item_id=uuid4();now=datetime.now(timezone.utc);result=await db.execute(text("INSERT INTO external_progress_targets(id,tenant_id,client_id,metric_definition_id,numeric_target,text_target,target_date,status,created_by,created_at,updated_at) SELECT :id,:tenant,:client,id,:numeric,:text,:target,'ACTIVE',:actor,:now,:now FROM external_progress_metric_definitions WHERE id=:metric AND tenant_id=:tenant"),{"id":item_id,"tenant":ctx["tenant_id"],"client":client_id,"metric":body.metric_definition_id,"numeric":body.numeric_target,"text":body.text_target,"target":body.target_date,"actor":ctx["user_id"],"now":now})
    if result.rowcount != 1:return error(request,404,"PROGRESS_METRIC_NOT_FOUND","Progress metric not found")
    await db.commit();return {"success":True,"data":{"id":str(item_id)},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/clients/{client_id}/progress/milestones",status_code=201)
async def create_progress_milestone(request:Request,client_id:str,body:ProgressMilestoneCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=await _progress_guard(request,db,ctx)
    if denied:return denied
    item_id=uuid4();now=datetime.now(timezone.utc);await db.execute(text("INSERT INTO external_progress_milestones(id,tenant_id,client_id,title,description,status,target_date,created_by,created_at,updated_at) VALUES (:id,:tenant,:client,:title,:description,'PLANNED',:target,:actor,:now,:now)"),{"id":item_id,"tenant":ctx["tenant_id"],"client":client_id,"title":body.title,"description":body.description,"target":body.target_date,"actor":ctx["user_id"],"now":now});await db.commit();return {"success":True,"data":{"id":str(item_id)},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/profession-intake/{token}")
async def read_profession_intake(request: Request, token: str, db: AsyncSession=Depends(get_db)):
    scope, denied = await _profession_token_scope(request, token, "READ", db)
    if denied: return denied
    sections = (await db.execute(text("""SELECT s.id,s.section_key,s.title,s.description,s.sort_order
      FROM external_intake_template_sections s WHERE s.tenant_id=:tenant AND s.template_version_id=:template ORDER BY s.sort_order"""), {"tenant":scope["tenant_id"],"template":scope["template_version_id"]})).mappings().all()
    questions = (await db.execute(text("""SELECT q.id,q.section_id,q.question_key,q.prompt,q.question_type,q.required,q.options,q.sort_order,a.answer
      FROM external_intake_template_questions q JOIN external_intake_template_sections s ON s.id=q.section_id
      LEFT JOIN external_client_intake_answers a ON a.question_id=q.id AND a.intake_instance_id=:instance AND a.tenant_id=:tenant AND a.client_id=:client
      WHERE q.tenant_id=:tenant AND s.template_version_id=:template ORDER BY s.sort_order,q.sort_order"""), {"tenant":scope["tenant_id"],"client":scope["client_id"],"instance":scope["id"],"template":scope["template_version_id"]})).mappings().all()
    grouped=[]
    for section in sections:
        item=dict(section); item["questions"]=[dict(q) for q in questions if q["section_id"]==section["id"]]; grouped.append(item)
    custom=[dict(row) for row in (await db.execute(text("""SELECT id,question_key,prompt,question_type,required,options,sort_order,answer
      FROM external_client_intake_custom_questions WHERE tenant_id=:tenant AND client_id=:client AND intake_instance_id=:instance ORDER BY sort_order"""), {"tenant":scope["tenant_id"],"client":scope["client_id"],"instance":scope["id"]})).mappings().all()]
    if custom: grouped.append({"id":None,"section_key":"consultant_questions","title":"Your practitioner's questions","description":None,"sort_order":len(grouped),"questions":custom})
    if scope["status"] == "NOT_STARTED":
        await db.execute(text("UPDATE external_client_intake_instances SET status='IN_PROGRESS',updated_at=:now WHERE id=:id AND tenant_id=:tenant"), {"now":datetime.now(timezone.utc),"id":scope["id"],"tenant":scope["tenant_id"]})
        scope["status"]="IN_PROGRESS"
    return {"success":True,"data":{"instance":{"id":scope["id"],"professionCode":scope["profession_code"],"status":scope["status"],"completionPercent":scope["completion_percent"]},"sections":grouped},"error":None,"request_id":request.state.correlation_id}


@app.patch("/api/v1/profession-intake/{token}/answers")
async def save_profession_answers(request: Request, token: str, body: ProfessionIntakeAnswerSave, db: AsyncSession=Depends(get_db)):
    scope, denied = await _profession_token_scope(request, token, "SAVE", db)
    if denied: return denied
    if scope["status"] == "COMPLETED": return error(request, 409, "INTAKE_ALREADY_SUBMITTED", "This intake has already been submitted")
    available = (await db.execute(text("""SELECT q.id,q.question_key FROM external_intake_template_questions q
      JOIN external_intake_template_sections s ON s.id=q.section_id
      WHERE q.tenant_id=:tenant AND s.template_version_id=:template"""), {"tenant":scope["tenant_id"],"template":scope["template_version_id"]})).mappings().all()
    question_ids={row["question_key"]:row["id"] for row in available}
    custom_ids={row["question_key"]:row["id"] for row in (await db.execute(text("SELECT id,question_key FROM external_client_intake_custom_questions WHERE tenant_id=:tenant AND client_id=:client AND intake_instance_id=:instance"), {"tenant":scope["tenant_id"],"client":scope["client_id"],"instance":scope["id"]})).mappings().all()}
    if set(body.answers)-set(question_ids)-set(custom_ids): return error(request,400,"UNKNOWN_QUESTION","One or more questions are not part of this intake template")
    now=datetime.now(timezone.utc)
    for key,value in body.answers.items():
        if key in custom_ids:
            await db.execute(text("""UPDATE external_client_intake_custom_questions SET answer=CAST(:answer AS jsonb),answer_version=answer_version+1
              WHERE id=:id AND tenant_id=:tenant AND client_id=:client AND intake_instance_id=:instance"""), {"answer":json.dumps(value),"id":custom_ids[key],"tenant":scope["tenant_id"],"client":scope["client_id"],"instance":scope["id"]})
            continue
        await db.execute(text("""INSERT INTO external_client_intake_answers
          (id,intake_instance_id,tenant_id,client_id,question_id,answer,version,answered_at)
          VALUES (:id,:instance,:tenant,:client,:question,CAST(:answer AS jsonb),1,:now)
          ON CONFLICT (intake_instance_id,question_id) DO UPDATE SET answer=EXCLUDED.answer,version=external_client_intake_answers.version+1,answered_at=EXCLUDED.answered_at
          WHERE external_client_intake_answers.tenant_id=EXCLUDED.tenant_id AND external_client_intake_answers.client_id=EXCLUDED.client_id"""), {"id":uuid4(),"instance":scope["id"],"tenant":scope["tenant_id"],"client":scope["client_id"],"question":question_ids[key],"answer":json.dumps(value),"now":now})
    answered=(await db.execute(text("SELECT COUNT(*) FROM external_client_intake_answers WHERE tenant_id=:tenant AND client_id=:client AND intake_instance_id=:instance"), {"tenant":scope["tenant_id"],"client":scope["client_id"],"instance":scope["id"]})).scalar_one()
    custom_answered=(await db.execute(text("SELECT COUNT(*) FROM external_client_intake_custom_questions WHERE tenant_id=:tenant AND client_id=:client AND intake_instance_id=:instance AND answer IS NOT NULL"), {"tenant":scope["tenant_id"],"client":scope["client_id"],"instance":scope["id"]})).scalar_one()
    completion=round(((answered+custom_answered)/max(len(available)+len(custom_ids),1))*100)
    await db.execute(text("UPDATE external_client_intake_instances SET status='IN_PROGRESS',completion_percent=:completion,updated_at=:now WHERE id=:id AND tenant_id=:tenant AND client_id=:client"), {"completion":completion,"now":now,"id":scope["id"],"tenant":scope["tenant_id"],"client":scope["client_id"]})
    return {"success":True,"data":{"completionPercent":completion,"status":"IN_PROGRESS"},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/profession-intake/{token}/submit")
async def submit_profession_intake(request: Request, token: str, body: ProfessionIntakeSubmit, db: AsyncSession=Depends(get_db)):
    scope, denied = await _profession_token_scope(request, token, "SUBMIT", db)
    if denied: return denied
    missing=(await db.execute(text("""SELECT q.question_key FROM external_intake_template_questions q
      JOIN external_intake_template_sections s ON s.id=q.section_id
      LEFT JOIN external_client_intake_answers a ON a.question_id=q.id AND a.intake_instance_id=:instance AND a.tenant_id=:tenant AND a.client_id=:client
      WHERE q.tenant_id=:tenant AND s.template_version_id=:template AND q.required=TRUE AND a.id IS NULL"""), {"instance":scope["id"],"tenant":scope["tenant_id"],"client":scope["client_id"],"template":scope["template_version_id"]})).scalars().all()
    if missing: return error(request,409,"REQUIRED_ANSWERS_MISSING","Complete all required questions before submitting")
    missing_custom=(await db.execute(text("""SELECT question_key FROM external_client_intake_custom_questions
      WHERE tenant_id=:tenant AND client_id=:client AND intake_instance_id=:instance AND required=TRUE AND answer IS NULL"""), {"tenant":scope["tenant_id"],"client":scope["client_id"],"instance":scope["id"]})).scalars().all()
    if missing_custom: return error(request,409,"REQUIRED_ANSWERS_MISSING","Complete all required questions before submitting")
    now=datetime.now(timezone.utc)
    await db.execute(text("UPDATE external_client_intake_instances SET status='COMPLETED',completion_percent=100,submitted_at=:now,updated_at=:now WHERE id=:id AND tenant_id=:tenant AND client_id=:client"), {"now":now,"id":scope["id"],"tenant":scope["tenant_id"],"client":scope["client_id"]})
    await db.execute(text("""INSERT INTO external_client_intake_audit_events
      (id,intake_instance_id,tenant_id,client_id,event_type,actor_id,metadata,created_at)
      VALUES (:id,:instance,:tenant,:client,'INTAKE_SUBMITTED',NULL,CAST(:metadata AS jsonb),:now)"""), {"id":uuid4(),"instance":scope["id"],"tenant":scope["tenant_id"],"client":scope["client_id"],"metadata":json.dumps({"consent_version":body.consent_version}),"now":now})
    await _preconsultation_event_once(db,scope["tenant_id"],scope["client_id"],"INTAKE_COMPLETED",actor_type="CLIENT",metadata={"intake_instance_id":str(scope["id"])})
    await _record_preconsultation_readiness(db,scope["tenant_id"],scope["client_id"])
    return {"success":True,"data":{"status":"COMPLETED","completionPercent":100,"submittedAt":now},"error":None,"request_id":request.state.correlation_id}


async def _preconsultation_event_once(db, tenant_id, client_id, event_type, actor_id=None, actor_type="SYSTEM", metadata=None):
    await db.execute(text("""INSERT INTO external_preconsultation_events
      (id,checklist_id,tenant_id,client_id,event_type,actor_id,actor_type,metadata,created_at)
      SELECT :id,c.id,c.tenant_id,c.client_id,:event,:actor,:actor_type,CAST(:metadata AS jsonb),:now
      FROM external_preconsultation_checklists c WHERE c.tenant_id=:tenant AND c.client_id=:client
      AND NOT EXISTS (SELECT 1 FROM external_preconsultation_events e WHERE e.checklist_id=c.id AND e.event_type=:event)
      LIMIT 1"""),{"id":uuid4(),"tenant":tenant_id,"client":client_id,"event":event_type,"actor":actor_id,
      "actor_type":actor_type,"metadata":json.dumps(metadata or {}),"now":datetime.now(timezone.utc)})


async def _preconsultation_projection(db, tenant_id, client_id, checklist=None):
    checklist = checklist or (await db.execute(text("""SELECT id,tenant_id,client_id,lead_id,appointment_id,enrolment_id,
      profession_code,service_id,acquisition_source,lifecycle_state,requirements,invited_at,
      completed_at,ready_at,created_by,created_at,updated_at FROM external_preconsultation_checklists
      WHERE tenant_id=:tenant AND client_id=:client"""), {"tenant": tenant_id, "client": client_id})).mappings().first()
    if not checklist:
        return None
    requirements = dict(checklist["requirements"] or {})
    params = {"tenant": tenant_id, "client": client_id, "appointment": checklist["appointment_id"]}
    intake = (await db.execute(text("""SELECT status FROM (
      SELECT status,created_at FROM external_client_intake_instances WHERE tenant_id=:tenant AND client_id=:client AND status<>'REVOKED'
      UNION ALL
      SELECT a.status,a.assigned_at FROM external_form_assignments a JOIN external_form_definitions d ON d.id=a.form_definition_id
      WHERE a.tenant_id=:tenant AND a.client_id=:client AND d.form_type IN ('INTAKE','ONBOARDING','PRE_CONSULTATION')
      ) intake ORDER BY created_at DESC LIMIT 1"""), params)).mappings().first()
    consent = (await db.execute(text("""SELECT status FROM external_consent_records WHERE tenant_id=:tenant AND client_id=:client
      AND revoked_at IS NULL AND (expires_at IS NULL OR expires_at>NOW()) ORDER BY created_at DESC LIMIT 1"""), params)).mappings().first()
    assessment = (await db.execute(text("""SELECT status FROM external_assessment_instances WHERE tenant_id=:tenant AND client_id=:client
      ORDER BY assigned_at DESC LIMIT 1"""), params)).mappings().first()
    document_rows = (await db.execute(text("""SELECT category,title FROM external_documents WHERE tenant_id=:tenant AND client_id=:client
      AND status='AVAILABLE' AND visibility<>'PRACTITIONER_PRIVATE'
      UNION ALL SELECT media_type AS category,title FROM external_client_portal_documents WHERE tenant_id=:tenant AND client_id=:client
      AND status NOT IN ('REMOVED','QUARANTINED')"""), params)).mappings().all()
    appointment = (await db.execute(text("""SELECT status,starts_at FROM external_scheduled_appointments WHERE tenant_id=:tenant AND client_id=:client
      AND (CAST(:appointment AS uuid) IS NULL OR id=CAST(:appointment AS uuid))
      ORDER BY starts_at DESC LIMIT 1"""), params)).mappings().first()
    portal = (await db.execute(text("""SELECT id FROM external_client_portal_access_grants WHERE tenant_id=:tenant AND client_id=:client
      AND revoked_at IS NULL AND expires_at>NOW() ORDER BY created_at DESC LIMIT 1"""), params)).mappings().first()
    required_documents = requirements.get("DOCUMENTS", {}).get("requests", [])
    def document_matches(requested):
        needle=str(requested).strip().lower().replace("_"," ")
        return any(needle in f"{row['category'] or ''} {row['title'] or ''}".lower().replace("_"," ") for row in document_rows)
    document_count=sum(1 for requested in required_documents if document_matches(requested))
    facts = {
      "PROFILE": {"state": "COMPLETE", "detail": "Governed client relationship established"},
      "INTAKE": {"state": "COMPLETE" if intake and intake["status"] == "COMPLETED" else "IN_PROGRESS" if intake and intake["status"] in {"STARTED", "IN_PROGRESS"} else "PENDING"},
      "CONSENT": {"state": "COMPLETE" if consent and consent["status"] == "ACCEPTED" else "NEEDS_ATTENTION" if consent and consent["status"] in {"DECLINED", "REVOKED"} else "PENDING"},
      "ASSESSMENT": {"state": "COMPLETE" if assessment and assessment["status"] in {"COMPLETED", "REVIEWED"} else "IN_PROGRESS" if assessment and assessment["status"] == "IN_PROGRESS" else "PENDING"},
      "DOCUMENTS": {"state": "COMPLETE" if len(required_documents) <= document_count else "PENDING", "detail": f"{document_count} of {len(required_documents)} requested documents available"},
      "APPOINTMENT": {"state": "COMPLETE" if appointment and appointment["status"] in {"BOOKED", "CONFIRMED", "SCHEDULED"} else "NEEDS_ATTENTION" if appointment and appointment["status"] == "CANCELLED" else "PENDING", "detail": appointment["starts_at"].isoformat() if appointment and appointment["starts_at"] else None},
      "PAYMENT": {"state": "NOT_REQUIRED"},
      "PORTAL": {"state": "COMPLETE" if portal else "PENDING"},
      "QUESTIONS": {"state": "COMPLETE" if intake and intake["status"] == "COMPLETED" else "PENDING"},
    }
    projection = project_readiness(requirements, facts)
    projection.update({"id": str(checklist["id"]), "clientId": client_id, "professionCode": checklist["profession_code"],
      "appointmentId": str(checklist["appointment_id"]) if checklist["appointment_id"] else None,
      "acquisitionSource": checklist["acquisition_source"], "updatedAt": checklist["updated_at"]})
    return projection


async def _record_preconsultation_readiness(db, tenant_id, client_id):
    projection=await _preconsultation_projection(db,tenant_id,client_id)
    if projection and projection["readyForConsultation"]:
        await _preconsultation_event_once(db,tenant_id,client_id,"READY_FOR_CONSULTATION",actor_type="SYSTEM",
          metadata={"required_complete":projection["requiredComplete"],"required_total":projection["requiredTotal"]})


@app.get("/api/v1/practice-operations/clients/{client_id}/pre-consultation")
async def get_preconsultation(request:Request, client_id:str, ctx=Depends(context), db:AsyncSession=Depends(get_db)):
    denied, _ = await _team_guard(request, db, ctx, "CLIENT_LIST_VIEW", client_id)
    if denied:return denied
    projection = await _preconsultation_projection(db, ctx["tenant_id"], client_id)
    if not projection:return error(request,404,"PRECONSULTATION_NOT_FOUND","Pre-consultation onboarding has not been invited")
    return {"success":True,"data":projection,"error":None,"request_id":request.state.correlation_id}


@app.get("/api/v1/practice-operations/pre-consultation/analytics")
async def preconsultation_analytics(request:Request, ctx=Depends(context), db:AsyncSession=Depends(get_db)):
    denied, _ = await _team_guard(request, db, ctx, "ANALYTICS_VIEW")
    if denied:return denied
    rows=(await db.execute(text("""SELECT id,tenant_id,client_id,lead_id,appointment_id,enrolment_id,
      profession_code,service_id,acquisition_source,lifecycle_state,requirements,invited_at,
      completed_at,ready_at,created_by,created_at,updated_at FROM external_preconsultation_checklists
      WHERE tenant_id=:tenant"""),{"tenant":ctx["tenant_id"]})).mappings().all()
    projections=[await _preconsultation_projection(db,ctx["tenant_id"],row["client_id"],row) for row in rows]
    ready=sum(1 for item in projections if item["readyForConsultation"])
    blocked={}
    for item in projections:
        for blocker in item["blockers"]:blocked[blocker]=blocked.get(blocker,0)+1
    data={"total":len(projections),"ready":ready,"in_progress":len(projections)-ready,
      "completion_rate":round(ready/len(projections)*100,2) if projections else None,"blocker_counts":blocked,
      "classification":"OPERATIONAL_NOT_CLINICAL","state":"READY" if projections else "CONFIRMED_EMPTY"}
    return {"success":True,"data":data,"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/clients/{client_id}/pre-consultation/invite", status_code=201)
async def invite_preconsultation(request:Request, client_id:str, body:PreConsultationInvite, ctx=Depends(context), db:AsyncSession=Depends(get_db)):
    denied, _ = await _team_guard(request, db, ctx, "CLIENT_EDIT", client_id)
    if denied:return denied
    cfg = await configuration(db,ctx); tenant=ctx["tenant_id"]; now=datetime.now(timezone.utc)
    source = "PRACTICE"
    if body.lead_id:
        lead=(await db.execute(text("SELECT converted_client_id,source FROM external_leads WHERE id=:id AND tenant_id=:tenant"),{"id":body.lead_id,"tenant":tenant})).mappings().first()
        if not lead or lead["converted_client_id"] != client_id:return error(request,409,"GOVERNED_CLIENT_LINK_REQUIRED","Lead must already be converted to this client")
        source=lead["source"] or "CRM"
    if body.enrolment_id:
        enrol=(await db.execute(text("SELECT status FROM external_consultant_marketplace_enrolments WHERE id=:id AND tenant_id=:tenant"),{"id":body.enrolment_id,"tenant":tenant})).mappings().first()
        if not enrol or enrol["status"] not in {"ACCEPTED","BOOKED","CONVERTED"}:return error(request,409,"ENROLMENT_NOT_ACCEPTED","Enrolment must be accepted before onboarding")
        source="ENROLMENT"
    if body.appointment_id:
        appointment=(await db.execute(text("SELECT client_id,lead_id,status,marketplace_source FROM external_scheduled_appointments WHERE id=:id AND tenant_id=:tenant"),{"id":body.appointment_id,"tenant":tenant})).mappings().first()
        if not appointment or appointment["client_id"] != client_id or appointment["status"] not in {"BOOKED","CONFIRMED","SCHEDULED"}:return error(request,409,"CONFIRMED_CLIENT_BOOKING_REQUIRED","A confirmed booking linked to this client is required")
        source=appointment["marketplace_source"] or source
    overrides={"DOCUMENTS":{"required":bool(body.required_documents),"requests":body.required_documents},"PORTAL":{"required":body.require_portal},"QUESTIONS":{"required":body.require_pre_session_questions}}
    requirements=resolve_requirements(cfg["profession"],cfg["capabilities"],overrides)
    checklist_id=uuid4()
    row=(await db.execute(text("""INSERT INTO external_preconsultation_checklists
      (id,tenant_id,client_id,lead_id,appointment_id,enrolment_id,profession_code,service_id,acquisition_source,lifecycle_state,requirements,invited_at,created_by,created_at,updated_at)
      VALUES (:id,:tenant,:client,:lead,:appointment,:enrolment,:profession,:service,:source,'ONBOARDING_INVITED',CAST(:requirements AS jsonb),:now,:actor,:now,:now)
      ON CONFLICT(tenant_id,client_id) DO UPDATE SET appointment_id=COALESCE(EXCLUDED.appointment_id,external_preconsultation_checklists.appointment_id),
      enrolment_id=COALESCE(EXCLUDED.enrolment_id,external_preconsultation_checklists.enrolment_id),service_id=COALESCE(EXCLUDED.service_id,external_preconsultation_checklists.service_id),
      profession_code=EXCLUDED.profession_code,requirements=EXCLUDED.requirements,lifecycle_state='ONBOARDING_INVITED',invited_at=:now,updated_at=:now RETURNING *"""),
      {"id":checklist_id,"tenant":tenant,"client":client_id,"lead":body.lead_id,"appointment":body.appointment_id,"enrolment":body.enrolment_id,
       "profession":cfg["profession"],"service":body.service_id,"source":source,"requirements":json.dumps(requirements),"now":now,"actor":ctx["user_id"]})).mappings().one()
    checklist_id=row["id"]
    form=(await db.execute(text("""SELECT d.id,v.id version_id FROM external_form_definitions d JOIN external_form_versions v ON v.definition_id=d.id AND v.version=d.current_version
      WHERE d.tenant_id=:tenant AND d.status='PUBLISHED' AND v.status='PUBLISHED' AND d.form_type IN ('INTAKE','ONBOARDING','PRE_CONSULTATION')
      AND (v.settings->>'profession_code' IS NULL OR v.settings->>'profession_code'=:profession) ORDER BY (v.settings->>'profession_code'=:profession) DESC,d.updated_at DESC LIMIT 1"""),{"tenant":tenant,"profession":cfg["profession"]})).mappings().first()
    if form and not (await db.execute(text("SELECT 1 FROM external_form_assignments WHERE tenant_id=:tenant AND client_id=:client AND form_definition_id=:definition AND status IN ('ASSIGNED','STARTED','COMPLETED')"),{"tenant":tenant,"client":client_id,"definition":form["id"]})).first():
        await db.execute(text("""INSERT INTO external_form_assignments(id,tenant_id,client_id,form_definition_id,form_version_id,linked_type,linked_id,status,assigned_by,assigned_at,expires_at)
          VALUES (:id,:tenant,:client,:definition,:version,'PRECONSULTATION',:linked,'ASSIGNED',:actor,:now,:expires)"""),{"id":uuid4(),"tenant":tenant,"client":client_id,"definition":form["id"],"version":form["version_id"],"linked":str(checklist_id),"actor":ctx["user_id"],"now":now,"expires":now+timedelta(hours=body.expires_in_hours)})
    consent=(await db.execute(text("""SELECT t.id,v.id version_id,v.scope FROM external_consent_templates t JOIN external_consent_template_versions v ON v.template_id=t.id AND v.version=t.current_version
      WHERE t.tenant_id=:tenant AND t.status='PUBLISHED' AND v.status='PUBLISHED'
      AND (t.profession_code IS NULL OR t.profession_code=:profession)
      ORDER BY (t.profession_code=:profession) DESC,t.updated_at DESC LIMIT 1"""),{"tenant":tenant,"profession":cfg["profession"]})).mappings().first()
    if consent and not (await db.execute(text("SELECT 1 FROM external_consent_records WHERE tenant_id=:tenant AND client_id=:client AND template_id=:template AND status IN ('PENDING','ACCEPTED')"),{"tenant":tenant,"client":client_id,"template":consent["id"]})).first():
        await db.execute(text("""INSERT INTO external_consent_records(id,tenant_id,client_id,template_id,template_version_id,status,scope,assigned_by,created_at,updated_at)
          VALUES (:id,:tenant,:client,:template,:version,'PENDING',CAST(:scope AS jsonb),:actor,:now,:now)"""),{"id":uuid4(),"tenant":tenant,"client":client_id,"template":consent["id"],"version":consent["version_id"],"scope":json.dumps(consent["scope"]),"actor":ctx["user_id"],"now":now})
    if requirements["ASSESSMENT"]["required"]:
        assessment_definition=(await db.execute(text("""SELECT d.id,v.id version_id FROM external_assessment_definitions d
          JOIN external_assessment_versions v ON v.definition_id=d.id AND v.status='ACTIVE'
          WHERE d.active=TRUE AND d.profession_code=:profession AND (d.tenant_id IS NULL OR d.tenant_id=:tenant)
          ORDER BY d.scope DESC,d.title LIMIT 1"""),{"profession":cfg["profession"],"tenant":tenant})).mappings().first()
        if assessment_definition and not (await db.execute(text("SELECT 1 FROM external_assessment_instances WHERE tenant_id=:tenant AND client_id=:client AND definition_id=:definition AND status IN ('ASSIGNED','IN_PROGRESS','COMPLETED','REVIEWED')"),{"tenant":tenant,"client":client_id,"definition":assessment_definition["id"]})).first():
            await db.execute(text("""INSERT INTO external_assessment_instances(id,tenant_id,client_id,definition_id,version_id,profession_code,status,assigned_by,assigned_at,updated_at)
              VALUES (:id,:tenant,:client,:definition,:version,:profession,'ASSIGNED',:actor,:now,:now)"""),{"id":uuid4(),"tenant":tenant,"client":client_id,"definition":assessment_definition["id"],"version":assessment_definition["version_id"],"profession":cfg["profession"],"actor":ctx["user_id"],"now":now})
    portal_url=None
    if body.require_portal:
        grant_id=uuid4();expires=now+timedelta(hours=body.expires_in_hours);actions=("READ","COMPLETE_TASK","UPLOAD_DOCUMENT","SUBMIT_FORM","DECIDE_CONSENT")
        token=issue_portal_token(secret=get_settings().client_portal_secret,tenant_id=tenant,client_id=client_id,grant_id=str(grant_id),expires_at=int(expires.timestamp()),allowed_actions=actions)
        await db.execute(text("""INSERT INTO external_client_portal_access_grants(id,tenant_id,client_id,token_hash,token_version,allowed_actions,expires_at,created_by,created_at)
          VALUES (:id,:tenant,:client,:hash,1,CAST(:actions AS jsonb),:expires,:actor,:now)"""),{"id":grant_id,"tenant":tenant,"client":client_id,"hash":portal_token_hash(token),"actions":json.dumps(actions),"expires":expires,"actor":ctx["user_id"],"now":now})
        portal_url=f"{get_settings().client_portal_public_url.rstrip('/')}/{token}"
    reminder_due=now+timedelta(hours=24)
    for item in ("INTAKE","CONSENT","ASSESSMENT","DOCUMENTS","APPOINTMENT"):
        if not requirements[item]["required"]:continue
        reminder_key=f"p37:{checklist_id}:{item}"
        if (await db.execute(text("SELECT 1 FROM external_communication_reminders WHERE tenant_id=:tenant AND idempotency_key=:key"),{"tenant":tenant,"key":reminder_key})).first():continue
        preparation_id=uuid4()
        await db.execute(text("""INSERT INTO external_communication_preparations(id,tenant_id,client_id,channel,purpose,subject,body,status,created_by,created_at,updated_at)
          VALUES (:id,:tenant,:client,'CLIENT_PORTAL_NOTIFICATION',:purpose,:subject,:body,'PREPARED',:actor,:now,:now)"""),{"id":preparation_id,"tenant":tenant,"client":client_id,"purpose":f"PRECONSULTATION_{item}","subject":"Pre-consultation step reminder","body":f"Please complete your {item.lower().replace('_',' ')} step in the secure client portal.","actor":ctx["user_id"],"now":now})
        await db.execute(text("""INSERT INTO external_communication_reminders(id,tenant_id,client_id,preparation_id,channel,due_at,status,idempotency_key,created_by,created_at)
          VALUES (:id,:tenant,:client,:preparation,'CLIENT_PORTAL_NOTIFICATION',:due,'SCHEDULED',:key,:actor,:now)
          ON CONFLICT(tenant_id,idempotency_key) DO NOTHING"""),{"id":uuid4(),"tenant":tenant,"client":client_id,"preparation":preparation_id,"due":reminder_due,"key":reminder_key,"actor":ctx["user_id"],"now":now})
    await db.execute(text("""INSERT INTO external_preconsultation_events(id,checklist_id,tenant_id,client_id,event_type,actor_id,actor_type,metadata,created_at)
      VALUES (:id,:checklist,:tenant,:client,'ONBOARDING_INVITED',:actor,'PRACTITIONER',CAST(:metadata AS jsonb),:now)"""),{"id":uuid4(),"checklist":checklist_id,"tenant":tenant,"client":client_id,"actor":ctx["user_id"],"metadata":json.dumps({"source":source,"profession_code":cfg["profession"]}),"now":now})
    await db.commit();projection=await _preconsultation_projection(db,tenant,client_id,row)
    return {"success":True,"data":{**projection,"portalUrl":portal_url},"error":None,"request_id":request.state.correlation_id}


async def _portal_scope(request: Request, token: str, action: str, db: AsyncSession):
    try:
        claims = validate_portal_token(
            token, secret=get_settings().client_portal_secret, required_action=action
        )
    except PortalTokenError as exc:
        return None, error(request, 401, "CLIENT_PORTAL_LINK_INVALID", str(exc))
    row = (await db.execute(text("""SELECT id,tenant_id,client_id,allowed_actions,expires_at,revoked_at,token_version
      FROM external_client_portal_access_grants
      WHERE id=:grant AND tenant_id=:tenant AND client_id=:client AND token_hash=:token_hash"""), {
        "grant": claims.grant_id, "tenant": claims.tenant_id, "client": claims.client_id,
        "token_hash": portal_token_hash(token),
    })).mappings().first()
    now = datetime.now(timezone.utc)
    if not row or row["revoked_at"] or row["expires_at"] <= now:
        return None, error(request, 401, "CLIENT_PORTAL_LINK_INVALID", "This client portal link is unavailable")
    if row["token_version"] != claims.token_version or action not in set(row["allowed_actions"]):
        return None, error(request, 403, "CLIENT_PORTAL_ACTION_DENIED", "This portal action is not permitted")
    await db.execute(text("UPDATE external_client_portal_access_grants SET last_used_at=:now WHERE id=:grant AND tenant_id=:tenant AND client_id=:client"), {
        "now": now, "grant": row["id"], "tenant": row["tenant_id"], "client": row["client_id"],
    })
    return dict(row), None


@app.post("/api/v1/practice-operations/clients/{client_id}/portal-invitations", status_code=201)
async def create_client_portal_invitation(request: Request, client_id: str, body: ClientPortalInvitationCreate,
                                          ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied = external_only(request, ctx)
    if denied:
        return denied
    denied = await require_capability(request, db, ctx, "CLIENT_CRM")
    if denied:
        return denied
    grant_id, now = uuid4(), datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=body.expires_in_hours)
    actions = ["READ"]
    if body.allow_task_completion:
        actions.append("COMPLETE_TASK")
    if body.allow_document_upload:
        actions.append("UPLOAD_DOCUMENT")
    if body.allow_resource_access:
        actions.append("READ_RESOURCES")
    if body.allow_homework_checkin:
        actions.extend(["READ_HOMEWORK", "SUBMIT_HOMEWORK_CHECKIN"])
    if body.allow_form_response:
        actions.append("SUBMIT_FORM")
    if body.allow_consent_decision:
        actions.append("DECIDE_CONSENT")
    token = issue_portal_token(
        secret=get_settings().client_portal_secret, tenant_id=ctx["tenant_id"],
        client_id=client_id, grant_id=str(grant_id), expires_at=int(expires_at.timestamp()),
        allowed_actions=tuple(actions),
    )
    await db.execute(text("""INSERT INTO external_client_portal_access_grants
      (id,tenant_id,client_id,token_hash,token_version,allowed_actions,expires_at,created_by,created_at)
      VALUES (:id,:tenant,:client,:token_hash,1,CAST(:actions AS jsonb),:expires,:actor,:now)"""), {
        "id": grant_id, "tenant": ctx["tenant_id"], "client": client_id,
        "token_hash": portal_token_hash(token), "actions": json.dumps(actions),
        "expires": expires_at, "actor": ctx["user_id"], "now": now,
    })
    await db.execute(text("""INSERT INTO external_client_portal_audit_events
      (id,tenant_id,client_id,access_grant_id,event_type,actor_type,metadata,created_at)
      VALUES (:id,:tenant,:client,:grant,'PORTAL_INVITATION_CREATED','PRACTITIONER',CAST(:metadata AS jsonb),:now)"""), {
        "id": uuid4(), "tenant": ctx["tenant_id"], "client": client_id, "grant": grant_id,
        "metadata": json.dumps({"allowed_actions": actions, "expires_at": expires_at.isoformat()}), "now": now,
    })
    return {"success": True, "data": {
        "url": f"{get_settings().client_portal_public_url.rstrip('/')}/{token}",
        "expiresAt": expires_at, "allowedActions": actions,
    }, "error": None, "request_id": request.state.correlation_id}


@app.post("/api/v1/practice-operations/clients/{client_id}/portal-invitations/revoke")
async def revoke_client_portal_invitations(request: Request, client_id: str, ctx=Depends(context),
                                            db: AsyncSession=Depends(get_db)):
    denied = external_only(request, ctx)
    if denied:
        return denied
    now = datetime.now(timezone.utc)
    result = await db.execute(text("""UPDATE external_client_portal_access_grants
      SET revoked_at=:now WHERE tenant_id=:tenant AND client_id=:client AND revoked_at IS NULL"""), {
        "now": now, "tenant": ctx["tenant_id"], "client": client_id,
    })
    return {"success": True, "data": {"revoked": result.rowcount}, "error": None,
            "request_id": request.state.correlation_id}


def _package_snapshot(body):
    return body.snapshot() if hasattr(body, "snapshot") else body.model_dump(mode="json", exclude={"expected_version"})


@app.get("/api/v1/practice-operations/packages")
async def list_service_packages(request: Request, include_inactive: bool=False,
                                ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx) or await require_capability(request,db,ctx,"CLIENT_CRM")
    if denied: return denied
    rows=(await db.execute(text("""SELECT id,name,profession_code,capability_code,description,
      session_allowance,duration_days,price_minor,currency,active,current_version,created_at,updated_at
      FROM external_service_packages WHERE tenant_id=:tenant
      AND (:include_inactive OR active=TRUE) ORDER BY active DESC,lower(name)"""),
      {"tenant":ctx["tenant_id"],"include_inactive":include_inactive})).mappings().all()
    return {"success":True,"data":{"items":[dict(row) for row in rows]},"error":None,
            "request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/packages",status_code=201)
async def create_service_package(request: Request, body: ServicePackageCreate,
                                 ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx) or await require_capability(request,db,ctx,"CLIENT_CRM")
    if denied: return denied
    if (body.price_minor is None) != (body.currency is None):
        return error(request,422,"PACKAGE_PRICE_INVALID","Price and currency must be provided together")
    package_id,now=uuid4(),datetime.now(timezone.utc); snapshot=_package_snapshot(body)
    await db.execute(text("""INSERT INTO external_service_packages
      (id,tenant_id,name,profession_code,capability_code,description,session_allowance,duration_days,
       price_minor,currency,active,current_version,created_by,created_at,updated_at)
      VALUES (:id,:tenant,:name,:profession,:capability,:description,:sessions,:duration,
       :price,:currency,:active,1,:actor,:now,:now)"""),{
      "id":package_id,"tenant":ctx["tenant_id"],"name":body.name,"profession":body.profession_code,
      "capability":body.capability_code,"description":body.description,"sessions":body.session_allowance,
      "duration":body.duration_days,"price":body.price_minor,"currency":body.currency,
      "active":body.active,"actor":ctx["user_id"],"now":now})
    await db.execute(text("""INSERT INTO external_package_versions
      (id,package_id,tenant_id,version,snapshot,created_by,created_at)
      VALUES (:id,:package,:tenant,1,CAST(:snapshot AS jsonb),:actor,:now)"""),{
      "id":uuid4(),"package":package_id,"tenant":ctx["tenant_id"],"snapshot":json.dumps(snapshot),
      "actor":ctx["user_id"],"now":now})
    return {"success":True,"data":{"id":str(package_id),"version":1},"error":None,
            "request_id":request.state.correlation_id}


@app.patch("/api/v1/practice-operations/packages/{package_id}")
async def update_service_package(request: Request, package_id: UUID, body: ServicePackageUpdate,
                                 ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx) or await require_capability(request,db,ctx,"CLIENT_CRM")
    if denied: return denied
    if (body.price_minor is None) != (body.currency is None):
        return error(request,422,"PACKAGE_PRICE_INVALID","Price and currency must be provided together")
    now=datetime.now(timezone.utc); next_version=body.expected_version+1
    row=(await db.execute(text("""UPDATE external_service_packages SET name=:name,
      profession_code=:profession,capability_code=:capability,description=:description,
      session_allowance=:sessions,duration_days=:duration,price_minor=:price,currency=:currency,
      active=:active,current_version=:next_version,updated_at=:now
      WHERE id=:id AND tenant_id=:tenant AND current_version=:expected RETURNING id"""),{
      "id":package_id,"tenant":ctx["tenant_id"],"name":body.name,"profession":body.profession_code,
      "capability":body.capability_code,"description":body.description,"sessions":body.session_allowance,
      "duration":body.duration_days,"price":body.price_minor,"currency":body.currency,"active":body.active,
      "expected":body.expected_version,"next_version":next_version,"now":now})).first()
    if not row: return error(request,409,"PACKAGE_VERSION_CONFLICT","Package changed; refresh and retry")
    await db.execute(text("""INSERT INTO external_package_versions
      (id,package_id,tenant_id,version,snapshot,created_by,created_at)
      VALUES (:id,:package,:tenant,:version,CAST(:snapshot AS jsonb),:actor,:now)"""),{
      "id":uuid4(),"package":package_id,"tenant":ctx["tenant_id"],"version":next_version,
      "snapshot":json.dumps(_package_snapshot(body)),"actor":ctx["user_id"],"now":now})
    return {"success":True,"data":{"id":str(package_id),"version":next_version},"error":None,
            "request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/client-packages",status_code=201)
async def assign_client_package(request: Request, body: ClientPackageAssign,
                                ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx) or await require_capability(request,db,ctx,"CLIENT_CRM")
    if denied: return denied
    if body.end_date < body.start_date:
        return error(request,422,"PACKAGE_DATE_INVALID","End date must be on or after start date")
    package=(await db.execute(text("""SELECT id,current_version,session_allowance FROM external_service_packages
      WHERE id=:id AND tenant_id=:tenant AND active=TRUE"""),{"id":body.package_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not package: return error(request,404,"PACKAGE_NOT_FOUND","Package not found")
    assignment_id,now=uuid4(),datetime.now(timezone.utc)
    await db.execute(text("""INSERT INTO external_client_packages
      (id,tenant_id,client_id,package_id,package_version,start_date,end_date,status,sessions_total,
       renewal_date,notes,created_by,created_at,updated_at)
      VALUES (:id,:tenant,:client,:package,:version,:start,:end,:status,:sessions,
       :renewal,:notes,:actor,:now,:now)"""),{
      "id":assignment_id,"tenant":ctx["tenant_id"],"client":body.client_id,"package":body.package_id,
      "version":package["current_version"],"start":body.start_date,"end":body.end_date,"status":body.status,
      "sessions":body.sessions_total or package["session_allowance"],"renewal":body.renewal_date,
      "notes":body.notes,"actor":ctx["user_id"],"now":now})
    return {"success":True,"data":{"id":str(assignment_id)},"error":None,
            "request_id":request.state.correlation_id}


@app.get("/api/v1/practice-operations/client-packages")
async def list_client_packages(request: Request, client_id: str | None=None,
                               ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx) or await require_capability(request,db,ctx,"CLIENT_CRM")
    if denied: return denied
    rows=(await db.execute(text("""SELECT cp.id,cp.client_id,cp.package_id,p.name,p.profession_code,
      cp.start_date,cp.end_date,cp.status,cp.sessions_total,cp.renewal_date,cp.notes,
      COUNT(s.id)::int AS sessions_used,
      GREATEST(cp.sessions_total-COUNT(s.id)::int,0) AS sessions_remaining,
      MIN(c.due_at) FILTER (WHERE c.status='SCHEDULED' AND c.due_at >= NOW()) AS next_session
      FROM external_client_packages cp
      JOIN external_service_packages p ON p.id=cp.package_id AND p.tenant_id=cp.tenant_id
      LEFT JOIN external_client_package_sessions s ON s.client_package_id=cp.id AND s.tenant_id=cp.tenant_id
      LEFT JOIN practice_consultations c ON c.tenant_id=cp.tenant_id AND c.client_id=cp.client_id
      WHERE cp.tenant_id=:tenant
        AND (CAST(:client AS text) IS NULL OR cp.client_id=CAST(:client AS text))
      GROUP BY cp.id,p.id ORDER BY cp.end_date,cp.created_at DESC"""),
      {"tenant":ctx["tenant_id"],"client":client_id})).mappings().all()
    return {"success":True,"data":{"items":[dict(row) for row in rows]},"error":None,
            "request_id":request.state.correlation_id}


@app.patch("/api/v1/practice-operations/client-packages/{assignment_id}")
async def update_client_package(request: Request, assignment_id: UUID, body: ClientPackageStatusUpdate,
                                ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx) or await require_capability(request,db,ctx,"CLIENT_CRM")
    if denied: return denied
    row=(await db.execute(text("""UPDATE external_client_packages SET status=:status,
      renewal_date=:renewal,notes=:notes,updated_at=:now WHERE id=:id AND tenant_id=:tenant RETURNING id"""),
      {"status":body.status,"renewal":body.renewal_date,"notes":body.notes,"now":datetime.now(timezone.utc),
       "id":assignment_id,"tenant":ctx["tenant_id"]})).first()
    if not row: return error(request,404,"CLIENT_PACKAGE_NOT_FOUND","Client package not found")
    return {"success":True,"data":{"id":str(assignment_id),"status":body.status},"error":None,
            "request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/client-packages/{assignment_id}/sessions",status_code=201)
async def record_package_session(request: Request, assignment_id: UUID, body: PackageSessionUse,
                                 ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx) or await require_capability(request,db,ctx,"CLIENT_CRM")
    if denied: return denied
    package=(await db.execute(text("""SELECT id,client_id,sessions_total FROM external_client_packages
      WHERE id=:id AND tenant_id=:tenant AND status IN ('ACTIVE','PAUSED')"""),
      {"id":assignment_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not package: return error(request,404,"CLIENT_PACKAGE_NOT_FOUND","Active client package not found")
    used=(await db.execute(text("SELECT COUNT(*) FROM external_client_package_sessions WHERE tenant_id=:tenant AND client_package_id=:id"),
      {"tenant":ctx["tenant_id"],"id":assignment_id})).scalar_one()
    if used >= package["sessions_total"]:
        return error(request,409,"PACKAGE_SESSIONS_EXHAUSTED","No package sessions remain")
    session_id,now=uuid4(),datetime.now(timezone.utc)
    await db.execute(text("""INSERT INTO external_client_package_sessions
      (id,tenant_id,client_id,client_package_id,consultation_id,occurred_at,notes,recorded_by,created_at)
      VALUES (:id,:tenant,:client,:package,:consultation,:occurred,:notes,:actor,:now)"""),{
      "id":session_id,"tenant":ctx["tenant_id"],"client":package["client_id"],"package":assignment_id,
      "consultation":body.consultation_id,"occurred":body.occurred_at,"notes":body.notes,
      "actor":ctx["user_id"],"now":now})
    return {"success":True,"data":{"id":str(session_id),"sessions_used":used+1,
      "sessions_remaining":package["sessions_total"]-used-1},"error":None,
      "request_id":request.state.correlation_id}


@app.get("/api/v1/practice-operations/renewal-signals")
async def list_renewal_signals(request: Request, ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx) or await require_capability(request,db,ctx,"CLIENT_CRM")
    if denied: return denied
    rows=(await db.execute(text("""WITH package_state AS (
      SELECT cp.id,cp.client_id,p.name,cp.status,cp.end_date,cp.renewal_date,cp.sessions_total,
       COUNT(s.id)::int used,
       EXISTS(SELECT 1 FROM practice_consultations c WHERE c.tenant_id=cp.tenant_id
         AND c.client_id=cp.client_id AND c.status='SCHEDULED' AND c.due_at >= NOW()) has_future
      FROM external_client_packages cp JOIN external_service_packages p ON p.id=cp.package_id
      LEFT JOIN external_client_package_sessions s ON s.client_package_id=cp.id AND s.tenant_id=cp.tenant_id
      WHERE cp.tenant_id=:tenant AND cp.status IN ('ACTIVE','PAUSED') GROUP BY cp.id,p.id)
      SELECT *,ARRAY_REMOVE(ARRAY[
       CASE WHEN end_date < CURRENT_DATE THEN 'PROGRAMME_EXPIRED' END,
       CASE WHEN end_date BETWEEN CURRENT_DATE AND CURRENT_DATE+INTERVAL '14 days' THEN 'PACKAGE_ENDING_SOON' END,
       CASE WHEN sessions_total-used <= 2 THEN 'SESSIONS_LOW' END,
       CASE WHEN NOT has_future THEN 'NO_FUTURE_SESSION' END,
       CASE WHEN renewal_date IS NOT NULL AND renewal_date <= CURRENT_DATE+INTERVAL '14 days' THEN 'RENEWAL_DUE' END
      ],NULL) signals FROM package_state"""),{"tenant":ctx["tenant_id"]})).mappings().all()
    items=[]
    for row in rows:
        for signal in row["signals"]:
            items.append({"client_id":row["client_id"],"client_package_id":str(row["id"]),
                          "package_name":row["name"],"signal":signal,"end_date":row["end_date"]})
    return {"success":True,"data":{"items":items},"error":None,
            "request_id":request.state.correlation_id}


async def _calendar_access(request,db,ctx,permission):
    denied=external_only(request,ctx) or await require_capability(request,db,ctx,"CALENDAR")
    if denied:return denied
    denied,_=await _team_guard(request,db,ctx,permission)
    return denied


@app.get("/api/v1/practice-operations/scheduling/appointment-types")
async def list_appointment_types(request: Request, include_inactive: bool=False,
                                 ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied=await _calendar_access(request,db,ctx,"CALENDAR_VIEW")
    if denied: return denied
    rows=(await db.execute(text("""SELECT id,name,description,duration_minutes,buffer_before_minutes,
      buffer_after_minutes,location_type,location_details,active FROM external_appointment_types
      WHERE tenant_id=:tenant AND (:inactive OR active=TRUE) ORDER BY name"""),
      {"tenant":ctx["tenant_id"],"inactive":include_inactive})).mappings().all()
    return {"success":True,"data":{"items":[dict(row) for row in rows]},"error":None,
            "request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/scheduling/appointment-types",status_code=201)
async def create_appointment_type(request: Request, body: AppointmentTypeCreate,
                                  ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied=await _calendar_access(request,db,ctx,"CALENDAR_MANAGE")
    if denied: return denied
    item_id,now=uuid4(),datetime.now(timezone.utc)
    await db.execute(text("""INSERT INTO external_appointment_types
      (id,tenant_id,name,description,duration_minutes,buffer_before_minutes,buffer_after_minutes,
       location_type,location_details,active,created_by,created_at,updated_at)
      VALUES (:id,:tenant,:name,:description,:duration,:before,:after,:location,:details,TRUE,:actor,:now,:now)"""),{
      "id":item_id,"tenant":ctx["tenant_id"],"name":body.name,"description":body.description,
      "duration":body.duration_minutes,"before":body.buffer_before_minutes,"after":body.buffer_after_minutes,
      "location":body.location_type,"details":body.location_details,"actor":ctx["user_id"],"now":now})
    return {"success":True,"data":{"id":str(item_id)},"error":None,"request_id":request.state.correlation_id}


@app.get("/api/v1/practice-operations/scheduling/availability")
async def list_availability(request: Request, ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied=await _calendar_access(request,db,ctx,"CALENDAR_VIEW")
    if denied: return denied
    rows=(await db.execute(text("""SELECT id,weekday,start_time,end_time,timezone,effective_from,effective_until,active
      FROM external_availability_rules WHERE tenant_id=:tenant ORDER BY weekday,start_time"""),
      {"tenant":ctx["tenant_id"]})).mappings().all()
    return {"success":True,"data":{"items":[dict(row) for row in rows]},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/scheduling/availability",status_code=201)
async def create_availability(request: Request, body: AvailabilityRuleCreate,
                              ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied=await _calendar_access(request,db,ctx,"CALENDAR_MANAGE")
    if denied: return denied
    if body.end_time <= body.start_time or (body.effective_from and body.effective_until and body.effective_until<body.effective_from):
        return error(request,422,"AVAILABILITY_WINDOW_INVALID","Availability end must follow its start")
    overlap=(await db.execute(text("""SELECT 1 FROM external_availability_rules WHERE tenant_id=:tenant AND weekday=:weekday AND active=TRUE
      AND CAST(:start AS time)<end_time AND CAST(:end AS time)>start_time LIMIT 1"""),{"tenant":ctx["tenant_id"],"weekday":body.weekday,"start":body.start_time,"end":body.end_time})).first()
    if overlap:return error(request,409,"AVAILABILITY_OVERLAP","This availability window overlaps an existing window")
    item_id,now=uuid4(),datetime.now(timezone.utc)
    await db.execute(text("""INSERT INTO external_availability_rules
      (id,tenant_id,weekday,start_time,end_time,timezone,effective_from,effective_until,active,created_by,created_at,updated_at)
      VALUES (:id,:tenant,:weekday,CAST(:start AS time),CAST(:end AS time),:timezone,:effective_from,:effective_until,TRUE,:actor,:now,:now)"""),{
      "id":item_id,"tenant":ctx["tenant_id"],"weekday":body.weekday,"start":body.start_time,"end":body.end_time,
      "timezone":body.timezone,"effective_from":body.effective_from,"effective_until":body.effective_until,
      "actor":ctx["user_id"],"now":now})
    await db.commit()
    return {"success":True,"data":{"id":str(item_id)},"error":None,"request_id":request.state.correlation_id}

@app.delete("/api/v1/practice-operations/scheduling/availability/{rule_id}")
async def delete_availability(request:Request,rule_id:UUID,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=await _calendar_access(request,db,ctx,"CALENDAR_MANAGE")
    if denied:return denied
    row=(await db.execute(text("UPDATE external_availability_rules SET active=FALSE,updated_at=:now WHERE id=:id AND tenant_id=:tenant AND active=TRUE RETURNING id"),{"now":datetime.now(timezone.utc),"id":rule_id,"tenant":ctx["tenant_id"]})).scalar_one_or_none()
    if not row:return error(request,404,"AVAILABILITY_NOT_FOUND","Availability window was not found")
    await db.commit();return {"success":True,"data":{"id":str(row),"active":False},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/scheduling/booking-links",status_code=201)
async def create_booking_link(request: Request, body: BookingLinkCreate,
                              ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied=await _calendar_access(request,db,ctx,"APPOINTMENT_BOOK")
    if denied: return denied
    kind=(await db.execute(text("SELECT id FROM external_appointment_types WHERE id=:id AND tenant_id=:tenant AND active=TRUE"),
      {"id":body.appointment_type_id,"tenant":ctx["tenant_id"]})).first()
    if not kind: return error(request,404,"APPOINTMENT_TYPE_NOT_FOUND","Appointment type not found")
    raw_token=uuid4().hex+uuid4().hex; item_id,now=uuid4(),datetime.now(timezone.utc)
    await db.execute(text("""INSERT INTO external_booking_links
      (id,tenant_id,appointment_type_id,client_id,token_hash,label,expires_at,active,created_by,created_at)
      VALUES (:id,:tenant,:type,:client,:hash,:label,:expires,TRUE,:actor,:now)"""),{
      "id":item_id,"tenant":ctx["tenant_id"],"type":body.appointment_type_id,"client":body.client_id,
      "hash":hashlib.sha256(raw_token.encode()).hexdigest(),"label":body.label,"expires":body.expires_at,
      "actor":ctx["user_id"],"now":now})
    return {"success":True,"data":{"id":str(item_id),"token":raw_token},"error":None,"request_id":request.state.correlation_id}


@app.get("/api/v1/practice-operations/scheduling/appointments")
async def list_scheduled_appointments(request: Request, client_id: str | None=None,
                                      ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied=await _calendar_access(request,db,ctx,"CALENDAR_VIEW")
    if denied: return denied
    rows=(await db.execute(text("""SELECT a.id,a.client_id,a.starts_at,a.ends_at,a.status,a.attendance_status,
      t.name,t.location_type,t.location_details FROM external_scheduled_appointments a
      JOIN external_appointment_types t ON t.id=a.appointment_type_id AND t.tenant_id=a.tenant_id
      WHERE a.tenant_id=:tenant
        AND (CAST(:client AS text) IS NULL OR a.client_id=CAST(:client AS text))
      ORDER BY a.starts_at"""),
      {"tenant":ctx["tenant_id"],"client":client_id})).mappings().all()
    return {"success":True,"data":{"items":[dict(row) for row in rows]},"error":None,"request_id":request.state.correlation_id}


async def _create_appointment(request, db, tenant_id, client_id, appointment_type_id, starts_at,
                              actor_id, actor_type, booking_link_id=None):
    kind=(await db.execute(text("""SELECT id,duration_minutes,buffer_before_minutes,buffer_after_minutes
      FROM external_appointment_types WHERE id=:id AND tenant_id=:tenant AND active=TRUE"""),
      {"id":appointment_type_id,"tenant":tenant_id})).mappings().first()
    if not kind: return None,error(request,404,"APPOINTMENT_TYPE_NOT_FOUND","Appointment type not found")
    ends_at=starts_at+timedelta(minutes=kind["duration_minutes"])
    conflict=(await db.execute(text("""SELECT id FROM external_scheduled_appointments
      WHERE tenant_id=:tenant AND status IN ('BOOKED','CONFIRMED')
      AND starts_at < :blocked_end AND ends_at > :blocked_start LIMIT 1"""),{
      "tenant":tenant_id,"blocked_start":starts_at-timedelta(minutes=kind["buffer_before_minutes"]),
      "blocked_end":ends_at+timedelta(minutes=kind["buffer_after_minutes"])})).first()
    if conflict: return None,error(request,409,"APPOINTMENT_SLOT_UNAVAILABLE","This time is no longer available")
    item_id,now=uuid4(),datetime.now(timezone.utc)
    await db.execute(text("""INSERT INTO external_scheduled_appointments
      (id,tenant_id,client_id,appointment_type_id,booking_link_id,starts_at,ends_at,status,
       booked_by_type,created_by,created_at,updated_at)
      VALUES (:id,:tenant,:client,:type,:link,:start,:end,'BOOKED',:actor_type,:actor,:now,:now)"""),{
      "id":item_id,"tenant":tenant_id,"client":client_id,"type":appointment_type_id,"link":booking_link_id,
      "start":starts_at,"end":ends_at,"actor_type":actor_type,"actor":actor_id,"now":now})
    await db.execute(text("""INSERT INTO external_scheduling_audit_events
      (id,tenant_id,appointment_id,event_type,actor_id,actor_type,details,created_at)
      VALUES (:id,:tenant,:appointment,'BOOKED',:actor,:actor_type,'{}'::jsonb,:now)"""),{
      "id":uuid4(),"tenant":tenant_id,"appointment":item_id,"actor":actor_id,"actor_type":actor_type,"now":now})
    return {"id":str(item_id),"starts_at":starts_at,"ends_at":ends_at,"status":"BOOKED"},None


@app.post("/api/v1/practice-operations/scheduling/appointments",status_code=201)
async def create_scheduled_appointment(request: Request, body: AppointmentCreate,
                                       ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied=await _calendar_access(request,db,ctx,"APPOINTMENT_BOOK")
    if denied: return denied
    result,denied=await _create_appointment(request,db,ctx["tenant_id"],body.client_id,
      body.appointment_type_id,body.starts_at,ctx["user_id"],"CONSULTANT")
    if denied: return denied
    return {"success":True,"data":result,"error":None,"request_id":request.state.correlation_id}


@app.patch("/api/v1/practice-operations/scheduling/appointments/{appointment_id}")
async def update_scheduled_appointment(request: Request, appointment_id: UUID, body: AppointmentStatusUpdate,
                                       ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied=await _calendar_access(request,db,ctx,"APPOINTMENT_RESCHEDULE")
    if denied: return denied
    now=datetime.now(timezone.utc); attendance="NO_SHOW" if body.status=="NO_SHOW" else "ATTENDED" if body.status=="COMPLETED" else None
    row=(await db.execute(text("""UPDATE external_scheduled_appointments SET status=:status,
      attendance_status=:attendance,cancellation_reason=:reason,updated_at=:now
      WHERE id=:id AND tenant_id=:tenant RETURNING id"""),{"status":body.status,"attendance":attendance,
      "reason":body.cancellation_reason,"now":now,"id":appointment_id,"tenant":ctx["tenant_id"]})).first()
    if not row: return error(request,404,"APPOINTMENT_NOT_FOUND","Appointment not found")
    await db.execute(text("""INSERT INTO external_scheduling_audit_events
      (id,tenant_id,appointment_id,event_type,actor_id,actor_type,details,created_at)
      VALUES (:id,:tenant,:appointment,:event,:actor,'CONSULTANT',CAST(:details AS jsonb),:now)"""),{
      "id":uuid4(),"tenant":ctx["tenant_id"],"appointment":appointment_id,"event":body.status,
      "actor":ctx["user_id"],"details":json.dumps({"reason":body.cancellation_reason}),"now":now})
    return {"success":True,"data":{"id":str(appointment_id),"status":body.status},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/scheduling/waitlist",status_code=201)
async def create_waitlist_entry(request: Request, body: WaitlistCreate,
                                ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied=await _calendar_access(request,db,ctx,"WAITLIST_MANAGE")
    if denied: return denied
    if body.preferred_from and body.preferred_until and body.preferred_until<body.preferred_from:
        return error(request,422,"WAITLIST_WINDOW_INVALID","Preferred end must follow its start")
    kind=(await db.execute(text("SELECT id FROM external_appointment_types WHERE id=:id AND tenant_id=:tenant"),
      {"id":body.appointment_type_id,"tenant":ctx["tenant_id"]})).first()
    if not kind: return error(request,404,"APPOINTMENT_TYPE_NOT_FOUND","Appointment type not found")
    item_id,now=uuid4(),datetime.now(timezone.utc)
    await db.execute(text("""INSERT INTO external_scheduling_waitlist
      (id,tenant_id,client_id,appointment_type_id,preferred_from,preferred_until,status,notes,created_by,created_at,updated_at)
      VALUES (:id,:tenant,:client,:type,:from_at,:until,'WAITING',:notes,:actor,:now,:now)"""),{
      "id":item_id,"tenant":ctx["tenant_id"],"client":body.client_id,"type":body.appointment_type_id,
      "from_at":body.preferred_from,"until":body.preferred_until,"notes":body.notes,"actor":ctx["user_id"],"now":now})
    return {"success":True,"data":{"id":str(item_id),"status":"WAITING"},"error":None,"request_id":request.state.correlation_id}


@app.get("/api/v1/practice-operations/scheduling/waitlist")
async def list_waitlist(request: Request, ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied=await _calendar_access(request,db,ctx,"CALENDAR_VIEW")
    if denied: return denied
    rows=(await db.execute(text("""SELECT w.id,w.client_id,w.preferred_from,w.preferred_until,w.status,w.notes,
      t.name AS appointment_type FROM external_scheduling_waitlist w
      JOIN external_appointment_types t ON t.id=w.appointment_type_id AND t.tenant_id=w.tenant_id
      WHERE w.tenant_id=:tenant ORDER BY CASE WHEN w.status='WAITING' THEN 0 ELSE 1 END,w.created_at"""),
      {"tenant":ctx["tenant_id"]})).mappings().all()
    return {"success":True,"data":{"items":[dict(row) for row in rows]},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/public-booking/{token}",status_code=201)
async def public_self_booking(request: Request, token: str, starts_at: datetime=Query(...), db: AsyncSession=Depends(get_db)):
    token_digest=hashlib.sha256(token.encode()).hexdigest()
    link=(await db.execute(text("""SELECT id,tenant_id,client_id,appointment_type_id FROM external_booking_links
      WHERE token_hash=:hash AND active=TRUE AND (expires_at IS NULL OR expires_at>NOW())"""),{"hash":token_digest})).mappings().first()
    if not link or not link["client_id"]: return error(request,404,"BOOKING_LINK_INVALID","Booking link is invalid or expired")
    available=(await db.execute(text("""SELECT id FROM external_availability_rules
      WHERE tenant_id=:tenant AND active=TRUE
      AND (EXTRACT(ISODOW FROM (:start AT TIME ZONE timezone))::int-1)=weekday
      AND CAST(:start AT TIME ZONE timezone AS time)>=start_time
      AND CAST(:start AT TIME ZONE timezone AS time)<end_time
      AND (effective_from IS NULL OR CAST(:start AT TIME ZONE timezone AS date)>=effective_from)
      AND (effective_until IS NULL OR CAST(:start AT TIME ZONE timezone AS date)<=effective_until)
      LIMIT 1"""),{"tenant":link["tenant_id"],"start":starts_at})).first()
    if not available: return error(request,409,"APPOINTMENT_OUTSIDE_AVAILABILITY","This time is outside current availability")
    result,denied=await _create_appointment(request,db,link["tenant_id"],link["client_id"],
      link["appointment_type_id"],starts_at,link["client_id"],"CLIENT",link["id"])
    if denied: return denied
    return {"success":True,"data":result,"error":None,"request_id":request.state.correlation_id}


@app.get("/api/v1/practice-operations/public-booking/{token}")
async def public_booking_details(request: Request, token: str, db: AsyncSession=Depends(get_db)):
    token_digest=hashlib.sha256(token.encode()).hexdigest()
    link=(await db.execute(text("""SELECT l.id,l.tenant_id,l.label,t.name,t.description,t.duration_minutes,
      t.location_type,t.location_details FROM external_booking_links l
      JOIN external_appointment_types t ON t.id=l.appointment_type_id AND t.tenant_id=l.tenant_id
      WHERE l.token_hash=:hash AND l.active=TRUE AND l.client_id IS NOT NULL
      AND (l.expires_at IS NULL OR l.expires_at>NOW())"""),{"hash":token_digest})).mappings().first()
    if not link: return error(request,404,"BOOKING_LINK_INVALID","Booking link is invalid or expired")
    rules=(await db.execute(text("""SELECT weekday,start_time,end_time,timezone,effective_from,effective_until
      FROM external_availability_rules WHERE tenant_id=:tenant AND active=TRUE
      ORDER BY weekday,start_time"""),{"tenant":link["tenant_id"]})).mappings().all()
    return {"success":True,"data":{"label":link["label"],"appointment_type":link["name"],
      "description":link["description"],"duration_minutes":link["duration_minutes"],
      "location_type":link["location_type"],"location_details":link["location_details"],
      "availability":[dict(row) for row in rules]},"error":None,"request_id":request.state.correlation_id}


async def _billing_access(request, db, ctx):
    denied=external_only(request,ctx) or await require_capability(request,db,ctx,"BILLING")
    if denied:return denied
    denied,_=await _team_guard(request,db,ctx,"BILLING_VIEW" if request.method=="GET" else "BILLING_MANAGE")
    return denied


async def _billing_audit(db, ctx, event_type, *, invoice_id=None, service_id=None,
                         payment_id=None, receipt_id=None, details=None):
    await db.execute(text("""INSERT INTO external_invoice_audit_events
      (id,tenant_id,invoice_id,service_id,payment_id,receipt_id,event_type,actor_id,actor_type,details,created_at)
      VALUES (:id,:tenant,:invoice,:service,:payment,:receipt,:event,:actor,'CONSULTANT',CAST(:details AS jsonb),:now)"""),{
      "id":uuid4(),"tenant":ctx["tenant_id"],"invoice":invoice_id,"service":service_id,
      "payment":payment_id,"receipt":receipt_id,"event":event_type,"actor":ctx["user_id"],
      "details":json.dumps(details or {}),"now":datetime.now(timezone.utc)})


def _invoice_totals(items):
    calculated=[]
    for position,item in enumerate(items):
        line=calculate_line(item.quantity,item.unit_price_minor,item.discount_type,
                            item.discount_value,item.tax_rate_bps)
        calculated.append((position,item,line))
    return calculated,{
      "subtotal_minor":sum(row.subtotal_minor for _,_,row in calculated),
      "discount_amount_minor":sum(row.discount_minor for _,_,row in calculated),
      "tax_total_minor":sum(row.tax_minor for _,_,row in calculated),
      "grand_total_minor":sum(row.total_minor for _,_,row in calculated),
    }


async def _validate_billing_links(request,db,ctx,body):
    if body.client_package_id:
        row=(await db.execute(text("SELECT client_id FROM external_client_packages WHERE id=:id AND tenant_id=:tenant"),
          {"id":body.client_package_id,"tenant":ctx["tenant_id"]})).mappings().first()
        if not row or row["client_id"] != body.client_id:
            return error(request,404,"CLIENT_PACKAGE_NOT_FOUND","Client package not found")
    if body.appointment_id:
        row=(await db.execute(text("SELECT client_id FROM external_scheduled_appointments WHERE id=:id AND tenant_id=:tenant"),
          {"id":body.appointment_id,"tenant":ctx["tenant_id"]})).mappings().first()
        if not row or row["client_id"] != body.client_id:
            return error(request,404,"APPOINTMENT_NOT_FOUND","Appointment not found")
    for item in body.items:
        if item.service_id and not (await db.execute(text("SELECT id FROM external_billable_services WHERE id=:id AND tenant_id=:tenant AND active=TRUE"),
          {"id":item.service_id,"tenant":ctx["tenant_id"]})).first():
            return error(request,404,"BILLABLE_SERVICE_NOT_FOUND","Billable service not found")
    return None


async def _replace_invoice_items(db,ctx,invoice_id,calculated):
    await db.execute(text("DELETE FROM external_invoice_items WHERE invoice_id=:invoice AND tenant_id=:tenant"),
                     {"invoice":invoice_id,"tenant":ctx["tenant_id"]})
    for position,item,line in calculated:
        await db.execute(text("""INSERT INTO external_invoice_items
          (id,tenant_id,invoice_id,service_id,description,quantity,unit_price_minor,discount_type,
           discount_value,discount_amount_minor,tax_type,tax_rate_bps,line_subtotal_minor,line_tax_minor,line_total_minor,display_order)
          VALUES (:id,:tenant,:invoice,:service,:description,:quantity,:unit_price,:discount_type,
           :discount_value,:discount_amount,:tax_type,:tax_rate,:subtotal,:tax,:total,:position)"""),{
          "id":uuid4(),"tenant":ctx["tenant_id"],"invoice":invoice_id,"service":item.service_id,
          "description":item.description,"quantity":item.quantity,"unit_price":item.unit_price_minor,
          "discount_type":item.discount_type,"discount_value":item.discount_value,
          "discount_amount":line.discount_minor,"tax_type":item.tax_type,"tax_rate":item.tax_rate_bps,
          "subtotal":line.subtotal_minor,"tax":line.tax_minor,"total":line.total_minor,"position":position})


@app.get("/api/v1/practice-operations/billing/services")
async def list_billable_services(request: Request, include_inactive: bool=False,
                                  ctx=Depends(context),db: AsyncSession=Depends(get_db)):
    denied=await _billing_access(request,db,ctx)
    if denied: return denied
    rows=(await db.execute(text("""SELECT id,name,description,category,default_price_minor,currency,
      default_tax_type,default_tax_rate_bps,active FROM external_billable_services
      WHERE tenant_id=:tenant AND (:inactive OR active=TRUE) ORDER BY name"""),
      {"tenant":ctx["tenant_id"],"inactive":include_inactive})).mappings().all()
    return {"success":True,"data":{"items":[dict(row) for row in rows]},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/billing/services",status_code=201)
async def create_billable_service(request: Request, body: BillableServiceCreate,
                                   ctx=Depends(context),db: AsyncSession=Depends(get_db)):
    denied=await _billing_access(request,db,ctx)
    if denied: return denied
    item_id,now=uuid4(),datetime.now(timezone.utc)
    await db.execute(text("""INSERT INTO external_billable_services
      (id,tenant_id,name,description,category,default_price_minor,currency,default_tax_type,
       default_tax_rate_bps,active,created_by,created_at,updated_at)
      VALUES (:id,:tenant,:name,:description,:category,:price,:currency,:tax_type,:tax_rate,:active,:actor,:now,:now)"""),{
      "id":item_id,"tenant":ctx["tenant_id"],"name":body.name,"description":body.description,
      "category":body.category,"price":body.default_price_minor,"currency":body.currency,
      "tax_type":body.default_tax_type,"tax_rate":body.default_tax_rate_bps,"active":body.active,
      "actor":ctx["user_id"],"now":now})
    await _billing_audit(db,ctx,"SERVICE_CREATED",service_id=item_id)
    return {"success":True,"data":{"id":str(item_id)},"error":None,"request_id":request.state.correlation_id}


@app.patch("/api/v1/practice-operations/billing/services/{service_id}")
async def update_billable_service(request: Request, service_id: UUID, body: BillableServiceUpdate,
                                   ctx=Depends(context),db: AsyncSession=Depends(get_db)):
    denied=await _billing_access(request,db,ctx)
    if denied: return denied
    row=(await db.execute(text("""UPDATE external_billable_services SET name=:name,description=:description,
      category=:category,default_price_minor=:price,currency=:currency,default_tax_type=:tax_type,
      default_tax_rate_bps=:tax_rate,active=:active,updated_at=:now WHERE id=:id AND tenant_id=:tenant RETURNING id"""),{
      "id":service_id,"tenant":ctx["tenant_id"],"name":body.name,"description":body.description,
      "category":body.category,"price":body.default_price_minor,"currency":body.currency,
      "tax_type":body.default_tax_type,"tax_rate":body.default_tax_rate_bps,"active":body.active,
      "now":datetime.now(timezone.utc)})).first()
    if not row: return error(request,404,"BILLABLE_SERVICE_NOT_FOUND","Billable service not found")
    await _billing_audit(db,ctx,"SERVICE_UPDATED",service_id=service_id)
    return {"success":True,"data":{"id":str(service_id)},"error":None,"request_id":request.state.correlation_id}


@app.get("/api/v1/practice-operations/billing/invoices")
async def list_invoices(request: Request, status: str|None=None, client_id: str|None=None,
                        search: str|None=None,ctx=Depends(context),db: AsyncSession=Depends(get_db)):
    denied=await _billing_access(request,db,ctx)
    if denied: return denied
    rows=(await db.execute(text("""SELECT id,client_id,invoice_number,
      CASE WHEN status IN ('ISSUED','PART_PAID') AND due_date<CURRENT_DATE AND balance_due_minor>0 THEN 'OVERDUE' ELSE status END AS status,
      currency,issue_date,due_date,subtotal_minor,discount_amount_minor,tax_total_minor,grand_total_minor,
      amount_paid_minor,balance_due_minor,created_at FROM external_invoices WHERE tenant_id=:tenant
      AND (CAST(:client AS text) IS NULL OR client_id=CAST(:client AS text))
      AND (CAST(:status AS text) IS NULL OR status=CAST(:status AS text))
      AND (CAST(:search AS text) IS NULL OR invoice_number ILIKE '%'||CAST(:search AS text)||'%'
        OR client_id ILIKE '%'||CAST(:search AS text)||'%')
      ORDER BY created_at DESC"""),{"tenant":ctx["tenant_id"],"client":client_id,"status":status,"search":search})).mappings().all()
    return {"success":True,"data":{"items":[dict(row) for row in rows]},"error":None,"request_id":request.state.correlation_id}


@app.get("/api/v1/practice-operations/billing/overview")
async def billing_overview(request: Request,ctx=Depends(context),db: AsyncSession=Depends(get_db)):
    denied=await _billing_access(request,db,ctx)
    if denied: return denied
    row=(await db.execute(text("""SELECT
      COALESCE(SUM(balance_due_minor) FILTER (WHERE status IN ('ISSUED','PART_PAID','OVERDUE')),0)::bigint AS outstanding_minor,
      COALESCE(SUM(amount_paid_minor) FILTER (WHERE paid_at>=date_trunc('month',CURRENT_DATE)),0)::bigint AS paid_this_month_minor,
      COUNT(*) FILTER (WHERE status IN ('ISSUED','PART_PAID','OVERDUE') AND due_date<CURRENT_DATE AND balance_due_minor>0)::int AS overdue_count,
      COUNT(*) FILTER (WHERE status IN ('ISSUED','PART_PAID','OVERDUE'))::int AS open_count
      FROM external_invoices WHERE tenant_id=:tenant"""),{"tenant":ctx["tenant_id"]})).mappings().one()
    return {"success":True,"data":dict(row),"error":None,"request_id":request.state.correlation_id}


@app.get("/api/v1/practice-operations/billing/clients/{client_id}")
async def client_billing_projection(request: Request,client_id: str,ctx=Depends(context),db: AsyncSession=Depends(get_db)):
    denied=await _billing_access(request,db,ctx)
    if denied: return denied
    invoices=(await db.execute(text("""SELECT id,invoice_number,status,currency,issue_date,due_date,grand_total_minor,
      amount_paid_minor,balance_due_minor,client_package_id FROM external_invoices
      WHERE tenant_id=:tenant AND client_id=:client ORDER BY created_at DESC"""),
      {"tenant":ctx["tenant_id"],"client":client_id})).mappings().all()
    payments=(await db.execute(text("""SELECT p.id,p.invoice_id,p.amount_minor,p.currency,p.method,p.payment_date,
      r.id AS receipt_id,r.receipt_number FROM external_payment_records p
      JOIN external_receipts r ON r.payment_id=p.id AND r.tenant_id=p.tenant_id
      WHERE p.tenant_id=:tenant AND p.client_id=:client ORDER BY p.payment_date DESC"""),
      {"tenant":ctx["tenant_id"],"client":client_id})).mappings().all()
    return {"success":True,"data":{"invoices":[dict(row) for row in invoices],"payments":[dict(row) for row in payments],
      "outstanding_minor":sum(row["balance_due_minor"] for row in invoices if row["status"] not in {"DRAFT","CANCELLED"})},
      "error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/billing/invoices",status_code=201)
async def create_invoice(request: Request, body: InvoiceCreate,ctx=Depends(context),db: AsyncSession=Depends(get_db)):
    denied=await _billing_access(request,db,ctx)
    if denied: return denied
    denied=await _validate_billing_links(request,db,ctx,body)
    if denied: return denied
    calculated,totals=_invoice_totals(body.items); invoice_id,now=uuid4(),datetime.now(timezone.utc)
    await db.execute(text("""INSERT INTO external_invoices
      (id,tenant_id,client_id,status,currency,issue_date,due_date,client_package_id,appointment_id,notes,terms,
       subtotal_minor,discount_type,discount_value,discount_amount_minor,tax_total_minor,grand_total_minor,
       amount_paid_minor,balance_due_minor,tax_snapshot,created_by,created_at,updated_at)
      VALUES (:id,:tenant,:client,'DRAFT',:currency,:issue,:due,:package,:appointment,:notes,:terms,
       :subtotal,'NONE',0,:discount,:tax,:total,0,:total,'{}'::jsonb,:actor,:now,:now)"""),{
      "id":invoice_id,"tenant":ctx["tenant_id"],"client":body.client_id,"currency":body.currency,
      "issue":body.issue_date,"due":body.due_date,"package":body.client_package_id,"appointment":body.appointment_id,
      "notes":body.notes,"terms":body.terms,"subtotal":totals["subtotal_minor"],"discount":totals["discount_amount_minor"],
      "tax":totals["tax_total_minor"],"total":totals["grand_total_minor"],"actor":ctx["user_id"],"now":now})
    await _replace_invoice_items(db,ctx,invoice_id,calculated)
    await _billing_audit(db,ctx,"INVOICE_CREATED",invoice_id=invoice_id,details=totals)
    return {"success":True,"data":{"id":str(invoice_id),"status":"DRAFT",**totals,"balance_due_minor":totals["grand_total_minor"]},"error":None,"request_id":request.state.correlation_id}


@app.patch("/api/v1/practice-operations/billing/invoices/{invoice_id}")
async def update_invoice(request: Request, invoice_id: UUID, body: InvoiceUpdate,
                         ctx=Depends(context),db: AsyncSession=Depends(get_db)):
    denied=await _billing_access(request,db,ctx)
    if denied: return denied
    denied=await _validate_billing_links(request,db,ctx,body)
    if denied: return denied
    calculated,totals=_invoice_totals(body.items)
    row=(await db.execute(text("""UPDATE external_invoices SET client_id=:client,currency=:currency,issue_date=:issue,
      due_date=:due,client_package_id=:package,appointment_id=:appointment,notes=:notes,terms=:terms,
      subtotal_minor=:subtotal,discount_amount_minor=:discount,tax_total_minor=:tax,grand_total_minor=:total,
      balance_due_minor=:total,updated_at=:now WHERE id=:id AND tenant_id=:tenant AND status='DRAFT' RETURNING id"""),{
      "id":invoice_id,"tenant":ctx["tenant_id"],"client":body.client_id,"currency":body.currency,
      "issue":body.issue_date,"due":body.due_date,"package":body.client_package_id,"appointment":body.appointment_id,
      "notes":body.notes,"terms":body.terms,"subtotal":totals["subtotal_minor"],"discount":totals["discount_amount_minor"],
      "tax":totals["tax_total_minor"],"total":totals["grand_total_minor"],"now":datetime.now(timezone.utc)})).first()
    if not row: return error(request,409,"INVOICE_NOT_EDITABLE","Only draft invoices may be edited")
    await _replace_invoice_items(db,ctx,invoice_id,calculated)
    await _billing_audit(db,ctx,"INVOICE_UPDATED",invoice_id=invoice_id,details=totals)
    return {"success":True,"data":{"id":str(invoice_id),**totals},"error":None,"request_id":request.state.correlation_id}


@app.get("/api/v1/practice-operations/billing/invoices/{invoice_id}")
async def get_invoice(request: Request, invoice_id: UUID,ctx=Depends(context),db: AsyncSession=Depends(get_db)):
    denied=await _billing_access(request,db,ctx)
    if denied: return denied
    invoice=(await db.execute(text("""SELECT id,tenant_id,client_id,invoice_number,status,currency,issue_date,due_date,
      client_package_id,appointment_id,notes,terms,subtotal_minor,discount_type,discount_value,
      discount_amount_minor,tax_total_minor,grand_total_minor,amount_paid_minor,balance_due_minor,
      tax_snapshot,created_by,issued_by,cancelled_by,created_at,updated_at,issued_at,paid_at,cancelled_at
      FROM external_invoices WHERE id=:id AND tenant_id=:tenant"""),
      {"id":invoice_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not invoice: return error(request,404,"INVOICE_NOT_FOUND","Invoice not found")
    items=(await db.execute(text("""SELECT id,service_id,description,quantity,unit_price_minor,discount_type,
      discount_value,discount_amount_minor,tax_type,tax_rate_bps,line_subtotal_minor,line_tax_minor,
      line_total_minor,display_order FROM external_invoice_items
      WHERE invoice_id=:id AND tenant_id=:tenant ORDER BY display_order"""),
      {"id":invoice_id,"tenant":ctx["tenant_id"]})).mappings().all()
    payments=(await db.execute(text("""SELECT id,amount_minor,currency,method,provenance,reference_number,
      provider_name,provider_reference,payment_date,notes,recorded_by,created_at
      FROM external_payment_records WHERE invoice_id=:id AND tenant_id=:tenant ORDER BY payment_date,created_at"""),
      {"id":invoice_id,"tenant":ctx["tenant_id"]})).mappings().all()
    audit=(await db.execute(text("SELECT event_type,actor_id,actor_type,details,created_at FROM external_invoice_audit_events WHERE invoice_id=:id AND tenant_id=:tenant ORDER BY created_at"),
      {"id":invoice_id,"tenant":ctx["tenant_id"]})).mappings().all()
    return {"success":True,"data":{**dict(invoice),"items":[dict(row) for row in items],"payments":[dict(row) for row in payments],"audit":[dict(row) for row in audit]},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/billing/invoices/{invoice_id}/issue")
async def issue_invoice(request: Request, invoice_id: UUID,ctx=Depends(context),db: AsyncSession=Depends(get_db)):
    denied=await _billing_access(request,db,ctx)
    if denied: return denied
    invoice=(await db.execute(text("SELECT id,issue_date,due_date FROM external_invoices WHERE id=:id AND tenant_id=:tenant AND status='DRAFT' FOR UPDATE"),
      {"id":invoice_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not invoice: return error(request,409,"INVOICE_NOT_ISSUABLE","Only a draft invoice may be issued")
    now=datetime.now(timezone.utc)
    sequence=(await db.execute(text("""INSERT INTO external_invoice_sequences(tenant_id,prefix,next_number,updated_at)
      VALUES (:tenant,'INV',2,:now) ON CONFLICT (tenant_id) DO UPDATE SET next_number=external_invoice_sequences.next_number+1,
      updated_at=EXCLUDED.updated_at RETURNING prefix,next_number-1 AS allocated"""),{"tenant":ctx["tenant_id"],"now":now})).mappings().one()
    number=f"{sequence['prefix']}-{now.year}-{int(sequence['allocated']):04d}"
    row=(await db.execute(text("""UPDATE external_invoices SET invoice_number=:number,status='ISSUED',
      issue_date=COALESCE(issue_date,CURRENT_DATE),due_date=COALESCE(due_date,CURRENT_DATE),issued_by=:actor,
      issued_at=:now,updated_at=:now WHERE id=:id AND tenant_id=:tenant AND status='DRAFT'
      RETURNING id,invoice_number,status"""),{"number":number,"actor":ctx["user_id"],"now":now,"id":invoice_id,"tenant":ctx["tenant_id"]})).mappings().one()
    await _billing_audit(db,ctx,"INVOICE_ISSUED",invoice_id=invoice_id,details={"invoice_number":number})
    return {"success":True,"data":dict(row),"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/billing/invoices/{invoice_id}/cancel")
async def cancel_invoice(request: Request, invoice_id: UUID,ctx=Depends(context),db: AsyncSession=Depends(get_db)):
    denied=await _billing_access(request,db,ctx)
    if denied: return denied
    now=datetime.now(timezone.utc)
    row=(await db.execute(text("""UPDATE external_invoices SET status='CANCELLED',cancelled_by=:actor,cancelled_at=:now,updated_at=:now
      WHERE id=:id AND tenant_id=:tenant AND status IN ('DRAFT','ISSUED','PART_PAID','OVERDUE') RETURNING id"""),
      {"actor":ctx["user_id"],"now":now,"id":invoice_id,"tenant":ctx["tenant_id"]})).first()
    if not row: return error(request,409,"INVOICE_NOT_CANCELLABLE","Invoice cannot be cancelled")
    await _billing_audit(db,ctx,"INVOICE_CANCELLED",invoice_id=invoice_id)
    return {"success":True,"data":{"id":str(invoice_id),"status":"CANCELLED"},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/billing/invoices/{invoice_id}/payments",status_code=201)
async def record_payment(request: Request, invoice_id: UUID, body: PaymentCreate,
                         ctx=Depends(context),db: AsyncSession=Depends(get_db)):
    denied=await _billing_access(request,db,ctx)
    if denied: return denied
    invoice=(await db.execute(text("""SELECT id,client_id,currency,status,balance_due_minor FROM external_invoices
      WHERE id=:id AND tenant_id=:tenant FOR UPDATE"""),{"id":invoice_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not invoice: return error(request,404,"INVOICE_NOT_FOUND","Invoice not found")
    if invoice["status"] not in {"ISSUED","PART_PAID","OVERDUE"}: return error(request,409,"PAYMENT_NOT_ALLOWED","Payment cannot be recorded for this invoice")
    if invoice["currency"] != body.currency: return error(request,422,"PAYMENT_CURRENCY_MISMATCH","Payment currency must match the invoice")
    if body.amount_minor > invoice["balance_due_minor"]: return error(request,422,"OVERPAYMENT_NOT_ALLOWED","Payment cannot exceed the outstanding balance")
    payment_id,receipt_id,now=uuid4(),uuid4(),datetime.now(timezone.utc)
    remaining=invoice["balance_due_minor"]-body.amount_minor; status="PAID" if remaining==0 else "PART_PAID"
    await db.execute(text("""INSERT INTO external_payment_records
      (id,tenant_id,client_id,invoice_id,amount_minor,currency,method,provenance,reference_number,
       provider_name,provider_reference,payment_date,notes,recorded_by,created_at)
      VALUES (:id,:tenant,:client,:invoice,:amount,:currency,:method,:provenance,:reference,:provider,
       :provider_reference,:payment_date,:notes,:actor,:now)"""),{
      "id":payment_id,"tenant":ctx["tenant_id"],"client":invoice["client_id"],"invoice":invoice_id,
      "amount":body.amount_minor,"currency":body.currency,"method":body.method,"provenance":body.provenance,
      "reference":body.reference_number,"provider":body.provider_name,"provider_reference":body.provider_reference,
      "payment_date":body.payment_date,"notes":body.notes,"actor":ctx["user_id"],"now":now})
    await db.execute(text("""UPDATE external_invoices SET amount_paid_minor=amount_paid_minor+:amount,
      balance_due_minor=:remaining,status=:status,paid_at=CASE WHEN :status='PAID' THEN :now ELSE paid_at END,updated_at=:now
      WHERE id=:id AND tenant_id=:tenant"""),{"amount":body.amount_minor,"remaining":remaining,"status":status,
      "now":now,"id":invoice_id,"tenant":ctx["tenant_id"]})
    receipt_number=f"RCT-{now:%Y%m%d}-{str(receipt_id)[:8].upper()}"
    await db.execute(text("""INSERT INTO external_receipts
      (id,tenant_id,client_id,payment_id,invoice_id,receipt_number,amount_minor,currency,remaining_balance_minor,created_at)
      VALUES (:id,:tenant,:client,:payment,:invoice,:number,:amount,:currency,:remaining,:now)"""),{
      "id":receipt_id,"tenant":ctx["tenant_id"],"client":invoice["client_id"],"payment":payment_id,
      "invoice":invoice_id,"number":receipt_number,"amount":body.amount_minor,"currency":body.currency,
      "remaining":remaining,"now":now})
    await _billing_audit(db,ctx,"PAYMENT_RECORDED",invoice_id=invoice_id,payment_id=payment_id,details={"amount_minor":body.amount_minor,"provenance":body.provenance})
    await _billing_audit(db,ctx,"RECEIPT_CREATED",invoice_id=invoice_id,payment_id=payment_id,receipt_id=receipt_id)
    return {"success":True,"data":{"id":str(payment_id),"receipt_id":str(receipt_id),"receipt_number":receipt_number,"status":status,"balance_due_minor":remaining},"error":None,"request_id":request.state.correlation_id}


@app.get("/api/v1/practice-operations/billing/payments")
async def list_payments(request: Request,client_id: str|None=None,ctx=Depends(context),db: AsyncSession=Depends(get_db)):
    denied=await _billing_access(request,db,ctx)
    if denied: return denied
    rows=(await db.execute(text("""SELECT p.id,p.client_id,p.invoice_id,p.amount_minor,p.currency,p.method,p.provenance,
      p.reference_number,p.payment_date,p.created_at,i.invoice_number,r.id AS receipt_id,r.receipt_number
      FROM external_payment_records p JOIN external_invoices i ON i.id=p.invoice_id AND i.tenant_id=p.tenant_id
      JOIN external_receipts r ON r.payment_id=p.id AND r.tenant_id=p.tenant_id
      WHERE p.tenant_id=:tenant
        AND (CAST(:client AS text) IS NULL OR p.client_id=CAST(:client AS text))
      ORDER BY p.payment_date DESC,p.created_at DESC"""),
      {"tenant":ctx["tenant_id"],"client":client_id})).mappings().all()
    return {"success":True,"data":{"items":[dict(row) for row in rows]},"error":None,"request_id":request.state.correlation_id}


@app.get("/api/v1/practice-operations/billing/receipts/{receipt_id}")
async def get_receipt(request: Request,receipt_id: UUID,ctx=Depends(context),db: AsyncSession=Depends(get_db)):
    denied=await _billing_access(request,db,ctx)
    if denied: return denied
    row=(await db.execute(text("""SELECT r.*,i.invoice_number,p.payment_date,p.method,p.reference_number
      FROM external_receipts r JOIN external_invoices i ON i.id=r.invoice_id AND i.tenant_id=r.tenant_id
      JOIN external_payment_records p ON p.id=r.payment_id AND p.tenant_id=r.tenant_id
      WHERE r.id=:id AND r.tenant_id=:tenant"""),{"id":receipt_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not row: return error(request,404,"RECEIPT_NOT_FOUND","Receipt not found")
    return {"success":True,"data":dict(row),"error":None,"request_id":request.state.correlation_id}


async def _p15_access(request, db, ctx, capability="RESOURCE_LIBRARY"):
    denied=external_only(request, ctx) or await require_capability(request, db, ctx, capability)
    if denied:return denied
    denied,_=await _team_guard(request,db,ctx,"RESOURCE_VIEW" if request.method=="GET" else "RESOURCE_MANAGE")
    return denied


async def _p15_audit(db, ctx, event_type, *, client_id=None, resource_id=None,
                     assignment_id=None, homework_id=None, actor_type="PRACTITIONER", metadata=None):
    await db.execute(text("""INSERT INTO external_resource_audit_events
      (id,tenant_id,client_id,resource_id,assignment_id,homework_id,event_type,actor_id,actor_type,metadata,created_at)
      VALUES (:id,:tenant,:client,:resource,:assignment,:homework,:event,:actor,:actor_type,CAST(:metadata AS jsonb),:now)"""), {
        "id":uuid4(),"tenant":ctx.get("tenant_id"),"client":client_id,"resource":resource_id,
        "assignment":assignment_id,"homework":homework_id,"event":event_type,
        "actor":ctx.get("user_id"),"actor_type":actor_type,"metadata":json.dumps(metadata or {}),
        "now":datetime.now(timezone.utc),
    })


def _validate_resource_reference(body):
    if body.resource_type.endswith("_LINK"):
        parsed=urlparse(body.content_reference)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("External resource links must use HTTPS")


@app.get("/api/v1/practice-operations/resources")
async def list_professional_resources(request:Request, scope:str|None=None, resource_type:str|None=None,
                                      active:bool|None=True, ctx=Depends(context), db:AsyncSession=Depends(get_db)):
    denied=await _p15_access(request,db,ctx)
    if denied:return denied
    rows=(await db.execute(text("""SELECT d.*,v.id AS version_id,v.version,v.content_reference,v.media_type,
      v.duration_minutes,v.instructions,v.tags,v.capability_required
      FROM external_resource_definitions d JOIN LATERAL
       (SELECT rv.id,rv.resource_id,rv.tenant_id,rv.version,rv.content_reference,rv.media_type,
        rv.duration_minutes,rv.instructions,rv.tags,rv.capability_required,rv.created_by,rv.created_at
        FROM external_resource_versions rv WHERE rv.resource_id=d.id ORDER BY rv.version DESC LIMIT 1) v ON TRUE
      WHERE (d.tenant_id=:tenant OR (d.scope='SYSTEM' AND d.tenant_id IS NULL))
      AND (CAST(:scope AS text) IS NULL OR d.scope=CAST(:scope AS text))
      AND (CAST(:type AS text) IS NULL OR d.resource_type=CAST(:type AS text))
      AND (CAST(:active AS boolean) IS NULL OR d.active=CAST(:active AS boolean))
      ORDER BY d.scope,d.title"""),{
        "tenant":ctx["tenant_id"],"scope":scope,"type":resource_type,"active":active})).mappings().all()
    return {"success":True,"data":{"items":[dict(r) for r in rows]},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/resources",status_code=201)
async def create_professional_resource(request:Request,body:ProfessionalResourceCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=await _p15_access(request,db,ctx)
    if denied:return denied
    try:_validate_resource_reference(body)
    except ValueError as exc:return error(request,422,"RESOURCE_REFERENCE_INVALID",str(exc))
    now,rid,vid=datetime.now(timezone.utc),uuid4(),uuid4()
    owner=ctx["user_id"] if body.scope=="PRACTITIONER" else None
    await db.execute(text("""INSERT INTO external_resource_definitions
      (id,tenant_id,scope,profession_code,title,description,resource_type,active,owner_practitioner_id,created_by,created_at,updated_at)
      VALUES (:id,:tenant,:scope,:profession,:title,:description,:type,TRUE,:owner,:actor,:now,:now)"""),{
      "id":rid,"tenant":ctx["tenant_id"],"scope":body.scope,"profession":body.profession_code,"title":body.title,
      "description":body.description,"type":body.resource_type,"owner":owner,"actor":ctx["user_id"],"now":now})
    await db.execute(text("""INSERT INTO external_resource_versions
      (id,resource_id,tenant_id,version,content_reference,media_type,duration_minutes,instructions,tags,capability_required,created_by,created_at)
      VALUES (:id,:resource,:tenant,1,:reference,:media,:duration,:instructions,CAST(:tags AS jsonb),:capability,:actor,:now)"""),{
      "id":vid,"resource":rid,"tenant":ctx["tenant_id"],"reference":body.content_reference,"media":body.media_type,
      "duration":body.duration_minutes,"instructions":body.instructions,"tags":json.dumps(body.tags),
      "capability":body.capability_required,"actor":ctx["user_id"],"now":now})
    await _p15_audit(db,ctx,"RESOURCE_CREATED",resource_id=rid)
    return {"success":True,"data":{"id":rid,"version":1},"error":None,"request_id":request.state.correlation_id}


@app.get("/api/v1/practice-operations/resources/{resource_id}")
async def get_professional_resource(request:Request,resource_id:UUID,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=await _p15_access(request,db,ctx)
    if denied:return denied
    row=(await db.execute(text("""SELECT d.*,v.id AS version_id,v.version,v.content_reference,v.media_type,v.duration_minutes,
      v.instructions,v.tags,v.capability_required FROM external_resource_definitions d JOIN external_resource_versions v ON v.resource_id=d.id
      WHERE d.id=:id AND (d.tenant_id=:tenant OR (d.scope='SYSTEM' AND d.tenant_id IS NULL)) ORDER BY v.version DESC LIMIT 1"""),
      {"id":resource_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not row:return error(request,404,"RESOURCE_NOT_FOUND","Resource not found")
    return {"success":True,"data":dict(row),"error":None,"request_id":request.state.correlation_id}


@app.patch("/api/v1/practice-operations/resources/{resource_id}")
async def update_professional_resource(request:Request,resource_id:UUID,body:ProfessionalResourceUpdate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=await _p15_access(request,db,ctx)
    if denied:return denied
    row=(await db.execute(text("""SELECT d.scope,d.resource_type,COALESCE(MAX(v.version),0) AS version FROM external_resource_definitions d
      LEFT JOIN external_resource_versions v ON v.resource_id=d.id WHERE d.id=:id AND d.tenant_id=:tenant GROUP BY d.scope,d.resource_type"""),
      {"id":resource_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not row:return error(request,404,"RESOURCE_NOT_FOUND","Resource not found")
    if row["scope"]=="SYSTEM":return error(request,403,"SYSTEM_RESOURCE_IMMUTABLE","System resources cannot be edited")
    if row["resource_type"].endswith("_LINK"):
        parsed=urlparse(body.content_reference)
        if parsed.scheme!="https" or not parsed.netloc:return error(request,422,"RESOURCE_REFERENCE_INVALID","External resource links must use HTTPS")
    now,version=datetime.now(timezone.utc),row["version"]+1
    await db.execute(text("UPDATE external_resource_definitions SET title=:title,description=:description,updated_at=:now WHERE id=:id AND tenant_id=:tenant"),
      {"title":body.title,"description":body.description,"now":now,"id":resource_id,"tenant":ctx["tenant_id"]})
    await db.execute(text("""INSERT INTO external_resource_versions
      (id,resource_id,tenant_id,version,content_reference,media_type,duration_minutes,instructions,tags,capability_required,created_by,created_at)
      VALUES (:id,:resource,:tenant,:version,:reference,:media,:duration,:instructions,CAST(:tags AS jsonb),:capability,:actor,:now)"""),{
      "id":uuid4(),"resource":resource_id,"tenant":ctx["tenant_id"],"version":version,"reference":body.content_reference,
      "media":body.media_type,"duration":body.duration_minutes,"instructions":body.instructions,"tags":json.dumps(body.tags),
      "capability":body.capability_required,"actor":ctx["user_id"],"now":now})
    await _p15_audit(db,ctx,"RESOURCE_UPDATED",resource_id=resource_id,metadata={"version":version})
    return {"success":True,"data":{"id":resource_id,"version":version},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/resources/{resource_id}/archive")
async def archive_professional_resource(request:Request,resource_id:UUID,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=await _p15_access(request,db,ctx)
    if denied:return denied
    row=(await db.execute(text("UPDATE external_resource_definitions SET active=FALSE,updated_at=:now WHERE id=:id AND tenant_id=:tenant AND scope<>'SYSTEM' RETURNING id"),
      {"now":datetime.now(timezone.utc),"id":resource_id,"tenant":ctx["tenant_id"]})).first()
    if not row:return error(request,404,"RESOURCE_NOT_FOUND","Resource not found")
    await _p15_audit(db,ctx,"RESOURCE_ARCHIVED",resource_id=resource_id)
    return {"success":True,"data":{"id":resource_id,"active":False},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/clients/{client_id}/resources",status_code=201)
async def assign_professional_resource(request:Request,client_id:str,body:ResourceAssignmentCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=await _p15_access(request,db,ctx)
    if denied:return denied
    version=(await db.execute(text("""SELECT v.id FROM external_resource_definitions d JOIN external_resource_versions v ON v.resource_id=d.id
      WHERE d.id=:id AND d.active=TRUE AND (d.tenant_id=:tenant OR (d.scope='SYSTEM' AND d.tenant_id IS NULL))
      ORDER BY v.version DESC LIMIT 1"""),{"id":body.resource_id,"tenant":ctx["tenant_id"]})).first()
    if not version:return error(request,404,"RESOURCE_NOT_FOUND","Resource not found")
    context_tables={"SESSION":"practice_consultations","PLAN":"external_profession_plans","TASK":"practice_tasks","HOMEWORK":"external_homework_assignments","FOLLOWUP":"practice_follow_ups"}
    if body.context_type in context_tables:
        if not body.context_id:return error(request,422,"RESOURCE_CONTEXT_REQUIRED","Context identifier is required")
        linked=(await db.execute(text(f"SELECT id FROM {context_tables[body.context_type]} WHERE id=:id AND tenant_id=:tenant AND client_id=:client"),
          {"id":body.context_id,"tenant":ctx["tenant_id"],"client":client_id})).first()
        if not linked:return error(request,404,"RESOURCE_CONTEXT_NOT_FOUND","Assignment context not found")
    aid,now=uuid4(),datetime.now(timezone.utc)
    await db.execute(text("""INSERT INTO external_resource_assignments
      (id,tenant_id,resource_id,resource_version_id,client_id,context_type,context_id,assigned_by,assigned_at,due_at,instructions,required,status)
      VALUES (:id,:tenant,:resource,:version,:client,:context,:context_id,:actor,:now,:due,:instructions,:required,'ASSIGNED')"""),{
      "id":aid,"tenant":ctx["tenant_id"],"resource":body.resource_id,"version":version[0],"client":client_id,
      "context":body.context_type,"context_id":body.context_id,"actor":ctx["user_id"],"now":now,"due":body.due_at,
      "instructions":body.instructions,"required":body.required})
    await _p15_audit(db,ctx,"RESOURCE_ASSIGNED",client_id=client_id,resource_id=body.resource_id,assignment_id=aid)
    return {"success":True,"data":{"id":aid,"status":"ASSIGNED"},"error":None,"request_id":request.state.correlation_id}


@app.get("/api/v1/practice-operations/clients/{client_id}/homework")
async def list_client_homework(request:Request,client_id:str,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=await _p15_access(request,db,ctx,"HOMEWORK")
    if denied:return denied
    rows=(await db.execute(text("""SELECT id,tenant_id,client_id,profession_code,title,description,homework_type,instructions,
      assigned_by,assigned_at,start_date,due_date,cadence,every_n_days,target_count,status,resource_assignment_id,
      goal_id,plan_id,session_id,completed_at,cancelled_at,updated_at FROM external_homework_assignments
      WHERE tenant_id=:tenant AND client_id=:client ORDER BY due_date NULLS LAST,assigned_at DESC"""),
      {"tenant":ctx["tenant_id"],"client":client_id})).mappings().all()
    return {"success":True,"data":{"items":[dict(r) for r in rows]},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/clients/{client_id}/homework",status_code=201)
async def create_client_homework(request:Request,client_id:str,body:HomeworkCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=await _p15_access(request,db,ctx,"HOMEWORK")
    if denied:return denied
    if (body.cadence=="CUSTOM_INTERVAL") != (body.every_n_days is not None):
        return error(request,422,"HOMEWORK_CADENCE_INVALID","Custom interval requires every_n_days")
    for value,table,code in ((body.goal_id,"practice_goals","GOAL"),(body.plan_id,"external_profession_plans","PLAN"),(body.session_id,"practice_consultations","SESSION"),(body.resource_assignment_id,"external_resource_assignments","RESOURCE_ASSIGNMENT")):
        if value is not None:
            linked=(await db.execute(text(f"SELECT id FROM {table} WHERE id=:id AND tenant_id=:tenant AND client_id=:client"),
              {"id":value,"tenant":ctx["tenant_id"],"client":client_id})).first()
            if not linked:return error(request,404,f"HOMEWORK_{code}_NOT_FOUND",f"{code.replace('_',' ').title()} not found")
    hid,now=uuid4(),datetime.now(timezone.utc)
    await db.execute(text("""INSERT INTO external_homework_assignments
      (id,tenant_id,client_id,profession_code,title,description,homework_type,instructions,assigned_by,assigned_at,start_date,due_date,cadence,every_n_days,target_count,status,resource_assignment_id,goal_id,plan_id,session_id,updated_at)
      VALUES (:id,:tenant,:client,:profession,:title,:description,:type,:instructions,:actor,:now,:start,:due,:cadence,:interval,:target,'NOT_STARTED',:resource,:goal,:plan,:session,:now)"""),{
      "id":hid,"tenant":ctx["tenant_id"],"client":client_id,"profession":body.profession_code,"title":body.title,
      "description":body.description,"type":body.homework_type,"instructions":body.instructions,"actor":ctx["user_id"],
      "now":now,"start":body.start_date,"due":body.due_date,"cadence":body.cadence,"interval":body.every_n_days,
      "target":body.target_count,"resource":body.resource_assignment_id,"goal":body.goal_id,"plan":body.plan_id,"session":body.session_id})
    await _p15_audit(db,ctx,"HOMEWORK_ASSIGNED",client_id=client_id,homework_id=hid)
    return {"success":True,"data":{"id":hid,"status":"NOT_STARTED"},"error":None,"request_id":request.state.correlation_id}


@app.patch("/api/v1/practice-operations/clients/{client_id}/homework/{homework_id}")
async def update_client_homework(request:Request,client_id:str,homework_id:UUID,body:HomeworkStatusUpdate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=await _p15_access(request,db,ctx,"HOMEWORK")
    if denied:return denied
    row=(await db.execute(text("SELECT status,due_date FROM external_homework_assignments WHERE id=:id AND tenant_id=:tenant AND client_id=:client"),
      {"id":homework_id,"tenant":ctx["tenant_id"],"client":client_id})).mappings().first()
    if not row:return error(request,404,"HOMEWORK_NOT_FOUND","Homework not found")
    if body.status=="MISSED" and (row["due_date"] is None or row["due_date"]>=date.today()):
        return error(request,409,"HOMEWORK_NOT_DUE","Homework cannot be marked missed before its due-date policy applies")
    try:status=homework_transition(row["status"],body.status)
    except ValueError as exc:return error(request,409,"HOMEWORK_TRANSITION_INVALID",str(exc))
    now=datetime.now(timezone.utc)
    await db.execute(text("""UPDATE external_homework_assignments SET status=:status,updated_at=:now,
      completed_at=CASE WHEN :status='COMPLETED' THEN :now ELSE completed_at END,
      cancelled_at=CASE WHEN :status='CANCELLED' THEN :now ELSE cancelled_at END
      WHERE id=:id AND tenant_id=:tenant AND client_id=:client"""),{
      "status":status,"now":now,"id":homework_id,"tenant":ctx["tenant_id"],"client":client_id})
    await _p15_audit(db,ctx,"HOMEWORK_"+status,client_id=client_id,homework_id=homework_id)
    return {"success":True,"data":{"id":homework_id,"status":status},"error":None,"request_id":request.state.correlation_id}


@app.get("/api/v1/practice-operations/clients/{client_id}/adherence")
async def get_client_adherence(request:Request,client_id:str,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=await _p15_access(request,db,ctx,"ADHERENCE")
    if denied:return denied
    rows=[dict(r) for r in (await db.execute(text("SELECT start_date,due_date,status,completed_at,updated_at FROM external_homework_assignments WHERE tenant_id=:tenant AND client_id=:client"),
      {"tenant":ctx["tenant_id"],"client":client_id})).mappings().all()]
    today=date.today(); summaries=[]
    for window,days in (("7_DAY",7),("30_DAY",30)):
        summary=adherence_summary(rows,today=today,days=days);summary.update({"window_type":window,"window_start":today-timedelta(days=days-1),"window_end":today})
        summaries.append(summary)
    package=(await db.execute(text("""SELECT start_date,end_date FROM external_client_packages
      WHERE tenant_id=:tenant AND client_id=:client AND status IN ('ACTIVE','PAUSED','COMPLETED','EXPIRED')
      ORDER BY CASE WHEN status='ACTIVE' THEN 0 ELSE 1 END,start_date DESC LIMIT 1"""),
      {"tenant":ctx["tenant_id"],"client":client_id})).mappings().first()
    programme_start=package["start_date"] if package else min((row["start_date"] for row in rows),default=today)
    programme_end=min(package["end_date"],today) if package else today
    programme_days=max((programme_end-programme_start).days+1,1)
    programme=adherence_summary(rows,today=programme_end,days=programme_days)
    programme.update({"window_type":"PROGRAMME","window_start":programme_start,"window_end":programme_end})
    summaries.append(programme)
    return {"success":True,"data":{"client_id":client_id,"windows":summaries},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/client-portal/{token}/resources/{assignment_id}/open")
async def portal_open_resource(request:Request,token:str,assignment_id:UUID,db:AsyncSession=Depends(get_db)):
    scope,denied=await _portal_scope(request,token,"READ_RESOURCES",db)
    if denied:return denied
    row=(await db.execute(text("""UPDATE external_resource_assignments SET status=CASE WHEN status='ASSIGNED' THEN 'OPENED' ELSE status END
      WHERE id=:id AND tenant_id=:tenant AND client_id=:client AND status<>'CANCELLED'
      RETURNING id,resource_id,content_reference""".replace(",content_reference","")),{
      "id":assignment_id,"tenant":scope["tenant_id"],"client":scope["client_id"]})).mappings().first()
    if not row:return error(request,404,"RESOURCE_ASSIGNMENT_NOT_FOUND","Resource assignment not found")
    now=datetime.now(timezone.utc)
    await db.execute(text("""INSERT INTO external_resource_view_events
      (id,tenant_id,client_id,assignment_id,event_type,actor_type,actor_id,evidence,created_at)
      VALUES (:id,:tenant,:client,:assignment,'OPENED','CLIENT',NULL,CAST(:evidence AS jsonb),:now)"""),{
      "id":uuid4(),"tenant":scope["tenant_id"],"client":scope["client_id"],"assignment":assignment_id,
      "evidence":json.dumps({"action":"explicit_open"}),"now":now})
    return {"success":True,"data":{"id":assignment_id,"status":"OPENED"},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/client-portal/{token}/homework/{homework_id}/check-in",status_code=201)
async def portal_homework_checkin(request:Request,token:str,homework_id:UUID,body:HomeworkCheckinCreate,db:AsyncSession=Depends(get_db)):
    scope,denied=await _portal_scope(request,token,"SUBMIT_HOMEWORK_CHECKIN",db)
    if denied:return denied
    row=(await db.execute(text("SELECT status FROM external_homework_assignments WHERE id=:id AND tenant_id=:tenant AND client_id=:client"),
      {"id":homework_id,"tenant":scope["tenant_id"],"client":scope["client_id"]})).mappings().first()
    if not row:return error(request,404,"HOMEWORK_NOT_FOUND","Homework not found")
    if row["status"] in {"MISSED","CANCELLED"}:return error(request,409,"HOMEWORK_CHECKIN_CLOSED","Homework is closed")
    cid,now=uuid4(),datetime.now(timezone.utc)
    await db.execute(text("""INSERT INTO external_homework_checkins
      (id,tenant_id,client_id,homework_id,actor_type,actor_id,done,completion_count,numeric_adherence,reflection_text,note,difficulty_rating,created_at)
      VALUES (:id,:tenant,:client,:homework,'CLIENT',NULL,:done,:count,:numeric,:reflection,:note,:difficulty,:now)"""),{
      "id":cid,"tenant":scope["tenant_id"],"client":scope["client_id"],"homework":homework_id,"done":body.done,
      "count":body.completion_count,"numeric":body.numeric_adherence,"reflection":body.reflection_text,"note":body.note,
      "difficulty":body.difficulty_rating,"now":now})
    status="COMPLETED" if body.done is True else "IN_PROGRESS"
    await db.execute(text("""UPDATE external_homework_assignments SET status=:status,updated_at=:now,
      completed_at=CASE WHEN :status='COMPLETED' THEN :now ELSE completed_at END
      WHERE id=:id AND tenant_id=:tenant AND client_id=:client AND status IN ('NOT_STARTED','IN_PROGRESS')"""),{
      "status":status,"now":now,"id":homework_id,"tenant":scope["tenant_id"],"client":scope["client_id"]})
    await _p15_audit(db,{"tenant_id":scope["tenant_id"],"user_id":None},"HOMEWORK_CHECKIN",client_id=scope["client_id"],homework_id=homework_id,actor_type="CLIENT")
    if status=="COMPLETED":await _p15_audit(db,{"tenant_id":scope["tenant_id"],"user_id":None},"HOMEWORK_COMPLETED",client_id=scope["client_id"],homework_id=homework_id,actor_type="CLIENT")
    return {"success":True,"data":{"id":cid,"homework_id":homework_id,"status":status},"error":None,"request_id":request.state.correlation_id}


@app.get("/api/v1/client-portal/{token}")
async def client_portal_home(request: Request, token: str, db: AsyncSession=Depends(get_db)):
    scope, denied = await _portal_scope(request, token, "READ", db)
    if denied:
        return denied
    params = {"tenant": scope["tenant_id"], "client": scope["client_id"]}
    tasks = [dict(row) for row in (await db.execute(text("""SELECT id,title,status,due_at,payload
      FROM practice_tasks WHERE tenant_id=:tenant AND client_id=:client AND status NOT IN ('CANCELLED')
      ORDER BY due_at NULLS LAST,created_at DESC LIMIT 100"""), params)).mappings().all()]
    appointments = [dict(row) for row in (await db.execute(text("""SELECT id,title,status,due_at AS scheduled_at,payload
      FROM practice_consultations WHERE tenant_id=:tenant AND client_id=:client
      AND status IN ('SCHEDULED','COMPLETED','CANCELLED','NO_SHOW')
      ORDER BY due_at DESC NULLS LAST LIMIT 50"""), params)).mappings().all()]
    goals = [dict(row) for row in (await db.execute(text("""SELECT id,title,status,due_at,payload
      FROM practice_goals WHERE tenant_id=:tenant AND client_id=:client
      AND status NOT IN ('CANCELLED') ORDER BY updated_at DESC LIMIT 50"""), params)).mappings().all()]
    plans = [dict(row) for row in (await db.execute(text("""SELECT p.id,p.plan_type,p.title,p.status,p.current_version,v.published_at
      FROM external_profession_plans p JOIN external_profession_plan_versions v
        ON v.plan_id=p.id AND v.tenant_id=p.tenant_id AND v.client_id=p.client_id
       AND v.version=p.current_version AND v.status='PUBLISHED'
      WHERE p.tenant_id=:tenant AND p.client_id=:client AND p.status='PUBLISHED'
      ORDER BY v.published_at DESC"""), params)).mappings().all()]
    assessments = [dict(row) for row in (await db.execute(text("""SELECT i.id,d.title,i.status,i.due_at,i.completed_at
      FROM external_assessment_instances i JOIN external_assessment_definitions d ON d.id=i.definition_id
      WHERE i.tenant_id=:tenant AND i.client_id=:client
      AND i.status IN ('ASSIGNED','IN_PROGRESS','COMPLETED','REVIEWED')
      ORDER BY i.assigned_at DESC"""), params)).mappings().all()]
    instructions = [dict(row) for row in (await db.execute(text("""SELECT n.id,n.title,s.title AS section_title,s.content,n.updated_at
      FROM external_session_notes n JOIN external_session_note_versions v
        ON v.note_id=n.id AND v.tenant_id=n.tenant_id AND v.client_id=n.client_id
       AND v.version=n.current_version AND v.status IN ('FINALISED','AMENDED')
      JOIN external_session_note_sections s ON s.note_version_id=v.id AND s.tenant_id=n.tenant_id
      WHERE n.tenant_id=:tenant AND n.client_id=:client AND s.visibility='CLIENT_INSTRUCTION'
      ORDER BY n.updated_at DESC"""), params)).mappings().all()]
    progress = [dict(row) for row in (await db.execute(text("""SELECT m.label,m.unit,m.direction,o.numeric_value,o.text_value,o.observed_at
      FROM external_progress_observations o JOIN external_progress_metric_definitions m
        ON m.id=o.metric_definition_id AND m.tenant_id=o.tenant_id
      WHERE o.tenant_id=:tenant AND o.client_id=:client ORDER BY o.observed_at DESC LIMIT 100"""), params)).mappings().all()]
    documents = [dict(row) for row in (await db.execute(text("""SELECT id,title,media_type,status,submitted_at,'PORTAL_SUBMISSION' AS source
      FROM external_client_portal_documents WHERE tenant_id=:tenant AND client_id=:client
      AND status NOT IN ('REMOVED','QUARANTINED') ORDER BY submitted_at DESC"""), params)).mappings().all()]
    documents.extend([dict(row) for row in (await db.execute(text("""SELECT d.id,d.title,d.category AS media_type,d.status,d.created_at AS submitted_at,'VAULT' AS source
      FROM external_documents d WHERE d.tenant_id=:tenant AND d.client_id=:client AND d.status='AVAILABLE'
      AND (d.visibility='CLIENT_VISIBLE' OR EXISTS(SELECT 1 FROM external_document_share_grants g
        WHERE g.document_id=d.id AND g.tenant_id=d.tenant_id AND g.client_id=:client AND g.active=TRUE
        AND (g.expires_at IS NULL OR g.expires_at>NOW()))) ORDER BY d.created_at DESC"""),params)).mappings().all()])
    resources = [dict(row) for row in (await db.execute(text("""SELECT a.id,a.status,a.assigned_at,a.due_at,a.instructions,a.required,
      d.title,d.description,d.resource_type,v.content_reference,v.media_type,v.duration_minutes
      FROM external_resource_assignments a JOIN external_resource_definitions d
        ON d.id=a.resource_id JOIN external_resource_versions v ON v.id=a.resource_version_id
      WHERE a.tenant_id=:tenant AND a.client_id=:client AND a.status<>'CANCELLED'
      ORDER BY a.assigned_at DESC"""), params)).mappings().all()] if "READ_RESOURCES" in set(scope["allowed_actions"]) else []
    homework = [dict(row) for row in (await db.execute(text("""SELECT id,title,description,homework_type,instructions,
      start_date,due_date,cadence,target_count,status,goal_id,plan_id,session_id,completed_at
      FROM external_homework_assignments WHERE tenant_id=:tenant AND client_id=:client AND status<>'CANCELLED'
      ORDER BY due_date NULLS LAST,assigned_at DESC"""), params)).mappings().all()] if "READ_HOMEWORK" in set(scope["allowed_actions"]) else []
    packages = [dict(row) for row in (await db.execute(text("""SELECT cp.id,p.name,cp.start_date,cp.end_date,
      cp.status,cp.sessions_total,COUNT(s.id)::int AS sessions_used,
      GREATEST(cp.sessions_total-COUNT(s.id)::int,0) AS sessions_remaining,
      MIN(c.due_at) FILTER (WHERE c.status='SCHEDULED' AND c.due_at >= NOW()) AS next_session
      FROM external_client_packages cp
      JOIN external_service_packages p ON p.id=cp.package_id AND p.tenant_id=cp.tenant_id
      LEFT JOIN external_client_package_sessions s ON s.client_package_id=cp.id AND s.tenant_id=cp.tenant_id
      LEFT JOIN practice_consultations c ON c.tenant_id=cp.tenant_id AND c.client_id=cp.client_id
      WHERE cp.tenant_id=:tenant AND cp.client_id=:client AND cp.status IN ('ACTIVE','PAUSED','COMPLETED','EXPIRED')
      GROUP BY cp.id,p.id ORDER BY cp.end_date DESC"""), params)).mappings().all()]
    invoices = [dict(row) for row in (await db.execute(text("""SELECT i.id,i.invoice_number,i.status,i.currency,
      i.issue_date,i.due_date,i.grand_total_minor,i.amount_paid_minor,i.balance_due_minor
      FROM external_invoices i WHERE i.tenant_id=:tenant AND i.client_id=:client
      AND i.status IN ('ISSUED','PART_PAID','PAID','OVERDUE') ORDER BY i.issue_date DESC,i.created_at DESC"""), params)).mappings().all()]
    receipts = [dict(row) for row in (await db.execute(text("""SELECT r.id,r.receipt_number,r.invoice_id,
      r.amount_minor,r.currency,r.remaining_balance_minor,r.created_at FROM external_receipts r
      WHERE r.tenant_id=:tenant AND r.client_id=:client ORDER BY r.created_at DESC"""), params)).mappings().all()]
    referral_consents = [dict(row) for row in (await db.execute(text("""SELECT r.id,r.receiving_profession_code,
      r.destination_name,r.reason,r.status,c.consent_version,c.allowed_data_scopes,c.expires_at
      FROM external_referrals r JOIN external_referral_consents c ON c.referral_id=r.id AND c.tenant_id=r.tenant_id
      WHERE r.tenant_id=:tenant AND r.client_id=:client AND r.status='CONSENT_PENDING' AND c.status='PENDING'
      ORDER BY r.created_at DESC"""), params)).mappings().all()]
    shared_reports = [dict(row) for row in (await db.execute(text("""SELECT r.id,r.title,r.report_type,r.period_start,r.period_end,
      r.current_version,v.source_snapshot,v.generated_at FROM external_progress_reports r
      JOIN external_progress_report_versions v ON v.report_id=r.id AND v.tenant_id=r.tenant_id AND v.version=r.current_version
      WHERE r.tenant_id=:tenant AND r.client_id=:client AND r.status='SHARED' AND r.revoked_at IS NULL ORDER BY r.shared_at DESC"""), params)).mappings().all()]
    forms = [dict(row) for row in (await db.execute(text("""SELECT a.id,a.status,a.due_at,a.assigned_at,d.title,d.form_type,v.version,COALESCE(r.answers,'{}'::jsonb) answers
      FROM external_form_assignments a JOIN external_form_definitions d ON d.id=a.form_definition_id AND d.tenant_id=a.tenant_id
      JOIN external_form_versions v ON v.id=a.form_version_id AND v.tenant_id=a.tenant_id
      LEFT JOIN external_form_responses r ON r.assignment_id=a.id AND r.tenant_id=a.tenant_id AND r.client_id=a.client_id
      WHERE a.tenant_id=:tenant AND a.client_id=:client AND a.status IN ('ASSIGNED','STARTED','COMPLETED') ORDER BY a.assigned_at DESC"""),params)).mappings().all()]
    consents = [dict(row) for row in (await db.execute(text("""SELECT r.id,r.status,r.scope,r.expires_at,r.created_at,t.title,t.consent_type,v.body,v.version
      FROM external_consent_records r JOIN external_consent_templates t ON t.id=r.template_id AND t.tenant_id=r.tenant_id
      JOIN external_consent_template_versions v ON v.id=r.template_version_id AND v.tenant_id=r.tenant_id
      WHERE r.tenant_id=:tenant AND r.client_id=:client AND r.status IN ('PENDING','ACCEPTED','DECLINED','REVOKED') ORDER BY r.created_at DESC"""),params)).mappings().all()]
    notifications = [dict(row) for row in (await db.execute(text("""SELECT p.id,p.purpose,p.subject,p.body,p.created_at,(n.read_at IS NOT NULL) is_read
      FROM external_communication_preparations p LEFT JOIN external_client_portal_notification_reads n ON n.preparation_id=p.id AND n.tenant_id=p.tenant_id AND n.client_id=p.client_id
      WHERE p.tenant_id=:tenant AND p.client_id=:client AND p.channel='CLIENT_PORTAL_NOTIFICATION' AND p.status='PREPARED' ORDER BY p.created_at DESC LIMIT 100"""),params)).mappings().all()]
    activity = [dict(row) for row in (await db.execute(text("""SELECT event_type,resource_type,resource_id,created_at FROM external_client_portal_audit_events
      WHERE tenant_id=:tenant AND client_id=:client AND actor_type='CLIENT' ORDER BY created_at DESC LIMIT 100"""),params)).mappings().all()]
    preconsultation = await _preconsultation_projection(db, scope["tenant_id"], scope["client_id"])
    post_row=(await db.execute(text("""SELECT id,tenant_id,client_id,consultation_id,session_note_id,profession_code,service_id,client_package_id,lifecycle_state,action_requirements,started_at,operationally_closed_at,created_by,created_at,updated_at
      FROM external_post_session_checklists WHERE tenant_id=:tenant AND client_id=:client ORDER BY started_at DESC LIMIT 1"""),params)).mappings().first()
    post_session=await _post_session_projection(db,scope["tenant_id"],post_row) if post_row else None
    feedback_requests=[dict(row) for row in (await db.execute(text("""SELECT id,feedback_type,status,expires_at,opened_at,created_at
      FROM external_client_feedback_requests WHERE tenant_id=:tenant AND client_id=:client
      AND status IN ('REQUESTED','OPENED') AND expires_at>NOW() ORDER BY created_at DESC"""),params)).mappings().all()]
    online_sessions=[dict(row) for row in (await db.execute(text("""SELECT s.id,s.appointment_id,s.provider_mode,s.status,a.starts_at,a.ends_at,t.name title
      FROM external_teleconsult_sessions s JOIN external_scheduled_appointments a ON a.id=s.appointment_id AND a.tenant_id=s.tenant_id
      JOIN external_appointment_types t ON t.id=a.appointment_type_id AND t.tenant_id=a.tenant_id
      WHERE s.tenant_id=:tenant AND s.client_id=:client AND s.status IN ('UPCOMING','WAITING_FOR_CONSULTANT','SESSION_ACTIVE')
      ORDER BY a.starts_at"""),params)).mappings().all()]
    secure_messages=[dict(row) for row in (await db.execute(text("""SELECT m.id,m.conversation_id,m.sender_type,m.message_type,m.body,m.reference_id,m.status,m.sent_at
      FROM external_secure_messages m WHERE m.tenant_id=:tenant AND m.client_id=:client ORDER BY m.sent_at DESC LIMIT 100"""),params)).mappings().all()]
    return {"success": True, "data": {
        "clientId": scope["client_id"], "tasks": tasks, "appointments": appointments,
        "goals": goals, "plans": plans, "assessments": assessments,
        "instructions": instructions, "progress": progress, "documents": documents,
        "resources": resources, "homework": homework, "notifications": notifications, "packages": packages, "invoices": invoices, "receipts": receipts,
        "referralConsents": referral_consents, "sharedReports": shared_reports, "forms": forms, "consents": consents, "activity": activity,
        "preConsultation": preconsultation,
        "postSession": post_session,
        "feedbackRequests": feedback_requests,
        "onlineSessions": online_sessions,
        "secureMessages": secure_messages,
        "documentsConfigured": bool(get_settings().document_storage_bucket),
    }, "error": None, "request_id": request.state.correlation_id}

@app.put("/api/v1/client-portal/{token}/forms/{assignment_id}/response")
async def portal_form_response(request:Request,token:str,assignment_id:UUID,body:FormResponseSave,db:AsyncSession=Depends(get_db)):
    scope,denied=await _portal_scope(request,token,"SUBMIT_FORM",db)
    if denied:return denied
    assignment=(await db.execute(text("SELECT id,status FROM external_form_assignments WHERE id=:id AND tenant_id=:tenant AND client_id=:client AND status IN ('ASSIGNED','STARTED')"),{"id":assignment_id,"tenant":scope["tenant_id"],"client":scope["client_id"]})).mappings().first()
    if not assignment:return error(request,404,"PORTAL_FORM_NOT_FOUND","Available form assignment not found")
    now=datetime.now(timezone.utc);status='COMPLETED' if body.submit else 'STARTED';await db.execute(text("""INSERT INTO external_form_responses(id,assignment_id,tenant_id,client_id,answers,status,response_version,submitted_at,updated_at)
      VALUES (:id,:assignment,:tenant,:client,CAST(:answers AS jsonb),:status,1,:submitted,:now) ON CONFLICT (assignment_id) DO UPDATE SET answers=EXCLUDED.answers,status=EXCLUDED.status,response_version=external_form_responses.response_version+1,submitted_at=EXCLUDED.submitted_at,updated_at=EXCLUDED.updated_at"""),{"id":uuid4(),"assignment":assignment_id,"tenant":scope["tenant_id"],"client":scope["client_id"],"answers":json.dumps(body.answers),"status":status,"submitted":now if body.submit else None,"now":now});await db.execute(text("UPDATE external_form_assignments SET status=:status,started_at=COALESCE(started_at,:now),completed_at=CASE WHEN :status='COMPLETED' THEN :now ELSE completed_at END WHERE id=:id AND tenant_id=:tenant AND client_id=:client"),{"status":status,"now":now,"id":assignment_id,"tenant":scope["tenant_id"],"client":scope["client_id"]});
    if body.submit:await _preconsultation_event_once(db,scope["tenant_id"],scope["client_id"],"INTAKE_COMPLETED",actor_type="CLIENT",metadata={"form_assignment_id":str(assignment_id)})
    else:await _preconsultation_event_once(db,scope["tenant_id"],scope["client_id"],"ONBOARDING_STARTED",actor_type="CLIENT")
    if body.submit:await _record_preconsultation_readiness(db,scope["tenant_id"],scope["client_id"])
    await db.commit();return {"success":True,"data":{"id":str(assignment_id),"status":status},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/client-portal/{token}/consents/{record_id}/decision")
async def portal_consent_decision(request:Request,token:str,record_id:UUID,body:ConsentDecision,db:AsyncSession=Depends(get_db)):
    scope,denied=await _portal_scope(request,token,"DECIDE_CONSENT",db)
    if denied:return denied
    now=datetime.now(timezone.utc);status='ACCEPTED' if body.decision=='ACCEPT' else 'DECLINED';result=await db.execute(text("UPDATE external_consent_records SET status=:status,signatory_name=:name,signatory_type=:type,signature_method=:method,signature_evidence=CAST(:evidence AS jsonb),accepted_at=CASE WHEN :status='ACCEPTED' THEN :now END,declined_at=CASE WHEN :status='DECLINED' THEN :now END,updated_at=:now WHERE id=:id AND tenant_id=:tenant AND client_id=:client AND status='PENDING'"),{"status":status,"name":body.signatory_name,"type":body.signatory_type,"method":body.signature_method,"evidence":json.dumps(body.signature_evidence),"now":now,"id":record_id,"tenant":scope["tenant_id"],"client":scope["client_id"]})
    if result.rowcount!=1:return error(request,404,"PORTAL_CONSENT_NOT_FOUND","Pending consent not found")
    if status=="ACCEPTED":await _preconsultation_event_once(db,scope["tenant_id"],scope["client_id"],"CONSENT_COMPLETED",actor_type="CLIENT",metadata={"consent_record_id":str(record_id)})
    if status=="ACCEPTED":await _record_preconsultation_readiness(db,scope["tenant_id"],scope["client_id"])
    await db.commit();return {"success":True,"data":{"id":str(record_id),"status":status,"classification":"ELECTRONIC_ACKNOWLEDGEMENT"},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/client-portal/{token}/vault-documents/{document_id}/download")
async def client_portal_download_vault_document(request:Request,token:str,document_id:UUID,db:AsyncSession=Depends(get_db)):
    scope,denied=await _portal_scope(request,token,"READ",db)
    if denied:return denied
    row=(await db.execute(text("""SELECT d.id,v.object_key,v.filename FROM external_documents d
      JOIN external_document_versions v ON v.document_id=d.id AND v.tenant_id=d.tenant_id AND v.version=d.current_version
      WHERE d.id=:id AND d.tenant_id=:tenant AND d.client_id=:client AND d.status='AVAILABLE'
      AND (d.visibility='CLIENT_VISIBLE' OR EXISTS(SELECT 1 FROM external_document_share_grants g
        WHERE g.document_id=d.id AND g.tenant_id=d.tenant_id AND g.client_id=:client AND g.active=TRUE
        AND (g.expires_at IS NULL OR g.expires_at>NOW())))"""),{"id":document_id,"tenant":scope["tenant_id"],"client":scope["client_id"]})).mappings().first()
    if not row:return error(request,404,"PORTAL_DOCUMENT_NOT_FOUND","Shared document not found")
    try:url=signed_download(row["object_key"],row["filename"])
    except StorageUnavailable as exc:return error(request,503,"DOCUMENT_STORAGE_NOT_CONFIGURED",str(exc),retryable=False)
    now=datetime.now(timezone.utc)
    await db.execute(text("INSERT INTO external_document_access_events(id,document_id,tenant_id,event_type,actor_id,created_at) VALUES (:id,:document,:tenant,'DOWNLOADED',:actor,:now)"),{"id":uuid4(),"document":document_id,"tenant":scope["tenant_id"],"actor":f'PORTAL:{scope["id"]}',"now":now})
    await db.commit();return {"success":True,"data":{"download_url":url,"expires_in":300},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/client-portal/{token}/tasks/{task_id}/complete")
async def client_portal_complete_task(request: Request, token: str, task_id: UUID,
                                      db: AsyncSession=Depends(get_db)):
    scope, denied = await _portal_scope(request, token, "COMPLETE_TASK", db)
    if denied:
        return denied
    now = datetime.now(timezone.utc)
    row = (await db.execute(text("""UPDATE practice_tasks SET status='COMPLETED',version=version+1,updated_at=:now
      WHERE id=:id AND tenant_id=:tenant AND client_id=:client
      AND status IN ('TODO','IN_PROGRESS','OVERDUE')
      RETURNING id,title,status,version"""), {
        "now": now, "id": task_id, "tenant": scope["tenant_id"], "client": scope["client_id"],
    })).mappings().first()
    if not row:
        return error(request, 404, "PORTAL_TASK_NOT_FOUND", "Task not found")
    await db.execute(text("""INSERT INTO external_client_portal_audit_events
      (id,tenant_id,client_id,access_grant_id,event_type,actor_type,resource_type,resource_id,created_at)
      VALUES (:id,:tenant,:client,:grant,'TASK_COMPLETED','CLIENT','TASK',:resource,:now)"""), {
        "id": uuid4(), "tenant": scope["tenant_id"], "client": scope["client_id"],
        "grant": scope["id"], "resource": str(task_id), "now": now,
    })
    return {"success": True, "data": dict(row), "error": None,
            "request_id": request.state.correlation_id}


@app.post("/api/v1/client-portal/{token}/documents", status_code=201)
async def client_portal_submit_document(request: Request, token: str, body: ClientPortalDocumentCreate,
                                        db: AsyncSession=Depends(get_db)):
    scope, denied = await _portal_scope(request, token, "UPLOAD_DOCUMENT", db)
    if denied:
        return denied
    document_id, now = uuid4(), datetime.now(timezone.utc)
    await db.execute(text("""INSERT INTO external_client_portal_documents
      (id,tenant_id,client_id,access_grant_id,title,document_reference,media_type,status,submitted_at)
      VALUES (:id,:tenant,:client,:grant,:title,:reference,:media_type,'SUBMITTED',:now)"""), {
        "id": document_id, "tenant": scope["tenant_id"], "client": scope["client_id"],
        "grant": scope["id"], "title": body.title, "reference": body.document_reference,
        "media_type": body.media_type, "now": now,
    })
    await _preconsultation_event_once(db,scope["tenant_id"],scope["client_id"],"DOCUMENT_UPLOADED",actor_type="CLIENT",metadata={"document_id":str(document_id)})
    await _record_preconsultation_readiness(db,scope["tenant_id"],scope["client_id"])
    return {"success": True, "data": {"id": str(document_id), "status": "SUBMITTED"},
            "error": None, "request_id": request.state.correlation_id}


# P16 is an additive consumer of the existing service_outbox_events stream.
async def _automation_audit(db,ctx,event_type,*,automation_id=None,version_id=None,execution_id=None,action_result_id=None,metadata=None):
    await db.execute(text("""INSERT INTO external_automation_audit_events
      (id,tenant_id,automation_id,automation_version_id,execution_id,action_result_id,event_type,actor_id,actor_type,metadata,created_at)
      VALUES (:id,:tenant,:automation,:version,:execution,:result,:event,:actor,:actor_type,CAST(:metadata AS jsonb),:now)"""),{
      "id":uuid4(),"tenant":ctx["tenant_id"],"automation":automation_id,"version":version_id,
      "execution":execution_id,"result":action_result_id,"event":event_type,"actor":ctx.get("user_id") or "SYSTEM",
      "actor_type":"SYSTEM" if ctx.get("system") else "PRACTITIONER","metadata":json.dumps(metadata or {}),"now":datetime.now(timezone.utc)})


async def _write_automation_version(db,ctx,automation_id,version,body,status="DRAFT"):
    now=datetime.now(timezone.utc);version_id=uuid4()
    await db.execute(text("""INSERT INTO external_automation_versions
      (id,definition_id,tenant_id,version,trigger_type,requires_confirmation,max_retries,cooldown_minutes,active_from,active_until,status,created_by,created_at)
      VALUES (:id,:definition,:tenant,:version,:trigger,:confirm,:retries,:cooldown,:active_from,:active_until,:status,:actor,:now)"""),{
      "id":version_id,"definition":automation_id,"tenant":ctx["tenant_id"],"version":version,"trigger":body.trigger_type,
      "confirm":body.requires_confirmation,"retries":body.max_retries,"cooldown":body.cooldown_minutes,
      "active_from":body.active_from,"active_until":body.active_until,"status":status,"actor":ctx["user_id"],"now":now})
    for index,condition in enumerate(body.conditions):
        evaluate_condition({},condition.field_key,condition.operator,condition.expected_value)
        await db.execute(text("""INSERT INTO external_automation_conditions
          (id,automation_version_id,tenant_id,condition_index,field_key,operator,expected_value,created_at)
          VALUES (:id,:version,:tenant,:index,:field,:operator,CAST(:expected AS jsonb),:now)"""),{
          "id":uuid4(),"version":version_id,"tenant":ctx["tenant_id"],"index":index,"field":condition.field_key,
          "operator":condition.operator,"expected":json.dumps(condition.expected_value),"now":now})
    for index,action in enumerate(body.actions):
        if action.action_type not in ACTION_TYPES: raise ValueError("UNSUPPORTED_AUTOMATION_ACTION")
        confirmation=action.confirmation_required or action.action_type in CONFIRMATION_ACTIONS
        await db.execute(text("""INSERT INTO external_automation_actions
          (id,automation_version_id,tenant_id,action_index,action_type,confirmation_required,configuration,created_at)
          VALUES (:id,:version,:tenant,:index,:type,:confirm,CAST(:configuration AS jsonb),:now)"""),{
          "id":uuid4(),"version":version_id,"tenant":ctx["tenant_id"],"index":index,"type":action.action_type,
          "confirm":confirmation,"configuration":json.dumps(action.configuration),"now":now})
    return version_id


@app.get("/api/v1/practice-operations/automations")
async def list_automations(request:Request,state:str|None=None,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"AUTOMATION_VIEW")
    if denied:return denied
    rows=(await db.execute(text("""SELECT d.id,d.name,d.description,d.profession_code,d.trigger_type,d.enabled,d.current_version,d.archived_at,d.updated_at,
      v.requires_confirmation,v.max_retries,v.cooldown_minutes,v.status
      FROM external_automation_definitions d JOIN external_automation_versions v ON v.definition_id=d.id AND v.version=d.current_version
      WHERE d.tenant_id=:tenant AND (CAST(:state AS text) IS NULL
        OR (CAST(:state AS text)='ACTIVE' AND d.enabled)
        OR (CAST(:state AS text)='DISABLED' AND NOT d.enabled)
        OR v.status=CAST(:state AS text))
      ORDER BY d.updated_at DESC"""),{"tenant":ctx["tenant_id"],"state":state})).mappings().all()
    return {"success":True,"data":{"items":[dict(row) for row in rows]},"error":None,"request_id":request.state.correlation_id}


@app.get("/api/v1/practice-operations/automations/templates")
async def automation_templates(request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"AUTOMATION_VIEW")
    if denied:return denied
    items=[
      {"name":"Post-session follow-up","trigger_type":"SESSION_COMPLETED","actions":["CREATE_FOLLOWUP"]},
      {"name":"No-show recovery","trigger_type":"NO_SHOW","actions":["CREATE_FOLLOWUP","PREPARE_MESSAGE"]},
      {"name":"Package renewal","trigger_type":"PACKAGE_ENDING_SOON","actions":["CREATE_RENEWAL_TASK"]},
      {"name":"Invoice overdue","trigger_type":"INVOICE_OVERDUE","actions":["CREATE_INVOICE_REMINDER","PREPARE_MESSAGE"]},
      {"name":"Homework missed","trigger_type":"HOMEWORK_OVERDUE","actions":["CREATE_HOMEWORK_REVIEW"]},
    ]
    return {"success":True,"data":{"items":items},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/automations",status_code=201)
async def create_automation(request:Request,body:AutomationCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"AUTOMATION_MANAGE")
    if denied:return denied
    now=datetime.now(timezone.utc);automation_id=uuid4()
    await db.execute(text("""INSERT INTO external_automation_definitions
      (id,tenant_id,name,description,profession_code,capability_required,trigger_type,enabled,current_version,created_by,created_at,updated_at)
      VALUES (:id,:tenant,:name,:description,:profession,:capability,:trigger,FALSE,1,:actor,:now,:now)"""),{
      "id":automation_id,"tenant":ctx["tenant_id"],"name":body.name,"description":body.description,"profession":body.profession_code,
      "capability":body.capability_required,"trigger":body.trigger_type,"actor":ctx["user_id"],"now":now})
    version_id=await _write_automation_version(db,ctx,automation_id,1,body)
    await _automation_audit(db,ctx,"AUTOMATION_CREATED",automation_id=automation_id,version_id=version_id)
    return {"success":True,"data":{"id":str(automation_id),"version":1,"status":"DRAFT"},"error":None,"request_id":request.state.correlation_id}


@app.put("/api/v1/practice-operations/automations/{automation_id}")
async def edit_automation(request:Request,automation_id:UUID,body:AutomationCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"AUTOMATION_MANAGE")
    if denied:return denied
    row=(await db.execute(text("SELECT current_version FROM external_automation_definitions WHERE id=:id AND tenant_id=:tenant AND archived_at IS NULL"),{"id":automation_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not row:return error(request,404,"AUTOMATION_NOT_FOUND","Automation not found")
    version=row["current_version"]+1;version_id=await _write_automation_version(db,ctx,automation_id,version,body)
    await db.execute(text("""UPDATE external_automation_definitions SET name=:name,description=:description,profession_code=:profession,
      capability_required=:capability,trigger_type=:trigger,current_version=:version,enabled=FALSE,updated_at=:now WHERE id=:id AND tenant_id=:tenant"""),{
      "name":body.name,"description":body.description,"profession":body.profession_code,"capability":body.capability_required,
      "trigger":body.trigger_type,"version":version,"now":datetime.now(timezone.utc),"id":automation_id,"tenant":ctx["tenant_id"]})
    await _automation_audit(db,ctx,"AUTOMATION_UPDATED",automation_id=automation_id,version_id=version_id)
    return {"success":True,"data":{"id":str(automation_id),"version":version,"status":"DRAFT"},"error":None,"request_id":request.state.correlation_id}


@app.patch("/api/v1/practice-operations/automations/{automation_id}/state")
async def set_automation_state(request:Request,automation_id:UUID,body:AutomationStateUpdate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"AUTOMATION_MANAGE")
    if denied:return denied
    row=(await db.execute(text("""UPDATE external_automation_definitions SET enabled=:enabled,updated_at=:now
      WHERE id=:id AND tenant_id=:tenant AND archived_at IS NULL RETURNING current_version"""),{
      "enabled":body.enabled,"now":datetime.now(timezone.utc),"id":automation_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not row:return error(request,404,"AUTOMATION_NOT_FOUND","Automation not found")
    await db.execute(text("UPDATE external_automation_versions SET status=:status WHERE definition_id=:id AND tenant_id=:tenant AND version=:version"),{
      "status":"ENABLED" if body.enabled else "DISABLED","id":automation_id,"tenant":ctx["tenant_id"],"version":row["current_version"]})
    await _automation_audit(db,ctx,"AUTOMATION_ENABLED" if body.enabled else "AUTOMATION_DISABLED",automation_id=automation_id)
    return {"success":True,"data":{"id":str(automation_id),"enabled":body.enabled},"error":None,"request_id":request.state.correlation_id}


async def _automation_version_graph(db,tenant,automation_id):
    version=(await db.execute(text("""SELECT v.* FROM external_automation_versions v JOIN external_automation_definitions d ON d.id=v.definition_id
      WHERE d.id=:id AND d.tenant_id=:tenant AND v.version=d.current_version"""),{"id":automation_id,"tenant":tenant})).mappings().first()
    if not version:return None,[],[]
    conditions=(await db.execute(text("SELECT id,condition_index,field_key,operator,expected_value FROM external_automation_conditions WHERE automation_version_id=:id AND tenant_id=:tenant ORDER BY condition_index"),{"id":version["id"],"tenant":tenant})).mappings().all()
    actions=(await db.execute(text("SELECT id,automation_version_id,action_index,action_type,confirmation_required,configuration FROM external_automation_actions WHERE automation_version_id=:id AND tenant_id=:tenant ORDER BY action_index"),{"id":version["id"],"tenant":tenant})).mappings().all()
    return version,conditions,actions


@app.post("/api/v1/practice-operations/automations/{automation_id}/dry-run")
async def dry_run_automation(request:Request,automation_id:UUID,body:AutomationDryRun,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"AUTOMATION_MANAGE")
    if denied:return denied
    version,conditions,actions=await _automation_version_graph(db,ctx["tenant_id"],automation_id)
    if not version:return error(request,404,"AUTOMATION_NOT_FOUND","Automation not found")
    results=[{"field":c["field_key"],"operator":c["operator"],"passed":evaluate_condition(body.sample_payload,c["field_key"],c["operator"],c["expected_value"])} for c in conditions]
    matched=body.event_type==version["trigger_type"] and all(item["passed"] for item in results)
    return {"success":True,"data":{"trigger_matched":body.event_type==version["trigger_type"],"conditions":results,"matched":matched,
      "actions":[{"action_type":a["action_type"],"would_execute":matched,"confirmation_required":a["confirmation_required"]} for a in actions],"writes_performed":0},"error":None,"request_id":request.state.correlation_id}


async def _execute_safe_automation_action(db,ctx,event,action,idem):
    action_type=action["action_type"];client_id=str((event["payload"] or {}).get("client_id") or "")
    if not client_id:return None,"CLIENT_CONTEXT_REQUIRED"
    table="practice_follow_ups" if action_type=="CREATE_FOLLOWUP" else "practice_tasks"
    target_id=uuid4();now=datetime.now(timezone.utc);due=now+timedelta(days=int((action["configuration"] or {}).get("delay_days",0)))
    title=(action["configuration"] or {}).get("title") or action_type.replace("_"," ").title()
    await db.execute(text(f"""INSERT INTO {table}
      (id,tenant_id,client_id,type,title,status,due_at,payload,version,created_by,idempotency_key,created_at,updated_at)
      VALUES (:id,:tenant,:client,:type,:title,'TODO',:due,CAST(:payload AS jsonb),1,'AUTOMATION',:idem,:now,:now)
      ON CONFLICT (tenant_id,idempotency_key) DO NOTHING"""),{"id":target_id,"tenant":ctx["tenant_id"],"client":client_id,
      "type":action_type,"title":title,"due":due,"payload":json.dumps({"source_automation_id":str(action["automation_version_id"]),"originating_event_id":str(event["id"])}),"idem":idem,"now":now})
    return str(target_id),None


@app.post("/api/v1/practice-operations/automations/events/{event_id}/execute")
async def execute_automations(request:Request,event_id:UUID,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"AUTOMATION_MANAGE")
    if denied:return denied
    event=(await db.execute(text("SELECT id,event_type,aggregate_type,aggregate_id,payload,created_at FROM service_outbox_events WHERE id=:id AND tenant_id=:tenant"),{"id":event_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not event:return error(request,404,"OUTBOX_EVENT_NOT_FOUND","Outbox event not found")
    payload=dict(event["payload"] or {});depth=int(payload.get("execution_depth",0));assert_chain_depth(depth)
    definitions=(await db.execute(text("""SELECT id,current_version FROM external_automation_definitions WHERE tenant_id=:tenant AND enabled=TRUE
      AND archived_at IS NULL AND trigger_type=:trigger"""),{"tenant":ctx["tenant_id"],"trigger":event["event_type"]})).mappings().all()
    execution_ids=[]
    for definition in definitions:
        version,conditions,actions=await _automation_version_graph(db,ctx["tenant_id"],definition["id"])
        now=datetime.now(timezone.utc)
        if (version["active_from"] and version["active_from"]>now) or (version["active_until"] and version["active_until"]<now):continue
        if version["cooldown_minutes"] and payload.get("client_id"):
            recent=(await db.execute(text("""SELECT 1 FROM external_automation_executions
              WHERE tenant_id=:tenant AND automation_version_id=:version AND client_id=:client AND created_at>=:cutoff LIMIT 1"""),{
              "tenant":ctx["tenant_id"],"version":version["id"],"client":str(payload["client_id"]),
              "cutoff":now-timedelta(minutes=version["cooldown_minutes"])})).scalar_one_or_none()
            if recent:continue
        condition_results=[{"field":c["field_key"],"passed":evaluate_condition(payload,c["field_key"],c["operator"],c["expected_value"])} for c in conditions]
        if not all(item["passed"] for item in condition_results):continue
        execution_id=uuid4()
        inserted=(await db.execute(text("""INSERT INTO external_automation_executions
          (id,tenant_id,automation_id,automation_version_id,event_id,client_id,status,attempt_count,execution_depth,condition_results,started_at,created_at)
          VALUES (:id,:tenant,:automation,:version,:event,:client,'RUNNING',1,:depth,CAST(:conditions AS jsonb),:now,:now)
          ON CONFLICT (tenant_id,automation_version_id,event_id) DO NOTHING RETURNING id"""),{
          "id":execution_id,"tenant":ctx["tenant_id"],"automation":definition["id"],"version":version["id"],"event":event_id,
          "client":payload.get("client_id"),"depth":depth,"conditions":json.dumps(condition_results),"now":now})).scalar_one_or_none()
        if not inserted:continue
        pending=False
        for action in actions:
            idem=idempotency_key(ctx["tenant_id"],str(version["id"]),str(event_id),action["action_index"]);result_id=uuid4()
            await db.execute(text("""INSERT INTO external_automation_idempotency_keys
              (tenant_id,idempotency_key,automation_version_id,event_id,action_index,action_result_id,created_at)
              VALUES (:tenant,:key,:version,:event,:index,:result,:now) ON CONFLICT DO NOTHING"""),{
              "tenant":ctx["tenant_id"],"key":idem,"version":version["id"],"event":event_id,"index":action["action_index"],"result":result_id,"now":now})
            confirmation=version["requires_confirmation"] or action["confirmation_required"] or action["action_type"] in CONFIRMATION_ACTIONS
            status="PENDING_CONFIRMATION" if confirmation else "SUCCEEDED";target_id=None;error_code=None
            if confirmation:pending=True
            else:target_id,error_code=await _execute_safe_automation_action(db,ctx,event,action,idem);status="FAILED" if error_code else "SUCCEEDED"
            await db.execute(text("""INSERT INTO external_automation_action_results
              (id,tenant_id,execution_id,action_id,action_index,action_type,status,target_type,target_id,result_summary,error_code,attempt_count,created_at,updated_at)
              VALUES (:id,:tenant,:execution,:action,:index,:type,:status,:target_type,:target,:summary,:error,1,:now,:now)"""),{
              "id":result_id,"tenant":ctx["tenant_id"],"execution":execution_id,"action":action["id"],"index":action["action_index"],
              "type":action["action_type"],"status":status,"target_type":"FOLLOWUP" if action["action_type"]=="CREATE_FOLLOWUP" else "TASK",
              "target":target_id,"summary":"Waiting for practitioner confirmation" if confirmation else "Operational action completed",
              "error":error_code,"now":now})
            if not confirmation:
                await _automation_audit(db,{**ctx,"system":True},"ACTION_FAILED" if error_code else "ACTION_SUCCEEDED",
                  automation_id=definition["id"],version_id=version["id"],execution_id=execution_id,action_result_id=result_id,
                  metadata={"action_type":action["action_type"],"target_id":target_id})
                if target_id and payload.get("client_id"):
                    await db.execute(text("""INSERT INTO practice_timeline_events
                      (id,tenant_id,client_id,event_type,source_type,source_id,summary,metadata,occurred_at)
                      VALUES (:id,:tenant,:client,'AUTOMATION_ACTION_CREATED','AUTOMATION',:source,:summary,CAST(:metadata AS jsonb),:now)
                      ON CONFLICT (tenant_id,event_type,source_type,source_id) DO NOTHING"""),{
                      "id":uuid4(),"tenant":ctx["tenant_id"],"client":str(payload["client_id"]),"source":target_id,
                      "summary":f"Created by automation: {action['action_type'].replace('_',' ').title()}",
                      "metadata":json.dumps({"automation_id":str(definition["id"]),"execution_id":str(execution_id)}),"now":now})
        final="PENDING_CONFIRMATION" if pending else "SUCCEEDED"
        await db.execute(text("UPDATE external_automation_executions SET status=:status,completed_at=CASE WHEN :status='SUCCEEDED' THEN :now ELSE NULL END WHERE id=:id AND tenant_id=:tenant"),{"status":final,"now":now,"id":execution_id,"tenant":ctx["tenant_id"]})
        await _automation_audit(db,{**ctx,"system":True},"AUTOMATION_EXECUTED",automation_id=definition["id"],version_id=version["id"],execution_id=execution_id)
        execution_ids.append(str(execution_id))
    await db.execute(text("""INSERT INTO service_outbox_deliveries(consumer_name,event_id,tenant_id,delivered_at)
      VALUES ('P16_AUTOMATION_ENGINE',:event,:tenant,:now) ON CONFLICT DO NOTHING"""),{"event":event_id,"tenant":ctx["tenant_id"],"now":datetime.now(timezone.utc)})
    return {"success":True,"data":{"event_id":str(event_id),"executions":execution_ids},"error":None,"request_id":request.state.correlation_id}


@app.get("/api/v1/practice-operations/automations/executions/history")
async def automation_history(request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"AUTOMATION_VIEW")
    if denied:return denied
    rows=(await db.execute(text("""SELECT e.id,d.name AS automation,e.client_id,d.trigger_type,e.status,e.attempt_count,e.condition_results,e.error_code,e.error_summary,e.created_at
      FROM external_automation_executions e JOIN external_automation_definitions d ON d.id=e.automation_id
      WHERE e.tenant_id=:tenant ORDER BY e.created_at DESC LIMIT 100"""),{"tenant":ctx["tenant_id"]})).mappings().all()
    return {"success":True,"data":{"items":[dict(row) for row in rows]},"error":None,"request_id":request.state.correlation_id}


@app.get("/api/v1/practice-operations/automations/actions/pending")
async def pending_automation_actions(request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"AUTOMATION_VIEW")
    if denied:return denied
    rows=(await db.execute(text("""SELECT r.id,r.action_type,r.result_summary,r.created_at,e.client_id,d.name AS automation
      FROM external_automation_action_results r JOIN external_automation_executions e ON e.id=r.execution_id
      JOIN external_automation_definitions d ON d.id=e.automation_id
      WHERE r.tenant_id=:tenant AND r.status='PENDING_CONFIRMATION' ORDER BY r.created_at"""),{"tenant":ctx["tenant_id"]})).mappings().all()
    return {"success":True,"data":{"items":[dict(row) for row in rows]},"error":None,"request_id":request.state.correlation_id}


async def _execute_confirmed_automation_action(db,ctx,row,configuration):
    now=datetime.now(timezone.utc);action_type=row["action_type"];client_id=str((row["payload"] or {}).get("client_id") or "")
    if not client_id:return None,"CLIENT_CONTEXT_REQUIRED"
    config={**dict(row["configuration"] or {}),**dict(configuration or {})}
    if action_type=="PREPARE_MESSAGE":
        target_id=uuid4()
        await db.execute(text("""INSERT INTO practice_communication_activity
          (id,tenant_id,client_id,channel,event_type,purpose,metadata,created_by,created_at)
          VALUES (:id,:tenant,:client,'DRAFT','MESSAGE_PREPARED',:purpose,CAST(:metadata AS jsonb),:actor,:now)"""),{
          "id":target_id,"tenant":ctx["tenant_id"],"client":client_id,"purpose":str(config.get("purpose") or "Automation prepared message")[:120],
          "metadata":json.dumps({"status":"DRAFT","message":str(config.get("message") or "")[:2000],"execution_id":str(row["execution_id"])}),"actor":ctx["user_id"],"now":now})
        return str(target_id),None
    if action_type=="CREATE_CLIENT_CHECKIN":
        target_id=uuid4();idem=idempotency_key(ctx["tenant_id"],str(row["automation_version_id"]),str(row["event_id"]),row["action_index"])
        await db.execute(text("""INSERT INTO practice_checkins
          (id,tenant_id,client_id,type,title,status,due_at,payload,version,created_by,idempotency_key,created_at,updated_at)
          VALUES (:id,:tenant,:client,'AUTOMATION_CHECKIN',:title,'TODO',:due,CAST(:payload AS jsonb),1,:actor,:idem,:now,:now)
          ON CONFLICT (tenant_id,idempotency_key) DO NOTHING"""),{
          "id":target_id,"tenant":ctx["tenant_id"],"client":client_id,"title":str(config.get("title") or "Client check-in")[:240],
          "due":now+timedelta(days=int(config.get("delay_days",0))),"payload":json.dumps({"execution_id":str(row["execution_id"])}),
          "actor":ctx["user_id"],"idem":idem,"now":now})
        return str(target_id),None
    if action_type=="ASSIGN_ASSESSMENT":
        definition_id=config.get("definition_id")
        if not definition_id:return None,"ASSESSMENT_DEFINITION_REQUIRED"
        definition=(await db.execute(text("""SELECT d.id,d.profession_code,v.id AS version_id FROM external_assessment_definitions d
          JOIN external_assessment_versions v ON v.definition_id=d.id AND v.status='ACTIVE'
          WHERE d.id=CAST(:id AS uuid) AND d.active=TRUE AND (d.tenant_id IS NULL OR d.tenant_id=:tenant)
          ORDER BY v.version DESC LIMIT 1"""),{"id":str(definition_id),"tenant":ctx["tenant_id"]})).mappings().first()
        if not definition:return None,"ASSESSMENT_DEFINITION_NOT_FOUND"
        target_id=uuid4()
        await db.execute(text("""INSERT INTO external_assessment_instances
          (id,tenant_id,client_id,definition_id,version_id,profession_code,status,assigned_by,assigned_at,due_at,updated_at)
          VALUES (:id,:tenant,:client,:definition,:version,:profession,'ASSIGNED',:actor,:now,:due,:now)"""),{
          "id":target_id,"tenant":ctx["tenant_id"],"client":client_id,"definition":definition["id"],"version":definition["version_id"],
          "profession":definition["profession_code"],"actor":ctx["user_id"],"now":now,"due":None})
        return str(target_id),None
    if action_type=="CREATE_RESOURCE_ASSIGNMENT":
        resource_id=config.get("resource_id")
        if not resource_id:return None,"RESOURCE_ID_REQUIRED"
        resource=(await db.execute(text("""SELECT d.id,v.id AS version_id FROM external_resource_definitions d
          JOIN external_resource_versions v ON v.resource_id=d.id AND v.version=d.current_version
          WHERE d.id=CAST(:id AS uuid) AND d.active=TRUE AND (d.scope='SYSTEM' OR d.tenant_id=:tenant)"""),{"id":str(resource_id),"tenant":ctx["tenant_id"]})).mappings().first()
        if not resource:return None,"RESOURCE_NOT_FOUND"
        target_id=uuid4()
        await db.execute(text("""INSERT INTO external_resource_assignments
          (id,tenant_id,resource_id,resource_version_id,client_id,context_type,assigned_by,assigned_at,instructions,required,status)
          VALUES (:id,:tenant,:resource,:version,:client,'CLIENT',:actor,:now,:instructions,:required,'ASSIGNED')"""),{
          "id":target_id,"tenant":ctx["tenant_id"],"resource":resource["id"],"version":resource["version_id"],"client":client_id,
          "actor":ctx["user_id"],"now":now,"instructions":config.get("instructions"),"required":bool(config.get("required",False))})
        return str(target_id),None
    return None,"UNSUPPORTED_CONFIRMED_ACTION"


@app.patch("/api/v1/practice-operations/automations/actions/{result_id}")
async def decide_automation_action(request:Request,result_id:UUID,body:AutomationActionDecision,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"AUTOMATION_MANAGE")
    if denied:return denied
    status="RUNNING" if body.decision=="APPROVE" else "CANCELLED";now=datetime.now(timezone.utc)
    row=(await db.execute(text("""UPDATE external_automation_action_results SET status=:status,
      approved_by=CASE WHEN :decision='APPROVE' THEN :actor ELSE approved_by END,approved_at=CASE WHEN :decision='APPROVE' THEN :now ELSE approved_at END,
      dismissed_by=CASE WHEN :decision='DISMISS' THEN :actor ELSE dismissed_by END,dismissed_at=CASE WHEN :decision='DISMISS' THEN :now ELSE dismissed_at END,updated_at=:now
      WHERE id=:id AND tenant_id=:tenant AND status='PENDING_CONFIRMATION' RETURNING execution_id,action_id,action_index,action_type"""),{
      "status":status,"decision":body.decision,"actor":ctx["user_id"],"now":now,"id":result_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not row:return error(request,404,"AUTOMATION_ACTION_NOT_FOUND","Pending automation action not found")
    error_code=None;target_id=None
    if body.decision=="APPROVE":
        graph=(await db.execute(text("""SELECT r.execution_id,r.action_index,r.action_type,a.configuration,e.automation_version_id,e.event_id,o.payload
          FROM external_automation_action_results r JOIN external_automation_actions a ON a.id=r.action_id
          JOIN external_automation_executions e ON e.id=r.execution_id JOIN service_outbox_events o ON o.id=e.event_id
          WHERE r.id=:id AND r.tenant_id=:tenant AND e.tenant_id=:tenant AND o.tenant_id=:tenant"""),{"id":result_id,"tenant":ctx["tenant_id"]})).mappings().first()
        target_id,error_code=await _execute_confirmed_automation_action(db,ctx,graph,body.configuration)
        status="FAILED" if error_code else "SUCCEEDED"
        await db.execute(text("""UPDATE external_automation_action_results SET status=:status,target_id=:target,
          target_type=:target_type,error_code=:error,result_summary=:summary,updated_at=:now WHERE id=:id AND tenant_id=:tenant"""),{
          "status":status,"target":target_id,"target_type":row["action_type"],"error":error_code,
          "summary":"Confirmed action completed" if not error_code else "Confirmed action failed validation","now":now,"id":result_id,"tenant":ctx["tenant_id"]})
    await _automation_audit(db,ctx,"ACTION_APPROVED" if body.decision=="APPROVE" else "ACTION_DISMISSED",execution_id=row["execution_id"],action_result_id=result_id)
    return {"success":True,"data":{"id":str(result_id),"status":status,"target_id":target_id,"error_code":error_code},"error":None,"request_id":request.state.correlation_id}


# P17 External Practice RBAC. Auth identities and tenant headers remain authoritative;
# this layer only adds External practice roles, permissions, assignments, and audit.
async def _team_principal(db, ctx):
    row=(await db.execute(text("""SELECT id,role,status,profession_code,permission_grants,permission_restrictions,
      practice_wide_client_access FROM external_practice_role_profiles
      WHERE tenant_id=:tenant AND user_id=:user"""),{"tenant":ctx["tenant_id"],"user":ctx["user_id"]})).mappings().first()
    config=await configuration(db,ctx)
    if not row:
        permissions=set(resolve_permissions("PRACTICE_OWNER",capabilities=config["capabilities"]))
        permissions.update({p for p in ("PRIVATE_NOTE_VIEW","PRIVATE_NOTE_CREATE") if "PRIVATE_NOTES" in config["capabilities"]})
        return {"role":"PRACTICE_OWNER","status":"ACTIVE","profession_code":config["profession"],
          "permissions":permissions,"practice_wide_client_access":True,"legacy_solo":True}
    permissions=resolve_permissions(row["role"],row["permission_grants"] or [],row["permission_restrictions"] or [],config["capabilities"])
    return {**dict(row),"permissions":set(permissions),"legacy_solo":False}


async def _team_guard(request,db,ctx,permission,client_id=None):
    denied=external_only(request,ctx)
    if denied:return denied,None
    principal=await _team_principal(db,ctx)
    if principal["status"]!="ACTIVE":return error(request,403,"TEAM_MEMBERSHIP_INACTIVE","Practice membership is not active"),principal
    if permission not in principal["permissions"]:return error(request,403,"PERMISSION_DENIED",f"{permission.replace('_',' ').title()} permission is required"),principal
    if client_id and principal["role"]=="PRACTITIONER" and not principal["practice_wide_client_access"] and not principal["legacy_solo"]:
        assigned=(await db.execute(text("""SELECT 1 FROM external_client_team_assignments WHERE tenant_id=:tenant
          AND client_id=:client AND user_id=:user AND ended_at IS NULL LIMIT 1"""),{"tenant":ctx["tenant_id"],"client":client_id,"user":ctx["user_id"]})).scalar_one_or_none()
        if not assigned:return error(request,403,"CLIENT_ASSIGNMENT_REQUIRED","This client is not assigned to the practitioner"),principal
    return None,principal


async def _team_audit(db,ctx,event_type,target_user_id=None,client_id=None,old_value=None,new_value=None,metadata=None):
    await db.execute(text("""INSERT INTO external_team_audit_events
      (id,tenant_id,event_type,actor_id,target_user_id,client_id,old_value,new_value,metadata,created_at)
      VALUES (:id,:tenant,:event,:actor,:target,:client,CAST(:old AS jsonb),CAST(:new AS jsonb),CAST(:metadata AS jsonb),:now)"""),{
      "id":uuid4(),"tenant":ctx["tenant_id"],"event":event_type,"actor":ctx["user_id"],"target":target_user_id,
      "client":client_id,"old":json.dumps(old_value) if old_value is not None else None,
      "new":json.dumps(new_value) if new_value is not None else None,"metadata":json.dumps(metadata or {}),"now":datetime.now(timezone.utc)})


async def _authenticated_user_email(ctx):
    if ctx.get("email"):return ctx["email"]
    url=f"{get_settings().auth_service_url.rstrip('/')}/api/v1/auth/me"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response=await client.get(url,headers={"X-User-Id":ctx["user_id"]})
        response.raise_for_status();payload=response.json();return str((payload.get("data") or {}).get("email") or "").lower()
    except (httpx.HTTPError,ValueError,TypeError):
        return ""


@app.get("/api/v1/practice-operations/team/access")
async def team_access(request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    principal=await _team_principal(db,ctx)
    return {"success":True,"data":{"role":principal["role"],"status":principal["status"],
      "profession_code":principal.get("profession_code"),"permissions":sorted(principal["permissions"]),
      "legacy_solo":principal["legacy_solo"]},"error":None,"request_id":request.state.correlation_id}


@app.get("/api/v1/practice-operations/team/roles")
async def team_roles(request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"TEAM_VIEW")
    if denied:return denied
    return {"success":True,"data":{"roles":[{"role":role,"permissions":sorted(perms),
      "private_notes_default":False} for role,perms in ROLE_PERMISSIONS.items()],"permission_registry":sorted(PERMISSIONS)},
      "error":None,"request_id":request.state.correlation_id}


@app.get("/api/v1/practice-operations/team")
async def list_team(request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,principal=await _team_guard(request,db,ctx,"TEAM_VIEW")
    if denied:return denied
    rows=(await db.execute(text("""SELECT p.id,p.user_id,p.display_name,p.role,p.status,p.profession_code,p.specialisation,
      p.location_code,p.practice_wide_client_access,p.active_from,p.active_until,
      COUNT(a.id) FILTER (WHERE a.ended_at IS NULL) AS assigned_clients_count
      FROM external_practice_role_profiles p LEFT JOIN external_client_team_assignments a
      ON a.tenant_id=p.tenant_id AND a.user_id=p.user_id WHERE p.tenant_id=:tenant
      GROUP BY p.id ORDER BY p.created_at"""),{"tenant":ctx["tenant_id"]})).mappings().all()
    items=[dict(row) for row in rows]
    if principal["legacy_solo"]:
        items.insert(0,{"id":None,"user_id":ctx["user_id"],"display_name":"Practice owner","role":"PRACTICE_OWNER",
          "status":"ACTIVE","profession_code":principal.get("profession_code"),"specialisation":None,"location_code":None,
          "practice_wide_client_access":True,"active_from":None,"active_until":None,"assigned_clients_count":0,"legacy_solo":True})
    return {"success":True,"data":{"items":items,"permissions":sorted(principal["permissions"])},"error":None,"request_id":request.state.correlation_id}


@app.get("/api/v1/practice-operations/team/invitations")
async def list_team_invitations(request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"TEAM_VIEW")
    if denied:return denied
    rows=(await db.execute(text("""SELECT id,email,display_name,role,profession_code,specialisation,location_code,status,
      invited_by,expires_at,accepted_at,created_at FROM external_team_invitations WHERE tenant_id=:tenant ORDER BY created_at DESC"""),{"tenant":ctx["tenant_id"]})).mappings().all()
    return {"success":True,"data":{"items":[dict(row) for row in rows]},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/team/invitations",status_code=201)
async def create_team_invitation(request:Request,body:TeamInvitationCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,principal=await _team_guard(request,db,ctx,"TEAM_MANAGE")
    if denied:return denied
    if body.role=="PRACTITIONER" and not body.profession_code:return error(request,409,"PRACTITIONER_PROFESSION_REQUIRED","Practitioners require a profession profile")
    if body.role=="PRACTICE_ADMIN" and principal["role"]!="PRACTICE_OWNER":return error(request,403,"ROLE_ESCALATION_DENIED","Only a practice owner can invite an administrator")
    invalid=(set(body.permission_grants)|set(body.permission_restrictions))-PERMISSIONS
    if invalid:return error(request,409,"INVALID_PERMISSION","One or more permission codes are invalid")
    token=secrets.token_urlsafe(32);now=datetime.now(timezone.utc);invitation_id=uuid4()
    await db.execute(text("""INSERT INTO external_team_invitations
      (id,tenant_id,email,display_name,role,profession_code,specialisation,location_code,permission_grants,permission_restrictions,
       token_hash,status,invited_by,expires_at,created_at,updated_at)
      VALUES (:id,:tenant,:email,:name,:role,:profession,:specialisation,:location,CAST(:grants AS jsonb),CAST(:restrictions AS jsonb),
       :token_hash,'INVITED',:actor,:expires,:now,:now)"""),{"id":invitation_id,"tenant":ctx["tenant_id"],"email":body.email.lower(),
      "name":body.name,"role":body.role,"profession":body.profession_code,"specialisation":body.specialisation,"location":body.location_code,
      "grants":json.dumps(body.permission_grants),"restrictions":json.dumps(body.permission_restrictions),
      "token_hash":hashlib.sha256(token.encode()).hexdigest(),"actor":ctx["user_id"],"expires":now+timedelta(hours=body.expires_in_hours),"now":now})
    await _team_audit(db,ctx,"TEAM_MEMBER_INVITED",new_value={"invitation_id":str(invitation_id),"role":body.role,"email":body.email.lower()})
    await db.commit()
    return {"success":True,"data":{"id":str(invitation_id),"status":"INVITED","acceptance_token":token,"expires_at":now+timedelta(hours=body.expires_in_hours)},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/team/invitations/{invitation_id}/resend")
async def resend_team_invitation(request:Request,invitation_id:UUID,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"TEAM_MANAGE")
    if denied:return denied
    token=secrets.token_urlsafe(32);now=datetime.now(timezone.utc)
    row=(await db.execute(text("""UPDATE external_team_invitations SET token_hash=:hash,expires_at=:expires,updated_at=:now
      WHERE id=:id AND tenant_id=:tenant AND status='INVITED' RETURNING id"""),{"hash":hashlib.sha256(token.encode()).hexdigest(),
      "expires":now+timedelta(days=7),"now":now,"id":invitation_id,"tenant":ctx["tenant_id"]})).scalar_one_or_none()
    if not row:return error(request,404,"INVITATION_NOT_FOUND","Active invitation not found")
    await db.commit();return {"success":True,"data":{"id":str(invitation_id),"status":"INVITED","acceptance_token":token},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/team/invitations/accept")
async def accept_team_invitation(request:Request,body:TeamInvitationAccept,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    now=datetime.now(timezone.utc);digest=hashlib.sha256(body.token.encode()).hexdigest()
    invite=(await db.execute(text("""SELECT id,email,display_name,role,profession_code,specialisation,location_code,
      permission_grants,permission_restrictions,status,invited_by,expires_at FROM external_team_invitations
      WHERE token_hash=:hash AND tenant_id=:tenant"""),{"hash":digest,"tenant":ctx["tenant_id"]})).mappings().first()
    if not invite:return error(request,404,"INVITATION_NOT_FOUND","Invitation not found")
    if invite["status"]!="INVITED":return error(request,409,"INVITATION_ALREADY_USED","Invitation has already been accepted")
    if invite["expires_at"]<=now:return error(request,403,"INVITATION_EXPIRED","Invitation has expired")
    authenticated_email=await _authenticated_user_email(ctx)
    if not authenticated_email:return error(request,503,"AUTH_IDENTITY_UNAVAILABLE","Authenticated email could not be verified",True)
    if authenticated_email!=invite["email"].lower():return error(request,403,"INVITATION_EMAIL_MISMATCH","Sign in with the invited email address")
    await db.execute(text("""INSERT INTO external_practice_role_profiles
      (id,tenant_id,user_id,role,status,display_name,profession_code,specialisation,location_code,permission_grants,
       permission_restrictions,practice_wide_client_access,active_from,created_by,created_at,updated_at)
      VALUES (:id,:tenant,:user,:role,'ACTIVE',:name,:profession,:specialisation,:location,CAST(:grants AS jsonb),
       CAST(:restrictions AS jsonb),FALSE,:now,:invited_by,:now,:now) ON CONFLICT (tenant_id,user_id) DO NOTHING"""),{
      "id":uuid4(),"tenant":ctx["tenant_id"],"user":ctx["user_id"],"role":invite["role"],"name":invite["display_name"],
      "profession":invite["profession_code"],"specialisation":invite["specialisation"],"location":invite["location_code"],
      "grants":json.dumps(invite["permission_grants"] or []),"restrictions":json.dumps(invite["permission_restrictions"] or []),
      "now":now,"invited_by":invite["invited_by"]})
    await db.execute(text("UPDATE external_team_invitations SET status='ACCEPTED',accepted_by=:user,accepted_at=:now,updated_at=:now WHERE id=:id"),{"user":ctx["user_id"],"now":now,"id":invite["id"]})
    await _team_audit(db,ctx,"TEAM_MEMBER_ACTIVATED",ctx["user_id"],new_value={"role":invite["role"]});await db.commit()
    return {"success":True,"data":{"status":"ACTIVE","role":invite["role"]},"error":None,"request_id":request.state.correlation_id}


@app.patch("/api/v1/practice-operations/team/members/{member_id}")
async def update_team_member(request:Request,member_id:UUID,body:TeamMemberUpdate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,principal=await _team_guard(request,db,ctx,"TEAM_MANAGE")
    if denied:return denied
    target=(await db.execute(text("SELECT user_id,role,status FROM external_practice_role_profiles WHERE id=:id AND tenant_id=:tenant"),{"id":member_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not target:return error(request,404,"TEAM_MEMBER_NOT_FOUND","Team member not found")
    if target["user_id"]==ctx["user_id"]:return error(request,403,"SELF_ROLE_ESCALATION_DENIED","You cannot change your own role or permissions")
    if not can_manage_role(principal["role"],target["role"],body.role):return error(request,403,"ROLE_ESCALATION_DENIED","This role transition is not permitted")
    if body.role=="PRACTITIONER" and not body.profession_code:return error(request,409,"PRACTITIONER_PROFESSION_REQUIRED","Practitioners require a profession profile")
    if (set(body.permission_grants)|set(body.permission_restrictions))-PERMISSIONS:return error(request,409,"INVALID_PERMISSION","One or more permission codes are invalid")
    await db.execute(text("""UPDATE external_practice_role_profiles SET role=:role,profession_code=:profession,
      specialisation=:specialisation,location_code=:location,permission_grants=CAST(:grants AS jsonb),
      permission_restrictions=CAST(:restrictions AS jsonb),practice_wide_client_access=:wide,updated_at=:now
      WHERE id=:id AND tenant_id=:tenant"""),{"role":body.role,"profession":body.profession_code,"specialisation":body.specialisation,
      "location":body.location_code,"grants":json.dumps(body.permission_grants),"restrictions":json.dumps(body.permission_restrictions),
      "wide":body.practice_wide_client_access,"now":datetime.now(timezone.utc),"id":member_id,"tenant":ctx["tenant_id"]})
    await _team_audit(db,ctx,"ROLE_CHANGED",target["user_id"],old_value={"role":target["role"]},new_value={"role":body.role,
      "permission_grants":body.permission_grants,"permission_restrictions":body.permission_restrictions});await db.commit()
    return {"success":True,"data":{"id":str(member_id),"role":body.role},"error":None,"request_id":request.state.correlation_id}


async def _set_member_status(request,member_id,status,event,ctx,db):
    denied,principal=await _team_guard(request,db,ctx,"TEAM_MANAGE")
    if denied:return denied
    target=(await db.execute(text("SELECT user_id,role,status FROM external_practice_role_profiles WHERE id=:id AND tenant_id=:tenant"),{"id":member_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not target:return error(request,404,"TEAM_MEMBER_NOT_FOUND","Team member not found")
    if target["user_id"]==ctx["user_id"] or target["role"]=="PRACTICE_OWNER":return error(request,403,"ROLE_ESCALATION_DENIED","This member cannot be changed by the current actor")
    if principal["role"]=="PRACTICE_ADMIN" and target["role"]=="PRACTICE_ADMIN":return error(request,403,"ROLE_ESCALATION_DENIED","Administrators cannot change peer administrators")
    now=datetime.now(timezone.utc);await db.execute(text("UPDATE external_practice_role_profiles SET status=:status,active_until=:until,updated_at=:now WHERE id=:id AND tenant_id=:tenant"),{"status":status,"until":now if status=="DEACTIVATED" else None,"now":now,"id":member_id,"tenant":ctx["tenant_id"]})
    await _team_audit(db,ctx,event,target["user_id"],old_value={"status":target["status"]},new_value={"status":status});await db.commit()
    return {"success":True,"data":{"id":str(member_id),"status":status},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/team/members/{member_id}/suspend")
async def suspend_team_member(request:Request,member_id:UUID,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    return await _set_member_status(request,member_id,"SUSPENDED","MEMBER_SUSPENDED",ctx,db)


@app.post("/api/v1/practice-operations/team/members/{member_id}/deactivate")
async def deactivate_team_member(request:Request,member_id:UUID,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    return await _set_member_status(request,member_id,"DEACTIVATED","MEMBER_DEACTIVATED",ctx,db)


@app.get("/api/v1/practice-operations/clients/{client_id}/team")
async def client_team(request:Request,client_id:str,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"CLIENT360_VIEW",client_id)
    if denied:return denied
    rows=(await db.execute(text("""SELECT a.id,a.user_id,a.assignment_role,a.assigned_by,a.assigned_at,a.ended_at,a.reason,
      p.display_name,p.role,p.profession_code,p.specialisation FROM external_client_team_assignments a
      JOIN external_practice_role_profiles p ON p.tenant_id=a.tenant_id AND p.user_id=a.user_id
      WHERE a.tenant_id=:tenant AND a.client_id=:client ORDER BY a.ended_at NULLS FIRST,a.assigned_at"""),{"tenant":ctx["tenant_id"],"client":client_id})).mappings().all()
    return {"success":True,"data":{"items":[dict(row) for row in rows]},"error":None,"request_id":request.state.correlation_id}


@app.get("/api/v1/practice-operations/team/client-assignments")
async def current_user_client_assignments(request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,principal=await _team_guard(request,db,ctx,"CLIENT_LIST_VIEW")
    if denied:return denied
    wide=bool(principal["practice_wide_client_access"] or principal["legacy_solo"])
    rows=(await db.execute(text("""SELECT client_id,user_id,assignment_role,assigned_at FROM external_client_team_assignments
      WHERE tenant_id=:tenant AND (:wide OR user_id=:user) AND ended_at IS NULL ORDER BY assigned_at DESC"""),{"tenant":ctx["tenant_id"],"user":ctx["user_id"],"wide":wide})).mappings().all()
    return {"success":True,"data":{"items":[dict(row) for row in rows],"practice_wide":wide,"current_user_id":ctx["user_id"]},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/clients/{client_id}/team",status_code=201)
async def assign_client_team(request:Request,client_id:str,body:ClientTeamAssignmentCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"CLIENT_ASSIGN")
    if denied:return denied
    member=(await db.execute(text("SELECT role,status FROM external_practice_role_profiles WHERE tenant_id=:tenant AND user_id=:user"),{"tenant":ctx["tenant_id"],"user":body.user_id})).mappings().first()
    if not member:return error(request,404,"TEAM_MEMBER_NOT_FOUND","Team member not found")
    if member["status"]!="ACTIVE":return error(request,409,"TEAM_MEMBER_INACTIVE","Only active team members can be assigned")
    if body.assignment_role in {"PRIMARY_PRACTITIONER","SECONDARY_PRACTITIONER"} and member["role"]!="PRACTITIONER":return error(request,409,"PRACTITIONER_REQUIRED","Clinical assignments require a practitioner")
    now=datetime.now(timezone.utc);prior=None
    if body.assignment_role=="PRIMARY_PRACTITIONER":
        prior=(await db.execute(text("""UPDATE external_client_team_assignments SET ended_at=:now,reason='PRIMARY_TRANSFER'
          WHERE tenant_id=:tenant AND client_id=:client AND assignment_role='PRIMARY_PRACTITIONER' AND ended_at IS NULL
          RETURNING user_id"""),{"now":now,"tenant":ctx["tenant_id"],"client":client_id})).scalar_one_or_none()
    assignment_id=uuid4();await db.execute(text("""INSERT INTO external_client_team_assignments
      (id,tenant_id,client_id,user_id,assignment_role,assigned_by,assigned_at,reason)
      VALUES (:id,:tenant,:client,:user,:role,:actor,:now,:reason)"""),{"id":assignment_id,"tenant":ctx["tenant_id"],"client":client_id,
      "user":body.user_id,"role":body.assignment_role,"actor":ctx["user_id"],"now":now,"reason":body.reason})
    await _team_audit(db,ctx,"CLIENT_TRANSFERRED" if prior else "CLIENT_ASSIGNED",body.user_id,client_id,
      old_value={"user_id":prior} if prior else None,new_value={"assignment_role":body.assignment_role});await db.commit()
    return {"success":True,"data":{"id":str(assignment_id),"assignment_role":body.assignment_role},"error":None,"request_id":request.state.correlation_id}


@app.patch("/api/v1/practice-operations/clients/{client_id}/team/{assignment_id}")
async def update_client_assignment(request:Request,client_id:str,assignment_id:UUID,body:ClientTeamAssignmentUpdate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"CLIENT_TRANSFER")
    if denied:return denied
    row=(await db.execute(text("SELECT user_id,assignment_role FROM external_client_team_assignments WHERE id=:id AND tenant_id=:tenant AND client_id=:client AND ended_at IS NULL"),{"id":assignment_id,"tenant":ctx["tenant_id"],"client":client_id})).mappings().first()
    if not row:return error(request,404,"CLIENT_ASSIGNMENT_NOT_FOUND","Client assignment not found")
    if body.assignment_role=="PRIMARY_PRACTITIONER":await db.execute(text("UPDATE external_client_team_assignments SET ended_at=:now,reason='PRIMARY_CHANGED' WHERE tenant_id=:tenant AND client_id=:client AND assignment_role='PRIMARY_PRACTITIONER' AND ended_at IS NULL AND id<>:id"),{"now":datetime.now(timezone.utc),"tenant":ctx["tenant_id"],"client":client_id,"id":assignment_id})
    await db.execute(text("UPDATE external_client_team_assignments SET assignment_role=:role,reason=:reason WHERE id=:id AND tenant_id=:tenant"),{"role":body.assignment_role,"reason":body.reason,"id":assignment_id,"tenant":ctx["tenant_id"]})
    await _team_audit(db,ctx,"CLIENT_TRANSFERRED",row["user_id"],client_id,old_value={"assignment_role":row["assignment_role"]},new_value={"assignment_role":body.assignment_role});await db.commit()
    return {"success":True,"data":{"id":str(assignment_id),"assignment_role":body.assignment_role},"error":None,"request_id":request.state.correlation_id}


@app.delete("/api/v1/practice-operations/clients/{client_id}/team/{assignment_id}")
async def unassign_client_team(request:Request,client_id:str,assignment_id:UUID,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"CLIENT_ASSIGN")
    if denied:return denied
    now=datetime.now(timezone.utc);row=(await db.execute(text("""UPDATE external_client_team_assignments SET ended_at=:now
      WHERE id=:id AND tenant_id=:tenant AND client_id=:client AND ended_at IS NULL RETURNING user_id,assignment_role"""),{"now":now,"id":assignment_id,"tenant":ctx["tenant_id"],"client":client_id})).mappings().first()
    if not row:return error(request,404,"CLIENT_ASSIGNMENT_NOT_FOUND","Client assignment not found")
    await _team_audit(db,ctx,"CLIENT_UNASSIGNED",row["user_id"],client_id,old_value={"assignment_role":row["assignment_role"]});await db.commit()
    return {"success":True,"data":{"id":str(assignment_id),"ended_at":now},"error":None,"request_id":request.state.correlation_id}


# P18 reads accepted operational domains without copying their raw records.
async def _analytics_scalar(db, sql, params):
    return (await db.execute(text(sql),params)).scalar() or 0


@app.get("/api/v1/practice-operations/analytics/practice")
async def practice_analytics(request:Request,preset:str="30d",start:datetime=None,end:datetime=None,
                             ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,principal=await _team_guard(request,db,ctx,"ANALYTICS_VIEW")
    if denied:return denied
    try:period_start,period_end=analytics_window(preset,start,end)
    except ValueError as exc:return error(request,422,"INVALID_ANALYTICS_RANGE",str(exc))
    p={"tenant":ctx["tenant_id"],"start":period_start,"end":period_end}
    appointments=(await db.execute(text("""SELECT COUNT(*) total,
      COUNT(*) FILTER (WHERE status='COMPLETED') completed,
      COUNT(*) FILTER (WHERE status='CANCELLED') cancelled,
      COUNT(*) FILTER (WHERE status='NO_SHOW' OR attendance_status='NO_SHOW') no_shows
      FROM external_scheduled_appointments WHERE tenant_id=:tenant AND starts_at>=:start AND starts_at<:end"""),p)).mappings().one()
    invoices=(await db.execute(text("""SELECT COUNT(*) FILTER (WHERE status<>'DRAFT' AND status<>'CANCELLED') invoice_count,
      COALESCE(SUM(grand_total_minor) FILTER (WHERE status<>'DRAFT' AND status<>'CANCELLED'),0) invoice_total,
      COALESCE(SUM(amount_paid_minor) FILTER (WHERE status<>'DRAFT' AND status<>'CANCELLED'),0) paid,
      COALESCE(SUM(balance_due_minor) FILTER (WHERE status IN ('ISSUED','PART_PAID','OVERDUE')),0) outstanding,
      COALESCE(SUM(balance_due_minor) FILTER (WHERE status='OVERDUE'),0) overdue,
      MAX(currency) currency FROM external_invoices WHERE tenant_id=:tenant AND created_at>=:start AND created_at<:end"""),p)).mappings().one()
    async def completion(table):
        row=(await db.execute(text(f"""SELECT COUNT(*) total,COUNT(*) FILTER (WHERE status='COMPLETED') completed
          FROM {table} WHERE tenant_id=:tenant AND created_at>=:start AND created_at<:end"""),p)).mappings().one()
        return {"completed":row["completed"],"total":row["total"],"rate":rate(row["completed"],row["total"])}
    followups=await completion("practice_follow_ups");tasks=await completion("practice_tasks")
    homework=await completion("external_homework_assignments")
    assessments=await completion("external_client_assessments")
    automation=(await db.execute(text("""SELECT COUNT(*) total,COUNT(*) FILTER (WHERE status='SUCCEEDED') succeeded,
      COUNT(*) FILTER (WHERE status='FAILED') failed FROM external_automation_executions
      WHERE tenant_id=:tenant AND created_at>=:start AND created_at<:end"""),p)).mappings().one()
    packages=(await db.execute(text("""SELECT COUNT(*) FILTER (WHERE created_at>=:start AND created_at<:end) sales,
      COUNT(*) FILTER (WHERE status='ACTIVE' AND end_date BETWEEN CURRENT_DATE AND CURRENT_DATE+30) ending_soon,
      COUNT(*) FILTER (WHERE renewal_date BETWEEN CURRENT_DATE AND CURRENT_DATE+30) renewals_due,
      COUNT(*) FILTER (WHERE status='COMPLETED' AND updated_at>=:start AND updated_at<:end) renewals_completed
      FROM external_client_packages WHERE tenant_id=:tenant"""),p)).mappings().one()
    waitlist=await _analytics_scalar(db,"SELECT COUNT(*) FROM external_scheduling_waitlist WHERE tenant_id=:tenant AND status='WAITING'",p)
    engagement=(await db.execute(text("""WITH activity AS (
      SELECT client_id,MAX(updated_at) last_at FROM practice_tasks WHERE tenant_id=:tenant GROUP BY client_id
      UNION ALL SELECT client_id,MAX(updated_at) FROM practice_follow_ups WHERE tenant_id=:tenant GROUP BY client_id
    ),latest AS (SELECT client_id,MAX(last_at) last_at FROM activity GROUP BY client_id)
    SELECT COUNT(*) FILTER (WHERE last_at>=:end-INTERVAL '14 days') high,
      COUNT(*) FILTER (WHERE last_at<:end-INTERVAL '14 days' AND last_at>=:end-INTERVAL '30 days') moderate,
      COUNT(*) FILTER (WHERE last_at<:end-INTERVAL '30 days') needs_attention FROM latest"""),p)).mappings().one()
    workload=[]
    if principal["role"] in {"PRACTICE_OWNER","PRACTICE_ADMIN"}:
        rows=(await db.execute(text("""SELECT p.user_id,p.display_name,COUNT(DISTINCT a.client_id) active_clients,
          COUNT(DISTINCT s.id) FILTER (WHERE s.starts_at>=:start AND s.starts_at<:end) sessions
          FROM external_practice_role_profiles p LEFT JOIN external_client_team_assignments a
          ON a.tenant_id=p.tenant_id AND a.user_id=p.user_id AND a.ended_at IS NULL
          LEFT JOIN external_scheduled_appointments s ON s.tenant_id=p.tenant_id AND s.created_by=p.user_id
          WHERE p.tenant_id=:tenant AND p.status='ACTIVE' GROUP BY p.user_id,p.display_name ORDER BY p.display_name"""),p)).mappings().all()
        workload=[dict(row) for row in rows]
    outcome_rows=(await db.execute(text("""SELECT d.code,d.label,d.unit,d.direction,
      COUNT(DISTINCT o.client_id) cohort_size,COUNT(o.id) observations
      FROM external_progress_metric_definitions d JOIN external_progress_observations o
      ON o.metric_definition_id=d.id AND o.tenant_id=d.tenant_id
      WHERE d.tenant_id=:tenant AND o.observed_at>=:start AND o.observed_at<:end
      GROUP BY d.code,d.label,d.unit,d.direction ORDER BY d.label"""),p)).mappings().all()
    outcomes=[{"code":row["code"],"label":row["label"],"unit":row["unit"],"direction":row["direction"],
      **cohort_result(row["cohort_size"],{"observations":row["observations"]})} for row in outcome_rows]
    total_sessions=appointments["total"]
    data={"state":"LOADED","period":{"preset":preset,"start":period_start,"end":period_end,"timezone":"practice"},
      "business":{"active_clients":{"value":None,"state":"UNAVAILABLE_SOURCE"},"total_sessions":total_sessions,
        "completed_sessions":appointments["completed"],"cancelled_sessions":appointments["cancelled"],"no_shows":appointments["no_shows"],
        "session_utilisation":rate(appointments["completed"],total_sessions),"package_sales":packages["sales"],
        "packages_ending_soon":packages["ending_soon"],"renewals_due":packages["renewals_due"],"renewals_completed":packages["renewals_completed"],
        "invoice_total_minor":invoices["invoice_total"],"paid_amount_minor":invoices["paid"],"outstanding_amount_minor":invoices["outstanding"],
        "overdue_amount_minor":invoices["overdue"],"average_invoice_value_minor":round(invoices["invoice_total"]/invoices["invoice_count"]) if invoices["invoice_count"] else None,"currency":invoices["currency"]},
      "operations":{"followups":followups,"tasks":tasks,"assessments":assessments,"homework":homework,"waitlist_size":waitlist,
        "automation":{"total":automation["total"],"execution_rate":rate(automation["succeeded"],automation["total"]),"failure_rate":rate(automation["failed"],automation["total"])}},
      "engagement":{"HIGH":engagement["high"],"MODERATE":engagement["moderate"],"NEEDS_ATTENTION":engagement["needs_attention"],"INSUFFICIENT_DATA":0,
        "explanation":"Operational engagement only; not medical risk."},"team":{"items":workload,"restricted":not bool(workload) and principal["role"] not in {"PRACTICE_OWNER","PRACTICE_ADMIN"}},
      "outcomes":{"minimum_cohort_size":MIN_COHORT_SIZE,"items":outcomes},
      "unavailable":["active_clients","new_clients","revenue_by_service","average_time_to_book","onboarding_completion_rate"]}
    return {"success":True,"data":data,"error":None,"request_id":request.state.correlation_id}


# P19 is referral-scoped. It never grants Client360 or changes client ownership.
async def _referral_event(db,row,event,actor_id,actor_type="PRACTITIONER",message=None,old_value=None,new_value=None):
    now=datetime.now(timezone.utc)
    await db.execute(text("""INSERT INTO external_referral_events
      (id,tenant_id,referral_id,event_type,actor_id,actor_type,message,metadata,created_at)
      VALUES (:id,:tenant,:referral,:event,:actor,:actor_type,:message,'{}'::jsonb,:now)"""),{
      "id":uuid4(),"tenant":row["tenant_id"],"referral":row["id"],"event":event,"actor":actor_id,"actor_type":actor_type,"message":message,"now":now})
    await db.execute(text("""INSERT INTO external_referral_audit_events
      (id,tenant_id,referral_id,event_type,actor_id,actor_type,old_value,new_value,created_at)
      VALUES (:id,:tenant,:referral,:event,:actor,:actor_type,CAST(:old AS jsonb),CAST(:new AS jsonb),:now)"""),{
      "id":uuid4(),"tenant":row["tenant_id"],"referral":row["id"],"event":event,"actor":actor_id,"actor_type":actor_type,
      "old":json.dumps(old_value) if old_value is not None else None,"new":json.dumps(new_value) if new_value is not None else None,"now":now})


@app.get("/api/v1/practice-operations/referrals")
async def list_referrals(request:Request,direction:str="outgoing",client_id:str=None,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"REFERRAL_VIEW",client_id)
    if denied:return denied
    if direction=="incoming":
        clause="r.receiving_tenant_id=:tenant AND (r.receiving_practitioner_id IS NULL OR r.receiving_practitioner_id=:actor)"
    else:clause="r.tenant_id=:tenant"
    if client_id:clause+=" AND r.client_id=:client"
    rows=(await db.execute(text(f"""SELECT r.id,r.tenant_id,r.client_id,r.referring_practitioner_id,r.receiving_practitioner_id,
      r.receiving_tenant_id,r.receiving_profession_code,r.destination_name,r.reason,r.status,r.created_at,r.sent_at,r.accepted_at,
      c.status consent_status,COALESCE(c.allowed_data_scopes,(SELECT jsonb_agg(s.scope_code ORDER BY s.scope_code) FROM external_referral_shared_scopes s WHERE s.tenant_id=r.tenant_id AND s.referral_id=r.id),'[]'::jsonb) allowed_data_scopes,c.expires_at FROM external_referrals r
      LEFT JOIN external_referral_consents c ON c.referral_id=r.id AND c.tenant_id=r.tenant_id
      WHERE {clause} ORDER BY r.created_at DESC"""),{"tenant":ctx["tenant_id"],"actor":ctx["user_id"],"client":client_id})).mappings().all()
    return {"success":True,"data":{"items":[dict(row) for row in rows],"direction":direction},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/referrals",status_code=201)
async def create_referral(request:Request,body:ReferralCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"REFERRAL_MANAGE",body.client_id)
    if denied:return denied
    try:scopes=validate_scopes(body.data_scopes)
    except ValueError as exc:return error(request,422,"REFERRAL_SCOPE_DENIED",str(exc))
    now=datetime.now(timezone.utc);referral_id=uuid4();row={"id":referral_id,"tenant_id":ctx["tenant_id"]}
    await db.execute(text("""INSERT INTO external_referrals
      (id,tenant_id,client_id,referring_practitioner_id,receiving_practitioner_id,receiving_tenant_id,
       receiving_profession_code,destination_name,destination_contact,reason,status,created_at,updated_at)
      VALUES (:id,:tenant,:client,:actor,:recipient,:receiving_tenant,:profession,:name,:contact,:reason,'DRAFT',:now,:now)"""),{
      "id":referral_id,"tenant":ctx["tenant_id"],"client":body.client_id,"actor":ctx["user_id"],"recipient":body.receiving_practitioner_id,
      "receiving_tenant":body.receiving_tenant_id,"profession":body.receiving_profession_code,"name":body.destination_name,
      "contact":body.destination_contact,"reason":body.reason,"now":now})
    for scope_code in scopes:
        await db.execute(text("""INSERT INTO external_referral_shared_scopes
          (id,tenant_id,referral_id,scope_code,selected_resource_ids,created_by,created_at)
          VALUES (:id,:tenant,:referral,:scope,'[]'::jsonb,:actor,:now)"""),{"id":uuid4(),"tenant":ctx["tenant_id"],"referral":referral_id,"scope":scope_code,"actor":ctx["user_id"],"now":now})
    await _referral_event(db,row,"REFERRAL_CREATED",ctx["user_id"],new_value={"status":"DRAFT","scopes":scopes});await db.commit()
    return {"success":True,"data":{"id":str(referral_id),"status":"DRAFT","data_scopes":scopes},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/practice-operations/referrals/{referral_id}/actions")
async def referral_action(request:Request,referral_id:UUID,body:ReferralAction,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"REFERRAL_MANAGE")
    if denied:return denied
    row=(await db.execute(text("""SELECT id,tenant_id,client_id,referring_practitioner_id,receiving_practitioner_id,
      receiving_tenant_id,receiving_profession_code,destination_name,destination_contact,reason,status,
      created_at,sent_at,accepted_at,completed_at,declined_at,cancelled_at,updated_at FROM external_referrals WHERE id=:id AND
      (tenant_id=:tenant OR (receiving_tenant_id=:tenant AND (receiving_practitioner_id IS NULL OR receiving_practitioner_id=:actor)))"""),{
      "id":referral_id,"tenant":ctx["tenant_id"],"actor":ctx["user_id"]})).mappings().first()
    if not row:return error(request,404,"REFERRAL_NOT_FOUND","Referral not found")
    incoming=row["tenant_id"]!=ctx["tenant_id"]
    if body.action=="REQUEST_CLARIFICATION":
        if not incoming or row["status"] not in {"SENT","ACCEPTED"}:return error(request,409,"REFERRAL_TRANSITION_DENIED","Clarification is not available")
        await _referral_event(db,row,"CLARIFICATION_REQUESTED",ctx["user_id"],message=body.message);await db.commit()
        return {"success":True,"data":{"id":str(referral_id),"status":row["status"]},"error":None,"request_id":request.state.correlation_id}
    if incoming and body.action not in {"ACCEPT","DECLINE","COMPLETE"}:return error(request,403,"REFERRAL_ACTION_DENIED","Recipient action is not permitted")
    if not incoming and body.action in {"ACCEPT","DECLINE","COMPLETE"}:return error(request,403,"REFERRAL_ACTION_DENIED","Source practice cannot perform the recipient action")
    try:target=referral_transition(row["status"],body.action)
    except ValueError as exc:return error(request,409,"REFERRAL_TRANSITION_DENIED",str(exc))
    if body.action=="SEND":
        consent=(await db.execute(text("""SELECT status,expires_at FROM external_referral_consents
          WHERE tenant_id=:tenant AND referral_id=:id"""),{"tenant":row["tenant_id"],"id":referral_id})).mappings().first()
        if not consent or consent["status"]!="GRANTED" or (consent["expires_at"] and consent["expires_at"]<=datetime.now(timezone.utc)):
            return error(request,403,"REFERRAL_CONSENT_REQUIRED","Current client consent is required before sending")
    now=datetime.now(timezone.utc);timestamps={"SENT":"sent_at","ACCEPTED":"accepted_at","DECLINED":"declined_at","COMPLETED":"completed_at","CANCELLED":"cancelled_at"}
    stamp=timestamps.get(target);set_stamp=f",{stamp}=:now" if stamp else ""
    await db.execute(text(f"UPDATE external_referrals SET status=:status,updated_at=:now{set_stamp} WHERE id=:id AND tenant_id=:source"),{
      "status":target,"now":now,"id":referral_id,"source":row["tenant_id"]})
    if body.action=="REQUEST_CONSENT":
        scopes=(await db.execute(text("SELECT scope_code FROM external_referral_shared_scopes WHERE tenant_id=:tenant AND referral_id=:id AND revoked_at IS NULL"),{"tenant":row["tenant_id"],"id":referral_id})).scalars().all()
        await db.execute(text("""INSERT INTO external_referral_consents
          (id,tenant_id,referral_id,client_id,consent_version,status,allowed_data_scopes,created_at,updated_at)
          VALUES (:cid,:tenant,:referral,:client,'P19_V1','PENDING',CAST(:scopes AS jsonb),:now,:now)
          ON CONFLICT (tenant_id,referral_id) DO UPDATE SET status='PENDING',allowed_data_scopes=EXCLUDED.allowed_data_scopes,updated_at=:now"""),{
          "cid":uuid4(),"tenant":row["tenant_id"],"referral":referral_id,"client":row["client_id"],"scopes":json.dumps(list(scopes)),"now":now})
    event={"REQUEST_CONSENT":"CONSENT_REQUESTED","SEND":"REFERRAL_SENT","ACCEPT":"REFERRAL_ACCEPTED","DECLINE":"REFERRAL_DECLINED","COMPLETE":"REFERRAL_COMPLETED","CANCEL":"REFERRAL_CANCELLED"}[body.action]
    await _referral_event(db,row,event,ctx["user_id"],message=body.message,old_value={"status":row["status"]},new_value={"status":target});await db.commit()
    return {"success":True,"data":{"id":str(referral_id),"status":target},"error":None,"request_id":request.state.correlation_id}


@app.get("/api/v1/practice-operations/referrals/{referral_id}/shared-data")
async def referral_shared_data(request:Request,referral_id:UUID,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"REFERRAL_VIEW")
    if denied:return denied
    row=(await db.execute(text("""SELECT r.*,c.status consent_status,c.allowed_data_scopes,c.expires_at FROM external_referrals r
      JOIN external_referral_consents c ON c.referral_id=r.id AND c.tenant_id=r.tenant_id
      WHERE r.id=:id AND r.receiving_tenant_id=:tenant AND (r.receiving_practitioner_id IS NULL OR r.receiving_practitioner_id=:actor)
      AND r.status IN ('SENT','ACCEPTED','COMPLETED')"""),{"id":referral_id,"tenant":ctx["tenant_id"],"actor":ctx["user_id"]})).mappings().first()
    if not row:return error(request,404,"REFERRAL_NOT_FOUND","Referral not found")
    if row["consent_status"]!="GRANTED" or (row["expires_at"] and row["expires_at"]<=datetime.now(timezone.utc)):
        return error(request,403,"REFERRAL_CONSENT_REQUIRED","Current client consent is required")
    scopes=set(row["allowed_data_scopes"] or []);params={"tenant":row["tenant_id"],"client":row["client_id"]};projection={}
    if "GOALS" in scopes:projection["goals"]=[dict(x) for x in (await db.execute(text("SELECT id,title,status,due_at FROM practice_goals WHERE tenant_id=:tenant AND client_id=:client"),params)).mappings().all()]
    if "PROGRESS_SUMMARY" in scopes:projection["progress"]=[dict(x) for x in (await db.execute(text("""SELECT d.label,d.unit,o.numeric_value,o.text_value,o.observed_at FROM external_progress_observations o
      JOIN external_progress_metric_definitions d ON d.id=o.metric_definition_id AND d.tenant_id=o.tenant_id
      WHERE o.tenant_id=:tenant AND o.client_id=:client ORDER BY o.observed_at DESC LIMIT 50"""),params)).mappings().all()]
    if "PUBLISHED_PLAN" in scopes:projection["published_plans"]=[dict(x) for x in (await db.execute(text("SELECT id,title,plan_type,current_version FROM external_profession_plans WHERE tenant_id=:tenant AND client_id=:client AND status='PUBLISHED'"),params)).mappings().all()]
    if "PROGRESS_REPORT" in scopes:projection["progress_reports"]=[dict(x) for x in (await db.execute(text("""SELECT r.id,r.title,r.report_type,r.current_version,v.source_snapshot
      FROM external_progress_reports r JOIN external_progress_report_versions v ON v.report_id=r.id AND v.tenant_id=r.tenant_id AND v.version=r.current_version
      WHERE r.tenant_id=:tenant AND r.client_id=:client AND r.status='SHARED' AND r.revoked_at IS NULL"""),params)).mappings().all()]
    return {"success":True,"data":{"referral_id":str(referral_id),"client_id":row["client_id"],"scopes":sorted(scopes),"projection":projection,"excluded":["PRIVATE_NOTES","RAW_SESSION_NOTES","BILLING","TEAM_NOTES"]},"error":None,"request_id":request.state.correlation_id}


@app.post("/api/v1/client-portal/{token}/referrals/{referral_id}/consent")
async def portal_referral_consent(request:Request,token:str,referral_id:UUID,body:ReferralConsentDecision,db:AsyncSession=Depends(get_db)):
    scope,denied=await _portal_scope(request,token,"READ",db)
    if denied:return denied
    row=(await db.execute(text("""SELECT r.id,r.tenant_id,r.client_id,r.status,c.allowed_data_scopes FROM external_referrals r
      JOIN external_referral_consents c ON c.referral_id=r.id AND c.tenant_id=r.tenant_id
      WHERE r.id=:id AND r.tenant_id=:tenant AND r.client_id=:client AND r.status='CONSENT_PENDING' AND c.status='PENDING'"""),{
      "id":referral_id,"tenant":scope["tenant_id"],"client":scope["client_id"]})).mappings().first()
    if not row:return error(request,404,"REFERRAL_CONSENT_NOT_FOUND","Referral consent request not found")
    requested=set(row["allowed_data_scopes"] or [])
    try:allowed=set(validate_scopes(body.allowed_data_scopes))
    except ValueError as exc:return error(request,422,"REFERRAL_SCOPE_DENIED",str(exc))
    if body.decision=="GRANT" and not allowed.issubset(requested):return error(request,403,"REFERRAL_SCOPE_DENIED","Consent cannot expand the requested sharing scope")
    now=datetime.now(timezone.utc);consent_status="GRANTED" if body.decision=="GRANT" else "DECLINED";referral_status="READY_TO_SEND" if body.decision=="GRANT" else "DRAFT"
    await db.execute(text("""UPDATE external_referral_consents SET status=:status,consent_version=:version,
      allowed_data_scopes=CAST(:scopes AS jsonb),consented_at=CASE WHEN :status='GRANTED' THEN :now END,
      declined_at=CASE WHEN :status='DECLINED' THEN :now END,updated_at=:now WHERE tenant_id=:tenant AND referral_id=:id"""),{
      "status":consent_status,"version":body.consent_version,"scopes":json.dumps(sorted(allowed) if body.decision=="GRANT" else []),"now":now,"tenant":row["tenant_id"],"id":referral_id})
    await db.execute(text("UPDATE external_referrals SET status=:status,updated_at=:now WHERE id=:id AND tenant_id=:tenant"),{"status":referral_status,"now":now,"id":referral_id,"tenant":row["tenant_id"]})
    await _referral_event(db,row,"CONSENT_GRANTED" if body.decision=="GRANT" else "CONSENT_DECLINED",None,"CLIENT",new_value={"scopes":sorted(allowed)});await db.commit()
    return {"success":True,"data":{"status":consent_status,"referral_status":referral_status},"error":None,"request_id":request.state.correlation_id}


# P20 is a separate reporting domain; the sealed Diet Plan document generator is not used.
REPORT_SECTIONS={"goals","sessions","assessments","progress","plans","homework","milestones","consultant_summary"}
async def _report_snapshot(db,row):
    params={"tenant":row["tenant_id"],"client":row["client_id"],"start":row["period_start"],"end":row["period_end"]+timedelta(days=1)}
    requested=set(row["included_sections"] or []) & REPORT_SECTIONS;sections=[]
    if "goals" in requested:
        rows=(await db.execute(text("SELECT title,status,due_at FROM practice_goals WHERE tenant_id=:tenant AND client_id=:client AND created_at>=:start AND created_at<:end"),params)).mappings().all()
        sections.append({"key":"goals","title":"Goals","items":[{"label":x["title"],"value":x["status"],"provenance":"PRACTITIONER_ENTERED"} for x in rows]})
    if "sessions" in requested:
        rows=(await db.execute(text("SELECT title,status,due_at FROM practice_consultations WHERE tenant_id=:tenant AND client_id=:client AND created_at>=:start AND created_at<:end"),params)).mappings().all()
        sections.append({"key":"sessions","title":"Sessions","items":[{"label":x["title"],"value":f"{x['status']} · {x['due_at'] or 'date unavailable'}","provenance":"SYSTEM_DERIVED"} for x in rows]})
    if "assessments" in requested:
        rows=(await db.execute(text("""SELECT d.title,i.status,i.completed_at FROM external_assessment_instances i JOIN external_assessment_definitions d ON d.id=i.definition_id
          WHERE i.tenant_id=:tenant AND i.client_id=:client AND i.assigned_at>=:start AND i.assigned_at<:end AND i.status IN ('COMPLETED','REVIEWED')"""),params)).mappings().all()
        sections.append({"key":"assessments","title":"Assessments","items":[{"label":x["title"],"value":x["status"],"provenance":"CLIENT_REPORTED"} for x in rows]})
    if "progress" in requested:
        rows=(await db.execute(text("""SELECT d.label,d.unit,o.numeric_value,o.text_value,o.source_type,o.observed_at
          FROM external_progress_observations o JOIN external_progress_metric_definitions d ON d.id=o.metric_definition_id AND d.tenant_id=o.tenant_id
          WHERE o.tenant_id=:tenant AND o.client_id=:client AND o.observed_at>=:start AND o.observed_at<:end ORDER BY o.observed_at"""),params)).mappings().all()
        provenance={"MANUAL":"PRACTITIONER_ENTERED","ASSESSMENT":"CLIENT_REPORTED","BIOMARKER_REFERENCE":"LAB_CONFIRMED"}
        sections.append({"key":"progress","title":"Progress trends","items":[{"label":x["label"],"value":f"{x['numeric_value'] if x['numeric_value'] is not None else x['text_value'] or '—'} {x['unit'] or ''}".strip(),"provenance":provenance.get(x["source_type"],"SYSTEM_DERIVED")} for x in rows]})
    if "plans" in requested:
        rows=(await db.execute(text("SELECT title,plan_type,current_version FROM external_profession_plans WHERE tenant_id=:tenant AND client_id=:client AND status='PUBLISHED'"),params)).mappings().all()
        sections.append({"key":"plans","title":"Published plans","items":[{"label":x["title"],"value":f"{x['plan_type']} · version {x['current_version']}","provenance":"PRACTITIONER_ENTERED"} for x in rows]})
    if "homework" in requested:
        rows=(await db.execute(text("SELECT title,status,due_date FROM external_homework_assignments WHERE tenant_id=:tenant AND client_id=:client AND assigned_at>=:start AND assigned_at<:end AND status<>'CANCELLED'"),params)).mappings().all()
        sections.append({"key":"homework","title":"Homework and adherence","items":[{"label":x["title"],"value":x["status"],"provenance":"SYSTEM_DERIVED"} for x in rows]})
    if "milestones" in requested:
        rows=(await db.execute(text("SELECT title,status,target_date FROM external_progress_milestones WHERE tenant_id=:tenant AND client_id=:client AND created_at>=:start AND created_at<:end AND status<>'CANCELLED'"),params)).mappings().all()
        sections.append({"key":"milestones","title":"Milestones","items":[{"label":x["title"],"value":x["status"],"provenance":"PRACTITIONER_ENTERED"} for x in rows]})
    return {"report_id":str(row["id"]),"title":row["title"],"report_type":row["report_type"],"profession_code":row["profession_code"],
      "client_id":row["client_id"],"period_start":row["period_start"].isoformat(),"period_end":row["period_end"].isoformat(),
      "consultant_id":row["created_by"],"consultant_summary":row["consultant_summary"] if "consultant_summary" in requested else None,
      "sections":sections,"excluded":["PRIVATE_NOTES","RAW_SESSION_NOTES","DRAFT_PLANS","INTERNAL_INTELLIGENCE"],"generated_at":datetime.now(timezone.utc).isoformat()}

async def _report_audit(db,row,event,actor,version_id=None,metadata=None):
    await db.execute(text("""INSERT INTO external_progress_report_audit_events
      (id,tenant_id,client_id,report_id,report_version_id,event_type,actor_id,metadata,created_at)
      VALUES (:id,:tenant,:client,:report,:version,:event,:actor,CAST(:metadata AS jsonb),:now)"""),{
      "id":uuid4(),"tenant":row["tenant_id"],"client":row["client_id"],"report":row["id"],"version":version_id,"event":event,"actor":actor,"metadata":json.dumps(metadata or {}),"now":datetime.now(timezone.utc)})

@app.get("/api/v1/practice-operations/progress-reports")
async def list_progress_reports(request:Request,client_id:str=None,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"REPORT_VIEW",client_id)
    if denied:return denied
    clause="tenant_id=:tenant"+(" AND client_id=:client" if client_id else "")
    rows=(await db.execute(text(f"""SELECT id,client_id,profession_code,report_type,title,period_start,period_end,
      included_sections,status,current_version,created_at,shared_at,revoked_at FROM external_progress_reports
      WHERE {clause} ORDER BY created_at DESC"""),{"tenant":ctx["tenant_id"],"client":client_id})).mappings().all()
    return {"success":True,"data":{"items":[dict(row) for row in rows]},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/progress-reports",status_code=201)
async def create_progress_report(request:Request,body:ProgressReportCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"REPORT_GENERATE",body.client_id)
    if denied:return denied
    invalid=set(body.included_sections)-REPORT_SECTIONS
    if invalid:return error(request,422,"INVALID_REPORT_SECTION","One or more report sections are not supported")
    if body.period_end<body.period_start:return error(request,422,"INVALID_REPORT_PERIOD","Report end date must not precede start date")
    now=datetime.now(timezone.utc);report_id=uuid4();row={"id":report_id,"tenant_id":ctx["tenant_id"],"client_id":body.client_id}
    await db.execute(text("""INSERT INTO external_progress_reports
      (id,tenant_id,client_id,profession_code,report_type,title,period_start,period_end,included_sections,
       consultant_summary,status,current_version,created_by,created_at,updated_at)
      VALUES (:id,:tenant,:client,:profession,:type,:title,:start,:end,CAST(:sections AS jsonb),:summary,'DRAFT',0,:actor,:now,:now)"""),{
      "id":report_id,"tenant":ctx["tenant_id"],"client":body.client_id,"profession":body.profession_code,"type":body.report_type,
      "title":body.title,"start":body.period_start,"end":body.period_end,"sections":json.dumps(body.included_sections),"summary":body.consultant_summary,"actor":ctx["user_id"],"now":now})
    await _report_audit(db,row,"REPORT_CREATED",ctx["user_id"]);await db.commit()
    return {"success":True,"data":{"id":str(report_id),"status":"DRAFT","version":0},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/progress-reports/{report_id}/preview")
async def preview_progress_report(request:Request,report_id:UUID,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    row=(await db.execute(text("SELECT id,tenant_id,client_id,profession_code,report_type,title,period_start,period_end,included_sections,consultant_summary,created_by,status FROM external_progress_reports WHERE id=:id AND tenant_id=:tenant"),{"id":report_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not row:return error(request,404,"PROGRESS_REPORT_NOT_FOUND","Progress report not found")
    denied,_=await _team_guard(request,db,ctx,"REPORT_VIEW",row["client_id"])
    if denied:return denied
    return {"success":True,"data":{"status":row["status"],"preview":await _report_snapshot(db,row)},"error":None,"request_id":request.state.correlation_id}

@app.patch("/api/v1/practice-operations/progress-reports/{report_id}")
async def update_progress_report(request:Request,report_id:UUID,body:ProgressReportUpdate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    row=(await db.execute(text("SELECT id,tenant_id,client_id,status FROM external_progress_reports WHERE id=:id AND tenant_id=:tenant"),{"id":report_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not row:return error(request,404,"PROGRESS_REPORT_NOT_FOUND","Progress report not found")
    denied,_=await _team_guard(request,db,ctx,"REPORT_GENERATE",row["client_id"])
    if denied:return denied
    if row["status"]!="DRAFT":return error(request,409,"REPORT_IMMUTABLE","Generated reports are immutable; create a new version")
    if set(body.included_sections)-REPORT_SECTIONS:return error(request,422,"INVALID_REPORT_SECTION","One or more report sections are not supported")
    await db.execute(text("UPDATE external_progress_reports SET included_sections=CAST(:sections AS jsonb),consultant_summary=:summary,updated_at=:now WHERE id=:id AND tenant_id=:tenant AND status='DRAFT'"),{
      "sections":json.dumps(body.included_sections),"summary":body.consultant_summary,"now":datetime.now(timezone.utc),"id":report_id,"tenant":ctx["tenant_id"]});await db.commit()
    return {"success":True,"data":{"id":str(report_id),"status":"DRAFT"},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/progress-reports/{report_id}/generate")
async def generate_progress_report(request:Request,report_id:UUID,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    row=(await db.execute(text("SELECT id,tenant_id,client_id,profession_code,report_type,title,period_start,period_end,included_sections,consultant_summary,created_by,status,current_version FROM external_progress_reports WHERE id=:id AND tenant_id=:tenant"),{"id":report_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not row:return error(request,404,"PROGRESS_REPORT_NOT_FOUND","Progress report not found")
    denied,_=await _team_guard(request,db,ctx,"REPORT_GENERATE",row["client_id"])
    if denied:return denied
    if row["status"]!="DRAFT":return error(request,409,"REPORT_IMMUTABLE","Generated reports are immutable; create a new report version")
    snapshot=await _report_snapshot(db,row);snapshot_bytes=json.dumps(snapshot,sort_keys=True,default=str).encode();digest=checksum(snapshot_bytes)
    now=datetime.now(timezone.utc);version=row["current_version"]+1;version_id=uuid4()
    await db.execute(text("""INSERT INTO external_progress_report_versions
      (id,report_id,tenant_id,client_id,version,source_snapshot,checksum,generated_by,generated_at)
      VALUES (:id,:report,:tenant,:client,:version,CAST(:snapshot AS jsonb),:checksum,:actor,:now)"""),{
      "id":version_id,"report":report_id,"tenant":ctx["tenant_id"],"client":row["client_id"],"version":version,"snapshot":snapshot_bytes.decode(),"checksum":digest,"actor":ctx["user_id"],"now":now})
    artifacts=[("PDF","application/pdf",build_pdf(snapshot)),("DOCX","application/vnd.openxmlformats-officedocument.wordprocessingml.document",build_docx(snapshot))]
    for fmt,media,content in artifacts:
        await db.execute(text("""INSERT INTO external_progress_report_artifacts
          (id,report_version_id,tenant_id,format,media_type,content_bytes,checksum,created_at)
          VALUES (:id,:version,:tenant,:format,:media,:content,:checksum,:now)"""),{"id":uuid4(),"version":version_id,"tenant":ctx["tenant_id"],"format":fmt,"media":media,"content":content,"checksum":checksum(content),"now":now})
    await db.execute(text("UPDATE external_progress_reports SET status='GENERATED',current_version=:version,updated_at=:now WHERE id=:id AND tenant_id=:tenant AND status='DRAFT'"),{"version":version,"now":now,"id":report_id,"tenant":ctx["tenant_id"]})
    await _report_audit(db,row,"REPORT_GENERATED",ctx["user_id"],version_id,{"checksum":digest,"formats":["PDF","DOCX"]});await db.commit()
    return {"success":True,"data":{"id":str(report_id),"status":"GENERATED","version":version,"checksum":digest,"formats":["PDF","DOCX"]},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/progress-reports/{report_id}/artifacts/{format_code}")
async def download_progress_report(request:Request,report_id:UUID,format_code:str,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    row=(await db.execute(text("""SELECT r.client_id,r.title,a.media_type,a.content_bytes,a.format FROM external_progress_reports r
      JOIN external_progress_report_versions v ON v.report_id=r.id AND v.version=r.current_version AND v.tenant_id=r.tenant_id
      JOIN external_progress_report_artifacts a ON a.report_version_id=v.id AND a.tenant_id=r.tenant_id
      WHERE r.id=:id AND r.tenant_id=:tenant AND a.format=:format"""),{"id":report_id,"tenant":ctx["tenant_id"],"format":format_code.upper()})).mappings().first()
    if not row:return error(request,404,"REPORT_ARTIFACT_NOT_FOUND","Report artifact not found")
    denied,_=await _team_guard(request,db,ctx,"REPORT_VIEW",row["client_id"])
    if denied:return denied
    filename="progress-report."+row["format"].lower()
    return Response(content=bytes(row["content_bytes"]),media_type=row["media_type"],headers={"Content-Disposition":f'attachment; filename="{filename}"'})

@app.post("/api/v1/practice-operations/progress-reports/{report_id}/share")
async def share_progress_report(request:Request,report_id:UUID,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    row=(await db.execute(text("SELECT id,tenant_id,client_id,status FROM external_progress_reports WHERE id=:id AND tenant_id=:tenant"),{"id":report_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not row:return error(request,404,"PROGRESS_REPORT_NOT_FOUND","Progress report not found")
    denied,_=await _team_guard(request,db,ctx,"REPORT_GENERATE",row["client_id"])
    if denied:return denied
    if row["status"] not in {"GENERATED","SHARED"}:return error(request,409,"REPORT_NOT_GENERATED","Generate the report before sharing")
    now=datetime.now(timezone.utc);await db.execute(text("UPDATE external_progress_reports SET status='SHARED',shared_at=:now,shared_by=:actor,revoked_at=NULL,updated_at=:now WHERE id=:id AND tenant_id=:tenant"),{"now":now,"actor":ctx["user_id"],"id":report_id,"tenant":ctx["tenant_id"]})
    await _report_audit(db,row,"REPORT_SHARED",ctx["user_id"]);await db.commit();return {"success":True,"data":{"id":str(report_id),"status":"SHARED"},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/progress-reports/{report_id}/revoke")
async def revoke_progress_report(request:Request,report_id:UUID,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    row=(await db.execute(text("SELECT id,tenant_id,client_id,status FROM external_progress_reports WHERE id=:id AND tenant_id=:tenant"),{"id":report_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not row:return error(request,404,"PROGRESS_REPORT_NOT_FOUND","Progress report not found")
    denied,_=await _team_guard(request,db,ctx,"REPORT_GENERATE",row["client_id"])
    if denied:return denied
    now=datetime.now(timezone.utc);await db.execute(text("UPDATE external_progress_reports SET status='REVOKED',revoked_at=:now,updated_at=:now WHERE id=:id AND tenant_id=:tenant AND status='SHARED'"),{"now":now,"id":report_id,"tenant":ctx["tenant_id"]})
    await _report_audit(db,row,"REPORT_REVOKED",ctx["user_id"]);await db.commit();return {"success":True,"data":{"id":str(report_id),"status":"REVOKED"},"error":None,"request_id":request.state.correlation_id}

async def _write_form_structure(db,tenant,version_id,sections):
    for si,section in enumerate(sections):
        sid=uuid4();await db.execute(text("INSERT INTO external_form_sections(id,form_version_id,tenant_id,section_key,title,description,sort_order) VALUES (:id,:version,:tenant,:key,:title,:description,:sort)"),{"id":sid,"version":version_id,"tenant":tenant,"key":section.key,"title":section.title,"description":section.description,"sort":si})
        for fi,field in enumerate(section.fields):
            await db.execute(text("INSERT INTO external_form_fields(id,section_id,tenant_id,field_key,label,field_type,required,config,condition,sort_order) VALUES (:id,:section,:tenant,:key,:label,:type,:required,CAST(:config AS jsonb),CAST(:condition AS jsonb),:sort)"),{"id":uuid4(),"section":sid,"tenant":tenant,"key":field.key,"label":field.label,"type":field.field_type,"required":field.required,"config":json.dumps(field.config),"condition":json.dumps(field.condition) if field.condition is not None else None,"sort":fi})

@app.get("/api/v1/practice-operations/forms")
async def list_forms(request:Request,status:str|None=None,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"TEMPLATE_VIEW")
    if denied:return denied
    rows=(await db.execute(text("SELECT id,title,form_type,status,current_version,created_at,updated_at FROM external_form_definitions WHERE tenant_id=:tenant AND (CAST(:status AS text) IS NULL OR status=CAST(:status AS text)) ORDER BY updated_at DESC"),{"tenant":ctx["tenant_id"],"status":status})).mappings().all()
    return {"success":True,"data":{"items":[dict(row) for row in rows]},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/forms",status_code=201)
async def create_form(request:Request,body:FormCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"TEMPLATE_MANAGE")
    if denied:return denied
    now=datetime.now(timezone.utc);definition=uuid4();version=uuid4();tenant=ctx["tenant_id"]
    await db.execute(text("INSERT INTO external_form_definitions(id,tenant_id,title,form_type,status,current_version,created_by,created_at,updated_at) VALUES (:id,:tenant,:title,:type,'DRAFT',1,:actor,:now,:now)"),{"id":definition,"tenant":tenant,"title":body.title,"type":body.form_type,"actor":ctx["user_id"],"now":now})
    await db.execute(text("INSERT INTO external_form_versions(id,definition_id,tenant_id,version,status,title,settings,created_by,created_at) VALUES (:id,:definition,:tenant,1,'DRAFT',:title,CAST(:settings AS jsonb),:actor,:now)"),{"id":version,"definition":definition,"tenant":tenant,"title":body.title,"settings":json.dumps(body.settings),"actor":ctx["user_id"],"now":now});await _write_form_structure(db,tenant,version,body.sections)
    await db.execute(text("INSERT INTO external_form_audit_events(id,tenant_id,definition_id,event_type,actor_id,created_at) VALUES (:id,:tenant,:definition,'FORM_CREATED',:actor,:now)"),{"id":uuid4(),"tenant":tenant,"definition":definition,"actor":ctx["user_id"],"now":now});await db.commit()
    return {"success":True,"data":{"id":str(definition),"version":1,"status":"DRAFT"},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/forms/{form_id}")
async def get_form(request:Request,form_id:UUID,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    row=(await db.execute(text("SELECT id,tenant_id,title,form_type,status,current_version,created_by,created_at,updated_at FROM external_form_definitions WHERE id=:id AND tenant_id=:tenant"),{"id":form_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not row:return error(request,404,"FORM_NOT_FOUND","Form not found")
    version=(await db.execute(text("SELECT id,definition_id,tenant_id,version,status,title,settings,published_at,created_by,created_at FROM external_form_versions WHERE definition_id=:id AND version=:version AND tenant_id=:tenant"),{"id":form_id,"version":row["current_version"],"tenant":ctx["tenant_id"]})).mappings().one();sections=[dict(x) for x in (await db.execute(text("SELECT id,form_version_id,tenant_id,section_key,title,description,sort_order FROM external_form_sections WHERE form_version_id=:version AND tenant_id=:tenant ORDER BY sort_order"),{"version":version["id"],"tenant":ctx["tenant_id"]})).mappings().all()]
    fields=[dict(x) for x in (await db.execute(text("SELECT f.id,f.section_id,f.tenant_id,f.field_key,f.label,f.field_type,f.required,f.config,f.condition,f.sort_order FROM external_form_fields f JOIN external_form_sections s ON s.id=f.section_id WHERE s.form_version_id=:version AND f.tenant_id=:tenant ORDER BY s.sort_order,f.sort_order"),{"version":version["id"],"tenant":ctx["tenant_id"]})).mappings().all()]
    for section in sections:section["fields"]=[field for field in fields if field["section_id"]==section["id"]]
    return {"success":True,"data":{"definition":dict(row),"version":dict(version),"sections":sections},"error":None,"request_id":request.state.correlation_id}

@app.put("/api/v1/practice-operations/forms/{form_id}")
async def update_form(request:Request,form_id:UUID,body:FormCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    row=(await db.execute(text("SELECT status,current_version FROM external_form_definitions WHERE id=:id AND tenant_id=:tenant AND status<>'ARCHIVED'"),{"id":form_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not row:return error(request,404,"FORM_NOT_FOUND","Editable form not found")
    now=datetime.now(timezone.utc);number=row["current_version"]+1;version=uuid4();tenant=ctx["tenant_id"]
    await db.execute(text("UPDATE external_form_versions SET status='SUPERSEDED' WHERE definition_id=:id AND status='DRAFT'"),{"id":form_id});await db.execute(text("INSERT INTO external_form_versions(id,definition_id,tenant_id,version,status,title,settings,created_by,created_at) VALUES (:id,:definition,:tenant,:number,'DRAFT',:title,CAST(:settings AS jsonb),:actor,:now)"),{"id":version,"definition":form_id,"tenant":tenant,"number":number,"title":body.title,"settings":json.dumps(body.settings),"actor":ctx["user_id"],"now":now});await _write_form_structure(db,tenant,version,body.sections)
    await db.execute(text("UPDATE external_form_definitions SET title=:title,form_type=:type,status='DRAFT',current_version=:version,updated_at=:now WHERE id=:id AND tenant_id=:tenant"),{"title":body.title,"type":body.form_type,"version":number,"now":now,"id":form_id,"tenant":tenant});await db.commit()
    return {"success":True,"data":{"id":str(form_id),"version":number,"status":"DRAFT"},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/forms/{form_id}/publish")
async def publish_form(request:Request,form_id:UUID,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    row=(await db.execute(text("SELECT id,current_version FROM external_form_definitions WHERE id=:id AND tenant_id=:tenant AND status='DRAFT'"),{"id":form_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not row:return error(request,404,"DRAFT_FORM_NOT_FOUND","Draft form not found")
    now=datetime.now(timezone.utc);await db.execute(text("UPDATE external_form_versions SET status='SUPERSEDED' WHERE definition_id=:id AND status='PUBLISHED'"),{"id":form_id});await db.execute(text("UPDATE external_form_versions SET status='PUBLISHED',published_at=:now WHERE definition_id=:id AND version=:version AND tenant_id=:tenant"),{"now":now,"id":form_id,"version":row["current_version"],"tenant":ctx["tenant_id"]});await db.execute(text("UPDATE external_form_definitions SET status='PUBLISHED',updated_at=:now WHERE id=:id AND tenant_id=:tenant"),{"now":now,"id":form_id,"tenant":ctx["tenant_id"]});await db.commit()
    return {"success":True,"data":{"id":str(form_id),"status":"PUBLISHED","version":row["current_version"]},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/forms/{form_id}/assign",status_code=201)
async def assign_form(request:Request,form_id:UUID,body:FormAssign,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"TEMPLATE_MANAGE",body.client_id)
    if denied:return denied
    row=(await db.execute(text("SELECT d.id,v.id version_id FROM external_form_definitions d JOIN external_form_versions v ON v.definition_id=d.id AND v.version=d.current_version WHERE d.id=:id AND d.tenant_id=:tenant AND d.status='PUBLISHED' AND v.status='PUBLISHED'"),{"id":form_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not row:return error(request,404,"PUBLISHED_FORM_NOT_FOUND","Published form not found")
    aid=uuid4();now=datetime.now(timezone.utc);await db.execute(text("INSERT INTO external_form_assignments(id,tenant_id,client_id,form_definition_id,form_version_id,linked_type,linked_id,status,due_at,assigned_by,assigned_at,expires_at) VALUES (:id,:tenant,:client,:definition,:version,:linked_type,:linked_id,'ASSIGNED',:due,:actor,:now,:expires)"),{"id":aid,"tenant":ctx["tenant_id"],"client":body.client_id,"definition":form_id,"version":row["version_id"],"linked_type":body.linked_type,"linked_id":body.linked_id,"due":body.due_at,"actor":ctx["user_id"],"now":now,"expires":body.expires_at});await db.commit()
    return {"success":True,"data":{"id":str(aid),"status":"ASSIGNED"},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/form-assignments")
async def list_form_assignments(request:Request,client_id:str|None=None,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    rows=(await db.execute(text("SELECT a.*,d.title,d.form_type FROM external_form_assignments a JOIN external_form_definitions d ON d.id=a.form_definition_id WHERE a.tenant_id=:tenant AND (CAST(:client AS text) IS NULL OR a.client_id=CAST(:client AS text)) ORDER BY a.assigned_at DESC"),{"tenant":ctx["tenant_id"],"client":client_id})).mappings().all();return {"success":True,"data":{"items":[dict(row) for row in rows]},"error":None,"request_id":request.state.correlation_id}

@app.put("/api/v1/practice-operations/form-assignments/{assignment_id}/response")
async def save_form_response(request:Request,assignment_id:UUID,body:FormResponseSave,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    row=(await db.execute(text("SELECT id,tenant_id,client_id,status,expires_at FROM external_form_assignments WHERE id=:id AND tenant_id=:tenant"),{"id":assignment_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not row:return error(request,404,"FORM_ASSIGNMENT_NOT_FOUND","Form assignment not found")
    if row["status"]=="COMPLETED":return error(request,409,"FORM_RESPONSE_IMMUTABLE","Completed form responses are immutable")
    now=datetime.now(timezone.utc);status="COMPLETED" if body.submit else "STARTED"
    await db.execute(text("INSERT INTO external_form_responses(id,assignment_id,tenant_id,client_id,answers,status,response_version,submitted_at,updated_at) VALUES (:id,:assignment,:tenant,:client,CAST(:answers AS jsonb),:status,1,:submitted,:now) ON CONFLICT(assignment_id) DO UPDATE SET answers=EXCLUDED.answers,status=EXCLUDED.status,response_version=external_form_responses.response_version+1,submitted_at=EXCLUDED.submitted_at,updated_at=EXCLUDED.updated_at"),{"id":uuid4(),"assignment":assignment_id,"tenant":ctx["tenant_id"],"client":row["client_id"],"answers":json.dumps(body.answers),"status":status,"submitted":now if body.submit else None,"now":now});await db.execute(text("UPDATE external_form_assignments SET status=:status,started_at=COALESCE(started_at,:now),completed_at=:completed WHERE id=:id AND tenant_id=:tenant"),{"status":status,"now":now,"completed":now if body.submit else None,"id":assignment_id,"tenant":ctx["tenant_id"]});await db.commit()
    return {"success":True,"data":{"id":str(assignment_id),"status":status},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/consents/templates")
async def list_consent_templates(request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    rows=(await db.execute(text("SELECT id,title,consent_type,profession_code,status,current_version,created_at,updated_at FROM external_consent_templates WHERE tenant_id=:tenant AND status<>'ARCHIVED' ORDER BY updated_at DESC"),{"tenant":ctx["tenant_id"]})).mappings().all();return {"success":True,"data":{"items":[dict(x) for x in rows]},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/consents/templates",status_code=201)
async def create_consent_template(request:Request,body:ConsentTemplateCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"TEMPLATE_MANAGE")
    if denied:return denied
    now=datetime.now(timezone.utc);tid=uuid4();vid=uuid4();tenant=ctx["tenant_id"]
    await db.execute(text("INSERT INTO external_consent_templates(id,tenant_id,title,consent_type,profession_code,status,current_version,created_by,created_at,updated_at) VALUES (:id,:tenant,:title,:type,:profession,'DRAFT',1,:actor,:now,:now)"),{"id":tid,"tenant":tenant,"title":body.title,"type":body.consent_type,"profession":body.profession_code,"actor":ctx["user_id"],"now":now});await db.execute(text("INSERT INTO external_consent_template_versions(id,template_id,tenant_id,version,title,body,scope,required_signatories,effective_date,expires_after_days,status,created_by,created_at) VALUES (:id,:template,:tenant,1,:title,:body,CAST(:scope AS jsonb),CAST(:signatories AS jsonb),:effective,:expires,'DRAFT',:actor,:now)"),{"id":vid,"template":tid,"tenant":tenant,"title":body.title,"body":body.body,"scope":json.dumps(body.scope),"signatories":json.dumps(body.required_signatories),"effective":body.effective_date,"expires":body.expires_after_days,"actor":ctx["user_id"],"now":now});await db.commit();return {"success":True,"data":{"id":str(tid),"version":1,"status":"DRAFT"},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/consents/templates/{template_id}/publish")
async def publish_consent_template(request:Request,template_id:UUID,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    row=(await db.execute(text("SELECT id,current_version FROM external_consent_templates WHERE id=:id AND tenant_id=:tenant AND status='DRAFT'"),{"id":template_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not row:return error(request,404,"DRAFT_CONSENT_NOT_FOUND","Draft consent template not found")
    now=datetime.now(timezone.utc);await db.execute(text("UPDATE external_consent_template_versions SET status='PUBLISHED',published_at=:now WHERE template_id=:id AND tenant_id=:tenant AND version=:version"),{"now":now,"id":template_id,"tenant":ctx["tenant_id"],"version":row["current_version"]});await db.execute(text("UPDATE external_consent_templates SET status='PUBLISHED',updated_at=:now WHERE id=:id AND tenant_id=:tenant"),{"now":now,"id":template_id,"tenant":ctx["tenant_id"]});await db.commit();return {"success":True,"data":{"id":str(template_id),"status":"PUBLISHED"},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/consents/templates/{template_id}/assign",status_code=201)
async def assign_consent(request:Request,template_id:UUID,body:ConsentAssign,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"TEMPLATE_MANAGE",body.client_id)
    if denied:return denied
    row=(await db.execute(text("SELECT t.id,v.id version_id,v.scope,v.expires_after_days FROM external_consent_templates t JOIN external_consent_template_versions v ON v.template_id=t.id AND v.version=t.current_version WHERE t.id=:id AND t.tenant_id=:tenant AND t.status='PUBLISHED' AND v.status='PUBLISHED'"),{"id":template_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not row:return error(request,404,"PUBLISHED_CONSENT_NOT_FOUND","Published consent template not found")
    now=datetime.now(timezone.utc);rid=uuid4();expires=now+timedelta(days=row["expires_after_days"]) if row["expires_after_days"] else None
    await db.execute(text("INSERT INTO external_consent_records(id,tenant_id,client_id,template_id,template_version_id,status,scope,expires_at,assigned_by,created_at,updated_at) VALUES (:id,:tenant,:client,:template,:version,'PENDING',CAST(:scope AS jsonb),:expires,:actor,:now,:now)"),{"id":rid,"tenant":ctx["tenant_id"],"client":body.client_id,"template":template_id,"version":row["version_id"],"scope":json.dumps(row["scope"]),"expires":expires,"actor":ctx["user_id"],"now":now});await db.commit();return {"success":True,"data":{"id":str(rid),"status":"PENDING"},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/consents")
async def list_consents(request:Request,client_id:str|None=None,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    rows=(await db.execute(text("SELECT r.id,r.client_id,r.status,r.signatory_name,r.signature_method,r.scope,r.accepted_at,r.declined_at,r.revoked_at,r.expires_at,t.title,t.consent_type,v.version FROM external_consent_records r JOIN external_consent_templates t ON t.id=r.template_id JOIN external_consent_template_versions v ON v.id=r.template_version_id WHERE r.tenant_id=:tenant AND (CAST(:client AS text) IS NULL OR r.client_id=CAST(:client AS text)) ORDER BY r.created_at DESC"),{"tenant":ctx["tenant_id"],"client":client_id})).mappings().all();return {"success":True,"data":{"items":[dict(x) for x in rows]},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/consents/{record_id}/decision")
async def decide_consent(request:Request,record_id:UUID,body:ConsentDecision,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    row=(await db.execute(text("SELECT id,client_id,status FROM external_consent_records WHERE id=:id AND tenant_id=:tenant"),{"id":record_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not row:return error(request,404,"CONSENT_NOT_FOUND","Consent record not found")
    if row["status"]!='PENDING':return error(request,409,"CONSENT_ALREADY_DECIDED","Consent has already been decided")
    now=datetime.now(timezone.utc);status='ACCEPTED' if body.decision=='ACCEPT' else 'DECLINED';await db.execute(text("UPDATE external_consent_records SET status=:status,signatory_name=:name,signatory_type=:type,signature_method=:method,signature_evidence=CAST(:evidence AS jsonb),accepted_at=:accepted,declined_at=:declined,updated_at=:now WHERE id=:id AND tenant_id=:tenant"),{"status":status,"name":body.signatory_name,"type":body.signatory_type,"method":body.signature_method,"evidence":json.dumps(body.signature_evidence),"accepted":now if status=='ACCEPTED' else None,"declined":now if status=='DECLINED' else None,"now":now,"id":record_id,"tenant":ctx["tenant_id"]});await db.commit();return {"success":True,"data":{"id":str(record_id),"status":status,"classification":"ELECTRONIC_ACKNOWLEDGEMENT"},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/consents/{record_id}/revoke")
async def revoke_consent(request:Request,record_id:UUID,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    now=datetime.now(timezone.utc);result=await db.execute(text("UPDATE external_consent_records SET status='REVOKED',revoked_at=:now,updated_at=:now WHERE id=:id AND tenant_id=:tenant AND status='ACCEPTED'"),{"now":now,"id":record_id,"tenant":ctx["tenant_id"]})
    if result.rowcount!=1:return error(request,404,"ACTIVE_CONSENT_NOT_FOUND","Active consent not found")
    await db.commit();return {"success":True,"data":{"id":str(record_id),"status":"REVOKED","historic_evidence_preserved":True},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/documents")
async def list_documents(request:Request,client_id:str|None=None,category:str|None=None,status:str|None=None,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,principal=await _team_guard(request,db,ctx,"DOCUMENT_VIEW",client_id)
    if denied:return denied
    rows=(await db.execute(text("SELECT id,client_id,title,category,visibility,status,tags,current_version,created_by,created_at,updated_at FROM external_documents WHERE tenant_id=:tenant AND (CAST(:client AS text) IS NULL OR client_id=CAST(:client AS text)) AND (CAST(:category AS text) IS NULL OR category=CAST(:category AS text)) AND (CAST(:status AS text) IS NULL OR status=CAST(:status AS text)) ORDER BY updated_at DESC"),{"tenant":ctx["tenant_id"],"client":client_id,"category":category,"status":status})).mappings().all()
    if principal["role"]=="PRACTITIONER" and not principal["practice_wide_client_access"] and not principal["legacy_solo"]:
        assigned=set((await db.execute(text("SELECT client_id FROM external_client_team_assignments WHERE tenant_id=:tenant AND user_id=:user AND ended_at IS NULL"),{"tenant":ctx["tenant_id"],"user":ctx["user_id"]})).scalars().all())
        rows=[row for row in rows if row["client_id"] in assigned or row["created_by"]==ctx["user_id"]]
    rows=[row for row in rows if not (row["visibility"]=="PRACTITIONER_PRIVATE" and row["created_by"]!=ctx["user_id"] and "DOCUMENT_MANAGE" not in principal["permissions"])]
    rows=[row for row in rows if not (row["visibility"]=="PRACTICE_ADMINISTRATIVE" and "DOCUMENT_MANAGE" not in principal["permissions"])]
    return {"success":True,"data":{"items":[dict(x) for x in rows]},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/documents",status_code=201)
async def create_document(request:Request,body:DocumentCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"DOCUMENT_UPLOAD",body.client_id)
    if denied:return denied
    try:filename=validate_document(body.filename,body.content_type,body.size_bytes)
    except InvalidDocument as exc:return error(request,422,"DOCUMENT_VALIDATION_FAILED",str(exc),retryable=False)
    document_id=uuid4();version_id=uuid4();key=new_object_key(ctx["tenant_id"],document_id,version_id,filename)
    try:url=signed_upload(key,body.content_type,body.size_bytes)
    except StorageUnavailable as exc:return error(request,503,"DOCUMENT_STORAGE_NOT_CONFIGURED",str(exc),retryable=False)
    now=datetime.now(timezone.utc);await db.execute(text("INSERT INTO external_documents(id,tenant_id,client_id,title,category,visibility,status,tags,current_version,created_by,created_at,updated_at) VALUES (:id,:tenant,:client,:title,:category,:visibility,'PENDING_UPLOAD',CAST(:tags AS jsonb),1,:actor,:now,:now)"),{"id":document_id,"tenant":ctx["tenant_id"],"client":body.client_id,"title":body.title,"category":body.category,"visibility":body.visibility,"tags":json.dumps(body.tags),"actor":ctx["user_id"],"now":now});await db.execute(text("INSERT INTO external_document_versions(id,document_id,tenant_id,version,status,object_key,filename,content_type,size_bytes,checksum_sha256,uploaded_by,uploaded_at) VALUES (:id,:document,:tenant,1,'PENDING_UPLOAD',:key,:filename,:content_type,:size,:checksum,:actor,NULL)"),{"id":version_id,"document":document_id,"tenant":ctx["tenant_id"],"key":key,"filename":filename,"content_type":body.content_type,"size":body.size_bytes,"checksum":body.checksum_sha256,"actor":ctx["user_id"]})
    for link in body.links:
        if link.get("link_type") and link.get("linked_id"):await db.execute(text("INSERT INTO external_document_links(id,document_id,tenant_id,link_type,linked_id,created_at) VALUES (:id,:document,:tenant,:type,:linked,:now)"),{"id":uuid4(),"document":document_id,"tenant":ctx["tenant_id"],"type":link["link_type"],"linked":link["linked_id"],"now":now})
    await db.execute(text("INSERT INTO external_document_audit_events(id,document_id,tenant_id,event_type,actor_id,metadata,created_at) VALUES (:id,:document,:tenant,'UPLOAD_REQUESTED',:actor,CAST(:metadata AS jsonb),:now)"),{"id":uuid4(),"document":document_id,"tenant":ctx["tenant_id"],"actor":ctx["user_id"],"metadata":json.dumps({"version_id":str(version_id),"status":"PENDING_UPLOAD"}),"now":now})
    await db.commit();return {"success":True,"data":{"id":str(document_id),"version_id":str(version_id),"status":"PENDING_UPLOAD","upload":{"url":url,"method":"PUT","expires_in":600,"required_headers":{"Content-Type":body.content_type,"Content-Length":str(body.size_bytes)}},"object_key_exposed":False},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/documents/{document_id}/versions",status_code=201)
async def create_document_version(request:Request,document_id:UUID,body:DocumentVersionCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    document=(await db.execute(text("SELECT id,client_id,current_version,status FROM external_documents WHERE id=:id AND tenant_id=:tenant"),{"id":document_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not document:return error(request,404,"DOCUMENT_NOT_FOUND","Document not found")
    denied,_=await _team_guard(request,db,ctx,"DOCUMENT_UPLOAD",document["client_id"])
    if denied:return denied
    if document["status"] in {"ARCHIVED","QUARANTINED"}:return error(request,409,"DOCUMENT_VERSION_BLOCKED","Archived or quarantined documents cannot receive a new version")
    pending=(await db.execute(text("SELECT 1 FROM external_document_versions WHERE document_id=:id AND tenant_id=:tenant AND status='PENDING_UPLOAD' LIMIT 1"),{"id":document_id,"tenant":ctx["tenant_id"]})).scalar_one_or_none()
    if pending:return error(request,409,"DOCUMENT_UPLOAD_ALREADY_PENDING","Finish or reconcile the pending document version first")
    try:filename=validate_document(body.filename,body.content_type,body.size_bytes)
    except InvalidDocument as exc:return error(request,422,"DOCUMENT_VALIDATION_FAILED",str(exc),retryable=False)
    version=int(document["current_version"])+1;version_id=uuid4();key=new_object_key(ctx["tenant_id"],document_id,version_id,filename)
    try:url=signed_upload(key,body.content_type,body.size_bytes)
    except StorageUnavailable as exc:return error(request,503,"DOCUMENT_STORAGE_NOT_CONFIGURED",str(exc),retryable=False)
    await db.execute(text("INSERT INTO external_document_versions(id,document_id,tenant_id,version,status,object_key,filename,content_type,size_bytes,checksum_sha256,uploaded_by,uploaded_at) VALUES (:id,:document,:tenant,:version,'PENDING_UPLOAD',:key,:filename,:type,:size,:checksum,:actor,NULL)"),{"id":version_id,"document":document_id,"tenant":ctx["tenant_id"],"version":version,"key":key,"filename":filename,"type":body.content_type,"size":body.size_bytes,"checksum":body.checksum_sha256,"actor":ctx["user_id"]})
    await db.commit();return {"success":True,"data":{"id":str(document_id),"version_id":str(version_id),"version":version,"status":"PENDING_UPLOAD","upload":{"url":url,"method":"PUT","expires_in":600,"required_headers":{"Content-Type":body.content_type,"Content-Length":str(body.size_bytes)}},"object_key_exposed":False},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/documents/{document_id}/finalise")
async def finalise_document(request:Request,document_id:UUID,body:DocumentFinalise,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    row=(await db.execute(text("SELECT d.client_id,d.status,v.id version_id,v.version,v.status version_status,v.object_key,v.content_type,v.size_bytes,v.checksum_sha256 FROM external_documents d JOIN external_document_versions v ON v.document_id=d.id WHERE d.id=:id AND d.tenant_id=:tenant AND v.tenant_id=:tenant AND v.id=:version"),{"id":document_id,"tenant":ctx["tenant_id"],"version":body.version_id})).mappings().first()
    if not row:return error(request,404,"PENDING_DOCUMENT_NOT_FOUND","Pending document version not found")
    denied,_=await _team_guard(request,db,ctx,"DOCUMENT_UPLOAD",row["client_id"])
    if denied:return denied
    if row["version_status"]!="PENDING_UPLOAD":return error(request,409,"DOCUMENT_NOT_PENDING","Document version is not pending upload")
    try:verify_uploaded_object(row["object_key"],row["content_type"],row["size_bytes"],row["checksum_sha256"])
    except StorageUnavailable as exc:return error(request,503,"DOCUMENT_STORAGE_NOT_CONFIGURED",str(exc),retryable=False)
    except InvalidDocument as exc:return error(request,409,"DOCUMENT_UPLOAD_VERIFICATION_FAILED",str(exc),retryable=True)
    now=datetime.now(timezone.utc)
    await db.execute(text("UPDATE external_documents SET status='AVAILABLE',current_version=:number,updated_at=:now WHERE id=:id AND tenant_id=:tenant"),{"number":row["version"],"now":now,"id":document_id,"tenant":ctx["tenant_id"]})
    await db.execute(text("UPDATE external_document_versions SET status='AVAILABLE',uploaded_at=:now WHERE id=:version AND tenant_id=:tenant AND status='PENDING_UPLOAD'"),{"now":now,"version":body.version_id,"tenant":ctx["tenant_id"]})
    await db.execute(text("INSERT INTO external_document_audit_events(id,document_id,tenant_id,event_type,actor_id,metadata,created_at) VALUES (:id,:document,:tenant,'UPLOAD_VERIFIED',:actor,CAST(:metadata AS jsonb),:now)"),{"id":uuid4(),"document":document_id,"tenant":ctx["tenant_id"],"actor":ctx["user_id"],"metadata":json.dumps({"version_id":str(body.version_id),"status":"AVAILABLE"}),"now":now})
    await db.commit();return {"success":True,"data":{"id":str(document_id),"status":"AVAILABLE","source_report_analysis_triggered":False},"error":None,"request_id":request.state.correlation_id}

@app.patch("/api/v1/practice-operations/documents/{document_id}")
async def update_document(request:Request,document_id:UUID,body:DocumentUpdate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    result=await db.execute(text("UPDATE external_documents SET title=:title,category=:category,visibility=:visibility,tags=CAST(:tags AS jsonb),updated_at=:now WHERE id=:id AND tenant_id=:tenant"),{"title":body.title,"category":body.category,"visibility":body.visibility,"tags":json.dumps(body.tags),"now":datetime.now(timezone.utc),"id":document_id,"tenant":ctx["tenant_id"]})
    if result.rowcount!=1:return error(request,404,"DOCUMENT_NOT_FOUND","Document not found")
    await db.commit();return {"success":True,"data":{"id":str(document_id)},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/documents/{document_id}/download")
async def document_download_route(request:Request,document_id:UUID,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    return await document_download(request,document_id,ctx,db)

@app.post("/api/v1/practice-operations/documents/{document_id}/{action}")
async def document_state(request:Request,document_id:UUID,action:str,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"DOCUMENT_MANAGE")
    if denied:return denied
    transitions={"archive":("AVAILABLE","ARCHIVED"),"restore":("ARCHIVED","AVAILABLE"),"quarantine":(("AVAILABLE","ARCHIVED"),"QUARANTINED")}
    if action not in transitions:return error(request,400,"DOCUMENT_ACTION_INVALID","Unsupported document action")
    source,target=transitions[action];sources=source if isinstance(source,tuple) else (source,)
    result=await db.execute(text("UPDATE external_documents SET status=:status,updated_at=:now WHERE id=:id AND tenant_id=:tenant AND status=ANY(CAST(:sources AS text[]))"),{"status":target,"sources":list(sources),"now":datetime.now(timezone.utc),"id":document_id,"tenant":ctx["tenant_id"]})
    if result.rowcount!=1:return error(request,404,"DOCUMENT_NOT_FOUND","Document not found")
    if target=="QUARANTINED":await db.execute(text("UPDATE external_document_versions SET status='QUARANTINED' WHERE document_id=:id AND tenant_id=:tenant AND status='AVAILABLE'"),{"id":document_id,"tenant":ctx["tenant_id"]})
    await db.commit();return {"success":True,"data":{"id":str(document_id),"status":target},"error":None,"request_id":request.state.correlation_id}

async def document_download(request:Request,document_id:UUID,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    row=(await db.execute(text("SELECT d.id,d.client_id,d.visibility,d.status,d.created_by,v.object_key,v.filename FROM external_documents d JOIN external_document_versions v ON v.document_id=d.id AND v.version=d.current_version WHERE d.id=:id AND d.tenant_id=:tenant AND v.tenant_id=:tenant"),{"id":document_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not row:return error(request,404,"DOCUMENT_NOT_FOUND","Document not found")
    denied,principal=await _team_guard(request,db,ctx,"DOCUMENT_VIEW",row["client_id"])
    if denied:return denied
    if row["status"]!='AVAILABLE':return error(request,403,"DOCUMENT_NOT_AVAILABLE","Only available documents can be downloaded")
    if row["visibility"]=="PRACTITIONER_PRIVATE" and row.get("created_by")!=ctx["user_id"] and "DOCUMENT_MANAGE" not in principal["permissions"]:return error(request,403,"DOCUMENT_PRIVATE","Private document access denied")
    if row["visibility"]=="PRACTICE_ADMINISTRATIVE" and "DOCUMENT_MANAGE" not in principal["permissions"]:return error(request,403,"DOCUMENT_ADMINISTRATIVE","Administrative document access denied")
    try:url=signed_download(row["object_key"],row["filename"])
    except StorageUnavailable as exc:return error(request,503,"DOCUMENT_STORAGE_NOT_CONFIGURED",str(exc),retryable=False)
    now=datetime.now(timezone.utc);await db.execute(text("INSERT INTO external_document_access_events(id,document_id,tenant_id,event_type,actor_id,created_at) VALUES (:id,:document,:tenant,'DOWNLOADED',:actor,:now)"),{"id":uuid4(),"document":document_id,"tenant":ctx["tenant_id"],"actor":ctx["user_id"],"now":now});await db.commit();return {"success":True,"data":{"download_url":url,"expires_in":300},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/leads")
async def list_leads(request:Request,stage:str|None=None,search:str|None=None,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"CLIENT_LIST_VIEW")
    if denied:return denied
    rows=(await db.execute(text("""SELECT l.id,l.first_name,l.last_name,l.email,l.phone,l.source,l.stage,l.assigned_practitioner_id,l.next_follow_up_at,l.notes,l.converted_client_id,l.created_at,l.updated_at,(SELECT COUNT(*) FROM external_leads d WHERE d.tenant_id=l.tenant_id AND d.id<>l.id AND ((l.email_key IS NOT NULL AND d.email_key=l.email_key) OR (l.phone_key IS NOT NULL AND d.phone_key=l.phone_key))) duplicate_count FROM external_leads l WHERE l.tenant_id=:tenant AND (CAST(:stage AS text) IS NULL OR l.stage=CAST(:stage AS text)) AND (CAST(:search AS text) IS NULL OR CONCAT_WS(' ',l.first_name,l.last_name,l.email,l.phone) ILIKE '%'||CAST(:search AS text)||'%') ORDER BY l.updated_at DESC"""),{"tenant":ctx["tenant_id"],"stage":stage,"search":search})).mappings().all()
    return {"success":True,"data":{"items":[dict(row) for row in rows]},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/leads",status_code=201)
async def create_lead(request:Request,body:LeadCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"CLIENT_CREATE")
    if denied:return denied
    email_key,phone_key=normal_email(body.email),normal_phone(body.phone)
    if not email_key and not phone_key:return error(request,422,"LEAD_CONTACT_REQUIRED","An email address or phone number is required")
    duplicate=(await db.execute(text("SELECT id,first_name,last_name,stage FROM external_leads WHERE tenant_id=:tenant AND ((:email IS NOT NULL AND email_key=:email) OR (:phone IS NOT NULL AND phone_key=:phone)) ORDER BY updated_at DESC LIMIT 1"),{"tenant":ctx["tenant_id"],"email":email_key,"phone":phone_key})).mappings().first()
    if duplicate:return JSONResponse(status_code=409,content={"success":False,"error":{"code":"POSSIBLE_DUPLICATE_LEAD","safe_message":"A matching lead already exists in this practice.","duplicate":{"id":str(duplicate["id"]),"name":f'{duplicate["first_name"]} {duplicate["last_name"] or ""}'.strip(),"stage":duplicate["stage"]}}})
    lead_id=uuid4();now=datetime.now(timezone.utc);params={"id":lead_id,"tenant":ctx["tenant_id"],"first":body.first_name.strip(),"last":body.last_name,"email":body.email,"phone":body.phone,"email_key":email_key,"phone_key":phone_key,"source":body.source,"assigned":body.assigned_practitioner_id,"follow_up":body.next_follow_up_at,"notes":body.notes,"actor":ctx["user_id"],"now":now}
    await db.execute(text("INSERT INTO external_leads(id,tenant_id,first_name,last_name,email,phone,email_key,phone_key,source,stage,assigned_practitioner_id,next_follow_up_at,notes,created_by,created_at,updated_at) VALUES (:id,:tenant,:first,:last,:email,:phone,:email_key,:phone_key,:source,'NEW',:assigned,:follow_up,:notes,:actor,:now,:now)"),params)
    await db.execute(text("INSERT INTO external_lead_stage_history(id,lead_id,tenant_id,previous_stage,resulting_stage,actor_id,created_at) VALUES (:id,:lead,:tenant,NULL,'NEW',:actor,:now)"),{"id":uuid4(),"lead":lead_id,"tenant":ctx["tenant_id"],"actor":ctx["user_id"],"now":now});await db.commit()
    return {"success":True,"data":{"id":str(lead_id),"stage":"NEW"},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/leads/{lead_id}/stage")
async def update_lead_stage(request:Request,lead_id:UUID,body:LeadStageUpdate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"CLIENT_EDIT")
    if denied:return denied
    current=(await db.execute(text("SELECT stage FROM external_leads WHERE id=:id AND tenant_id=:tenant FOR UPDATE"),{"id":lead_id,"tenant":ctx["tenant_id"]})).scalar_one_or_none()
    if not current:return error(request,404,"LEAD_NOT_FOUND","Lead not found")
    try:assert_lead_transition(current,body.stage)
    except ValueError as exc:return error(request,409,"LEAD_TRANSITION_DENIED",str(exc))
    now=datetime.now(timezone.utc);await db.execute(text("UPDATE external_leads SET stage=:stage,updated_at=:now WHERE id=:id AND tenant_id=:tenant"),{"stage":body.stage,"now":now,"id":lead_id,"tenant":ctx["tenant_id"]});await db.execute(text("INSERT INTO external_lead_stage_history(id,lead_id,tenant_id,previous_stage,resulting_stage,reason,actor_id,created_at) VALUES (:id,:lead,:tenant,:previous,:resulting,:reason,:actor,:now)"),{"id":uuid4(),"lead":lead_id,"tenant":ctx["tenant_id"],"previous":current,"resulting":body.stage,"reason":body.reason,"actor":ctx["user_id"],"now":now});await db.commit()
    return {"success":True,"data":{"id":str(lead_id),"stage":body.stage},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/leads/{lead_id}/follow-ups",status_code=201)
async def create_lead_follow_up(request:Request,lead_id:UUID,body:LeadFollowUpCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"FOLLOWUP_MANAGE")
    if denied:return denied
    follow_id=uuid4();now=datetime.now(timezone.utc);result=await db.execute(text("INSERT INTO external_lead_follow_ups(id,lead_id,tenant_id,due_at,status,note,created_by,created_at) SELECT :id,id,:tenant,:due,'OPEN',:note,:actor,:now FROM external_leads WHERE id=:lead AND tenant_id=:tenant"),{"id":follow_id,"lead":lead_id,"tenant":ctx["tenant_id"],"due":body.due_at,"note":body.note,"actor":ctx["user_id"],"now":now})
    if result.rowcount!=1:return error(request,404,"LEAD_NOT_FOUND","Lead not found")
    await db.execute(text("UPDATE external_leads SET next_follow_up_at=:due,updated_at=:now WHERE id=:lead AND tenant_id=:tenant"),{"due":body.due_at,"now":now,"lead":lead_id,"tenant":ctx["tenant_id"]});await db.commit();return {"success":True,"data":{"id":str(follow_id)},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/leads/{lead_id}/convert")
async def convert_lead(request:Request,lead_id:UUID,body:LeadConvert,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"CLIENT_CREATE")
    if denied:return denied
    current=(await db.execute(text("SELECT stage FROM external_leads WHERE id=:id AND tenant_id=:tenant FOR UPDATE"),{"id":lead_id,"tenant":ctx["tenant_id"]})).scalar_one_or_none()
    if not current:return error(request,404,"LEAD_NOT_FOUND","Lead not found")
    if current!="CONSULTATION_BOOKED":return error(request,409,"LEAD_NOT_READY","Only a consultation-booked lead can be converted")
    now=datetime.now(timezone.utc);await db.execute(text("UPDATE external_leads SET stage='CONVERTED',converted_client_id=:client,updated_at=:now WHERE id=:id AND tenant_id=:tenant"),{"client":body.client_id,"now":now,"id":lead_id,"tenant":ctx["tenant_id"]});await db.execute(text("INSERT INTO external_lead_stage_history(id,lead_id,tenant_id,previous_stage,resulting_stage,reason,actor_id,created_at) VALUES (:id,:lead,:tenant,:previous,'CONVERTED','Created through existing Client Core',:actor,:now)"),{"id":uuid4(),"lead":lead_id,"tenant":ctx["tenant_id"],"previous":current,"actor":ctx["user_id"],"now":now});await db.commit();return {"success":True,"data":{"id":str(lead_id),"stage":"CONVERTED","client_id":body.client_id},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/communication/centre")
async def communication_centre(request:Request,client_id:str|None=None,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"COMMUNICATION_VIEW",client_id)
    if denied:return denied
    rows=(await db.execute(text("SELECT id,client_id,channel,purpose,subject,body,status,automation_id,created_at,updated_at FROM external_communication_preparations WHERE tenant_id=:tenant AND (CAST(:client AS text) IS NULL OR client_id=CAST(:client AS text)) ORDER BY created_at DESC LIMIT 200"),{"tenant":ctx["tenant_id"],"client":client_id})).mappings().all()
    reminders=(await db.execute(text("SELECT id,client_id,preparation_id,channel,due_at,status,automation_id,created_at FROM external_communication_reminders WHERE tenant_id=:tenant AND (CAST(:client AS text) IS NULL OR client_id=CAST(:client AS text)) ORDER BY due_at ASC LIMIT 200"),{"tenant":ctx["tenant_id"],"client":client_id})).mappings().all()
    return {"success":True,"data":{"items":[dict(row) for row in rows],"reminders":[dict(row) for row in reminders],"delivery_truth":"PREPARATION_ONLY"},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/communication/centre",status_code=201)
async def prepare_communication(request:Request,body:CommunicationPreparationCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"COMMUNICATION_PREPARE",body.client_id)
    if denied:return denied
    item_id=uuid4();now=datetime.now(timezone.utc);await db.execute(text("INSERT INTO external_communication_preparations(id,tenant_id,client_id,channel,purpose,subject,body,status,automation_id,created_by,created_at,updated_at) VALUES (:id,:tenant,:client,:channel,:purpose,:subject,:body,'PREPARED',:automation,:actor,:now,:now)"),{"id":item_id,"tenant":ctx["tenant_id"],"client":body.client_id,"channel":body.channel,"purpose":body.purpose,"subject":body.subject,"body":body.body,"automation":body.automation_id,"actor":ctx["user_id"],"now":now});await db.commit()
    return {"success":True,"data":{"id":str(item_id),"status":"PREPARED","sent":False,"delivered":False,"read":False},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/communication/reminders",status_code=201)
async def create_communication_reminder(request:Request,body:CommunicationReminderCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"COMMUNICATION_PREPARE",body.client_id)
    if denied:return denied
    item_id=uuid4();result=await db.execute(text("INSERT INTO external_communication_reminders(id,tenant_id,client_id,preparation_id,channel,due_at,status,automation_id,idempotency_key,created_by,created_at) VALUES (:id,:tenant,:client,:preparation,:channel,:due,'SCHEDULED',:automation,:key,:actor,:now) ON CONFLICT (tenant_id,idempotency_key) DO NOTHING"),{"id":item_id,"tenant":ctx["tenant_id"],"client":body.client_id,"preparation":body.preparation_id,"channel":body.channel,"due":body.due_at,"automation":body.automation_id,"key":body.idempotency_key,"actor":ctx["user_id"],"now":datetime.now(timezone.utc)})
    if result.rowcount!=1:return error(request,409,"REMINDER_ALREADY_EXISTS","This reminder was already scheduled")
    await db.commit();return {"success":True,"data":{"id":str(item_id),"status":"SCHEDULED","automation_execution":False},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/locations")
async def list_locations(request:Request,include_inactive:bool=False,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"PRACTICE_VIEW")
    if denied:return denied
    rows=(await db.execute(text("""SELECT l.id,l.code,l.name,l.address,l.timezone,l.phone,l.active,l.created_at,l.updated_at,COUNT(r.id) FILTER(WHERE r.resource_type='TEAM_MEMBER') team_members,COUNT(r.id) FILTER(WHERE r.resource_type='CLIENT') clients,COUNT(r.id) FILTER(WHERE r.resource_type='APPOINTMENT') appointments,COUNT(r.id) FILTER(WHERE r.resource_type='SERVICE') services,COUNT(r.id) FILTER(WHERE r.resource_type='INVOICE') invoices,COUNT(r.id) FILTER(WHERE r.resource_type='LEAD') leads FROM external_practice_locations l LEFT JOIN external_location_resource_links r ON r.location_id=l.id AND r.tenant_id=l.tenant_id WHERE l.tenant_id=:tenant AND (:inactive OR l.active=TRUE) GROUP BY l.id ORDER BY l.name"""),{"tenant":ctx["tenant_id"],"inactive":include_inactive})).mappings().all()
    return {"success":True,"data":{"items":[dict(row) for row in rows],"tenant_id":ctx["tenant_id"],"model":"ONE_TENANT_MULTI_LOCATION"},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/locations",status_code=201)
async def create_location(request:Request,body:PracticeLocationCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"PRACTICE_EDIT")
    if denied:return denied
    item_id=uuid4();now=datetime.now(timezone.utc);await db.execute(text("INSERT INTO external_practice_locations(id,tenant_id,code,name,address,timezone,phone,active,created_by,created_at,updated_at) VALUES (:id,:tenant,:code,:name,CAST(:address AS jsonb),:timezone,:phone,TRUE,:actor,:now,:now)"),{"id":item_id,"tenant":ctx["tenant_id"],"code":body.code,"name":body.name,"address":json.dumps(body.address),"timezone":body.timezone,"phone":body.phone,"actor":ctx["user_id"],"now":now});await db.commit();return {"success":True,"data":{"id":str(item_id),"tenant_id":ctx["tenant_id"]},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/locations/{location_id}/resources",status_code=201)
async def assign_location_resource(request:Request,location_id:UUID,body:LocationResourceAssign,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"PRACTICE_EDIT")
    if denied:return denied
    try:validate_resource_type(body.resource_type)
    except ValueError as exc:return error(request,422,"LOCATION_RESOURCE_INVALID",str(exc))
    exists=(await db.execute(text("SELECT 1 FROM external_practice_locations WHERE id=:id AND tenant_id=:tenant AND active=TRUE"),{"id":location_id,"tenant":ctx["tenant_id"]})).scalar_one_or_none()
    if not exists:return error(request,404,"LOCATION_NOT_FOUND","Active location not found")
    now=datetime.now(timezone.utc)
    if body.primary_location:await db.execute(text("UPDATE external_location_resource_links SET primary_location=FALSE WHERE tenant_id=:tenant AND resource_type=:type AND resource_id=:resource"),{"tenant":ctx["tenant_id"],"type":body.resource_type,"resource":body.resource_id})
    await db.execute(text("INSERT INTO external_location_resource_links(id,tenant_id,location_id,resource_type,resource_id,primary_location,created_by,created_at) VALUES (:id,:tenant,:location,:type,:resource,:primary,:actor,:now) ON CONFLICT (tenant_id,resource_type,resource_id,location_id) DO UPDATE SET primary_location=EXCLUDED.primary_location"),{"id":uuid4(),"tenant":ctx["tenant_id"],"location":location_id,"type":body.resource_type,"resource":body.resource_id,"primary":body.primary_location,"actor":ctx["user_id"],"now":now});await db.commit();return {"success":True,"data":{"location_id":str(location_id),"resource_type":body.resource_type,"resource_id":body.resource_id},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/payments/provider")
async def payment_provider_status(request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"BILLING_VIEW")
    if denied:return denied
    settings=get_settings();configured=settings.payment_provider=='RAZORPAY' and bool(settings.razorpay_key_id and settings.razorpay_key_secret and settings.razorpay_webhook_secret)
    return {"success":True,"data":{"provider":"RAZORPAY" if configured else None,"status":"CONFIGURED" if configured else "NOT_CONFIGURED","browser_success_authoritative":False},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/payments/orders",status_code=201)
async def create_payment_order(request:Request,body:PaymentOrderCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"BILLING_MANAGE")
    if denied:return denied
    settings=get_settings()
    if settings.payment_provider!='RAZORPAY' or not settings.razorpay_key_secret:return error(request,503,"PAYMENT_PROVIDER_NOT_CONFIGURED","Live payment provider is not configured")
    invoice=(await db.execute(text("SELECT id,client_id,balance_due_minor,currency,status FROM external_invoices WHERE id=:id AND tenant_id=:tenant AND status IN ('ISSUED','PART_PAID','OVERDUE')"),{"id":body.invoice_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not invoice:return error(request,404,"PAYABLE_INVOICE_NOT_FOUND","Payable invoice not found")
    order_id=uuid4();now=datetime.now(timezone.utc);await db.execute(text("INSERT INTO external_payment_orders(id,tenant_id,invoice_id,client_id,provider,amount_minor,currency,status,idempotency_key,created_by,created_at,updated_at) VALUES (:id,:tenant,:invoice,:client,'RAZORPAY',:amount,:currency,'CREATED',:key,:actor,:now,:now) ON CONFLICT (tenant_id,idempotency_key) DO NOTHING"),{"id":order_id,"tenant":ctx["tenant_id"],"invoice":invoice["id"],"client":invoice["client_id"],"amount":invoice["balance_due_minor"],"currency":invoice["currency"],"key":body.idempotency_key,"actor":ctx["user_id"],"now":now});await db.commit();return {"success":True,"data":{"id":str(order_id),"status":"CREATED","provider_order_created":False},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/payments/orders/{order_id}/verify")
async def verify_payment(request:Request,order_id:UUID,body:PaymentVerification,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"PAYMENT_RECORD")
    if denied:return denied
    order=(await db.execute(text("SELECT id,provider_order_id,status FROM external_payment_orders WHERE id=:id AND tenant_id=:tenant"),{"id":order_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not order or order["provider_order_id"]!=body.provider_order_id:return error(request,404,"PAYMENT_ORDER_NOT_FOUND","Payment order not found")
    try:valid=verify_razorpay_payment(body.provider_order_id,body.provider_payment_id,body.signature,get_settings().razorpay_key_secret)
    except PaymentProviderNotConfigured as exc:return error(request,503,"PAYMENT_PROVIDER_NOT_CONFIGURED",str(exc))
    if not valid:return error(request,403,"PAYMENT_SIGNATURE_INVALID","Payment verification failed")
    now=datetime.now(timezone.utc);await db.execute(text("INSERT INTO external_payment_attempts(id,tenant_id,order_id,provider_payment_id,status,verification_evidence,created_at,verified_at) VALUES (:id,:tenant,:order,:payment,'VERIFIED',CAST(:evidence AS jsonb),:now,:now) ON CONFLICT (tenant_id,provider_payment_id) DO NOTHING"),{"id":uuid4(),"tenant":ctx["tenant_id"],"order":order_id,"payment":body.provider_payment_id,"evidence":json.dumps({"signature_valid":True}),"now":now});await db.execute(text("UPDATE external_payment_orders SET status='AUTHORISED',updated_at=:now WHERE id=:id AND tenant_id=:tenant"),{"now":now,"id":order_id,"tenant":ctx["tenant_id"]});await db.commit();return {"success":True,"data":{"id":str(order_id),"status":"AUTHORISED","invoice_reconciled":False},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/payments/orders/{order_id}")
async def lookup_payment(request:Request,order_id:UUID,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"BILLING_VIEW")
    if denied:return denied
    row=(await db.execute(text("SELECT id,invoice_id,client_id,provider,provider_order_id,amount_minor,currency,status,created_at,updated_at FROM external_payment_orders WHERE id=:id AND tenant_id=:tenant"),{"id":order_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not row:return error(request,404,"PAYMENT_ORDER_NOT_FOUND","Payment order not found")
    return {"success":True,"data":dict(row),"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/payments/webhooks/razorpay")
async def razorpay_webhook(request:Request,x_razorpay_signature:str|None=Header(None),db:AsyncSession=Depends(get_db)):
    payload=await request.body();settings=get_settings()
    try:valid=verify_razorpay_webhook(payload,x_razorpay_signature or '',settings.razorpay_webhook_secret)
    except PaymentProviderNotConfigured as exc:return error(request,503,"PAYMENT_PROVIDER_NOT_CONFIGURED",str(exc))
    if not valid:return error(request,403,"PAYMENT_WEBHOOK_SIGNATURE_INVALID","Webhook verification failed")
    try:event=json.loads(payload);event_id=str(event.get('event_id') or event.get('id') or canonical_payload_hash(payload))[:200]
    except (ValueError,TypeError):return error(request,400,"PAYMENT_WEBHOOK_INVALID","Webhook payload is invalid")
    result=await db.execute(text("INSERT INTO external_payment_webhook_events(id,provider,provider_event_id,payload_hash,signature_valid,processed,received_at) VALUES (:id,'RAZORPAY',:event,:hash,TRUE,FALSE,:now) ON CONFLICT (provider,provider_event_id) DO NOTHING"),{"id":uuid4(),"event":event_id,"hash":canonical_payload_hash(payload),"now":datetime.now(timezone.utc)})
    await db.commit();return {"success":True,"data":{"accepted":True,"replay":result.rowcount!=1,"processed":False},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/ai-copilot/status")
async def ai_copilot_status(request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"PRACTICE_VIEW")
    if denied:return denied
    provider=get_settings().ai_runtime_provider
    return {"success":True,"data":{"provider":provider,"status":"CONFIGURED" if provider else "NOT_CONFIGURED","classification":"AI_DRAFT","autonomous_actions":False},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/ai-copilot/drafts",status_code=201)
async def create_ai_draft(request:Request,body:AiDraftRequest,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"PRACTICE_EDIT",body.client_id)
    if denied:return denied
    try:validate_ai_request(body.purpose,body.instruction)
    except ValueError as exc:return error(request,422,"AI_REQUEST_OUT_OF_SCOPE",str(exc))
    provider=get_settings().ai_runtime_provider
    if not provider:return error(request,503,"AI_RUNTIME_NOT_CONFIGURED","AI runtime provider is not configured")
    request_id=uuid4();now=datetime.now(timezone.utc);await db.execute(text("INSERT INTO external_ai_draft_requests(id,tenant_id,client_id,purpose,instruction,source_references,status,requested_by,created_at) VALUES (:id,:tenant,:client,:purpose,:instruction,CAST(:sources AS jsonb),'PENDING',:actor,:now)"),{"id":request_id,"tenant":ctx["tenant_id"],"client":body.client_id,"purpose":body.purpose,"instruction":body.instruction,"sources":json.dumps(body.source_references),"actor":ctx["user_id"],"now":now});await db.commit()
    return {"success":True,"data":{"id":str(request_id),**classify_output(''),"status":"PENDING","provider_execution":"QUEUED"},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/compliance/audit")
async def compliance_audit(request:Request,client_id:str|None=None,limit:int=Query(100,ge=1,le=500),ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"SETTINGS_VIEW",client_id)
    if denied:return denied
    params={"tenant":ctx["tenant_id"],"client":client_id,"limit":limit}
    rows=(await db.execute(text("""SELECT domain,event_type,actor_id,resource_id,created_at FROM (
      SELECT 'CONSENT' domain,a.event_type,a.actor_id,COALESCE(a.consent_record_id::text,a.template_id::text) resource_id,a.created_at FROM external_consent_audit_events a WHERE a.tenant_id=:tenant AND (CAST(:client AS text) IS NULL OR EXISTS (SELECT 1 FROM external_consent_records r WHERE r.id=a.consent_record_id AND r.tenant_id=:tenant AND r.client_id=CAST(:client AS text)))
      UNION ALL SELECT 'PORTAL',event_type,COALESCE(actor_type,'UNKNOWN'),resource_id,created_at FROM external_client_portal_audit_events WHERE tenant_id=:tenant AND (CAST(:client AS text) IS NULL OR client_id=CAST(:client AS text))
      UNION ALL SELECT 'TEAM',event_type,actor_id,COALESCE(target_user_id,client_id),created_at FROM external_team_audit_events WHERE tenant_id=:tenant AND (CAST(:client AS text) IS NULL OR client_id=CAST(:client AS text))
      UNION ALL SELECT 'BILLING',a.event_type,a.actor_id,COALESCE(a.invoice_id::text,a.payment_id::text),a.created_at FROM external_invoice_audit_events a WHERE a.tenant_id=:tenant AND (CAST(:client AS text) IS NULL OR EXISTS (SELECT 1 FROM external_invoices i WHERE i.id=a.invoice_id AND i.tenant_id=:tenant AND i.client_id=CAST(:client AS text)))
      UNION ALL SELECT 'DOCUMENT',a.event_type,a.actor_id,a.document_id::text,a.created_at FROM external_document_audit_events a WHERE a.tenant_id=:tenant AND (CAST(:client AS text) IS NULL OR EXISTS (SELECT 1 FROM external_documents d WHERE d.id=a.document_id AND d.tenant_id=:tenant AND d.client_id=CAST(:client AS text)))
      UNION ALL SELECT 'REFERRAL',e.event_type,COALESCE(e.actor_id,'UNKNOWN'),e.referral_id::text,e.created_at FROM external_referral_events e WHERE e.tenant_id=:tenant AND (CAST(:client AS text) IS NULL OR EXISTS (SELECT 1 FROM external_referrals r WHERE r.id=e.referral_id AND r.tenant_id=:tenant AND r.client_id=CAST(:client AS text)))
      UNION ALL SELECT 'AUTOMATION',a.event_type,a.actor_id,COALESCE(a.automation_id::text,a.execution_id::text),a.created_at FROM external_automation_audit_events a WHERE a.tenant_id=:tenant AND (CAST(:client AS text) IS NULL OR EXISTS (SELECT 1 FROM external_automation_executions e WHERE e.id=a.execution_id AND e.tenant_id=:tenant AND e.client_id=CAST(:client AS text)))
      UNION ALL SELECT 'AI',a.event_type,a.actor_id,COALESCE(a.output_id::text,a.request_id::text),a.created_at FROM external_ai_audit_events a WHERE a.tenant_id=:tenant AND (CAST(:client AS text) IS NULL OR EXISTS (SELECT 1 FROM external_ai_draft_requests r WHERE r.id=a.request_id AND r.tenant_id=:tenant AND r.client_id=CAST(:client AS text)))
      UNION ALL SELECT 'COMPLIANCE',event_type,actor_id,resource_id,created_at FROM external_compliance_audit_events WHERE tenant_id=:tenant AND (CAST(:client AS text) IS NULL OR client_id=CAST(:client AS text))
    ) evidence ORDER BY created_at DESC LIMIT :limit"""),params)).mappings().all()
    return {"success":True,"data":{"items":[dict(row) for row in rows],"classification":"OPERATIONAL_AUDIT_EVIDENCE","legal_compliance_certification":False},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/compliance/exports/clients/{client_id}",status_code=201)
async def export_client_data(request:Request,client_id:str,body:ClientExportRequest,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"CLIENT360_VIEW",client_id)
    if denied:return denied
    try:sections=validate_export_sections(body.sections)
    except ValueError as exc:return error(request,422,"EXPORT_SCOPE_DENIED",str(exc))
    params={"tenant":ctx["tenant_id"],"client":client_id};payload={"client_id":client_id,"sections":{},"excluded":sorted(EXCLUDED_BY_DEFAULT)}
    queries={
      'CONSENTS':"SELECT id,status,scope,accepted_at,declined_at,revoked_at,expires_at,created_at FROM external_consent_records WHERE tenant_id=:tenant AND client_id=:client",
      'PORTAL_ACTIVITY':"SELECT event_type,resource_type,resource_id,created_at FROM external_client_portal_audit_events WHERE tenant_id=:tenant AND client_id=:client AND actor_type='CLIENT'",
      'BILLING':"SELECT id,invoice_number,status,currency,grand_total_minor,amount_paid_minor,balance_due_minor,issue_date,due_date FROM external_invoices WHERE tenant_id=:tenant AND client_id=:client",
      'DOCUMENTS':"SELECT id,title,category,visibility,status,current_version,created_at,updated_at FROM external_documents WHERE tenant_id=:tenant AND client_id=:client",
      'REFERRALS':"SELECT id,receiving_profession_code,destination_name,reason,status,created_at,updated_at FROM external_referrals WHERE tenant_id=:tenant AND client_id=:client",
      'AUTOMATIONS':"SELECT r.action_type,r.status,r.result_summary,r.created_at FROM external_automation_action_results r JOIN external_automation_executions e ON e.id=r.execution_id AND e.tenant_id=r.tenant_id WHERE r.tenant_id=:tenant AND e.client_id=:client",
      'AI_DRAFTS':"SELECT id,purpose,status,created_at,completed_at FROM external_ai_draft_requests WHERE tenant_id=:tenant AND client_id=:client",
      'FORMS':"SELECT id,status,due_at,assigned_at,started_at,completed_at FROM external_form_assignments WHERE tenant_id=:tenant AND client_id=:client",
      'GOALS':"SELECT id,title,status,due_at,created_at,updated_at FROM practice_goals WHERE tenant_id=:tenant AND client_id=:client",
      'TASKS':"SELECT id,title,status,due_at,created_at,updated_at FROM practice_tasks WHERE tenant_id=:tenant AND client_id=:client",
      'APPOINTMENTS':"SELECT id,title,status,due_at,created_at,updated_at FROM practice_consultations WHERE tenant_id=:tenant AND client_id=:client",
      'PROGRESS':"SELECT id,numeric_value,text_value,source_type,observed_at,created_at FROM external_progress_observations WHERE tenant_id=:tenant AND client_id=:client",
    }
    for section in sections:payload["sections"][section]=[dict(row) for row in (await db.execute(text(queries[section]),params)).mappings().all()]
    export_id=uuid4();now=datetime.now(timezone.utc);checksum_value=export_checksum(payload);await db.execute(text("INSERT INTO external_data_export_requests(id,tenant_id,client_id,sections,status,private_notes_included,requested_by,created_at,completed_at,content_checksum) VALUES (:id,:tenant,:client,CAST(:sections AS jsonb),'COMPLETED',FALSE,:actor,:now,:now,:checksum)"),{"id":export_id,"tenant":ctx["tenant_id"],"client":client_id,"sections":json.dumps(sections),"actor":ctx["user_id"],"now":now,"checksum":checksum_value});await db.execute(text("INSERT INTO external_compliance_audit_events(id,tenant_id,client_id,event_type,actor_id,resource_type,resource_id,metadata,created_at) VALUES (:id,:tenant,:client,'CLIENT_EXPORT_CREATED',:actor,'EXPORT',:resource,CAST(:metadata AS jsonb),:now)"),{"id":uuid4(),"tenant":ctx["tenant_id"],"client":client_id,"actor":ctx["user_id"],"resource":str(export_id),"metadata":json.dumps({"sections":sections,"private_notes_included":False}),"now":now});await db.commit();return {"success":True,"data":{"id":str(export_id),"checksum":checksum_value,"private_notes_included":False,"payload":payload},"error":None,"request_id":request.state.correlation_id}


@app.get("/api/v1/practice-operations/dashboard/command-centre")
async def dashboard_command_centre(request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    """Bounded, tenant-scoped operational read model. Sections fail independently."""
    denied=external_only(request,ctx)
    if denied:return denied
    principal=await _team_principal(db,ctx)
    if principal["status"]!="ACTIVE":return error(request,403,"TEAM_MEMBERSHIP_INACTIVE","Practice membership is not active")
    permissions=set(principal["permissions"]);tenant=ctx["tenant_id"];actor=ctx["user_id"]
    practice_wide=bool(principal["practice_wide_client_access"] or principal["legacy_solo"] or principal["role"] in {"PRACTICE_OWNER","PRACTICE_ADMIN","RECEPTIONIST"})
    visit=(await db.execute(text("SELECT dashboard_last_seen_at FROM external_consultant_dashboard_state WHERE tenant_id=:tenant AND user_id=:actor"),{"tenant":tenant,"actor":actor})).mappings().first()
    request_started_at=datetime.now(timezone.utc)
    last_seen_at=visit["dashboard_last_seen_at"] if visit else request_started_at-timedelta(days=7)
    params={"tenant":tenant,"actor":actor,"practice_wide":practice_wide,"last_seen":last_seen_at}

    async def read(name,sql,*,allowed=True):
        if not allowed:return command_section([],restricted=True)
        try:
            async with db.begin_nested(): rows=(await db.execute(text(sql),params)).mappings().all()
            return command_section([dict(row) for row in rows])
        except Exception as exc:
            logger.warning("command_centre_section_failed",section=name,error_type=type(exc).__name__)
            return command_section([],failed=True)

    scope="(:practice_wide OR EXISTS (SELECT 1 FROM external_client_team_assignments ca WHERE ca.tenant_id=:tenant AND ca.client_id=q.client_id AND ca.user_id=:actor AND ca.ended_at IS NULL))"
    schedule=await read("schedule",f"""SELECT q.id::text,q.client_id,q.starts_at AS due_at,q.ends_at,q.status,
      q.attendance_status,t.name AS title,t.location_type,t.location_details
      FROM external_scheduled_appointments q JOIN external_appointment_types t ON t.id=q.appointment_type_id AND t.tenant_id=q.tenant_id
      WHERE q.tenant_id=:tenant AND q.starts_at>=date_trunc('day',NOW()) AND q.starts_at<date_trunc('day',NOW())+INTERVAL '1 day'
      AND q.status NOT IN ('CANCELLED') AND {scope} ORDER BY q.starts_at LIMIT 20""",allowed="CALENDAR_VIEW" in permissions)
    work=await read("my_work",f"""SELECT id,client_id,title,status,due_at,updated_at,source_module FROM (
      SELECT q.id::text,q.client_id,q.title,q.status,q.due_at,q.updated_at,'TASK' source_module FROM practice_tasks q
      WHERE q.tenant_id=:tenant AND q.status NOT IN ('COMPLETED','CANCELLED') AND {scope}
      UNION ALL SELECT q.id::text,q.client_id,q.title,q.status,q.due_at,q.updated_at,'FOLLOW_UP' source_module FROM practice_follow_ups q
      WHERE q.tenant_id=:tenant AND q.status NOT IN ('COMPLETED','CANCELLED') AND {scope}
      UNION ALL SELECT q.id::text,q.client_id,q.title,q.status,q.due_date::timestamptz,q.updated_at,'HOMEWORK' source_module FROM external_homework_assignments q
      WHERE q.tenant_id=:tenant AND q.status IN ('NOT_STARTED','IN_PROGRESS','MISSED') AND {scope}
      UNION ALL SELECT q.id::text,q.client_id,q.title,q.status,q.period_end::timestamptz,q.updated_at,'REPORT' source_module FROM external_progress_reports q
      WHERE q.tenant_id=:tenant AND q.status IN ('DRAFT','GENERATED') AND {scope}
      UNION ALL SELECT q.id::text,q.client_id,q.title,q.status,q.due_at,q.updated_at,'TASK' source_module FROM practice_tasks q
      WHERE q.tenant_id=:tenant AND q.status='COMPLETED' AND q.updated_at>=NOW()-INTERVAL '7 days' AND {scope}
      UNION ALL SELECT q.id::text,q.client_id,q.title,q.status,q.due_at,q.updated_at,'FOLLOW_UP' source_module FROM practice_follow_ups q
      WHERE q.tenant_id=:tenant AND q.status='COMPLETED' AND q.updated_at>=NOW()-INTERVAL '7 days' AND {scope}
    ) work_items ORDER BY due_at NULLS LAST,updated_at DESC LIMIT 40""",allowed=bool({"TASK_VIEW","FOLLOWUP_VIEW","RESOURCE_VIEW","REPORT_VIEW"}&permissions))
    if work["status"] in {"READY","CONFIRMED_EMPTY"} and not work.get("restricted"):
        mapped=[]
        for row in work["items"]:
            signal=f"{row['source_module']}_OVERDUE" if row.get("status")!="COMPLETED" and row.get("due_at") and row["due_at"]<datetime.now(timezone.utc) else row["source_module"]
            mapped.append({**row,"signal":signal,"priority":operational_priority(row.get("due_at"),signal),"action":next_action(signal)})
        work["items"]=sort_work(mapped)
    attention=await read("clients_needing_attention",f"""SELECT id,client_id,signal,context,due_at FROM (
      SELECT q.id::text,q.client_id,'FOLLOWUP_OVERDUE' signal,'Follow-up is overdue' context,q.due_at FROM practice_follow_ups q WHERE q.tenant_id=:tenant AND q.status NOT IN ('COMPLETED','CANCELLED') AND q.due_at<NOW() AND {scope}
      UNION ALL SELECT q.id::text,q.client_id,'TASK_OVERDUE','Task is overdue',q.due_at FROM practice_tasks q WHERE q.tenant_id=:tenant AND q.status NOT IN ('COMPLETED','CANCELLED') AND q.due_at<NOW() AND {scope}
      UNION ALL SELECT q.id::text,q.client_id,'HOMEWORK_OVERDUE','Homework needs review',q.due_date::timestamptz FROM external_homework_assignments q WHERE q.tenant_id=:tenant AND q.status IN ('NOT_STARTED','IN_PROGRESS','MISSED') AND q.due_date<CURRENT_DATE AND {scope}
      UNION ALL SELECT q.id::text,q.client_id,'CONSENT_PENDING','Consent is pending',q.expires_at FROM external_consent_records q WHERE q.tenant_id=:tenant AND q.status='PENDING' AND {scope}
      UNION ALL SELECT q.id::text,q.client_id,'INVOICE_OVERDUE','Invoice has an overdue balance',q.due_date::timestamptz FROM external_invoices q WHERE q.tenant_id=:tenant AND q.status IN ('ISSUED','PART_PAID','OVERDUE') AND q.balance_due_minor>0 AND q.due_date<CURRENT_DATE AND {scope}
      UNION ALL SELECT q.id::text,q.client_id,'REPORT_PENDING','Progress report remains incomplete',q.period_end::timestamptz FROM external_progress_reports q WHERE q.tenant_id=:tenant AND q.status IN ('DRAFT','GENERATED') AND {scope}
      UNION ALL SELECT q.id::text,q.client_id,'REFERRAL_PENDING','Referral needs an operational decision',q.updated_at FROM external_referrals q WHERE q.tenant_id=:tenant AND q.status IN ('DRAFT','CONSENT_PENDING','READY_TO_SEND','SENT') AND {scope}
      UNION ALL SELECT q.id::text,q.client_id,'MISSED_APPOINTMENT','Appointment was missed',q.starts_at FROM external_scheduled_appointments q WHERE q.tenant_id=:tenant AND (q.status='NO_SHOW' OR q.attendance_status='NO_SHOW') AND q.starts_at>=NOW()-INTERVAL '30 days' AND {scope}
      UNION ALL SELECT q.id::text,q.client_id,'ONBOARDING_INCOMPLETE','Configured onboarding remains incomplete',q.updated_at FROM external_client_intake_instances q WHERE q.tenant_id=:tenant AND q.status NOT IN ('COMPLETED','REVOKED') AND q.completion_percent<100 AND {scope}
      UNION ALL SELECT q.id::text,q.client_id,'DOCUMENT_PENDING','Document upload or review remains incomplete',q.updated_at FROM external_documents q WHERE q.tenant_id=:tenant AND q.status IN ('PENDING_UPLOAD','UPLOAD_FAILED','QUARANTINED') AND q.visibility<>'PRACTITIONER_PRIVATE' AND {scope}
      UNION ALL SELECT q.id::text,q.client_id,'NO_FUTURE_APPOINTMENT','No future appointment is booked',q.updated_at FROM external_client_packages q WHERE q.tenant_id=:tenant AND q.status='ACTIVE' AND NOT EXISTS (SELECT 1 FROM external_scheduled_appointments a WHERE a.tenant_id=q.tenant_id AND a.client_id=q.client_id AND a.starts_at>NOW() AND a.status IN ('BOOKED','CONFIRMED')) AND {scope}
      UNION ALL SELECT q.id::text,q.client_id,'FEEDBACK_NEEDS_ATTENTION','Private client feedback needs a response',q.updated_at FROM external_client_feedback_requests q WHERE q.tenant_id=:tenant AND q.status='ACTION_REQUIRED' AND {scope}
    ) signals ORDER BY due_at NULLS LAST LIMIT 30""",allowed="CLIENT_LIST_VIEW" in permissions)
    if attention["status"] in {"READY","CONFIRMED_EMPTY"} and not attention.get("restricted"):
        attention["items"]=[{**row,"priority":operational_priority(row.get("due_at"),row["signal"]),"action":next_action(row["signal"])} for row in attention["items"]]
    onboarding=await read("onboarding",f"""SELECT q.id::text,q.client_id,q.status,q.completion_percent,q.updated_at,
      CASE WHEN q.completion_percent=100 THEN 'READY_FOR_CONSULTATION' ELSE 'ONBOARDING_INCOMPLETE' END signal
      FROM external_client_intake_instances q WHERE q.tenant_id=:tenant AND q.status NOT IN ('REVOKED') AND {scope}
      ORDER BY q.updated_at DESC LIMIT 20""",allowed="CLIENT_LIST_VIEW" in permissions)
    preconsultation=command_section([],restricted="CLIENT_LIST_VIEW" not in permissions)
    if "CLIENT_LIST_VIEW" in permissions:
        try:
            async with db.begin_nested():
                checklist_rows=(await db.execute(text(f"""SELECT q.* FROM external_preconsultation_checklists q
                  WHERE q.tenant_id=:tenant AND q.lifecycle_state<>'PAUSED' AND {scope}
                  ORDER BY q.updated_at DESC LIMIT 20"""),params)).mappings().all()
                projected=[]
                for checklist in checklist_rows:
                    item=await _preconsultation_projection(db,tenant,checklist["client_id"],checklist)
                    blocker_signals={"CONSENT_PENDING":"CONSENT_PENDING_BEFORE_SESSION","REQUIRED_INTAKE_PENDING":"INTAKE_PENDING_BEFORE_SESSION","REQUIRED_DOCUMENT_PENDING":"DOCUMENT_PENDING_BEFORE_SESSION"}
                    signals=[blocker_signals.get(value,"PRE_CONSULTATION_INCOMPLETE") for value in item["blockers"]]
                    if item["readyForConsultation"]:signals=["READY_FOR_CONSULTATION"]
                    elif item["readinessPercent"]==0:signals.insert(0,"NEW_CLIENT_ONBOARDING_STARTED")
                    if not signals:signals=["PRE_CONSULTATION_INCOMPLETE"]
                    appointment_item=next((value for value in item["items"] if value["key"]=="APPOINTMENT"),{})
                    due_at=datetime.fromisoformat(appointment_item["detail"]) if appointment_item.get("detail") else None
                    if due_at and due_at<=datetime.now(timezone.utc)+timedelta(hours=24) and not item["readyForConsultation"]:
                        signals.insert(0,"APPOINTMENT_APPROACHING_ONBOARDING_INCOMPLETE")
                    item.update({"client_id":item["clientId"],"due_at":due_at,"signals":list(dict.fromkeys(signals)),"signal":signals[0],
                      "priority":operational_priority(due_at,signals[0]),"action":next_action(signals[0])})
                    projected.append(item)
                preconsultation=command_section(projected)
        except Exception as exc:
            logger.warning("command_centre_section_failed",section="preconsultation",error_type=type(exc).__name__)
            preconsultation=command_section([],failed=True)
    post_session=command_section([],restricted="CLIENT_LIST_VIEW" not in permissions)
    if "CLIENT_LIST_VIEW" in permissions:
        try:
            async with db.begin_nested():
                rows=(await db.execute(text(f"""SELECT q.id,q.tenant_id,q.client_id,q.consultation_id,q.session_note_id,q.profession_code,q.service_id,q.client_package_id,q.lifecycle_state,q.action_requirements,q.started_at,q.operationally_closed_at,q.created_by,q.created_at,q.updated_at
                  FROM external_post_session_checklists q WHERE q.tenant_id=:tenant AND q.lifecycle_state<>'PAUSED' AND {scope}
                  ORDER BY q.updated_at DESC LIMIT 20"""),params)).mappings().all()
                projected=[]
                for row in rows:
                    item=await _post_session_projection(db,tenant,row)
                    next_item=next((value for value in item["items"] if value["key"]=="NEXT_APPOINTMENT"),{})
                    signals=[]
                    if not item["sessionOperationallyClosed"]:signals.append("POST_SESSION_ACTIONS_PENDING")
                    if next_item.get("status")=="PENDING":signals.append("NO_FUTURE_SESSION")
                    if item.get("package") and item["package"].get("sessions_remaining",99)<=2:signals.append("SESSIONS_LOW")
                    if item["sessionOperationallyClosed"]:signals.append("SESSION_OPERATIONALLY_CLOSED")
                    item.update({"client_id":item["clientId"],"signal":signals[0],"signals":signals,"priority":operational_priority(row["updated_at"],signals[0]),"action":next_action(signals[0])})
                    projected.append(item)
                post_session=command_section(projected)
        except Exception as exc:
            logger.warning("command_centre_section_failed",section="post_session",error_type=type(exc).__name__)
            post_session=command_section([],failed=True)
    recent=await read("recent_changes",f"""SELECT id,client_id,event_type,title,created_at FROM (
      SELECT q.id::text,q.client_id,q.event_type,q.title,q.created_at FROM practice_notifications q
        WHERE q.tenant_id=:tenant AND q.created_at>:last_seen AND {scope}
      UNION ALL SELECT q.id::text,q.client_id,q.event_type,'Client portal activity',q.created_at FROM external_client_portal_audit_events q
        WHERE q.tenant_id=:tenant AND q.created_at>:last_seen AND q.actor_type='CLIENT' AND {scope}
      UNION ALL SELECT q.id::text,q.client_id,'DOCUMENT_UPDATED',q.title,q.updated_at FROM external_documents q
        WHERE q.tenant_id=:tenant AND q.updated_at>:last_seen AND q.visibility<>'PRACTITIONER_PRIVATE' AND {scope}
      UNION ALL SELECT q.id::text,q.client_id,q.event_type,'Post-session activity',q.created_at FROM external_post_session_events q
        WHERE q.tenant_id=:tenant AND q.created_at>:last_seen AND {scope}
      UNION ALL SELECT q.id::text,q.client_id,q.event_type,'Private client feedback',q.created_at FROM external_client_feedback_audit_events q
        WHERE q.tenant_id=:tenant AND q.created_at>:last_seen AND {scope}
    ) changes ORDER BY created_at DESC LIMIT 20""",allowed="PRACTICE_VIEW" in permissions or "CLIENT_LIST_VIEW" in permissions)
    leads=await read("leads",f"""SELECT q.id::text,NULL::varchar client_id,(q.first_name||COALESCE(' '||q.last_name,'')) title,q.stage,q.next_follow_up_at AS due_at,q.updated_at,
      CASE WHEN q.stage='NEW' THEN 'NEW_LEAD' WHEN q.next_follow_up_at<NOW() THEN 'LEAD_FOLLOWUP_OVERDUE' ELSE 'LEAD_FOLLOWUP' END signal
      FROM external_leads q WHERE q.tenant_id=:tenant AND q.stage NOT IN ('CONVERTED','NOT_INTERESTED','LOST')
      ORDER BY q.next_follow_up_at NULLS LAST,q.updated_at DESC LIMIT 15""",allowed=principal["role"] in {"PRACTICE_OWNER","PRACTICE_ADMIN","PRACTITIONER","RECEPTIONIST"})
    renewals=await read("renewals",f"""SELECT q.id::text,q.client_id,p.name title,q.status,q.end_date::timestamptz due_at,q.renewal_date,q.sessions_total,
      CASE WHEN q.renewal_date<=CURRENT_DATE+14 THEN 'RENEWAL_DUE' ELSE 'PROGRAMME_ENDING' END signal
      FROM external_client_packages q JOIN external_service_packages p ON p.id=q.package_id AND p.tenant_id=q.tenant_id
      WHERE q.tenant_id=:tenant AND q.status IN ('ACTIVE','PAUSED') AND (q.renewal_date<=CURRENT_DATE+14 OR q.end_date<=CURRENT_DATE+30) AND {scope}
      ORDER BY q.renewal_date NULLS LAST,q.end_date NULLS LAST LIMIT 15""",allowed="PACKAGE_VIEW" in permissions)
    revenue=await read("revenue_attention","""SELECT COUNT(*) FILTER (WHERE status IN ('ISSUED','PART_PAID','OVERDUE') AND balance_due_minor>0)::int open_invoices,
      COUNT(*) FILTER (WHERE status IN ('ISSUED','PART_PAID','OVERDUE') AND due_date<CURRENT_DATE AND balance_due_minor>0)::int overdue_invoices,
      COUNT(*) FILTER (WHERE status='PART_PAID')::int part_paid_invoices,
      COALESCE(SUM(balance_due_minor) FILTER (WHERE status IN ('ISSUED','PART_PAID','OVERDUE')),0)::bigint outstanding_minor
      FROM external_invoices WHERE tenant_id=:tenant""",allowed="BILLING_VIEW" in permissions)
    confirmations=await read("automation_confirmations","""SELECT r.id::text,e.client_id,r.action_type,r.result_summary,r.created_at,d.name title
      FROM external_automation_action_results r JOIN external_automation_executions e ON e.id=r.execution_id AND e.tenant_id=r.tenant_id
      JOIN external_automation_definitions d ON d.id=e.automation_id AND d.tenant_id=e.tenant_id
      WHERE r.tenant_id=:tenant AND r.status='PENDING_CONFIRMATION' ORDER BY r.created_at LIMIT 15""",allowed="AUTOMATION_VIEW" in permissions)
    drafts=await read("continue_working",f"""SELECT id,client_id,title,status,updated_at,source_module FROM (
      SELECT q.id::text,q.client_id,q.title,q.status,q.updated_at,'SESSION_NOTE' source_module FROM external_session_notes q WHERE q.tenant_id=:tenant AND q.created_by=:actor AND q.status='DRAFT' AND {scope}
      UNION ALL SELECT q.id::text,q.client_id,q.title,q.status,q.updated_at,'REPORT' source_module FROM external_progress_reports q WHERE q.tenant_id=:tenant AND q.created_by=:actor AND q.status='DRAFT' AND {scope}
      UNION ALL SELECT q.id::text,q.client_id,COALESCE(q.invoice_number,'Draft invoice') title,q.status,q.updated_at,'INVOICE' source_module FROM external_invoices q WHERE q.tenant_id=:tenant AND q.created_by=:actor AND q.status='DRAFT' AND {scope}
      UNION ALL SELECT q.id::text,q.client_id,q.purpose title,q.status,q.updated_at,'COMMUNICATION' source_module FROM external_communication_preparations q WHERE q.tenant_id=:tenant AND q.created_by=:actor AND q.status='PREPARED' AND {scope}
      UNION ALL SELECT q.id::text,q.client_id,'Post-session follow-up' title,q.lifecycle_state status,q.updated_at,'POST_SESSION' source_module FROM external_post_session_checklists q WHERE q.tenant_id=:tenant AND q.created_by=:actor AND q.lifecycle_state IN ('POST_SESSION_STARTED','IN_PROGRESS') AND {scope}
    ) drafts ORDER BY updated_at DESC LIMIT 15""",allowed=bool({"SESSION_VIEW","REPORT_VIEW","BILLING_VIEW","COMMUNICATION_VIEW"}&permissions))

    session_briefs=await read("session_briefs",f"""SELECT q.id::text,q.client_id,q.starts_at AS due_at,
      (SELECT MAX(p.starts_at) FROM external_scheduled_appointments p WHERE p.tenant_id=q.tenant_id AND p.client_id=q.client_id AND p.starts_at<q.starts_at AND p.status='COMPLETED') last_session_at,
      (SELECT COUNT(*)::int FROM external_form_assignments f WHERE f.tenant_id=q.tenant_id AND f.client_id=q.client_id AND f.status='COMPLETED' AND f.completed_at>:last_seen) recent_assessments,
      (SELECT COUNT(*)::int FROM external_homework_assignments h WHERE h.tenant_id=q.tenant_id AND h.client_id=q.client_id AND h.status='COMPLETED') homework_completed,
      (SELECT COUNT(*)::int FROM external_documents d WHERE d.tenant_id=q.tenant_id AND d.client_id=q.client_id AND d.visibility<>'PRACTITIONER_PRIVATE' AND d.updated_at>:last_seen) new_documents,
      (SELECT COUNT(*)::int FROM external_consent_records c WHERE c.tenant_id=q.tenant_id AND c.client_id=q.client_id AND c.status='ACCEPTED') accepted_consents,
      COALESCE((SELECT cp.sessions_total-COUNT(cs.id) FROM external_client_packages cp LEFT JOIN external_client_package_sessions cs ON cs.client_package_id=cp.id AND cs.tenant_id=cp.tenant_id WHERE cp.tenant_id=q.tenant_id AND cp.client_id=q.client_id AND cp.status='ACTIVE' GROUP BY cp.id,cp.end_date ORDER BY cp.end_date LIMIT 1),0)::int sessions_remaining
      FROM external_scheduled_appointments q WHERE q.tenant_id=:tenant AND q.starts_at>=date_trunc('day',NOW()) AND q.starts_at<date_trunc('day',NOW())+INTERVAL '1 day' AND q.status<>'CANCELLED' AND {scope}
      ORDER BY q.starts_at LIMIT 20""",allowed="CALENDAR_VIEW" in permissions and "CLIENT_LIST_VIEW" in permissions)

    marketplace=await read("marketplace", """SELECT id,client_id,title,status,due_at,signal FROM (
      SELECT e.id::text,NULL::varchar client_id,e.full_name title,e.status,e.created_at due_at,
        CASE WHEN e.status='BOOKED' THEN 'NEW_MARKETPLACE_BOOKING' WHEN e.status='NEW' AND e.created_at<NOW()-INTERVAL '24 hours' THEN 'BOOKING_REQUEST_UNACTIONED' ELSE 'NEW_ENROLMENT_REQUEST' END signal
      FROM external_consultant_marketplace_enrolments e JOIN external_consultant_public_profiles p ON p.id=e.profile_id AND p.tenant_id=e.tenant_id
      WHERE e.tenant_id=:tenant AND p.consultant_user_id=:actor AND e.status IN ('NEW','BOOKED')
      UNION ALL SELECT a.id::text,NULL::varchar,p.slug,a.status,a.updated_at,'BOOKING_CANCELLED'
      FROM external_scheduled_appointments a JOIN external_consultant_public_profiles p ON p.tenant_id=a.tenant_id
      WHERE a.tenant_id=:tenant AND p.consultant_user_id=:actor AND a.marketplace_source IS NOT NULL AND a.status='CANCELLED' AND a.updated_at>NOW()-INTERVAL '7 days'
      UNION ALL SELECT p.id::text,NULL::varchar,p.slug,p.status,p.updated_at,
        CASE WHEN p.status='CHANGES_REQUIRED' THEN 'PROFILE_CHANGES_REQUIRED' WHEN p.status='APPROVED' AND p.public_visibility=FALSE THEN 'PROFILE_APPROVED_NOT_PUBLISHED' ELSE 'PROFILE_UNDER_REVIEW' END
      FROM external_consultant_public_profiles p WHERE p.tenant_id=:tenant AND p.consultant_user_id=:actor AND p.status IN ('CHANGES_REQUIRED','UNDER_REVIEW','APPROVED')
      UNION ALL SELECT q.id::text,NULL::varchar,q.title,q.verification_status,q.expiry_date::timestamptz,'CREDENTIAL_EXPIRING'
      FROM external_consultant_qualifications q JOIN external_consultant_public_profiles p ON p.id=q.profile_id AND p.tenant_id=q.tenant_id
      WHERE q.tenant_id=:tenant AND p.consultant_user_id=:actor AND q.expiry_date BETWEEN CURRENT_DATE AND CURRENT_DATE+60
    ) signals ORDER BY due_at LIMIT 20""",allowed=principal["role"] in {"PRACTICE_OWNER","PRACTICE_ADMIN","PRACTITIONER"})
    if marketplace["status"] in {"READY","CONFIRMED_EMPTY"} and not marketplace.get("restricted"):
        marketplace["items"]=[{**row,"priority":operational_priority(row.get("due_at"),row["signal"]),"action":next_action(row["signal"])} for row in marketplace["items"]]

    feedback=await read("feedback",f"""SELECT q.id::text,q.client_id,q.feedback_type title,q.status,q.updated_at due_at,
      CASE WHEN q.status='ACTION_REQUIRED' THEN 'FEEDBACK_NEEDS_ATTENTION'
           WHEN q.status='SUBMITTED' THEN 'NEW_CLIENT_FEEDBACK'
           WHEN q.status='OPENED' AND q.opened_at<NOW()-INTERVAL '48 hours' THEN 'FEEDBACK_ACKNOWLEDGEMENT_DUE'
           ELSE 'NEW_CLIENT_FEEDBACK' END signal
      FROM external_client_feedback_requests q WHERE q.tenant_id=:tenant
      AND q.status IN ('OPENED','SUBMITTED','ACTION_REQUIRED','ACKNOWLEDGED') AND {scope}
      ORDER BY CASE WHEN q.status='ACTION_REQUIRED' THEN 0 ELSE 1 END,q.updated_at DESC LIMIT 20""",allowed="CLIENT_LIST_VIEW" in permissions)
    if feedback["status"] in {"READY","CONFIRMED_EMPTY"} and not feedback.get("restricted"):
        feedback["items"]=[{**row,"priority":operational_priority(row.get("due_at"),row["signal"]),"action":next_action(row["signal"])} for row in feedback["items"]]
    teleconsult=await read("teleconsult",f"""SELECT q.id::text,q.client_id,t.name title,q.status,a.starts_at due_at,
      CASE WHEN q.status='WAITING_FOR_CONSULTANT' THEN 'TELECONSULT_WAITING' ELSE 'TELECONSULT_UPCOMING' END signal
      FROM external_teleconsult_sessions q JOIN external_scheduled_appointments a ON a.id=q.appointment_id AND a.tenant_id=q.tenant_id
      JOIN external_appointment_types t ON t.id=a.appointment_type_id AND t.tenant_id=a.tenant_id
      WHERE q.tenant_id=:tenant AND q.status IN ('UPCOMING','WAITING_FOR_CONSULTANT','SESSION_ACTIVE') AND {scope}
      ORDER BY CASE WHEN q.status='WAITING_FOR_CONSULTANT' THEN 0 ELSE 1 END,a.starts_at LIMIT 20""",allowed="TELECONSULT_VIEW" in permissions)
    if teleconsult["status"] in {"READY","CONFIRMED_EMPTY"} and not teleconsult.get("restricted"):
        teleconsult["items"]=[{**row,"priority":operational_priority(row.get("due_at"),row["signal"]),"action":next_action(row["signal"])} for row in teleconsult["items"]]
    messages=await read("messages",f"""SELECT c.id::text,c.client_id,'Secure conversation' title,c.status,c.updated_at due_at,
      CASE WHEN MAX(m.sent_at)<NOW()-INTERVAL '24 hours' THEN 'MESSAGE_REPLY_NEEDED' ELSE 'UNREAD_MESSAGE' END signal,
      COUNT(m.id)::int unread_count FROM external_secure_conversations c JOIN external_secure_messages m ON m.conversation_id=c.id AND m.tenant_id=c.tenant_id
      WHERE c.tenant_id=:tenant AND c.status='OPEN' AND m.sender_type='CLIENT' AND m.status<>'READ' AND {scope}
      GROUP BY c.id ORDER BY c.updated_at DESC LIMIT 20""",allowed="SECURE_MESSAGE_VIEW" in permissions)
    if messages["status"] in {"READY","CONFIRMED_EMPTY"} and not messages.get("restricted"):
        messages["items"]=[{**row,"priority":operational_priority(row.get("due_at"),row["signal"]),"action":next_action(row["signal"])} for row in messages["items"]]

    sections={"schedule":schedule,"my_work":work,"clients_needing_attention":attention,"onboarding":onboarding,"preconsultation":preconsultation,"post_session":post_session,
      "recent_changes":recent,"leads":leads,"renewals":renewals,"revenue_attention":revenue,
      "automation_confirmations":confirmations,"continue_working":drafts,"session_briefs":session_briefs,"marketplace":marketplace,"feedback":feedback,"teleconsult":teleconsult,"messages":messages}
    failed=[name for name,value in sections.items() if value["status"]=="FAILED"]
    daily_counts={
      "appointments_today":len(schedule["items"]) if schedule["status"]!="FAILED" and not schedule.get("restricted") else None,
      "work_due":len(work["items"]) if work["status"]!="FAILED" and not work.get("restricted") else None,
      "clients_needing_attention":len({row.get("client_id") for row in attention["items"] if row.get("client_id")}) if attention["status"]!="FAILED" and not attention.get("restricted") else None,
      "new_leads":sum(1 for row in leads["items"] if row.get("stage")=="NEW") if leads["status"]!="FAILED" and not leads.get("restricted") else None,
      "automation_confirmations":len(confirmations["items"]) if confirmations["status"]!="FAILED" and not confirmations.get("restricted") else None,
      "marketplace_enrolments":sum(1 for row in marketplace["items"] if row.get("signal") in {"NEW_ENROLMENT_REQUEST","BOOKING_REQUEST_UNACTIONED"}) if marketplace["status"]!="FAILED" and not marketplace.get("restricted") else None,
    }
    overall="PARTIAL_DATA" if failed else "READY" if any(value is not None and value>0 for value in daily_counts.values()) else "CONFIRMED_EMPTY"
    await db.execute(text("""INSERT INTO external_consultant_dashboard_state(tenant_id,user_id,dashboard_last_seen_at,updated_at)
      VALUES (:tenant,:actor,:seen,:seen) ON CONFLICT(tenant_id,user_id) DO UPDATE SET dashboard_last_seen_at=EXCLUDED.dashboard_last_seen_at,updated_at=EXCLUDED.updated_at"""),{"tenant":tenant,"actor":actor,"seen":request_started_at})
    await db.commit()
    return {"success":True,"data":{"state":overall,"role":principal["role"],"profession_code":principal.get("profession_code"),
      "daily_brief":daily_counts,"sections":sections,"failed_sections":failed,"last_seen_at":last_seen_at,"generated_at":request_started_at},
      "error":None,"request_id":request.state.correlation_id}


# P41 secure messaging; distinct from WhatsApp and private practitioner notes.
@app.post("/api/v1/practice-operations/messages/conversations",status_code=201)
async def create_secure_conversation(request:Request,body:SecureConversationCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"SECURE_MESSAGE_SEND")
    if denied:return denied
    cid=uuid4();now=datetime.now(timezone.utc)
    await db.execute(text("""INSERT INTO external_secure_conversations(id,tenant_id,client_id,conversation_type,status,created_by,created_at,updated_at)
      VALUES (:id,:tenant,:client,:type,'OPEN',:actor,:now,:now) ON CONFLICT(tenant_id,client_id,conversation_type) DO NOTHING"""),{"id":cid,"tenant":ctx["tenant_id"],"client":body.client_id,"type":body.conversation_type,"actor":ctx["user_id"],"now":now})
    row=(await db.execute(text("SELECT id,status FROM external_secure_conversations WHERE tenant_id=:tenant AND client_id=:client AND conversation_type=:type"),{"tenant":ctx["tenant_id"],"client":body.client_id,"type":body.conversation_type})).mappings().one();await db.commit()
    return {"success":True,"data":{"id":str(row["id"]),"status":row["status"]},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/messages/conversations")
async def list_secure_conversations(request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"SECURE_MESSAGE_VIEW")
    if denied:return denied
    rows=[dict(r) for r in (await db.execute(text("""SELECT c.id,c.client_id,c.conversation_type,c.status,c.updated_at,
      COUNT(m.id) FILTER(WHERE m.sender_type='CLIENT' AND m.status<>'READ')::int unread_count
      FROM external_secure_conversations c LEFT JOIN external_secure_messages m ON m.conversation_id=c.id AND m.tenant_id=c.tenant_id
      WHERE c.tenant_id=:tenant GROUP BY c.id ORDER BY c.updated_at DESC LIMIT 100"""),{"tenant":ctx["tenant_id"]})).mappings().all()]
    return {"success":True,"data":{"state":"READY" if rows else "CONFIRMED_EMPTY","items":rows},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/messages/conversations/{conversation_id}")
async def get_secure_conversation(request:Request,conversation_id:UUID,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"SECURE_MESSAGE_VIEW")
    if denied:return denied
    rows=[dict(r) for r in (await db.execute(text("SELECT id,sender_type,message_type,body,reference_id,status,sent_at,read_at FROM external_secure_messages WHERE conversation_id=:id AND tenant_id=:tenant ORDER BY sent_at LIMIT 200"),{"id":conversation_id,"tenant":ctx["tenant_id"]})).mappings().all()]
    return {"success":True,"data":{"state":"READY" if rows else "CONFIRMED_EMPTY","items":rows},"error":None,"request_id":request.state.correlation_id}

async def _persist_secure_message(db,conversation,body,sender_id,sender_type):
    validate_message(body.message_type,body.body,body.reference_id);mid=uuid4();now=datetime.now(timezone.utc)
    await db.execute(text("INSERT INTO external_secure_messages(id,conversation_id,tenant_id,client_id,sender_id,sender_type,message_type,body,reference_id,status,sent_at) VALUES (:id,:conversation,:tenant,:client,:sender,:sender_type,:type,:body,:reference,'SENT',:now)"),{"id":mid,"conversation":conversation["id"],"tenant":conversation["tenant_id"],"client":conversation["client_id"],"sender":sender_id,"sender_type":sender_type,"type":body.message_type,"body":body.body,"reference":body.reference_id,"now":now})
    await db.execute(text("INSERT INTO external_secure_message_events(id,message_id,tenant_id,event_type,actor_id,actor_type,created_at) VALUES (:id,:message,:tenant,'SECURE_MESSAGE_PERSISTED',:actor,:actor_type,:now)"),{"id":uuid4(),"message":mid,"tenant":conversation["tenant_id"],"actor":sender_id,"actor_type":sender_type,"now":now});await db.execute(text("UPDATE external_secure_conversations SET updated_at=:now WHERE id=:id"),{"now":now,"id":conversation["id"]});return mid

@app.post("/api/v1/practice-operations/messages/conversations/{conversation_id}",status_code=201)
async def send_secure_message(request:Request,conversation_id:UUID,body:SecureMessageCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"SECURE_MESSAGE_SEND")
    if denied:return denied
    row=(await db.execute(text("SELECT id,tenant_id,client_id,status FROM external_secure_conversations WHERE id=:id AND tenant_id=:tenant"),{"id":conversation_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not row or row["status"]!='OPEN':return error(request,404,"CONVERSATION_NOT_FOUND","Open conversation was not found")
    try:mid=await _persist_secure_message(db,row,body,ctx["user_id"],"PRACTITIONER")
    except ValueError as exc:return error(request,422,"INVALID_SECURE_MESSAGE",str(exc))
    await db.commit();return {"success":True,"data":{"id":str(mid),"status":"SENT","delivered":False,"read":False},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/client-portal/{token}/messages/{conversation_id}",status_code=201)
async def portal_send_secure_message(request:Request,token:str,conversation_id:UUID,body:SecureMessageCreate,db:AsyncSession=Depends(get_db)):
    scope,denied=await _portal_scope(request,token,"READ",db)
    if denied:return denied
    row=(await db.execute(text("SELECT id,tenant_id,client_id,status FROM external_secure_conversations WHERE id=:id AND tenant_id=:tenant AND client_id=:client"),{"id":conversation_id,"tenant":scope["tenant_id"],"client":scope["client_id"]})).mappings().first()
    if not row or row["status"]!='OPEN':return error(request,404,"CONVERSATION_NOT_FOUND","Open conversation was not found")
    try:mid=await _persist_secure_message(db,row,body,None,"CLIENT")
    except ValueError as exc:return error(request,422,"INVALID_SECURE_MESSAGE",str(exc))
    await db.commit();return {"success":True,"data":{"id":str(mid),"status":"SENT","delivered":False,"read":False},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/client-portal/{token}/messages/{message_id}/read")
async def portal_read_secure_message(request:Request,token:str,message_id:UUID,db:AsyncSession=Depends(get_db)):
    scope,denied=await _portal_scope(request,token,"READ",db)
    if denied:return denied
    now=datetime.now(timezone.utc);result=await db.execute(text("UPDATE external_secure_messages SET status='READ',read_at=:now WHERE id=:id AND tenant_id=:tenant AND client_id=:client AND sender_type<>'CLIENT'"),{"now":now,"id":message_id,"tenant":scope["tenant_id"],"client":scope["client_id"]})
    if result.rowcount!=1:return error(request,404,"MESSAGE_NOT_FOUND","Message was not found")
    await db.execute(text("INSERT INTO external_secure_message_events(id,message_id,tenant_id,event_type,actor_type,created_at) VALUES (:id,:message,:tenant,'MESSAGE_READ','CLIENT',:now)"),{"id":uuid4(),"message":message_id,"tenant":scope["tenant_id"],"now":now});await db.commit()
    return {"success":True,"data":{"id":str(message_id),"status":"READ"},"error":None,"request_id":request.state.correlation_id}

# P40 provider-neutral virtual-session authority; P13 appointments remain authoritative.
async def _teleconsult_event(db,row,event,actor,actor_type):
    await db.execute(text("INSERT INTO external_teleconsult_events(id,session_id,tenant_id,client_id,event_type,actor_id,actor_type,metadata,created_at) VALUES (:id,:session,:tenant,:client,:event,:actor,:actor_type,'{}'::jsonb,:now)"),{"id":uuid4(),"session":row["id"],"tenant":row["tenant_id"],"client":row["client_id"],"event":event,"actor":actor,"actor_type":actor_type,"now":datetime.now(timezone.utc)})

@app.put("/api/v1/practice-operations/appointments/{appointment_id}/teleconsult")
async def configure_teleconsult(request:Request,appointment_id:UUID,body:TeleconsultConfigure,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"TELECONSULT_MANAGE")
    if denied:return denied
    appointment=(await db.execute(text("""SELECT a.id,a.client_id,a.status,t.location_type FROM external_scheduled_appointments a
      JOIN external_appointment_types t ON t.id=a.appointment_type_id AND t.tenant_id=a.tenant_id
      WHERE a.id=:id AND a.tenant_id=:tenant"""),{"id":appointment_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not appointment:return error(request,404,"APPOINTMENT_NOT_FOUND","Appointment was not found")
    if appointment["location_type"]!="ONLINE":return error(request,409,"ONLINE_APPOINTMENT_REQUIRED","Teleconsultation requires an online appointment")
    try:url=validate_external_meeting_url(body.external_meeting_url)
    except ValueError as exc:return error(request,422,"INVALID_MEETING_URL",str(exc))
    if body.provider_mode=="EXTERNAL_MEETING_LINK" and not url:return error(request,422,"MEETING_URL_REQUIRED","External meeting mode requires a governed URL")
    now=datetime.now(timezone.utc);sid=uuid4()
    await db.execute(text("""INSERT INTO external_teleconsult_sessions(id,tenant_id,appointment_id,client_id,consultant_id,provider_mode,external_meeting_url,status,join_window_before_minutes,join_window_after_minutes,created_by,created_at,updated_at)
      VALUES (:id,:tenant,:appointment,:client,:consultant,:mode,:url,'UPCOMING',:before,:after,:actor,:now,:now)
      ON CONFLICT(tenant_id,appointment_id) DO UPDATE SET provider_mode=EXCLUDED.provider_mode,external_meeting_url=EXCLUDED.external_meeting_url,join_window_before_minutes=EXCLUDED.join_window_before_minutes,join_window_after_minutes=EXCLUDED.join_window_after_minutes,updated_at=EXCLUDED.updated_at
      RETURNING id,tenant_id,client_id,provider_mode,status"""),{"id":sid,"tenant":ctx["tenant_id"],"appointment":appointment_id,"client":appointment["client_id"],"consultant":ctx["user_id"],"mode":body.provider_mode,"url":url,"before":body.join_window_before_minutes,"after":body.join_window_after_minutes,"actor":ctx["user_id"],"now":now})
    row=(await db.execute(text("SELECT id,tenant_id,client_id,provider_mode,status FROM external_teleconsult_sessions WHERE tenant_id=:tenant AND appointment_id=:appointment"),{"tenant":ctx["tenant_id"],"appointment":appointment_id})).mappings().one();await _teleconsult_event(db,row,"SESSION_CONFIGURED",ctx["user_id"],"PRACTITIONER");await db.commit()
    return {"success":True,"data":{"id":str(row["id"]),"status":row["status"],"teleconsultProvider":provider_status(row["provider_mode"]),"presenceEvidence":False},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/teleconsult/{session_id}/transition")
async def transition_teleconsult(request:Request,session_id:UUID,body:TeleconsultTransition,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"TELECONSULT_MANAGE")
    if denied:return denied
    row=(await db.execute(text("SELECT id,tenant_id,client_id,status FROM external_teleconsult_sessions WHERE id=:id AND tenant_id=:tenant FOR UPDATE"),{"id":session_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not row:return error(request,404,"TELECONSULT_SESSION_NOT_FOUND","Session was not found")
    transitions={"START":({"UPCOMING","WAITING_FOR_CONSULTANT"},"SESSION_ACTIVE","SESSION_STARTED"),"COMPLETE":({"SESSION_ACTIVE"},"SESSION_COMPLETED","SESSION_COMPLETED"),"CANCEL":({"UPCOMING","WAITING_FOR_CONSULTANT"},"CANCELLED","SESSION_CANCELLED")};allowed,status,event=transitions[body.action]
    if row["status"] not in allowed:return error(request,409,"INVALID_SESSION_TRANSITION","Session state does not permit that action")
    now=datetime.now(timezone.utc);await db.execute(text("UPDATE external_teleconsult_sessions SET status=:status,started_at=CASE WHEN :status='SESSION_ACTIVE' THEN :now ELSE started_at END,completed_at=CASE WHEN :status='SESSION_COMPLETED' THEN :now ELSE completed_at END,updated_at=:now WHERE id=:id"),{"status":status,"now":now,"id":session_id});await _teleconsult_event(db,row,event,ctx["user_id"],"PRACTITIONER");await db.commit()
    return {"success":True,"data":{"id":str(session_id),"status":status,"presenceEvidence":False},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/client-portal/{token}/teleconsult/{appointment_id}")
async def portal_teleconsult(request:Request,token:str,appointment_id:UUID,db:AsyncSession=Depends(get_db)):
    scope,denied=await _portal_scope(request,token,"READ",db)
    if denied:return denied
    row=(await db.execute(text("""SELECT s.id,s.tenant_id,s.client_id,s.provider_mode,s.external_meeting_url,s.status,s.join_window_before_minutes,s.join_window_after_minutes,
      a.starts_at,a.ends_at,a.status appointment_status FROM external_teleconsult_sessions s JOIN external_scheduled_appointments a ON a.id=s.appointment_id AND a.tenant_id=s.tenant_id
      WHERE s.appointment_id=:appointment AND s.tenant_id=:tenant AND s.client_id=:client"""),{"appointment":appointment_id,"tenant":scope["tenant_id"],"client":scope["client_id"]})).mappings().first()
    if not row:return error(request,404,"TELECONSULT_SESSION_NOT_FOUND","Online session access was not configured")
    allowed=join_allowed(starts_at=row["starts_at"],ends_at=row["ends_at"],now=datetime.now(timezone.utc),before_minutes=row["join_window_before_minutes"],after_minutes=row["join_window_after_minutes"],status=row["appointment_status"])
    return {"success":True,"data":{"id":str(row["id"]),"status":row["status"],"joinAllowed":allowed,"teleconsultProvider":provider_status(row["provider_mode"]),"meetingUrl":row["external_meeting_url"] if allowed and row["provider_mode"]=="EXTERNAL_MEETING_LINK" else None,"presenceEvidence":False},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/client-portal/{token}/teleconsult/{appointment_id}/join")
async def join_portal_teleconsult(request:Request,token:str,appointment_id:UUID,db:AsyncSession=Depends(get_db)):
    scope,denied=await _portal_scope(request,token,"READ",db)
    if denied:return denied
    row=(await db.execute(text("""SELECT s.id,s.tenant_id,s.client_id,s.status,s.join_window_before_minutes,s.join_window_after_minutes,a.starts_at,a.ends_at,a.status appointment_status
      FROM external_teleconsult_sessions s JOIN external_scheduled_appointments a ON a.id=s.appointment_id AND a.tenant_id=s.tenant_id
      WHERE s.appointment_id=:appointment AND s.tenant_id=:tenant AND s.client_id=:client FOR UPDATE"""),{"appointment":appointment_id,"tenant":scope["tenant_id"],"client":scope["client_id"]})).mappings().first()
    if not row:return error(request,404,"TELECONSULT_SESSION_NOT_FOUND","Online session access was not configured")
    if not join_allowed(starts_at=row["starts_at"],ends_at=row["ends_at"],now=datetime.now(timezone.utc),before_minutes=row["join_window_before_minutes"],after_minutes=row["join_window_after_minutes"],status=row["appointment_status"]):return error(request,403,"JOIN_WINDOW_CLOSED","The appointment cannot be joined at this time")
    if row["status"]=="UPCOMING":await db.execute(text("UPDATE external_teleconsult_sessions SET status='WAITING_FOR_CONSULTANT',updated_at=:now WHERE id=:id"),{"now":datetime.now(timezone.utc),"id":row["id"]});await _teleconsult_event(db,row,"CLIENT_JOINED_WAITING_ROOM",None,"CLIENT");await db.commit()
    return {"success":True,"data":{"id":str(row["id"]),"status":"WAITING_FOR_CONSULTANT" if row["status"]=="UPCOMING" else row["status"],"admitted":row["status"]=="SESSION_ACTIVE","presenceEvidence":False},"error":None,"request_id":request.state.correlation_id}

# P39 private client-experience feedback. This domain never writes public reviews.
async def _feedback_audit(db,row,event,actor,actor_type,metadata=None):
    await db.execute(text("""INSERT INTO external_client_feedback_audit_events
      (id,request_id,tenant_id,client_id,event_type,actor_id,actor_type,metadata,created_at)
      VALUES (:id,:request,:tenant,:client,:event,:actor,:actor_type,CAST(:metadata AS jsonb),:now)"""),{
      "id":uuid4(),"request":row["id"],"tenant":row["tenant_id"],"client":row["client_id"],"event":event,
      "actor":actor,"actor_type":actor_type,"metadata":json.dumps(metadata or {}),"now":datetime.now(timezone.utc)})

@app.post("/api/v1/practice-operations/clients/{client_id}/feedback/requests",status_code=201)
async def create_feedback_request(request:Request,client_id:str,body:FeedbackRequestCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"FEEDBACK_MANAGE")
    if denied:return denied
    tenant=ctx["tenant_id"]
    if body.feedback_type=="POST_SESSION_FEEDBACK":
        if not body.consultation_id:return error(request,422,"CONSULTATION_REQUIRED","A completed consultation is required")
        session=(await db.execute(text("SELECT status FROM practice_consultations WHERE id=CAST(:id AS uuid) AND tenant_id=:tenant AND client_id=:client"),{"id":body.consultation_id,"tenant":tenant,"client":client_id})).mappings().first()
        if not session or session["status"]!="COMPLETED":return error(request,409,"COMPLETED_SESSION_REQUIRED","Feedback may be requested only after a completed session")
    now=datetime.now(timezone.utc);row={"id":uuid4(),"tenant_id":tenant,"client_id":client_id}
    try:
        await db.execute(text("""INSERT INTO external_client_feedback_requests
          (id,tenant_id,client_id,consultant_id,feedback_type,consultation_id,service_id,programme_id,template_id,template_version,status,expires_at,created_by,created_at,updated_at)
          VALUES (:id,:tenant,:client,:consultant,:type,:consultation,:service,:programme,:template,:version,'REQUESTED',:expires,:actor,:now,:now)"""),{
          "id":row["id"],"tenant":tenant,"client":client_id,"consultant":ctx["user_id"],"type":body.feedback_type,"consultation":body.consultation_id,
          "service":body.service_id,"programme":body.programme_id,"template":body.template_id,"version":body.template_version,
          "expires":now+timedelta(hours=body.expires_in_hours),"actor":ctx["user_id"],"now":now})
        await _feedback_audit(db,row,"FEEDBACK_REQUESTED",ctx["user_id"],"PRACTITIONER",{"feedback_type":body.feedback_type})
        await db.commit()
    except IntegrityError:
        await db.rollback();return error(request,409,"FEEDBACK_REQUEST_EXISTS","A feedback request already exists for this context")
    return {"success":True,"data":{"id":str(row["id"]),"status":"REQUESTED","communicationPrepared":False,"autoSend":False},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/clients/{client_id}/feedback")
async def list_client_feedback(request:Request,client_id:str,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"FEEDBACK_VIEW")
    if denied:return denied
    rows=[dict(row) for row in (await db.execute(text("""SELECT r.id,r.feedback_type,r.consultation_id,r.status,r.expires_at,r.opened_at,r.submitted_at,r.created_at,
      s.overall_experience,s.communication_rating,s.professionalism_rating,s.booking_experience_rating,s.support_experience_rating,
      s.went_well,s.could_improve,s.experience_label FROM external_client_feedback_requests r
      LEFT JOIN external_client_feedback_submissions s ON s.request_id=r.id AND s.tenant_id=r.tenant_id
      WHERE r.tenant_id=:tenant AND r.client_id=:client ORDER BY r.created_at DESC"""),{"tenant":ctx["tenant_id"],"client":client_id})).mappings().all()]
    return {"success":True,"data":{"state":"READY" if rows else "CONFIRMED_EMPTY","items":rows},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/client-portal/{token}/feedback/{feedback_id}")
async def open_portal_feedback(request:Request,token:str,feedback_id:UUID,db:AsyncSession=Depends(get_db)):
    scope,denied=await _portal_scope(request,token,"READ",db)
    if denied:return denied
    row=(await db.execute(text("SELECT id,tenant_id,client_id,consultant_id,feedback_type,consultation_id,status,expires_at,opened_at,submitted_at,created_by,created_at,updated_at FROM external_client_feedback_requests WHERE id=:id AND tenant_id=:tenant AND client_id=:client FOR UPDATE"),{"id":feedback_id,"tenant":scope["tenant_id"],"client":scope["client_id"]})).mappings().first()
    if not row:return error(request,404,"FEEDBACK_NOT_FOUND","Feedback request was not found")
    if row["expires_at"]<=datetime.now(timezone.utc):return error(request,410,"FEEDBACK_EXPIRED","This feedback request has expired")
    if row["status"] in {"SUBMITTED","ACKNOWLEDGED","ACTION_REQUIRED","RESOLVED","ARCHIVED"}:return error(request,409,"FEEDBACK_ALREADY_SUBMITTED","Feedback has already been submitted")
    if row["status"]=="REQUESTED":
        now=datetime.now(timezone.utc);await db.execute(text("UPDATE external_client_feedback_requests SET status='OPENED',opened_at=:now,updated_at=:now WHERE id=:id"),{"now":now,"id":feedback_id});await _feedback_audit(db,row,"FEEDBACK_OPENED",None,"CLIENT");await db.commit()
    return {"success":True,"data":{"id":str(feedback_id),"feedbackType":row["feedback_type"],"status":"OPENED","privacy":"PRIVATE_TO_PRACTICE"},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/client-portal/{token}/feedback/{feedback_id}/submit")
async def submit_portal_feedback(request:Request,token:str,feedback_id:UUID,body:FeedbackSubmit,db:AsyncSession=Depends(get_db)):
    scope,denied=await _portal_scope(request,token,"READ",db)
    if denied:return denied
    row=(await db.execute(text("SELECT id,tenant_id,client_id,consultant_id,feedback_type,consultation_id,status,expires_at,opened_at,submitted_at,created_by,created_at,updated_at FROM external_client_feedback_requests WHERE id=:id AND tenant_id=:tenant AND client_id=:client FOR UPDATE"),{"id":feedback_id,"tenant":scope["tenant_id"],"client":scope["client_id"]})).mappings().first()
    if not row:return error(request,404,"FEEDBACK_NOT_FOUND","Feedback request was not found")
    now=datetime.now(timezone.utc)
    if row["expires_at"]<=now:return error(request,410,"FEEDBACK_EXPIRED","This feedback request has expired")
    if row["status"] not in {"REQUESTED","OPENED"}:return error(request,409,"FEEDBACK_IMMUTABLE","Submitted feedback cannot be edited or replaced")
    values=validate_ratings(body.model_dump());label=experience_label(values["overall_experience"]);status="ACTION_REQUIRED" if label=="NEEDS_ATTENTION" else "SUBMITTED"
    try:
        await db.execute(text("""INSERT INTO external_client_feedback_submissions
          (id,request_id,tenant_id,client_id,overall_experience,communication_rating,professionalism_rating,booking_experience_rating,support_experience_rating,went_well,could_improve,experience_label,submitted_at)
          VALUES (:id,:request,:tenant,:client,:overall,:communication,:professionalism,:booking,:support,:well,:improve,:label,:now)"""),{
          "id":uuid4(),"request":feedback_id,"tenant":scope["tenant_id"],"client":scope["client_id"],"overall":values["overall_experience"],
          "communication":values.get("communication_rating"),"professionalism":values.get("professionalism_rating"),"booking":values.get("booking_experience_rating"),
          "support":values.get("support_experience_rating"),"well":values.get("went_well"),"improve":values.get("could_improve"),"label":label,"now":now})
        await db.execute(text("UPDATE external_client_feedback_requests SET status=:status,submitted_at=:now,updated_at=:now WHERE id=:id"),{"status":status,"now":now,"id":feedback_id})
        await _feedback_audit(db,row,"FEEDBACK_SUBMITTED",None,"CLIENT",{"experience_label":label});await db.commit()
    except IntegrityError:
        await db.rollback();return error(request,409,"FEEDBACK_IMMUTABLE","Submitted feedback cannot be edited or replaced")
    return {"success":True,"data":{"id":str(feedback_id),"status":status,"publicReviewCreated":False},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/feedback/{feedback_id}/actions",status_code=201)
async def act_on_feedback(request:Request,feedback_id:UUID,body:FeedbackAction,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"FEEDBACK_MANAGE")
    if denied:return denied
    row=(await db.execute(text("SELECT id,tenant_id,client_id,consultant_id,feedback_type,consultation_id,status,expires_at,opened_at,submitted_at,created_by,created_at,updated_at FROM external_client_feedback_requests WHERE id=:id AND tenant_id=:tenant FOR UPDATE"),{"id":feedback_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not row:return error(request,404,"FEEDBACK_NOT_FOUND","Feedback request was not found")
    if body.action_type in {"FOLLOWUP_CREATED","CLIENT_MESSAGE_PREPARED"} and not body.source_record_id:return error(request,422,"SOURCE_RECORD_REQUIRED","The governed source record is required")
    if body.action_type=="ESCALATE_GRIEVANCE" and not body.grievance_reference:return error(request,422,"GRIEVANCE_REFERENCE_REQUIRED","Create the grievance in the governed Super Admin system first")
    if body.action_type=="PUBLIC_REVIEW_INVITATION_PREPARED":
        verified=bool(row["consultation_id"] and (await db.execute(text("SELECT 1 FROM practice_consultations WHERE id=CAST(:id AS uuid) AND tenant_id=:tenant AND client_id=:client AND status='COMPLETED'"),{"id":row["consultation_id"],"tenant":row["tenant_id"],"client":row["client_id"]})).first())
        if not public_review_eligible(submitted=bool(row["submitted_at"]),verified_engagement=verified,invitation_enabled=True):return error(request,409,"PUBLIC_REVIEW_NOT_ELIGIBLE","A submitted response and verified engagement are required")
    now=datetime.now(timezone.utc);action_id=uuid4()
    await db.execute(text("""INSERT INTO external_client_feedback_actions(id,request_id,tenant_id,action_type,private_note,source_record_id,grievance_reference,actor_id,created_at)
      VALUES (:id,:request,:tenant,:type,:note,:source,:grievance,:actor,:now)"""),{"id":action_id,"request":feedback_id,"tenant":ctx["tenant_id"],"type":body.action_type,"note":body.private_note,"source":body.source_record_id,"grievance":body.grievance_reference,"actor":ctx["user_id"],"now":now})
    status={"ACKNOWLEDGE":"ACKNOWLEDGED","RESOLVE":"RESOLVED","ESCALATE_GRIEVANCE":"ACTION_REQUIRED"}.get(body.action_type)
    if status:await db.execute(text("UPDATE external_client_feedback_requests SET status=:status,updated_at=:now WHERE id=:id"),{"status":status,"now":now,"id":feedback_id})
    event={"ACKNOWLEDGE":"FEEDBACK_ACKNOWLEDGED","RESOLVE":"FEEDBACK_RESOLVED","ESCALATE_GRIEVANCE":"FEEDBACK_ESCALATED","PUBLIC_REVIEW_INVITATION_PREPARED":"PUBLIC_REVIEW_INVITATION_PREPARED"}.get(body.action_type,"FEEDBACK_ACTION_CREATED")
    await _feedback_audit(db,row,event,ctx["user_id"],"PRACTITIONER",{"action_type":body.action_type,"source_record_id":body.source_record_id,"grievance_reference":body.grievance_reference});await db.commit()
    return {"success":True,"data":{"id":str(action_id),"status":status or row["status"],"autoSend":False,"publicReviewCreated":False},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/feedback/analytics")
async def feedback_analytics(request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"ANALYTICS_VIEW")
    if denied:return denied
    row=(await db.execute(text("""SELECT COUNT(r.id)::int requested_count,COUNT(s.id)::int response_count,
      ROUND(AVG(s.overall_experience),2) overall_experience,ROUND(AVG(s.communication_rating),2) communication,
      ROUND(AVG(s.professionalism_rating),2) professionalism,ROUND(AVG(s.booking_experience_rating),2) booking_experience,
      ROUND(AVG(s.support_experience_rating),2) support_experience,
      COUNT(*) FILTER (WHERE r.status='ACTION_REQUIRED')::int needs_attention
      FROM external_client_feedback_requests r LEFT JOIN external_client_feedback_submissions s ON s.request_id=r.id AND s.tenant_id=r.tenant_id WHERE r.tenant_id=:tenant"""),{"tenant":ctx["tenant_id"]})).mappings().one()
    data=dict(row);data["response_rate"]=round((data["response_count"]/data["requested_count"]*100),2) if data["requested_count"] else None
    return {"success":True,"data":{"state":"READY" if data["requested_count"] else "CONFIRMED_EMPTY","dimensions":data,"serviceOutcomeScore":None},"error":None,"request_id":request.state.correlation_id}

# P31 Consultant Marketplace — additive External-only domain.
MARKETPLACE_ACQUISITION_SOURCES={'PUBLIC_CONSULTANT_DIRECTORY','HOMEPAGE_FEATURED_CONSULTANT','HOMEPAGE_PROFESSION_DISCOVERY','HOMEPAGE_SEARCH'}
def _platform_admin(request,ctx):
    role=str((ctx or {}).get("role") or "").upper()
    if role not in {"SUPER_ADMIN","SUPERUSER","PLATFORM_OWNER"}:return error(request,403,"PLATFORM_ADMIN_REQUIRED","Platform Super Admin authority is required")

async def _marketplace_profile(db,ctx,lock=False):
    suffix=" FOR UPDATE" if lock else ""
    return (await db.execute(text("SELECT id,tenant_id,consultant_user_id,slug,status,public_visibility,accepting_new_clients,current_published_version,working_version,approved_version,approval_valid,suspended_at,created_at,updated_at FROM external_consultant_public_profiles WHERE tenant_id=:tenant AND consultant_user_id=:actor"+suffix),{"tenant":ctx["tenant_id"],"actor":ctx["user_id"]})).mappings().first()

async def _marketplace_audit(db,profile,tenant,event,actor,role,reason=None,metadata=None):
    await db.execute(text("INSERT INTO external_consultant_marketplace_audit_events(id,profile_id,tenant_id,event_type,actor_id,actor_role,reason,metadata,created_at) VALUES (:id,:profile,:tenant,:event,:actor,:role,:reason,CAST(:metadata AS jsonb),:now)"),{"id":uuid4(),"profile":profile,"tenant":tenant,"event":event,"actor":actor,"role":role,"reason":reason,"metadata":json.dumps(metadata or {}),"now":datetime.now(timezone.utc)})

@app.get("/api/v1/practice-operations/marketplace/contact")
async def marketplace_contact(request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    row=(await db.execute(text("SELECT country_iso2,country_code,national_number,phone_e164,updated_at FROM external_consultant_contact_profiles WHERE tenant_id=:tenant AND consultant_user_id=:actor"),{"tenant":ctx["tenant_id"],"actor":ctx["user_id"]})).mappings().first()
    return {"success":True,"data":{"state":"READY" if row else "CONFIRMED_EMPTY","contact":dict(row) if row else None},"error":None,"request_id":request.state.correlation_id}

@app.put("/api/v1/practice-operations/marketplace/contact")
async def save_marketplace_contact(request:Request,body:ConsultantContactSave,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    try:
        parsed=phonenumbers.parse(body.national_number,body.country_iso2.upper())
        if not phonenumbers.is_valid_number(parsed):raise ValueError("invalid")
        e164=phonenumbers.format_number(parsed,phonenumbers.PhoneNumberFormat.E164)
        country_code=f"+{parsed.country_code}";national=str(parsed.national_number)
    except Exception:return error(request,422,"INVALID_PHONE","Enter a valid telephone number for the selected country")
    now=datetime.now(timezone.utc)
    await db.execute(text("""INSERT INTO external_consultant_contact_profiles(id,tenant_id,consultant_user_id,country_iso2,country_code,national_number,phone_e164,created_at,updated_at)
      VALUES(:id,:tenant,:actor,:iso,:code,:national,:e164,:now,:now)
      ON CONFLICT(tenant_id,consultant_user_id) DO UPDATE SET country_iso2=EXCLUDED.country_iso2,country_code=EXCLUDED.country_code,national_number=EXCLUDED.national_number,phone_e164=EXCLUDED.phone_e164,updated_at=EXCLUDED.updated_at"""),{"id":uuid4(),"tenant":ctx["tenant_id"],"actor":ctx["user_id"],"iso":body.country_iso2.upper(),"code":country_code,"national":national,"e164":e164,"now":now})
    await db.commit()
    return {"success":True,"data":{"country_iso2":body.country_iso2.upper(),"country_code":country_code,"national_number":national,"phone_e164":e164,"updated_at":now},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/marketplace/profile/photo-upload")
async def prepare_marketplace_photo(request:Request,body:ProfilePhotoPrepare,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    profile=await _marketplace_profile(db,ctx)
    if not profile:return error(request,409,"PROFILE_DRAFT_REQUIRED","Save the profile draft before uploading a photo")
    try:filename=validate_document(body.filename,body.content_type,body.size_bytes)
    except InvalidDocument as exc:return error(request,422,"INVALID_PROFILE_PHOTO",str(exc))
    photo_id=uuid4();key=new_object_key(ctx["tenant_id"],profile["id"],photo_id,filename)
    try:url=signed_upload(key,body.content_type,body.size_bytes)
    except StorageUnavailable:return error(request,503,"PROFILE_PHOTO_STORAGE_UNAVAILABLE","Profile photo storage is not configured")
    now=datetime.now(timezone.utc)
    await db.execute(text("INSERT INTO external_consultant_profile_photos(id,profile_id,tenant_id,object_key,filename,content_type,size_bytes,status,created_by,created_at) VALUES(:id,:profile,:tenant,:key,:filename,:type,:size,'PENDING_UPLOAD',:actor,:now)"),{"id":photo_id,"profile":profile["id"],"tenant":ctx["tenant_id"],"key":key,"filename":filename,"type":body.content_type,"size":body.size_bytes,"actor":ctx["user_id"],"now":now})
    await db.commit()
    return {"success":True,"data":{"photo_id":str(photo_id),"upload":{"url":url,"method":"PUT","required_headers":{"Content-Type":body.content_type,"Content-Length":str(body.size_bytes)}}},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/marketplace/profile/photo-finalise")
async def finalise_marketplace_photo(request:Request,body:ProfilePhotoFinalise,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    profile=await _marketplace_profile(db,ctx,True)
    if not profile:return error(request,404,"PROFILE_NOT_FOUND","Profile draft was not found")
    photo=(await db.execute(text("SELECT id,object_key,content_type,size_bytes FROM external_consultant_profile_photos WHERE id=:id AND profile_id=:profile AND tenant_id=:tenant AND status='PENDING_UPLOAD' FOR UPDATE"),{"id":body.photo_id,"profile":profile["id"],"tenant":ctx["tenant_id"]})).mappings().first()
    if not photo:return error(request,404,"PROFILE_PHOTO_UPLOAD_NOT_FOUND","Pending profile photo was not found")
    try:verify_uploaded_object(photo["object_key"],photo["content_type"],photo["size_bytes"])
    except InvalidDocument as exc:return error(request,422,"PROFILE_PHOTO_UPLOAD_INVALID",str(exc))
    now=datetime.now(timezone.utc);public_url=f"/api/gateway/api/v1/public/consultant-profile-photos/{body.photo_id}"
    await db.execute(text("UPDATE external_consultant_profile_photos SET status='REPLACED',replaced_at=:now WHERE profile_id=:profile AND status='AVAILABLE' AND replaced_at IS NULL"),{"now":now,"profile":profile["id"]})
    await db.execute(text("UPDATE external_consultant_profile_photos SET status='AVAILABLE',uploaded_at=:now WHERE id=:id"),{"now":now,"id":body.photo_id})
    version=(await db.execute(text("SELECT projection FROM external_consultant_public_profile_versions WHERE profile_id=:profile AND version=:version FOR UPDATE"),{"profile":profile["id"],"version":profile["working_version"]})).mappings().first()
    projection=dict(version["projection"] or {});projection["profile_photo_url"]=public_url
    qualifications=(await db.execute(text("SELECT COUNT(*) FROM external_consultant_qualifications WHERE profile_id=:profile AND verification_status IN ('PENDING','VERIFIED') AND (expiry_date IS NULL OR expiry_date>=CURRENT_DATE)"),{"profile":profile["id"]})).scalar_one();score,missing=completeness(projection,qualifications)
    await db.execute(text("UPDATE external_consultant_public_profile_versions SET projection=CAST(:projection AS jsonb),completeness=:score,missing_fields=CAST(:missing AS jsonb) WHERE profile_id=:profile AND version=:version"),{"projection":json.dumps(projection),"score":score,"missing":json.dumps(missing),"profile":profile["id"],"version":profile["working_version"]})
    await _marketplace_audit(db,profile["id"],ctx["tenant_id"],"PROFILE_PHOTO_UPDATED",ctx["user_id"],ctx["role"],metadata={"photo_id":str(body.photo_id)})
    await db.commit()
    return {"success":True,"data":{"profile_photo_url":public_url,"completeness":score,"missing_fields":missing},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/marketplace/profile/photo")
async def upload_marketplace_photo(request:Request,filename:str,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    profile=await _marketplace_profile(db,ctx,True)
    if not profile:return error(request,409,"PROFILE_DRAFT_REQUIRED","Save the profile draft before uploading a photo")
    content_type=(request.headers.get("content-type") or "").split(";",1)[0].lower()
    if content_type not in {"image/jpeg","image/png"}:return error(request,422,"INVALID_PROFILE_PHOTO","Profile photo must be a JPEG or PNG image")
    content_length=int(request.headers.get("content-length") or 0)
    if content_length>5*1024*1024:return error(request,422,"INVALID_PROFILE_PHOTO","Profile photo exceeds the 5 MB limit")
    content=await request.body()
    try:clean_name=validate_document(filename,content_type,len(content))
    except InvalidDocument as exc:return error(request,422,"INVALID_PROFILE_PHOTO",str(exc))
    if len(content)>5*1024*1024:return error(request,422,"INVALID_PROFILE_PHOTO","Profile photo exceeds the 5 MB limit")
    photo_id=uuid4();key=new_object_key(ctx["tenant_id"],profile["id"],photo_id,clean_name)
    try:upload_object(key,content_type,content);verify_uploaded_object(key,content_type,len(content))
    except StorageUnavailable:return error(request,503,"PROFILE_PHOTO_STORAGE_UNAVAILABLE","Profile photo storage is not configured")
    except InvalidDocument as exc:return error(request,422,"PROFILE_PHOTO_UPLOAD_INVALID",str(exc))
    now=datetime.now(timezone.utc);public_url=f"/api/gateway/api/v1/public/consultant-profile-photos/{photo_id}"
    await db.execute(text("UPDATE external_consultant_profile_photos SET status='REPLACED',replaced_at=:now WHERE profile_id=:profile AND status='AVAILABLE' AND replaced_at IS NULL"),{"now":now,"profile":profile["id"]})
    await db.execute(text("INSERT INTO external_consultant_profile_photos(id,profile_id,tenant_id,object_key,filename,content_type,size_bytes,status,created_by,created_at,uploaded_at) VALUES(:id,:profile,:tenant,:key,:filename,:type,:size,'AVAILABLE',:actor,:now,:now)"),{"id":photo_id,"profile":profile["id"],"tenant":ctx["tenant_id"],"key":key,"filename":clean_name,"type":content_type,"size":len(content),"actor":ctx["user_id"],"now":now})
    version=(await db.execute(text("SELECT projection FROM external_consultant_public_profile_versions WHERE profile_id=:profile AND version=:version FOR UPDATE"),{"profile":profile["id"],"version":profile["working_version"]})).mappings().first();projection=dict(version["projection"] or {});projection["profile_photo_url"]=public_url
    qualifications=(await db.execute(text("SELECT COUNT(*) FROM external_consultant_qualifications WHERE profile_id=:profile AND verification_status IN ('PENDING','VERIFIED') AND (expiry_date IS NULL OR expiry_date>=CURRENT_DATE)"),{"profile":profile["id"]})).scalar_one();score,missing=completeness(projection,qualifications)
    await db.execute(text("UPDATE external_consultant_public_profile_versions SET projection=CAST(:projection AS jsonb),completeness=:score,missing_fields=CAST(:missing AS jsonb) WHERE profile_id=:profile AND version=:version"),{"projection":json.dumps(projection),"score":score,"missing":json.dumps(missing),"profile":profile["id"],"version":profile["working_version"]})
    await _marketplace_audit(db,profile["id"],ctx["tenant_id"],"PROFILE_PHOTO_UPDATED",ctx["user_id"],ctx["role"],metadata={"photo_id":str(photo_id)})
    await db.commit();return {"success":True,"data":{"profile_photo_url":public_url,"completeness":score,"missing_fields":missing},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/public/consultant-profile-photos/{photo_id}")
async def public_marketplace_photo(photo_id:UUID,db:AsyncSession=Depends(get_db)):
    row=(await db.execute(text("SELECT object_key,content_type FROM external_consultant_profile_photos WHERE id=:id AND status='AVAILABLE' AND replaced_at IS NULL"),{"id":photo_id})).mappings().first()
    if not row:return Response(status_code=404)
    try:return RedirectResponse(signed_view(row["object_key"],row["content_type"]),status_code=307)
    except StorageUnavailable:return Response(status_code=503)

@app.get("/api/v1/practice-operations/marketplace/profile")
async def marketplace_profile(request:Request,include_analytics:bool=True,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    profile=await _marketplace_profile(db,ctx)
    if not profile:return {"success":True,"data":{"state":"CONFIRMED_EMPTY","profile":None,"qualifications":[],"analytics":None},"error":None,"request_id":request.state.correlation_id}
    version=(await db.execute(text("SELECT version,status,projection,completeness,missing_fields,submitted_at,approved_at,published_at FROM external_consultant_public_profile_versions WHERE profile_id=:profile AND version=:version"),{"profile":profile["id"],"version":profile["working_version"]})).mappings().first()
    qualifications=[dict(row) for row in (await db.execute(text("SELECT id,qualification_type,title,institution,award_year,country,registration_number,issuing_body,expiry_date,verification_status,credential_document_id,created_at,updated_at FROM external_consultant_qualifications WHERE profile_id=:profile ORDER BY created_at DESC"),{"profile":profile["id"]})).mappings().all()]
    if not include_analytics:
        return {"success":True,"data":{"state":"READY","profile":dict(profile),"version":dict(version) if version else None,"qualifications":qualifications,"analytics":None},"error":None,"request_id":request.state.correlation_id}
    analytics=(await db.execute(text("""SELECT
      (SELECT COUNT(*) FROM external_consultant_marketplace_events WHERE profile_id=:profile AND event_type='PROFILE_VIEW')::int profile_views,
      (SELECT COUNT(*) FROM external_consultant_marketplace_events WHERE profile_id=:profile AND event_type='ENROL_CLICK')::int enrol_clicks,
      (SELECT COUNT(*) FROM external_consultant_marketplace_events WHERE profile_id=:profile AND event_type='BOOK_CLICK')::int booking_clicks,
      (SELECT COUNT(*) FROM external_marketplace_homepage_events WHERE profile_id=:profile AND event_type='HOMEPAGE_CONSULTANT_IMPRESSION')::int homepage_impressions,
      (SELECT COUNT(*) FROM external_marketplace_homepage_events WHERE profile_id=:profile AND event_type='HOMEPAGE_CONSULTANT_VIEW_CLICK')::int homepage_profile_views,
      (SELECT COUNT(*) FROM external_marketplace_homepage_events WHERE profile_id=:profile AND event_type='HOMEPAGE_ENROL_CLICK')::int homepage_enrol_clicks,
      (SELECT COUNT(*) FROM external_marketplace_comparison_events WHERE profile_id=:profile AND event_type='CONSULTANT_SAVED')::int times_saved,
      (SELECT COUNT(*) FROM external_marketplace_comparison_events WHERE CAST(:profile AS text) IN (SELECT jsonb_array_elements_text(compared_profile_ids)) AND event_type='COMPARISON_OPENED')::int comparison_appearances,
      (SELECT COUNT(*) FROM external_marketplace_comparison_events WHERE profile_id=:profile AND event_type='COMPARE_PROFILE_CLICK')::int comparison_profile_clicks,
      (SELECT COUNT(*) FROM external_marketplace_comparison_events WHERE profile_id=:profile AND event_type='COMPARE_ENROL_CLICK')::int comparison_enrol_clicks,
      (SELECT COUNT(*) FROM external_marketplace_finder_events WHERE profile_id=:profile AND event_type='FINDER_RESULT_VIEW')::int finder_impressions,
      (SELECT COUNT(*) FROM external_marketplace_finder_events WHERE profile_id=:profile AND event_type='FINDER_PROFILE_CLICK')::int finder_profile_clicks,
      (SELECT COUNT(*) FROM external_marketplace_finder_events WHERE profile_id=:profile AND event_type='FINDER_ENROL_CLICK')::int finder_enrol_clicks"""),{"profile":profile["id"]})).mappings().one()
    funnel=(await db.execute(text("SELECT COUNT(*) FILTER(WHERE event_type='BOOKING_STARTED')::int booking_starts,COUNT(*) FILTER(WHERE event_type='ENROLMENT_SUBMITTED')::int enrolment_requests,COUNT(*) FILTER(WHERE event_type='BOOKING_CONFIRMED')::int direct_bookings,COUNT(*) FILTER(WHERE event_type='WAITLIST_JOINED')::int waitlist_joins,COUNT(*) FILTER(WHERE event_type='BOOKING_FAILED_SLOT_CONFLICT')::int slot_conflicts FROM external_consultant_marketplace_events WHERE profile_id=:profile"),{"profile":profile["id"]})).mappings().one()
    review=(await db.execute(text("SELECT COUNT(*)::int review_count,AVG(overall_rating)::numeric(3,2) average_rating FROM external_consultant_reviews WHERE profile_id=:profile AND verified_engagement=TRUE AND status='PUBLISHED'"),{"profile":profile["id"]})).mappings().one()
    enrolments=(await db.execute(text("SELECT COUNT(*)::int total,COUNT(*) FILTER(WHERE status='NEW')::int new_count FROM external_consultant_marketplace_enrolments WHERE profile_id=:profile"),{"profile":profile["id"]})).mappings().one()
    return {"success":True,"data":{"state":"READY","profile":dict(profile),"version":dict(version) if version else None,"qualifications":qualifications,"analytics":{**dict(analytics),**dict(review),**dict(funnel),"enrolments":dict(enrolments)}},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/marketplace/readiness")
async def marketplace_readiness(request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    packages=[dict(row) for row in (await db.execute(text("SELECT id,name,description,session_allowance,duration_days,price_minor,currency,active FROM external_service_packages WHERE tenant_id=:tenant AND active=TRUE ORDER BY name"),{"tenant":ctx["tenant_id"]})).mappings().all()]
    appointment_types=[dict(row) for row in (await db.execute(text("SELECT id,name,description,duration_minutes,location_type,location_details,active FROM external_appointment_types WHERE tenant_id=:tenant AND active=TRUE ORDER BY name"),{"tenant":ctx["tenant_id"]})).mappings().all()]
    locations=[dict(row) for row in (await db.execute(text("SELECT id,name,timezone,active FROM external_practice_locations WHERE tenant_id=:tenant AND active=TRUE ORDER BY name"),{"tenant":ctx["tenant_id"]})).mappings().all()]
    availability=[dict(row) for row in (await db.execute(text("SELECT id,weekday,start_time,end_time,timezone FROM external_availability_rules WHERE tenant_id=:tenant AND active=TRUE ORDER BY weekday,start_time"),{"tenant":ctx["tenant_id"]})).mappings().all()]
    documents=[dict(row) for row in (await db.execute(text("SELECT id,title,category,visibility,status FROM external_documents WHERE tenant_id=:tenant AND client_id IS NULL AND status='AVAILABLE' AND visibility IN ('PRACTITIONER_PRIVATE','PRACTICE_ADMINISTRATIVE') ORDER BY updated_at DESC LIMIT 100"),{"tenant":ctx["tenant_id"]})).mappings().all()]
    return {"success":True,"data":{"state":"READY","packages":packages,"appointment_types":appointment_types,"locations":locations,"availability":availability,"private_documents":documents,"direct_booking":"CONFIGURATION_DEPENDENT"},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/marketplace/reviews")
async def marketplace_reviews(request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    profile=await _marketplace_profile(db,ctx)
    if not profile:return {"success":True,"data":{"state":"CONFIRMED_EMPTY","items":[]},"error":None,"request_id":request.state.correlation_id}
    rows=[dict(row) for row in (await db.execute(text("SELECT id,overall_rating,review_text,status,verified_engagement,reported_at,created_at FROM external_consultant_reviews WHERE profile_id=:profile AND tenant_id=:tenant ORDER BY created_at DESC LIMIT 100"),{"profile":profile["id"],"tenant":ctx["tenant_id"]})).mappings().all()]
    return {"success":True,"data":{"state":"READY" if rows else "CONFIRMED_EMPTY","items":rows},"error":None,"request_id":request.state.correlation_id}

@app.put("/api/v1/practice-operations/marketplace/profile")
async def save_marketplace_profile(request:Request,body:ProfileSave,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    for service in body.services:
        valid=(await db.execute(text("SELECT 1 FROM external_appointment_types WHERE id=:id AND tenant_id=:tenant AND active=TRUE"),{"id":UUID(service.id),"tenant":ctx["tenant_id"]})).first()
        if not valid:return error(request,422,"GOVERNED_SERVICE_REQUIRED","Public services must reference an active tenant appointment type")
        if service.location_id:
            located=(await db.execute(text("SELECT 1 FROM external_practice_locations WHERE id=:id AND tenant_id=:tenant AND active=TRUE"),{"id":UUID(service.location_id),"tenant":ctx["tenant_id"]})).first()
            if not located:return error(request,422,"GOVERNED_LOCATION_REQUIRED","Public service location must reference an active tenant location")
    for programme in body.programmes:
        valid=(await db.execute(text("SELECT 1 FROM external_service_packages WHERE id=:id AND tenant_id=:tenant AND active=TRUE"),{"id":UUID(programme.id),"tenant":ctx["tenant_id"]})).first()
        if not valid:return error(request,422,"GOVERNED_PROGRAMME_REQUIRED","Public programmes must reference an active tenant package")
    for location in body.public_locations:
        if location.mode!="ONLINE":
            valid=(await db.execute(text("SELECT 1 FROM external_practice_locations WHERE id=:id AND tenant_id=:tenant AND active=TRUE"),{"id":UUID(location.id),"tenant":ctx["tenant_id"]})).first()
            if not valid:return error(request,422,"GOVERNED_LOCATION_REQUIRED","Public locations must reference an active tenant location")
    now=datetime.now(timezone.utc);payload=public_projection(body.model_dump());existing=await _marketplace_profile(db,ctx,True)
    if existing:
        if existing["status"] in {"SUBMITTED_FOR_REVIEW","UNDER_REVIEW"}:return error(request,409,"PROFILE_LOCKED_FOR_REVIEW","Withdraw or wait for review before editing")
        version=existing["working_version"]+1 if existing["status"] in {"PUBLISHED","APPROVED","UNPUBLISHED"} and existing["working_version"]==existing["current_published_version"] else existing["working_version"]
        profile_id=existing["id"];status="DRAFT";slug=existing["slug"]
    else:
        base=slug_base(body.display_name);candidate=base;suffix=1
        while (await db.execute(text("SELECT 1 FROM external_consultant_public_profiles WHERE slug=:slug"),{"slug":candidate})).first():suffix+=1;candidate=f"{base}-{suffix}"
        profile_id=uuid4();version=1;status="DRAFT";slug=candidate
        await db.execute(text("INSERT INTO external_consultant_public_profiles(id,tenant_id,consultant_user_id,slug,status,public_visibility,accepting_new_clients,working_version,approval_valid,created_at,updated_at) VALUES (:id,:tenant,:actor,:slug,'DRAFT',FALSE,:accepting,1,FALSE,:now,:now)"),{"id":profile_id,"tenant":ctx["tenant_id"],"actor":ctx["user_id"],"slug":slug,"accepting":body.accepting_new_clients,"now":now})
        await _marketplace_audit(db,profile_id,ctx["tenant_id"],"PROFILE_DRAFT_CREATED",ctx["user_id"],ctx["role"])
    qualifications=(await db.execute(text("SELECT COUNT(*) FROM external_consultant_qualifications WHERE profile_id=:profile AND verification_status IN ('PENDING','VERIFIED') AND (expiry_date IS NULL OR expiry_date>=CURRENT_DATE)"),{"profile":profile_id})).scalar_one()
    score,missing=completeness(payload,qualifications)
    await db.execute(text("INSERT INTO external_consultant_public_profile_versions(id,profile_id,tenant_id,version,status,projection,completeness,missing_fields,created_by,created_at) VALUES (:id,:profile,:tenant,:version,'DRAFT',CAST(:projection AS jsonb),:score,CAST(:missing AS jsonb),:actor,:now) ON CONFLICT(profile_id,version) DO UPDATE SET projection=EXCLUDED.projection,completeness=EXCLUDED.completeness,missing_fields=EXCLUDED.missing_fields,status='DRAFT'"),{"id":uuid4(),"profile":profile_id,"tenant":ctx["tenant_id"],"version":version,"projection":json.dumps(payload),"score":score,"missing":json.dumps(missing),"actor":ctx["user_id"],"now":now})
    live_approval=bool(existing and existing["current_published_version"] and existing["approval_valid"])
    await db.execute(text("UPDATE external_consultant_public_profiles SET status=:status,working_version=:version,accepting_new_clients=:accepting,approval_valid=:live_approval,approved_version=NULL,updated_at=:now WHERE id=:id AND tenant_id=:tenant"),{"status":status,"version":version,"accepting":body.accepting_new_clients,"live_approval":live_approval,"now":now,"id":profile_id,"tenant":ctx["tenant_id"]})
    await _marketplace_audit(db,profile_id,ctx["tenant_id"],"PROFILE_UPDATED",ctx["user_id"],ctx["role"],metadata={"version":version,"completeness":score});await db.commit()
    return {"success":True,"data":{"id":str(profile_id),"slug":slug,"status":status,"version":version,"completeness":score,"missing_fields":missing},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/marketplace/profile/submit")
async def submit_marketplace_profile(request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    profile=await _marketplace_profile(db,ctx,True)
    if not profile:return error(request,404,"PROFILE_NOT_FOUND","Create the public profile draft first")
    version=(await db.execute(text("SELECT completeness FROM external_consultant_public_profile_versions WHERE profile_id=:profile AND version=:version"),{"profile":profile["id"],"version":profile["working_version"]})).mappings().first()
    if not version or version["completeness"]<100:return error(request,422,"PROFILE_INCOMPLETE","Complete every required marketplace field before submission")
    try:assert_transition(profile["status"],"SUBMITTED_FOR_REVIEW")
    except ValueError as exc:return error(request,409,"INVALID_PROFILE_TRANSITION",str(exc))
    now=datetime.now(timezone.utc);await db.execute(text("UPDATE external_consultant_public_profiles SET status='SUBMITTED_FOR_REVIEW',updated_at=:now WHERE id=:id"),{"now":now,"id":profile["id"]});await db.execute(text("UPDATE external_consultant_public_profile_versions SET status='SUBMITTED_FOR_REVIEW',submitted_at=:now WHERE profile_id=:id AND version=:version"),{"now":now,"id":profile["id"],"version":profile["working_version"]});await _marketplace_audit(db,profile["id"],ctx["tenant_id"],"PROFILE_SUBMITTED",ctx["user_id"],ctx["role"]);await db.commit()
    return {"success":True,"data":{"status":"SUBMITTED_FOR_REVIEW"},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/marketplace/qualifications")
async def add_marketplace_qualification(request:Request,body:QualificationCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    profile=await _marketplace_profile(db,ctx)
    if not profile:return error(request,404,"PROFILE_NOT_FOUND","Create the public profile draft first")
    document=body.credential_document_id
    if document:
        owned=(await db.execute(text("SELECT 1 FROM external_documents WHERE id=:id AND tenant_id=:tenant AND visibility IN ('PRACTITIONER_PRIVATE','PRACTICE_ADMINISTRATIVE')"),{"id":document,"tenant":ctx["tenant_id"]})).first()
        if not owned:return error(request,422,"PRIVATE_CREDENTIAL_DOCUMENT_REQUIRED","Credential evidence must be a private governed document")
    item=uuid4();now=datetime.now(timezone.utc);await db.execute(text("INSERT INTO external_consultant_qualifications(id,profile_id,tenant_id,qualification_type,title,institution,award_year,country,registration_number,issuing_body,expiry_date,verification_status,credential_document_id,created_at,updated_at) VALUES (:id,:profile,:tenant,:type,:title,:institution,:year,:country,:registration,:issuer,:expiry,'PENDING',:document,:now,:now)"),{"id":item,"profile":profile["id"],"tenant":ctx["tenant_id"],"type":body.qualification_type,"title":body.title,"institution":body.institution,"year":body.award_year,"country":body.country,"registration":body.registration_number,"issuer":body.issuing_body,"expiry":body.expiry_date,"document":document,"now":now})
    current=(await db.execute(text("SELECT p.working_version,v.projection FROM external_consultant_public_profiles p JOIN external_consultant_public_profile_versions v ON v.profile_id=p.id AND v.version=p.working_version WHERE p.id=:profile"),{"profile":profile["id"]})).mappings().first()
    if current:
        count=(await db.execute(text("SELECT COUNT(*) FROM external_consultant_qualifications WHERE profile_id=:profile AND verification_status IN ('PENDING','VERIFIED') AND (expiry_date IS NULL OR expiry_date>=CURRENT_DATE)"),{"profile":profile["id"]})).scalar_one()
        score,missing=completeness(dict(current["projection"]),count);await db.execute(text("UPDATE external_consultant_public_profile_versions SET completeness=:score,missing_fields=CAST(:missing AS jsonb) WHERE profile_id=:profile AND version=:version"),{"score":score,"missing":json.dumps(missing),"profile":profile["id"],"version":current["working_version"]})
    await _marketplace_audit(db,profile["id"],ctx["tenant_id"],"QUALIFICATION_ADDED",ctx["user_id"],ctx["role"],metadata={"qualification_id":str(item)});await db.commit();return {"success":True,"data":{"id":str(item),"verification_status":"PENDING"},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/marketplace/qualifications/{qualification_id}/evidence-upload")
async def prepare_qualification_evidence(qualification_id:UUID,request:Request,body:QualificationEvidencePrepare,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    profile=await _marketplace_profile(db,ctx,True)
    if not profile:return error(request,404,"PROFILE_NOT_FOUND","Create the public profile draft first")
    qualification=(await db.execute(text("SELECT id,title FROM external_consultant_qualifications WHERE id=:id AND profile_id=:profile AND tenant_id=:tenant"),{"id":qualification_id,"profile":profile["id"],"tenant":ctx["tenant_id"]})).mappings().first()
    if not qualification:return error(request,404,"QUALIFICATION_NOT_FOUND","Qualification was not found")
    filename=body.filename.strip();content_type=body.content_type.lower()
    try:filename=validate_document(filename,content_type,body.size_bytes)
    except InvalidDocument as exc:return error(request,422,"INVALID_CREDENTIAL_EVIDENCE",str(exc))
    if body.size_bytes>10*1024*1024:return error(request,422,"INVALID_CREDENTIAL_EVIDENCE","Certificate evidence exceeds the 10 MB limit")
    document_id=uuid4();version_id=uuid4();key=new_credential_evidence_key(ctx["tenant_id"],profile["id"],qualification_id,filename)
    try:url=signed_upload(key,content_type,body.size_bytes)
    except StorageUnavailable:return error(request,503,"CREDENTIAL_EVIDENCE_STORAGE_UNAVAILABLE","Certificate storage is not configured")
    now=datetime.now(timezone.utc)
    await db.execute(text("INSERT INTO external_documents(id,tenant_id,client_id,title,category,visibility,status,tags,current_version,created_by,created_at,updated_at) VALUES (:id,:tenant,NULL,:title,'MARKETPLACE_CREDENTIAL','PRACTITIONER_PRIVATE','PENDING_UPLOAD',CAST(:tags AS jsonb),1,:actor,:now,:now)"),{"id":document_id,"tenant":ctx["tenant_id"],"title":f"{qualification['title']} certificate","tags":json.dumps(["marketplace-credential",str(qualification_id)]),"actor":ctx["user_id"],"now":now})
    await db.execute(text("INSERT INTO external_document_versions(id,document_id,tenant_id,version,status,object_key,filename,content_type,size_bytes,checksum_sha256,uploaded_by,uploaded_at) VALUES (:id,:document,:tenant,1,'PENDING_UPLOAD',:key,:filename,:content_type,:size,NULL,:actor,NULL)"),{"id":version_id,"document":document_id,"tenant":ctx["tenant_id"],"key":key,"filename":filename,"content_type":content_type,"size":body.size_bytes,"actor":ctx["user_id"]})
    await db.execute(text("INSERT INTO external_document_links(id,document_id,tenant_id,link_type,linked_id,created_at) VALUES (:id,:document,:tenant,'MARKETPLACE_QUALIFICATION',:linked,:now)"),{"id":uuid4(),"document":document_id,"tenant":ctx["tenant_id"],"linked":str(qualification_id),"now":now})
    await db.execute(text("INSERT INTO external_document_audit_events(id,document_id,tenant_id,event_type,actor_id,metadata,created_at) VALUES (:id,:document,:tenant,'UPLOAD_REQUESTED',:actor,CAST(:metadata AS jsonb),:now)"),{"id":uuid4(),"document":document_id,"tenant":ctx["tenant_id"],"actor":ctx["user_id"],"metadata":json.dumps({"qualification_id":str(qualification_id),"version_id":str(version_id)}),"now":now})
    await db.commit()
    return {"success":True,"data":{"document_id":str(document_id),"version_id":str(version_id),"upload":{"url":url,"method":"PUT","expires_in":600,"required_headers":{"Content-Type":content_type}}},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/marketplace/qualifications/{qualification_id}/evidence-finalise")
async def finalise_qualification_evidence(qualification_id:UUID,request:Request,body:QualificationEvidenceFinalise,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    profile=await _marketplace_profile(db,ctx,True)
    if not profile:return error(request,404,"PROFILE_NOT_FOUND","Profile was not found")
    row=(await db.execute(text("SELECT q.credential_document_id,d.id document_id,v.id version_id,v.object_key,v.content_type,v.size_bytes FROM external_consultant_qualifications q JOIN external_document_links l ON l.link_type='MARKETPLACE_QUALIFICATION' AND l.linked_id=CAST(q.id AS text) JOIN external_documents d ON d.id=l.document_id AND d.tenant_id=q.tenant_id JOIN external_document_versions v ON v.document_id=d.id AND v.id=:version WHERE q.id=:qualification AND q.profile_id=:profile AND q.tenant_id=:tenant AND d.id=:document AND d.status='PENDING_UPLOAD' AND v.status='PENDING_UPLOAD' FOR UPDATE"),{"qualification":qualification_id,"profile":profile["id"],"tenant":ctx["tenant_id"],"document":body.document_id,"version":body.version_id})).mappings().first()
    if not row:return error(request,404,"CREDENTIAL_EVIDENCE_UPLOAD_NOT_FOUND","Pending certificate upload was not found")
    try:verify_uploaded_object(row["object_key"],row["content_type"],row["size_bytes"])
    except StorageUnavailable:return error(request,503,"CREDENTIAL_EVIDENCE_STORAGE_UNAVAILABLE","Certificate storage is not configured")
    except InvalidDocument as exc:return error(request,422,"CREDENTIAL_EVIDENCE_UPLOAD_INVALID",str(exc))
    now=datetime.now(timezone.utc)
    await db.execute(text("UPDATE external_documents SET status='AVAILABLE',updated_at=:now WHERE id=:id AND tenant_id=:tenant"),{"now":now,"id":body.document_id,"tenant":ctx["tenant_id"]})
    await db.execute(text("UPDATE external_document_versions SET status='AVAILABLE',uploaded_at=:now WHERE id=:id AND tenant_id=:tenant"),{"now":now,"id":body.version_id,"tenant":ctx["tenant_id"]})
    await db.execute(text("UPDATE external_consultant_qualifications SET credential_document_id=:document,verification_status='PENDING',verified_by=NULL,verified_at=NULL,rejection_reason=NULL,updated_at=:now WHERE id=:id AND profile_id=:profile AND tenant_id=:tenant"),{"document":body.document_id,"now":now,"id":qualification_id,"profile":profile["id"],"tenant":ctx["tenant_id"]})
    await db.execute(text("INSERT INTO external_document_audit_events(id,document_id,tenant_id,event_type,actor_id,metadata,created_at) VALUES (:id,:document,:tenant,'UPLOAD_VERIFIED',:actor,CAST(:metadata AS jsonb),:now)"),{"id":uuid4(),"document":body.document_id,"tenant":ctx["tenant_id"],"actor":ctx["user_id"],"metadata":json.dumps({"qualification_id":str(qualification_id),"version_id":str(body.version_id)}),"now":now})
    await _marketplace_audit(db,profile["id"],ctx["tenant_id"],"QUALIFICATION_EVIDENCE_ATTACHED",ctx["user_id"],ctx["role"],metadata={"qualification_id":str(qualification_id),"document_id":str(body.document_id)})
    await db.commit()
    return {"success":True,"data":{"qualification_id":str(qualification_id),"evidence_status":"AVAILABLE","verification_status":"PENDING"},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/marketplace/enrolments")
async def marketplace_enrolments(request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    profile=await _marketplace_profile(db,ctx)
    if not profile:return {"success":True,"data":{"state":"CONFIRMED_EMPTY","items":[]},"error":None,"request_id":request.state.correlation_id}
    rows=[dict(row) for row in (await db.execute(text("SELECT id,lead_id,service_id,programme_id,full_name,email,phone,consultation_mode,location_id,preferred_at,message,status,created_at,updated_at FROM external_consultant_marketplace_enrolments WHERE profile_id=:profile AND tenant_id=:tenant ORDER BY created_at DESC LIMIT 100"),{"profile":profile["id"],"tenant":ctx["tenant_id"]})).mappings().all()]
    return {"success":True,"data":{"state":"READY" if rows else "CONFIRMED_EMPTY","items":rows},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/marketplace/enrolments/{enrolment_id}/action")
async def marketplace_enrolment_action(enrolment_id:UUID,request:Request,body:EnrolmentAction,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    profile=await _marketplace_profile(db,ctx)
    if not profile:return error(request,404,"PROFILE_NOT_FOUND","Marketplace profile was not found")
    row=(await db.execute(text("SELECT id,lead_id,status FROM external_consultant_marketplace_enrolments WHERE id=:id AND profile_id=:profile AND tenant_id=:tenant FOR UPDATE"),{"id":enrolment_id,"profile":profile["id"],"tenant":ctx["tenant_id"]})).mappings().first()
    if not row:return error(request,404,"ENROLMENT_NOT_FOUND","Enrolment was not found")
    action=body.action.upper();target={"CONTACT":"CONTACTED","ACCEPT":"ACCEPTED","BOOK":"BOOKED","DECLINE":"DECLINED","CANCEL":"CANCELLED","CONVERT":"CONVERTED"}.get(action)
    allowed={"NEW":{"CONTACTED","ACCEPTED","DECLINED","CANCELLED"},"CONTACTED":{"ACCEPTED","BOOKED","DECLINED","CANCELLED"},"ACCEPTED":{"BOOKED","DECLINED","CANCELLED"},"BOOKED":{"CONVERTED","DECLINED","CANCELLED"}}
    if target not in allowed.get(row["status"],set()):return error(request,409,"INVALID_ENROLMENT_TRANSITION","Enrolment transition is not permitted")
    if target=="CONVERTED":
        converted=(await db.execute(text("SELECT converted_client_id FROM external_leads WHERE id=:lead AND tenant_id=:tenant AND stage='CONVERTED'"),{"lead":row["lead_id"],"tenant":ctx["tenant_id"]})).scalar_one_or_none()
        if not converted:return error(request,409,"CLIENT_CORE_CONVERSION_REQUIRED","Convert the linked P24 lead through the governed Client Core flow first")
    lead_stage={"CONTACTED":"CONTACTED","ACCEPTED":"QUALIFIED","BOOKED":"CONSULTATION_BOOKED","DECLINED":"NOT_INTERESTED"}.get(target)
    if lead_stage:await db.execute(text("UPDATE external_leads SET stage=:stage,updated_at=:now WHERE id=:lead AND tenant_id=:tenant"),{"stage":lead_stage,"now":datetime.now(timezone.utc),"lead":row["lead_id"],"tenant":ctx["tenant_id"]})
    await db.execute(text("UPDATE external_consultant_marketplace_enrolments SET status=:status,updated_at=:now WHERE id=:id"),{"status":target,"now":datetime.now(timezone.utc),"id":enrolment_id});await _marketplace_audit(db,profile["id"],ctx["tenant_id"],f"ENROLMENT_{target}",ctx["user_id"],ctx["role"],body.reason,{"enrolment_id":str(enrolment_id)});await db.commit();return {"success":True,"data":{"status":target},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/admin/marketplace")
async def admin_marketplace(request:Request,status:str|None=None,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=_platform_admin(request,ctx)
    if denied:return denied
    params={"status":status};rows=[dict(row) for row in (await db.execute(text("SELECT p.id,p.tenant_id,p.consultant_user_id,p.slug,p.status,p.public_visibility,p.accepting_new_clients,p.current_published_version,p.working_version,p.approved_version,p.approval_valid,p.updated_at,v.projection,v.completeness,v.missing_fields,COALESCE(h.featured_on_homepage,FALSE) featured_on_homepage,h.featured_rank,h.featured_from,h.featured_until FROM external_consultant_public_profiles p JOIN external_consultant_public_profile_versions v ON v.profile_id=p.id AND v.version=p.working_version LEFT JOIN external_consultant_homepage_features h ON h.profile_id=p.id WHERE (CAST(:status AS text) IS NULL OR p.status=CAST(:status AS text)) ORDER BY p.updated_at DESC LIMIT 200"),params)).mappings().all()]
    return {"success":True,"data":{"state":"READY" if rows else "CONFIRMED_EMPTY","items":rows},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/admin/marketplace/consultants")
async def admin_marketplace_consultants(request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=_platform_admin(request,ctx)
    if denied:return denied
    identities=[]
    async with httpx.AsyncClient(timeout=10.0) as client:
        for role in ("consultant","senior_consultant","practitioner"):
            try:
                response=await client.get(
                    f"{get_settings().auth_service_url.rstrip('/')}/api/v1/owner/people-access/users",
                    params={"role":role,"page":1,"page_size":100},
                    headers={"X-User-Id":ctx["user_id"],"Accept":"application/json"},
                )
            except httpx.HTTPError:
                return error(request,503,"CONSULTANT_INVENTORY_UNAVAILABLE","Consultant account inventory is unavailable",True)
            if response.status_code!=200:
                return error(request,503,"CONSULTANT_INVENTORY_UNAVAILABLE","Consultant account inventory is unavailable",True)
            payload=response.json();identities.extend((payload.get("data") or {}).get("items") or [])
    unique={str(item.get("id")):item for item in identities if item.get("id")}
    profiles=[dict(row) for row in (await db.execute(text("""SELECT p.id,p.tenant_id,p.consultant_user_id,p.slug,p.status,p.public_visibility,p.accepting_new_clients,p.approval_valid,p.suspended_at,v.projection,v.completeness,v.missing_fields,COALESCE(h.featured_on_homepage,FALSE) featured_on_homepage,COALESCE(q.verified_count,0)::int verified_qualifications FROM external_consultant_public_profiles p JOIN external_consultant_public_profile_versions v ON v.profile_id=p.id AND v.version=p.working_version LEFT JOIN external_consultant_homepage_features h ON h.profile_id=p.id LEFT JOIN (SELECT profile_id,COUNT(*) FILTER(WHERE verification_status='VERIFIED') verified_count FROM external_consultant_qualifications GROUP BY profile_id) q ON q.profile_id=p.id"""))).mappings().all()]
    by_user={str(row["consultant_user_id"]):row for row in profiles}
    items=[]
    for user_id,user in unique.items():
        profile=by_user.get(user_id);projection=dict(profile["projection"]) if profile else {}
        status=profile["status"] if profile else "NOT_STARTED"
        blockers=[]
        if str(user.get("status") or "").upper()!="ACTIVE":blockers.append("ACCOUNT_INACTIVE")
        if not profile:blockers.append("PROFILE_INCOMPLETE")
        elif profile["completeness"]<100:blockers.append("PROFILE_INCOMPLETE")
        if not profile or profile["verified_qualifications"]<1:blockers.append("NO_VERIFIED_QUALIFICATION")
        if profile and status=="SUSPENDED":eligibility="SUSPENDED"
        elif profile and status=="PUBLISHED" and profile["public_visibility"] and profile["approval_valid"] and not profile["suspended_at"]:eligibility="PUBLIC"
        elif profile and status=="APPROVED":eligibility="APPROVED_NOT_PUBLISHED"
        elif profile and status in {"SUBMITTED_FOR_REVIEW","UNDER_REVIEW"}:eligibility="UNDER_REVIEW"
        elif blockers:eligibility="NOT_ELIGIBLE"
        else:eligibility="ELIGIBLE_TO_SUBMIT"
        if eligibility=="SUSPENDED":visibility="SUSPENDED"
        elif eligibility=="PUBLIC":visibility="DIRECTORY_AND_HOMEPAGE" if profile["featured_on_homepage"] else "DIRECTORY_ONLY"
        else:visibility="NOT_VISIBLE"
        items.append({"user_id":user_id,"name":user.get("name"),"email":user.get("email"),"phone":user.get("phone"),"profession":projection.get("profession_code") or projection.get("professional_title"),"practice":user.get("organization"),"account_status":user.get("status"),"profile_id":str(profile["id"]) if profile else None,"slug":profile["slug"] if profile else None,"marketplace_status":status,"profile_completeness":profile["completeness"] if profile else 0,"qualification_status":"VERIFIED" if profile and profile["verified_qualifications"] else "NOT_VERIFIED","eligibility":eligibility,"eligibility_blockers":blockers,"published":visibility in {"DIRECTORY_ONLY","DIRECTORY_AND_HOMEPAGE"},"homepage_featured":visibility=="DIRECTORY_AND_HOMEPAGE","accepting_new_clients":bool(profile and profile["accepting_new_clients"]),"website_visibility":visibility,"demo":str(user.get("name") or "").startswith("Demo Consultant —")})
    items.sort(key=lambda item:(item["name"] or "").lower())
    counts={key:sum(1 for item in items if item["marketplace_status"] in values) for key,values in {"not_started":{"NOT_STARTED"},"draft":{"DRAFT"},"pending_review":{"SUBMITTED_FOR_REVIEW","UNDER_REVIEW"},"changes_required":{"CHANGES_REQUIRED"},"approved":{"APPROVED"},"published":{"PUBLISHED"},"suspended":{"SUSPENDED"}}.items()}
    counts.update(total=len(items),featured=sum(1 for item in items if item["homepage_featured"]))
    return {"success":True,"data":{"state":"READY" if items else "CONFIRMED_EMPTY","items":items,"summary":counts},"error":None,"request_id":request.state.correlation_id}

@app.put("/api/v1/practice-operations/admin/marketplace/profiles/{profile_id}/homepage-feature")
async def admin_marketplace_homepage_feature(profile_id:UUID,request:Request,body:HomepageFeatureDecision,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=_platform_admin(request,ctx)
    if denied:return denied
    profile=(await db.execute(text("SELECT id,tenant_id,status,public_visibility,approval_valid,suspended_at FROM external_consultant_public_profiles WHERE id=:id FOR UPDATE"),{"id":profile_id})).mappings().first()
    if not profile:return error(request,404,"PROFILE_NOT_FOUND","Profile was not found")
    eligible=profile["status"]=="PUBLISHED" and profile["public_visibility"] and profile["approval_valid"] and not profile["suspended_at"]
    if body.featured_on_homepage and not eligible:return error(request,409,"PROFILE_NOT_SHOWCASE_ELIGIBLE","Only an approved, published, visible and unsuspended profile can be featured")
    if body.featured_on_homepage and body.featured_rank is None:return error(request,422,"FEATURED_RANK_REQUIRED","A deterministic homepage rank is required")
    now=datetime.now(timezone.utc)
    await db.execute(text("""INSERT INTO external_consultant_homepage_features(profile_id,tenant_id,featured_on_homepage,featured_rank,featured_from,featured_until,featured_by,featured_at,updated_at)
      VALUES (:profile,:tenant,:enabled,:rank,:start,:end,:actor,CASE WHEN :enabled THEN :now ELSE NULL END,:now)
      ON CONFLICT(profile_id) DO UPDATE SET featured_on_homepage=EXCLUDED.featured_on_homepage,featured_rank=EXCLUDED.featured_rank,featured_from=EXCLUDED.featured_from,featured_until=EXCLUDED.featured_until,featured_by=EXCLUDED.featured_by,featured_at=CASE WHEN EXCLUDED.featured_on_homepage THEN :now ELSE external_consultant_homepage_features.featured_at END,updated_at=:now"""),{"profile":profile_id,"tenant":profile["tenant_id"],"enabled":body.featured_on_homepage,"rank":body.featured_rank if body.featured_on_homepage else None,"start":body.featured_from,"end":body.featured_until,"actor":ctx["user_id"],"now":now})
    await _marketplace_audit(db,profile_id,profile["tenant_id"],"HOMEPAGE_FEATURED" if body.featured_on_homepage else "HOMEPAGE_REMOVED",ctx["user_id"],ctx["role"],metadata={"rank":body.featured_rank,"featured_from":body.featured_from.isoformat() if body.featured_from else None,"featured_until":body.featured_until.isoformat() if body.featured_until else None});await db.commit()
    return {"success":True,"data":{"featured_on_homepage":body.featured_on_homepage,"featured_rank":body.featured_rank if body.featured_on_homepage else None},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/admin/marketplace/profiles/{profile_id}/decision")
async def admin_marketplace_decision(profile_id:UUID,request:Request,body:AdminDecision,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=_platform_admin(request,ctx)
    if denied:return denied
    action=body.action.upper();target=ADMIN_ACTIONS.get(action)
    if not target:return error(request,422,"UNKNOWN_MARKETPLACE_ACTION","Marketplace action is not recognised")
    if action in REASON_REQUIRED and not body.reason:return error(request,422,"REASON_REQUIRED","A reason is required")
    profile=(await db.execute(text("SELECT id,tenant_id,status,public_visibility,working_version,approved_version,approval_valid,current_published_version FROM external_consultant_public_profiles WHERE id=:id FOR UPDATE"),{"id":profile_id})).mappings().first()
    if not profile:return error(request,404,"PROFILE_NOT_FOUND","Profile was not found")
    if action in {"APPROVE_PROFILE","PUBLISH_PROFILE","PUBLISH_SUBMISSION"}:
        verified=(await db.execute(text("SELECT COUNT(*) FROM external_consultant_qualifications WHERE profile_id=:profile AND verification_status='VERIFIED' AND (expiry_date IS NULL OR expiry_date>=CURRENT_DATE)"),{"profile":profile_id})).scalar_one()
        if not verified:return error(request,409,"VERIFIED_QUALIFICATION_REQUIRED","Verify at least one qualification before approval or publication")
    direct_publish=action=="PUBLISH_SUBMISSION" and profile["status"] in {"SUBMITTED_FOR_REVIEW","UNDER_REVIEW"}
    if action=="PUBLISH_SUBMISSION" and not direct_publish:return error(request,409,"INVALID_PROFILE_TRANSITION","Only a submitted profile can be published directly")
    if action=="PUBLISH_PROFILE" and not can_publish(profile):return error(request,409,"PROFILE_NOT_APPROVED_FOR_PUBLICATION","Approve this exact version before publication")
    try:assert_transition(profile["status"],target)
    except ValueError as exc:return error(request,409,"INVALID_PROFILE_TRANSITION",str(exc))
    now=datetime.now(timezone.utc);fields={"status":target,"visibility":profile["public_visibility"],"valid":profile["approval_valid"],"approved":profile["approved_version"],"published":profile["current_published_version"],"suspended":now if target=="SUSPENDED" else None}
    if target=="APPROVED":fields.update(valid=True,approved=profile["working_version"])
    if target=="PUBLISHED":fields.update(published=profile["working_version"],visibility=True,suspended=None)
    if direct_publish:fields.update(valid=True,approved=profile["working_version"])
    if target in {"UNPUBLISHED","SUSPENDED"}:fields.update(visibility=False)
    if target in {"CHANGES_REQUIRED","REJECTED"}:fields.update(valid=bool(profile["current_published_version"]),approved=None)
    await db.execute(text("UPDATE external_consultant_public_profiles SET status=:status,public_visibility=:visibility,approval_valid=:valid,approved_version=:approved,current_published_version=:published,suspended_at=:suspended,updated_at=:now WHERE id=:id"),{**fields,"now":now,"id":profile_id})
    await db.execute(text("UPDATE external_consultant_public_profile_versions SET status=CAST(:status AS VARCHAR),approved_at=CASE WHEN CAST(:status AS VARCHAR)='APPROVED' OR :direct_publish THEN :now ELSE approved_at END,published_at=CASE WHEN CAST(:status AS VARCHAR)='PUBLISHED' THEN :now ELSE published_at END WHERE profile_id=:id AND version=:version"),{"status":target,"direct_publish":direct_publish,"now":now,"id":profile_id,"version":profile["working_version"]})
    await _marketplace_audit(db,profile_id,profile["tenant_id"],action.replace("_PROFILE","") if action.startswith("PROFILE_") else action,ctx["user_id"],ctx["role"],body.reason,{"version":profile["working_version"]});await db.commit()
    return {"success":True,"data":{"status":target,"published":target=="PUBLISHED"},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/admin/marketplace/qualifications/{qualification_id}/decision")
async def admin_qualification_decision(qualification_id:UUID,request:Request,body:QualificationDecision,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=_platform_admin(request,ctx)
    if denied:return denied
    action=body.action.upper();status={"VERIFY_QUALIFICATION":"VERIFIED","REJECT_QUALIFICATION":"REJECTED","EXPIRE_QUALIFICATION":"EXPIRED"}.get(action)
    if not status:return error(request,422,"UNKNOWN_QUALIFICATION_ACTION","Qualification action is not recognised")
    if action in REASON_REQUIRED and not body.reason:return error(request,422,"REASON_REQUIRED","A reason is required")
    row=(await db.execute(text("UPDATE external_consultant_qualifications SET verification_status=:status,verified_by=:actor,verified_at=:now,rejection_reason=:reason,updated_at=:now WHERE id=:id RETURNING profile_id,tenant_id"),{"status":status,"actor":ctx["user_id"],"now":datetime.now(timezone.utc),"reason":body.reason,"id":qualification_id})).mappings().first()
    if not row:return error(request,404,"QUALIFICATION_NOT_FOUND","Qualification was not found")
    current=(await db.execute(text("SELECT p.working_version,v.projection FROM external_consultant_public_profiles p JOIN external_consultant_public_profile_versions v ON v.profile_id=p.id AND v.version=p.working_version WHERE p.id=:profile"),{"profile":row["profile_id"]})).mappings().first()
    verified=(await db.execute(text("SELECT COUNT(*) FROM external_consultant_qualifications WHERE profile_id=:profile AND verification_status IN ('PENDING','VERIFIED') AND (expiry_date IS NULL OR expiry_date>=CURRENT_DATE)"),{"profile":row["profile_id"]})).scalar_one()
    if current:
        score,missing=completeness(dict(current["projection"]),verified);await db.execute(text("UPDATE external_consultant_public_profile_versions SET completeness=:score,missing_fields=CAST(:missing AS jsonb) WHERE profile_id=:profile AND version=:version"),{"score":score,"missing":json.dumps(missing),"profile":row["profile_id"],"version":current["working_version"]})
    await _marketplace_audit(db,row["profile_id"],row["tenant_id"],f"QUALIFICATION_{status}",ctx["user_id"],ctx["role"],body.reason,{"qualification_id":str(qualification_id)});await db.commit();return {"success":True,"data":{"verification_status":status},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/admin/marketplace/qualifications/{qualification_id}/evidence")
async def admin_qualification_evidence(qualification_id:UUID,request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=_platform_admin(request,ctx)
    if denied:return denied
    row=(await db.execute(text("SELECT q.profile_id,d.id,d.tenant_id,d.title,v.object_key,v.filename,v.content_type,v.size_bytes FROM external_consultant_qualifications q JOIN external_documents d ON d.id=q.credential_document_id AND d.tenant_id=q.tenant_id JOIN external_document_versions v ON v.document_id=d.id AND v.version=d.current_version AND v.tenant_id=d.tenant_id WHERE q.id=:id AND d.status='AVAILABLE' AND v.status='AVAILABLE'"),{"id":qualification_id})).mappings().first()
    if not row:return error(request,404,"CREDENTIAL_EVIDENCE_NOT_AVAILABLE","Certificate evidence is not available")
    if row["content_type"] not in {"image/jpeg","image/png","image/webp","application/pdf"} or row["size_bytes"]>10*1024*1024:return error(request,409,"CREDENTIAL_EVIDENCE_INVALID","Certificate evidence does not satisfy the supported-format and 10 MB policy")
    try:url=signed_view(row["object_key"],row["content_type"])
    except StorageUnavailable:return error(request,503,"CREDENTIAL_EVIDENCE_STORAGE_UNAVAILABLE","Certificate storage is not configured")
    await db.execute(text("INSERT INTO external_document_access_events(id,document_id,tenant_id,event_type,actor_id,created_at) VALUES (:id,:document,:tenant,'OPENED',:actor,:now)"),{"id":uuid4(),"document":row["id"],"tenant":row["tenant_id"],"actor":ctx["user_id"],"now":datetime.now(timezone.utc)})
    await _marketplace_audit(db,row["profile_id"],row["tenant_id"],"QUALIFICATION_EVIDENCE_VIEWED",ctx["user_id"],ctx["role"],metadata={"qualification_id":str(qualification_id),"document_id":str(row["id"])})
    await db.commit()
    return {"success":True,"data":{"document_id":str(row["id"]),"title":row["title"],"filename":row["filename"],"content_type":row["content_type"],"size_bytes":row["size_bytes"],"view_url":url,"expires_in":300,"public":False},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/admin/marketplace/operations")
async def admin_marketplace_operations(request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=_platform_admin(request,ctx)
    if denied:return denied
    qualifications=[dict(row) for row in (await db.execute(text("SELECT q.id,q.profile_id,q.tenant_id,q.qualification_type,q.title,q.institution,q.award_year,q.country,q.registration_number,q.issuing_body,q.expiry_date,q.verification_status,q.credential_document_id,d.title credential_document_title,d.status credential_document_status FROM external_consultant_qualifications q LEFT JOIN external_documents d ON d.id=q.credential_document_id AND d.tenant_id=q.tenant_id ORDER BY q.updated_at DESC LIMIT 200"))).mappings().all()]
    reviews=[dict(row) for row in (await db.execute(text("SELECT id,profile_id,tenant_id,overall_rating,review_text,verified_engagement,status,reported_at,created_at FROM external_consultant_reviews ORDER BY updated_at DESC LIMIT 200"))).mappings().all()]
    enrolments=[dict(row) for row in (await db.execute(text("SELECT id,profile_id,tenant_id,lead_id,service_id,programme_id,full_name,consultation_mode,location_id,preferred_at,status,created_at FROM external_consultant_marketplace_enrolments ORDER BY updated_at DESC LIMIT 200"))).mappings().all()]
    return {"success":True,"data":{"state":"READY","qualifications":qualifications,"reviews":reviews,"enrolments":enrolments},"error":None,"request_id":request.state.correlation_id}

def _public_profile_sql(extra=""):
    return """SELECT p.id,p.tenant_id AS _tenant_id,p.slug,p.accepting_new_clients,v.projection,
      COALESCE(r.average_rating,0) average_rating,COALESCE(r.review_count,0)::int review_count
      FROM external_consultant_public_profiles p JOIN external_consultant_public_profile_versions v ON v.profile_id=p.id AND v.version=p.current_published_version
      LEFT JOIN (SELECT profile_id,AVG(overall_rating)::numeric(3,2) average_rating,COUNT(*) review_count FROM external_consultant_reviews WHERE verified_engagement=TRUE AND status='PUBLISHED' GROUP BY profile_id) r ON r.profile_id=p.id
      WHERE p.status='PUBLISHED' AND v.status='PUBLISHED' AND p.public_visibility=TRUE AND p.approval_valid=TRUE AND p.suspended_at IS NULL """+extra

def _public_marketplace_item(row):
    item=dict(row);item.pop("_tenant_id",None);item["projection"]=dict(item["projection"]);return item

@app.get("/api/v1/public/consultants/featured")
async def public_featured_consultants(request:Request,response:Response,limit:int=Query(6,ge=1,le=8),db:AsyncSession=Depends(get_db)):
    extra=""" AND EXISTS(SELECT 1 FROM external_consultant_homepage_features h WHERE h.profile_id=p.id AND h.tenant_id=p.tenant_id AND h.featured_on_homepage=TRUE AND (h.featured_from IS NULL OR h.featured_from<=CURRENT_TIMESTAMP) AND (h.featured_until IS NULL OR h.featured_until>CURRENT_TIMESTAMP))"""
    sql=_public_profile_sql(extra)+" ORDER BY (SELECT h.featured_rank FROM external_consultant_homepage_features h WHERE h.profile_id=p.id) ASC,p.id LIMIT :limit"
    raw=list((await db.execute(text(sql),{"limit":limit})).mappings().all());rows=[_public_marketplace_item(row) for row in raw]
    response.headers["Cache-Control"]="public, max-age=60, stale-while-revalidate=30"
    return {"success":True,"data":{"state":"READY" if rows else "CONFIRMED_EMPTY","items":rows},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/public/consultants/homepage-events")
async def public_homepage_event(request:Request,body:MarketplaceEventCreate,db:AsyncSession=Depends(get_db)):
    profile=None
    if body.profile_id:
        try:profile_id=UUID(body.profile_id)
        except ValueError:return error(request,422,"INVALID_PROFILE_ID","Profile identifier is invalid")
        profile=(await db.execute(text(_public_profile_sql(" AND p.id=:profile")),{"profile":profile_id})).mappings().first()
        if not profile:return error(request,404,"CONSULTANT_NOT_FOUND","Consultant profile was not found")
    if body.event_type in {"HOMEPAGE_CONSULTANT_IMPRESSION","HOMEPAGE_CONSULTANT_VIEW_CLICK","HOMEPAGE_ENROL_CLICK"} and not profile:return error(request,422,"PROFILE_REQUIRED","This event requires an eligible public consultant")
    await db.execute(text("INSERT INTO external_marketplace_homepage_events(id,profile_id,tenant_id,event_type,profession_code,metadata,created_at) VALUES (:id,:profile,:tenant,:event,:profession,'{}'::jsonb,:now)"),{"id":uuid4(),"profile":profile["id"] if profile else None,"tenant":profile["_tenant_id"] if profile else None,"event":body.event_type,"profession":body.profession_code,"now":datetime.now(timezone.utc)});await db.commit()
    return {"success":True,"data":{"recorded":True},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/public/consultants/compare")
async def public_compare_consultants(request:Request,c:list[str]=Query(...,min_length=2,max_length=4),db:AsyncSession=Depends(get_db)):
    slugs=list(dict.fromkeys(item.strip() for item in c if item.strip()))
    if len(slugs)<2 or len(slugs)>4:return error(request,422,"COMPARE_LIMIT","Compare between two and four consultants")
    raw=list((await db.execute(text(_public_profile_sql(" AND p.slug=ANY(:slugs)")),{"slugs":slugs})).mappings().all())
    by_slug={row["slug"]:row for row in raw};items=[]
    for slug in slugs:
        row=by_slug.get(slug)
        if not row:continue
        qualifications=[dict(item) for item in (await db.execute(text("SELECT title,institution,award_year FROM external_consultant_qualifications WHERE profile_id=:profile AND verification_status='VERIFIED' AND (expiry_date IS NULL OR expiry_date>=CURRENT_DATE) ORDER BY award_year DESC LIMIT 3"),{"profile":row["id"]})).mappings().all()]
        availability=(await db.execute(text("SELECT 1 FROM external_availability_rules WHERE tenant_id=:tenant AND active=TRUE AND (effective_from IS NULL OR effective_from<=CURRENT_DATE) AND (effective_until IS NULL OR effective_until>=CURRENT_DATE) LIMIT 1"),{"tenant":row["_tenant_id"]})).first()
        items.append({**_public_marketplace_item(row),"verified_qualifications":qualifications,"availability_state":"AVAILABLE_WINDOWS" if availability else "NOT_SHOWN"})
    return {"success":True,"data":{"state":"READY" if items else "CONFIRMED_EMPTY","items":items,"unavailable_count":len(slugs)-len(items)},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/public/consultants/finder/config")
async def public_finder_config(request:Request,db:AsyncSession=Depends(get_db)):
    row=(await db.execute(text("SELECT config FROM external_marketplace_finder_config WHERE config_key='PUBLIC_FINDER' AND active=TRUE"))).mappings().first()
    config=dict(row["config"]) if row else {"support_areas":SUPPORT_TAXONOMY,"questions":["support_area","mode","location","languages","availability","budget","experience"]}
    return {"success":True,"data":config,"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/public/consultants/finder/matches")
async def public_finder_matches(request:Request,body:FinderRequest,db:AsyncSession=Depends(get_db)):
    config=(await public_finder_config(request,db))["data"];area=(config.get("support_areas") or {}).get(body.support_area)
    if not area:return error(request,422,"UNKNOWN_SUPPORT_AREA","Choose a governed support area")
    professions=area.get("professions") or [];params={"professions":professions,"limit":24};extra=" AND v.projection->>'profession_code'=ANY(:professions)"
    if body.mode!="EITHER":extra+=" AND EXISTS(SELECT 1 FROM jsonb_array_elements_text(COALESCE(v.projection->'consultation_modes','[]'::jsonb)) m(value) WHERE m.value IN (:mode,'BOTH'))";params["mode"]=body.mode
    rows=list((await db.execute(text(_public_profile_sql(extra)+" ORDER BY p.accepting_new_clients DESC,p.id LIMIT :limit"),params)).mappings().all());relaxed=[]
    if not rows and body.mode!="EITHER":
        relaxed=["consultation_mode"]
        fallback={"professions":professions,"limit":24}
        rows=list((await db.execute(text(_public_profile_sql(" AND v.projection->>'profession_code'=ANY(:professions)")+" ORDER BY p.accepting_new_clients DESC,p.id LIMIT :limit"),fallback)).mappings().all())
    items=[]
    for row in rows:
        projection=dict(row["projection"]);available=(await db.execute(text("SELECT 1 FROM external_availability_rules WHERE tenant_id=:tenant AND active=TRUE LIMIT 1"),{"tenant":row["_tenant_id"]})).first() is not None
        score,reasons=explain_and_score(projection,body,available)
        if relaxed:reasons.append("Shown as an alternative because your consultation-mode preference was relaxed")
        items.append({**_public_marketplace_item(row),"match_reasons":reasons,"match_strength":"Strong match" if score>=140 else "Matches most preferences" if score>=115 else "Matches some preferences","availability_state":"PUBLIC_AVAILABILITY" if available else "NOT_SHOWN","_score":score})
    items.sort(key=lambda x:(-x.pop("_score"),x["slug"]))
    return {"success":True,"data":{"state":"READY" if items else "CONFIRMED_EMPTY","items":items,"professions":professions,"relaxed_preferences":relaxed},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/public/consultants/finder/events")
async def public_finder_event(request:Request,body:FinderEvent,db:AsyncSession=Depends(get_db)):
    if body.event_type not in FINDER_EVENTS:return error(request,422,"INVALID_FINDER_EVENT","Finder event is not allowed")
    profile=None
    if body.profile_id:
        try:profile=UUID(body.profile_id)
        except ValueError:return error(request,422,"INVALID_PROFILE_ID","Profile identifier is invalid")
    await db.execute(text("INSERT INTO external_marketplace_finder_events(id,profile_id,event_type,step,support_area,created_at) VALUES (:id,:profile,:event,:step,:area,:now)"),{"id":uuid4(),"profile":profile,"event":body.event_type,"step":body.step,"area":body.support_area,"now":datetime.now(timezone.utc)});await db.commit()
    return {"success":True,"data":{"recorded":True},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/public/consultants/comparison-events")
async def public_comparison_event(request:Request,body:MarketplaceComparisonEvent,db:AsyncSession=Depends(get_db)):
    ids=[]
    for value in body.compared_profile_ids:
        try:ids.append(UUID(value))
        except ValueError:return error(request,422,"INVALID_PROFILE_ID","Comparison contains an invalid profile identifier")
    profile_id=None
    if body.profile_id:
        try:profile_id=UUID(body.profile_id)
        except ValueError:return error(request,422,"INVALID_PROFILE_ID","Profile identifier is invalid")
    all_ids=list(dict.fromkeys(([profile_id] if profile_id else [])+ids))
    rows=list((await db.execute(text(_public_profile_sql(" AND p.id=ANY(:ids)")),{"ids":all_ids})).mappings().all()) if all_ids else []
    visible={row["id"]:row for row in rows}
    if profile_id and profile_id not in visible:return error(request,404,"CONSULTANT_NOT_FOUND","Consultant profile is no longer publicly available")
    safe_ids=[item for item in ids if item in visible]
    await db.execute(text("INSERT INTO external_marketplace_comparison_events(id,profile_id,tenant_id,event_type,compared_profile_ids,created_at) VALUES (:id,:profile,:tenant,:event,CAST(:compared AS jsonb),:now)"),{"id":uuid4(),"profile":profile_id,"tenant":visible[profile_id]["_tenant_id"] if profile_id else None,"event":body.event_type,"compared":json.dumps([str(item) for item in safe_ids]),"now":datetime.now(timezone.utc)});await db.commit()
    return {"success":True,"data":{"recorded":True},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/public/consultants")
async def public_consultants(request:Request,q:str|None=None,profession:list[str]|None=Query(None),specialisation:list[str]|None=Query(None),mode:list[str]|None=Query(None),location:list[str]|None=Query(None),language:list[str]|None=Query(None),experience_min:int|None=Query(None,ge=0,le=80),experience_max:int|None=Query(None,ge=0,le=80),availability:str|None=Query(None,pattern="^(NEXT_AVAILABLE|TODAY|NEXT_3_DAYS|NEXT_7_DAYS)$"),rating_min:float|None=Query(None,ge=1,le=5),fee_min:int|None=Query(None,ge=0),fee_max:int|None=Query(None,ge=0),fee_currency:str|None=Query(None,pattern="^[A-Z]{3}$"),accepting_new_clients:bool|None=None,service:list[str]|None=Query(None),sort:str=Query("recommended",pattern="^(recommended|next_available|rating_desc|most_reviewed|experience_desc|fee_asc|fee_desc)$"),page:int=Query(1,ge=1),page_size:int=Query(24,ge=1,le=60),db:AsyncSession=Depends(get_db)):
    if experience_min is not None and experience_max is not None and experience_min>experience_max:return error(request,422,"INVALID_EXPERIENCE_RANGE","Minimum experience cannot exceed maximum experience")
    if fee_min is not None and fee_max is not None and fee_min>fee_max:return error(request,422,"INVALID_FEE_RANGE","Minimum fee cannot exceed maximum fee")
    filters=[];params={"q":f"%{(q or '').lower()}%","professions":profession or [],"specialisations":specialisation or [],"modes":mode or [],"locations":[item.lower() for item in (location or [])],"languages":language or [],"experience_min":experience_min,"experience_max":experience_max,"rating_min":rating_min,"fee_min":fee_min,"fee_max":fee_max,"fee_currency":fee_currency,"accepting":accepting_new_clients,"services":[item.lower() for item in (service or [])],"limit":page_size,"offset":(page-1)*page_size}
    if q:filters.append("(lower(v.projection->>'display_name') LIKE :q OR lower(v.projection->>'professional_title') LIKE :q OR lower(v.projection->>'bio') LIKE :q OR lower((v.projection->'specialisations')::text) LIKE :q OR lower((v.projection->'services')::text) LIKE :q OR lower((v.projection->'programmes')::text) LIKE :q)")
    if profession:filters.append("v.projection->>'profession_code'=ANY(:professions)")
    if specialisation:filters.append("EXISTS(SELECT 1 FROM jsonb_array_elements_text(COALESCE(v.projection->'specialisations','[]'::jsonb)) x(value) WHERE x.value=ANY(:specialisations))")
    if mode:filters.append("EXISTS(SELECT 1 FROM jsonb_array_elements_text(COALESCE(v.projection->'consultation_modes','[]'::jsonb)) x(value) WHERE x.value=ANY(:modes) OR x.value='BOTH')")
    if location:filters.append("EXISTS(SELECT 1 FROM jsonb_array_elements(COALESCE(v.projection->'public_locations','[]'::jsonb)) x(value) WHERE lower(x.value->>'name')=ANY(:locations))")
    if language:filters.append("EXISTS(SELECT 1 FROM jsonb_array_elements_text(COALESCE(v.projection->'languages','[]'::jsonb)) x(value) WHERE x.value=ANY(:languages))")
    if experience_min is not None:filters.append("(v.projection->>'experience_years')::int>=:experience_min")
    if experience_max is not None:filters.append("(v.projection->>'experience_years')::int<=:experience_max")
    if rating_min is not None:filters.append("r.review_count>0 AND r.average_rating>=:rating_min")
    if fee_min is not None or fee_max is not None:
        filters.append("v.projection->>'public_fee_currency'=:fee_currency")
        if not fee_currency:return error(request,422,"FEE_CURRENCY_REQUIRED","Currency is required for fee filtering")
        if fee_min is not None:filters.append("(v.projection->>'public_fee_from')::bigint>=:fee_min")
        if fee_max is not None:filters.append("(v.projection->>'public_fee_from')::bigint<=:fee_max")
    if accepting_new_clients is not None:filters.append("p.accepting_new_clients=:accepting")
    if service:filters.append("EXISTS(SELECT 1 FROM jsonb_array_elements(COALESCE(v.projection->'services','[]'::jsonb)||COALESCE(v.projection->'programmes','[]'::jsonb)) x(value) WHERE COALESCE((x.value->>'active')::boolean,TRUE)=TRUE AND (lower(x.value->>'name')=ANY(:services) OR x.value->>'id'=ANY(:services)))")
    if availability:
        days={"TODAY":1,"NEXT_AVAILABLE":7,"NEXT_3_DAYS":3,"NEXT_7_DAYS":7}[availability];today=date.today();weekdays=[(today+timedelta(days=i)).weekday() for i in range(days)];params["weekdays"]=weekdays
        filters.append("EXISTS(SELECT 1 FROM external_availability_rules ar WHERE ar.tenant_id=p.tenant_id AND ar.active=TRUE AND ar.weekday=ANY(:weekdays) AND (ar.effective_from IS NULL OR ar.effective_from<=CURRENT_DATE) AND (ar.effective_until IS NULL OR ar.effective_until>=CURRENT_DATE))")
    where=" AND "+" AND ".join(filters) if filters else ""
    fee="NULLIF(v.projection->>'public_fee_from','')::bigint"
    availability_order="(SELECT MIN(((ar.weekday-EXTRACT(ISODOW FROM CURRENT_DATE)::int+7)%7)*1440+EXTRACT(HOUR FROM ar.start_time)*60+EXTRACT(MINUTE FROM ar.start_time)) FROM external_availability_rules ar WHERE ar.tenant_id=p.tenant_id AND ar.active=TRUE)"
    ordering={"next_available":f"{availability_order} ASC NULLS LAST","rating_desc":"average_rating DESC,review_count DESC","most_reviewed":"review_count DESC,average_rating DESC","experience_desc":"(v.projection->>'experience_years')::int DESC","fee_asc":f"{fee} ASC NULLS LAST","fee_desc":f"{fee} DESC NULLS LAST"}.get(sort,"p.accepting_new_clients DESC,"+availability_order+" ASC NULLS LAST,lower(v.projection->>'display_name') ASC")
    count_sql="SELECT COUNT(*) FROM ("+_public_profile_sql(where)+") visible"
    total=int((await db.execute(text(count_sql),params)).scalar_one())
    sql=_public_profile_sql(where)+f" ORDER BY {ordering},p.id LIMIT :limit OFFSET :offset"
    raw=list((await db.execute(text(sql),params)).mappings().all());rows=[_public_marketplace_item(row) for row in raw]
    for row in raw:await db.execute(text("INSERT INTO external_consultant_marketplace_events(id,profile_id,tenant_id,event_type,metadata,created_at) VALUES (:id,:profile,:tenant,'PROFILE_IMPRESSION','{}'::jsonb,:now)"),{"id":uuid4(),"profile":row["id"],"tenant":row["_tenant_id"],"now":datetime.now(timezone.utc)})
    facets={"professions":sorted({item["projection"].get("profession_code") for item in rows if item["projection"].get("profession_code")}),"specialisations":sorted({value for item in rows for value in item["projection"].get("specialisations",[])}),"locations":sorted({loc.get("name") for item in rows for loc in item["projection"].get("public_locations",[]) if loc.get("name")}),"languages":sorted({value for item in rows for value in item["projection"].get("languages",[])}),"modes":sorted({value for item in rows for value in item["projection"].get("consultation_modes",[])}),"services":sorted({offering.get("name") for item in rows for key in ("services","programmes") for offering in item["projection"].get(key,[]) if offering.get("active",True) and offering.get("name")})}
    await db.commit();return {"success":True,"data":{"state":"READY" if rows else "CONFIRMED_EMPTY","items":rows,"total":total,"page":page,"page_size":page_size,"pages":max(1,(total+page_size-1)//page_size),"facets":facets},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/public/consultants/{slug}")
async def public_consultant(slug:str,request:Request,db:AsyncSession=Depends(get_db)):
    row=(await db.execute(text(_public_profile_sql(" AND p.slug=:slug")),{"slug":slug})).mappings().first()
    if not row:return error(request,404,"CONSULTANT_NOT_FOUND","Consultant profile was not found")
    qualifications=[dict(item) for item in (await db.execute(text("SELECT qualification_type,title,institution,award_year,country,issuing_body,expiry_date FROM external_consultant_qualifications WHERE profile_id=:profile AND verification_status='VERIFIED' AND (expiry_date IS NULL OR expiry_date>=CURRENT_DATE) ORDER BY award_year DESC"),{"profile":row["id"]})).mappings().all()]
    reviews=[dict(item) for item in (await db.execute(text("SELECT overall_rating,review_text,communication_rating,professionalism_rating,support_experience_rating,created_at FROM external_consultant_reviews WHERE profile_id=:profile AND verified_engagement=TRUE AND status='PUBLISHED' ORDER BY created_at DESC LIMIT 30"),{"profile":row["id"]})).mappings().all()]
    await db.execute(text("INSERT INTO external_consultant_marketplace_events(id,profile_id,tenant_id,event_type,metadata,created_at) VALUES (:id,:profile,:tenant,'PROFILE_VIEW','{}'::jsonb,:now)"),{"id":uuid4(),"profile":row["id"],"tenant":row["_tenant_id"],"now":datetime.now(timezone.utc)});await db.commit()
    return {"success":True,"data":{**_public_marketplace_item(row),"qualifications":qualifications,"reviews":reviews,"review_state":"READY" if reviews else "CONFIRMED_EMPTY"},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/public/consultants/{slug}/availability")
async def public_consultant_availability(slug:str,request:Request,db:AsyncSession=Depends(get_db)):
    profile=(await db.execute(text("SELECT p.id,p.tenant_id,p.consultant_user_id FROM external_consultant_public_profiles p JOIN external_consultant_public_profile_versions v ON v.profile_id=p.id AND v.version=p.current_published_version WHERE p.slug=:slug AND v.status='PUBLISHED' AND p.public_visibility=TRUE AND p.approval_valid=TRUE AND p.suspended_at IS NULL"),{"slug":slug})).mappings().first()
    if not profile:return error(request,404,"CONSULTANT_NOT_FOUND","Consultant profile was not found")
    rules=[dict(row) for row in (await db.execute(text("SELECT weekday,start_time,end_time,timezone FROM external_availability_rules WHERE tenant_id=:tenant AND active=TRUE AND (effective_from IS NULL OR effective_from<=CURRENT_DATE) AND (effective_until IS NULL OR effective_until>=CURRENT_DATE) ORDER BY weekday,start_time"),{"tenant":profile["tenant_id"]})).mappings().all()]
    occupied=[row[0] for row in (await db.execute(text("SELECT starts_at FROM external_scheduled_appointments WHERE tenant_id=:tenant AND status IN ('BOOKED','CONFIRMED') AND starts_at>=NOW() AND starts_at<NOW()+INTERVAL '90 days' ORDER BY starts_at"),{"tenant":profile["tenant_id"]})).all()]
    return {"success":True,"data":{"state":"READY" if rules else "CONFIRMED_EMPTY","rules":rules,"occupied_starts_at":occupied,"refreshed_at":datetime.now(timezone.utc)},"error":None,"request_id":request.state.correlation_id}

async def _public_booking_context(slug,request,db):
    row=(await db.execute(text("SELECT p.id,p.tenant_id,p.consultant_user_id,p.accepting_new_clients,v.projection FROM external_consultant_public_profiles p JOIN external_consultant_public_profile_versions v ON v.profile_id=p.id AND v.version=p.current_published_version WHERE p.slug=:slug AND v.status='PUBLISHED' AND p.public_visibility=TRUE AND p.approval_valid=TRUE AND p.suspended_at IS NULL"),{"slug":slug})).mappings().first()
    if not row:return None,error(request,404,"CONSULTANT_NOT_FOUND","Consultant profile was not found")
    return row,None

def _public_service(projection,service_id):
    return next((item for item in projection.get("services",[]) if str(item.get("id"))==str(service_id) and item.get("active",True)),None)

async def _marketplace_lead(db,profile,body,phone):
    email_key,phone_key=normal_email(body.email),normal_phone(phone)
    existing=(await db.execute(text("SELECT id FROM external_leads WHERE tenant_id=:tenant AND ((:email_key IS NOT NULL AND email_key=:email_key) OR (:phone_key IS NOT NULL AND phone_key=:phone_key)) ORDER BY created_at LIMIT 1"),{"tenant":profile["tenant_id"],"email_key":email_key,"phone_key":phone_key})).scalar_one_or_none()
    if existing:return existing,True
    lead_id=uuid4();now=datetime.now(timezone.utc);parts=body.full_name.split()
    await db.execute(text("INSERT INTO external_leads(id,tenant_id,first_name,last_name,email,phone,email_key,phone_key,source,stage,assigned_practitioner_id,notes,created_by,created_at,updated_at) VALUES (:id,:tenant,:first,:last,:email,:phone,:email_key,:phone_key,:source,'NEW',:actor,:notes,'PUBLIC_MARKETPLACE',:now,:now)"),{"id":lead_id,"tenant":profile["tenant_id"],"first":parts[0],"last":" ".join(parts[1:]) or None,"email":body.email,"phone":phone,"email_key":email_key,"phone_key":phone_key,"source":body.source,"actor":profile["consultant_user_id"],"notes":"Marketplace booking conversion","now":now})
    return lead_id,False

async def _booking_event(db,profile,event,source,metadata=None):
    await db.execute(text("INSERT INTO external_consultant_marketplace_events(id,profile_id,tenant_id,event_type,metadata,created_at) VALUES (:id,:profile,:tenant,:event,CAST(:metadata AS jsonb),:now)"),{"id":uuid4(),"profile":profile["id"],"tenant":profile["tenant_id"],"event":event,"metadata":json.dumps({"source":source,**(metadata or {})}),"now":datetime.now(timezone.utc)})

@app.get("/api/v1/public/consultants/{slug}/booking-context")
async def public_booking_context(slug:str,request:Request,db:AsyncSession=Depends(get_db)):
    profile,denied=await _public_booking_context(slug,request,db)
    if denied:return denied
    services=[]
    for service in profile["projection"].get("services",[]):
        if not service.get("active",True):continue
        policy=(await db.execute(text("SELECT public_booking_policy FROM external_appointment_types WHERE id=:id AND tenant_id=:tenant AND active=TRUE"),{"id":UUID(str(service["id"])),"tenant":profile["tenant_id"]})).scalar_one_or_none()
        if policy is not None:services.append({**service,"booking_policy":policy})
    locations=[item for item in profile["projection"].get("public_locations",[]) if item.get("mode") in {"ONLINE","IN_PERSON","PHONE","OTHER"}]
    return {"success":True,"data":{"services":services,"programmes":[item for item in profile["projection"].get("programmes",[]) if item.get("active",True)],"locations":locations,"accepting_new_clients":profile["accepting_new_clients"]},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/public/consultants/{slug}/bookings",status_code=201)
async def public_marketplace_booking(slug:str,request:Request,body:PublicBookingCreate,db:AsyncSession=Depends(get_db)):
    if not body.consent_acknowledged:return error(request,422,"PRIVACY_ACKNOWLEDGEMENT_REQUIRED","Privacy acknowledgement is required")
    profile,denied=await _public_booking_context(slug,request,db)
    if denied:return denied
    service=_public_service(profile["projection"],body.service_id)
    if not service or service.get("enrolment_mode")!="DIRECT_BOOKING":return error(request,422,"DIRECT_BOOKING_NOT_ENABLED","This public service does not allow direct booking")
    if body.consultation_mode!=service.get("mode"):return error(request,422,"MODE_NOT_AVAILABLE","Choose a mode offered by this service")
    public_location_ids={str(item.get("id")) for item in profile["projection"].get("public_locations",[]) if item.get("mode")=="IN_PERSON"}
    if body.consultation_mode=="IN_PERSON" and (not body.location_id or body.location_id not in public_location_ids):return error(request,422,"PUBLIC_LOCATION_REQUIRED","Choose an approved public location")
    kind=(await db.execute(text("SELECT duration_minutes,buffer_before_minutes,buffer_after_minutes,public_booking_policy FROM external_appointment_types WHERE id=:id AND tenant_id=:tenant AND active=TRUE FOR UPDATE"),{"id":UUID(body.service_id),"tenant":profile["tenant_id"]})).mappings().first()
    if not kind or not kind["public_booking_policy"].get("direct_booking_enabled",False):return error(request,409,"DIRECT_BOOKING_NOT_ENABLED","Direct booking is not enabled")
    now=datetime.now(timezone.utc);policy=kind["public_booking_policy"]
    if body.starts_at<now+timedelta(minutes=int(policy.get("minimum_notice_minutes",60))) or body.starts_at>now+timedelta(days=int(policy.get("advance_window_days",60))):return error(request,409,"BOOKING_POLICY_WINDOW","This time is outside the public booking window")
    available=(await db.execute(text("SELECT 1 FROM external_availability_rules WHERE tenant_id=:tenant AND active=TRUE AND (EXTRACT(ISODOW FROM (:start AT TIME ZONE timezone))::int-1)=weekday AND CAST(:start AT TIME ZONE timezone AS time)>=start_time AND CAST(:end AT TIME ZONE timezone AS time)<=end_time AND (effective_from IS NULL OR CAST(:start AT TIME ZONE timezone AS date)>=effective_from) AND (effective_until IS NULL OR CAST(:start AT TIME ZONE timezone AS date)<=effective_until) LIMIT 1"),{"tenant":profile["tenant_id"],"start":body.starts_at,"end":body.starts_at+timedelta(minutes=kind["duration_minutes"])})).first()
    if not available:return error(request,409,"SLOT_NO_LONGER_AVAILABLE","That time has just been booked. Please choose another available time.")
    conflict=(await db.execute(text("SELECT 1 FROM external_scheduled_appointments WHERE tenant_id=:tenant AND status IN ('BOOKED','CONFIRMED') AND starts_at<:blocked_end AND ends_at>:blocked_start LIMIT 1"),{"tenant":profile["tenant_id"],"blocked_start":body.starts_at-timedelta(minutes=kind["buffer_before_minutes"]),"blocked_end":body.starts_at+timedelta(minutes=kind["duration_minutes"]+kind["buffer_after_minutes"])})).first()
    if conflict:await _booking_event(db,profile,"BOOKING_FAILED_SLOT_CONFLICT",body.source);await db.commit();return error(request,409,"SLOT_NO_LONGER_AVAILABLE","That time has just been booked. Please choose another available time.")
    phone=f"{body.country_code}{''.join(ch for ch in body.national_number if ch.isdigit())}";key=dedupe_key(profile["id"],body.email,phone,body.service_id);prior=(await db.execute(text("SELECT id,appointment_id,status FROM external_consultant_marketplace_enrolments WHERE profile_id=:profile AND deduplication_key=:key"),{"profile":profile["id"],"key":key})).mappings().first()
    if prior and prior["appointment_id"]:return {"success":True,"data":{"status":prior["status"],"appointment_id":str(prior["appointment_id"]),"duplicate":True},"error":None,"request_id":request.state.correlation_id}
    lead_id,_=await _marketplace_lead(db,profile,body,phone);enrolment_id=prior["id"] if prior else uuid4();appointment_id=uuid4();raw_token=secrets.token_urlsafe(32);ends=body.starts_at+timedelta(minutes=kind["duration_minutes"])
    if not prior:await db.execute(text("INSERT INTO external_consultant_marketplace_enrolments(id,profile_id,tenant_id,lead_id,service_id,full_name,email,phone,consultation_mode,location_id,preferred_at,message,consent_acknowledged,status,deduplication_key,created_at,updated_at) VALUES (:id,:profile,:tenant,:lead,:service,:name,:email,:phone,:mode,:location,:start,:message,TRUE,'BOOKED',:key,:now,:now)"),{"id":enrolment_id,"profile":profile["id"],"tenant":profile["tenant_id"],"lead":lead_id,"service":UUID(body.service_id),"name":body.full_name,"email":body.email,"phone":phone,"mode":body.consultation_mode,"location":UUID(body.location_id) if body.location_id else None,"start":body.starts_at,"message":body.message,"key":key,"now":now})
    try:
        await db.execute(text("INSERT INTO external_scheduled_appointments(id,tenant_id,client_id,lead_id,appointment_type_id,starts_at,ends_at,status,booked_by_type,created_by,marketplace_enrolment_id,marketplace_source,management_token_hash,management_token_expires_at,created_at,updated_at) VALUES (:id,:tenant,NULL,:lead,:type,:start,:end,'CONFIRMED','PUBLIC_PROSPECT',:actor,:enrolment,:source,:token_hash,:expires,:now,:now)"),{"id":appointment_id,"tenant":profile["tenant_id"],"lead":lead_id,"type":UUID(body.service_id),"start":body.starts_at,"end":ends,"actor":profile["consultant_user_id"],"enrolment":enrolment_id,"source":body.source,"token_hash":hashlib.sha256(raw_token.encode()).hexdigest(),"expires":ends+timedelta(days=30),"now":now})
        await db.execute(text("UPDATE external_consultant_marketplace_enrolments SET appointment_id=:appointment,status='BOOKED',updated_at=:now WHERE id=:id"),{"appointment":appointment_id,"now":now,"id":enrolment_id});await db.execute(text("UPDATE external_leads SET stage='CONSULTATION_BOOKED',updated_at=:now WHERE id=:lead AND tenant_id=:tenant"),{"now":now,"lead":lead_id,"tenant":profile["tenant_id"]})
        await db.execute(text("INSERT INTO external_communication_preparations(id,tenant_id,client_id,lead_id,channel,purpose,subject,body,status,created_by,created_at,updated_at) VALUES (:id,:tenant,NULL,:lead,'EMAIL_PREPARATION','Booking confirmation','Consultation booked',:body,'PREPARED',:actor,:now,:now)"),{"id":uuid4(),"tenant":profile["tenant_id"],"lead":lead_id,"body":f"Your {service['name']} consultation is booked for {body.starts_at.isoformat()} ({body.timezone}). Reference {str(appointment_id)[:8].upper()}.","actor":profile["consultant_user_id"],"now":now})
        await _booking_event(db,profile,"BOOKING_CONFIRMED",body.source,{"appointment_id":str(appointment_id)});await db.commit()
    except IntegrityError:
        await db.rollback();return error(request,409,"SLOT_NO_LONGER_AVAILABLE","That time has just been booked. Please choose another available time.")
    return {"success":True,"data":{"status":"CONFIRMED","appointment_id":str(appointment_id),"reference":str(appointment_id)[:8].upper(),"starts_at":body.starts_at,"ends_at":ends,"management_token":raw_token,"lead_id":str(lead_id)},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/public/consultants/{slug}/waitlist",status_code=201)
async def public_marketplace_waitlist(slug:str,request:Request,body:PublicWaitlistCreate,db:AsyncSession=Depends(get_db)):
    if not body.consent_acknowledged:return error(request,422,"PRIVACY_ACKNOWLEDGEMENT_REQUIRED","Privacy acknowledgement is required")
    profile,denied=await _public_booking_context(slug,request,db)
    if denied:return denied
    service=_public_service(profile["projection"],body.service_id)
    if not service:return error(request,404,"PUBLIC_SERVICE_NOT_FOUND","Public service was not found")
    lead_id,_=await _marketplace_lead(db,profile,body,body.phone);item_id=uuid4();now=datetime.now(timezone.utc)
    await db.execute(text("INSERT INTO external_scheduling_waitlist(id,tenant_id,client_id,lead_id,profile_id,appointment_type_id,preferred_from,preferred_until,status,notes,created_by,created_at,updated_at,location_id,consultation_mode,marketplace_source,time_preference) VALUES (:id,:tenant,NULL,:lead,:profile,:type,:from_at,:until,'WAITING',:notes,'PUBLIC_MARKETPLACE',:now,:now,:location,:mode,:source,:preference)"),{"id":item_id,"tenant":profile["tenant_id"],"lead":lead_id,"profile":profile["id"],"type":UUID(body.service_id),"from_at":body.preferred_at,"until":body.preferred_until,"notes":body.message,"now":now,"location":UUID(body.location_id) if body.location_id else None,"mode":body.consultation_mode,"source":body.source,"preference":body.time_preference});await _booking_event(db,profile,"WAITLIST_JOINED",body.source,{"waitlist_id":str(item_id)});await db.commit()
    return {"success":True,"data":{"id":str(item_id),"status":"WAITING"},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/public/booking-management/{token}")
async def public_booking_management(token:str,request:Request,body:BookingManagementAction,db:AsyncSession=Depends(get_db)):
    digest=hashlib.sha256(token.encode()).hexdigest();row=(await db.execute(text("SELECT a.id,a.tenant_id,a.starts_at,a.ends_at,a.status,a.appointment_type_id,t.duration_minutes,t.public_booking_policy FROM external_scheduled_appointments a JOIN external_appointment_types t ON t.id=a.appointment_type_id AND t.tenant_id=a.tenant_id WHERE a.management_token_hash=:hash AND a.management_token_expires_at>NOW() FOR UPDATE"),{"hash":digest})).mappings().first()
    if not row:return error(request,404,"BOOKING_MANAGEMENT_TOKEN_INVALID","This booking-management link is invalid or expired")
    now=datetime.now(timezone.utc);hours=int(row["public_booking_policy"].get("cancellation_window_hours" if body.action=="CANCEL" else "reschedule_window_hours",24))
    if row["starts_at"]<now+timedelta(hours=hours):return error(request,409,"BOOKING_CHANGE_WINDOW_CLOSED","The configured booking change window has closed")
    if body.action=="CANCEL":
        await db.execute(text("UPDATE external_scheduled_appointments SET status='CANCELLED',cancellation_reason=:reason,cancelled_at=:now,updated_at=:now WHERE id=:id"),{"reason":body.reason,"now":now,"id":row["id"]});event="CANCELLED"
    else:
        if not body.starts_at:return error(request,422,"REPLACEMENT_SLOT_REQUIRED","Choose a replacement time")
        conflict=(await db.execute(text("SELECT 1 FROM external_scheduled_appointments WHERE tenant_id=:tenant AND id<>:id AND status IN ('BOOKED','CONFIRMED') AND starts_at<:end AND ends_at>:start LIMIT 1"),{"tenant":row["tenant_id"],"id":row["id"],"start":body.starts_at,"end":body.starts_at+timedelta(minutes=row["duration_minutes"])})).first()
        if conflict:return error(request,409,"SLOT_NO_LONGER_AVAILABLE","That time has just been booked. Please choose another available time.")
        await db.execute(text("UPDATE external_scheduled_appointments SET starts_at=:start,ends_at=:end,status='CONFIRMED',updated_at=:now WHERE id=:id"),{"start":body.starts_at,"end":body.starts_at+timedelta(minutes=row["duration_minutes"]),"now":now,"id":row["id"]});event="RESCHEDULED"
    await db.execute(text("INSERT INTO external_scheduling_audit_events(id,tenant_id,appointment_id,event_type,actor_type,details,created_at) VALUES (:id,:tenant,:appointment,:event,'PUBLIC_PROSPECT',CAST(:details AS jsonb),:now)"),{"id":uuid4(),"tenant":row["tenant_id"],"appointment":row["id"],"event":event,"details":json.dumps({"reason":body.reason,"previous_starts_at":row["starts_at"].isoformat()}),"now":now});await db.commit()
    return {"success":True,"data":{"status":"CANCELLED" if body.action=="CANCEL" else "CONFIRMED","appointment_id":str(row["id"])},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/public/consultants/{slug}/enrolments")
async def public_consultant_enrolment(slug:str,request:Request,body:EnrolmentCreate,db:AsyncSession=Depends(get_db)):
    if not body.consent_acknowledged:return error(request,422,"PRIVACY_ACKNOWLEDGEMENT_REQUIRED","Privacy acknowledgement is required")
    profile=(await db.execute(text("SELECT p.id,p.tenant_id,p.consultant_user_id,p.accepting_new_clients FROM external_consultant_public_profiles p JOIN external_consultant_public_profile_versions v ON v.profile_id=p.id AND v.version=p.current_published_version WHERE p.slug=:slug AND v.status='PUBLISHED' AND p.public_visibility=TRUE AND p.approval_valid=TRUE AND p.suspended_at IS NULL"),{"slug":slug})).mappings().first()
    if not profile:return error(request,404,"CONSULTANT_NOT_FOUND","Consultant profile was not found")
    if not profile["accepting_new_clients"]:return error(request,409,"NOT_ACCEPTING_NEW_CLIENTS","This consultant is not accepting new clients")
    key=dedupe_key(profile["id"],body.email,body.phone,body.service_id);existing=(await db.execute(text("SELECT id,status FROM external_consultant_marketplace_enrolments WHERE profile_id=:profile AND deduplication_key=:key"),{"profile":profile["id"],"key":key})).mappings().first()
    if existing:return {"success":True,"data":{"id":str(existing["id"]),"status":existing["status"],"duplicate":True},"error":None,"request_id":request.state.correlation_id}
    now=datetime.now(timezone.utc);lead_id=uuid4();enrolment_id=uuid4();email_key=normal_email(body.email);phone_key=normal_phone(body.phone)
    await db.execute(text("INSERT INTO external_leads(id,tenant_id,first_name,last_name,email,phone,email_key,phone_key,source,stage,assigned_practitioner_id,notes,created_by,created_at,updated_at) VALUES (:id,:tenant,:first,:last,:email,:phone,:email_key,:phone_key,:source,'NEW',:actor,:notes,'PUBLIC_MARKETPLACE',:now,:now)"),{"id":lead_id,"tenant":profile["tenant_id"],"first":body.full_name.split()[0],"last":" ".join(body.full_name.split()[1:]) or None,"email":body.email,"phone":body.phone,"email_key":email_key,"phone_key":phone_key,"source":body.source,"actor":profile["consultant_user_id"],"notes":"Marketplace enrolment request","now":now})
    await db.execute(text("INSERT INTO external_consultant_marketplace_enrolments(id,profile_id,tenant_id,lead_id,service_id,programme_id,full_name,email,phone,consultation_mode,location_id,preferred_at,message,consent_acknowledged,status,deduplication_key,created_at,updated_at) VALUES (:id,:profile,:tenant,:lead,:service,:programme,:name,:email,:phone,:mode,:location,:preferred,:message,TRUE,'NEW',:key,:now,:now)"),{"id":enrolment_id,"profile":profile["id"],"tenant":profile["tenant_id"],"lead":lead_id,"service":UUID(body.service_id) if body.service_id else None,"programme":UUID(body.programme_id) if body.programme_id else None,"name":body.full_name,"email":body.email,"phone":body.phone,"mode":body.consultation_mode,"location":UUID(body.location_id) if body.location_id else None,"preferred":body.preferred_at,"message":body.message,"key":key,"now":now})
    await db.execute(text("INSERT INTO external_communication_preparations(id,tenant_id,client_id,lead_id,channel,purpose,subject,body,status,created_by,created_at,updated_at) VALUES (:id,:tenant,NULL,:lead,'EMAIL_PREPARATION','Enrolment request received','Request received',:body,'PREPARED',:actor,:now,:now)"),{"id":uuid4(),"tenant":profile["tenant_id"],"lead":lead_id,"body":"Your enrolment request has been received. This is not an appointment confirmation.","actor":profile["consultant_user_id"],"now":now})
    await _marketplace_audit(db,profile["id"],profile["tenant_id"],"ENROLMENT_CREATED","PUBLIC_PROSPECT","PUBLIC",metadata={"enrolment_id":str(enrolment_id),"lead_id":str(lead_id),"source":body.source});await db.execute(text("INSERT INTO external_consultant_marketplace_events(id,profile_id,tenant_id,event_type,metadata,created_at) VALUES (:id,:profile,:tenant,'ENROLMENT_SUBMITTED',CAST(:metadata AS jsonb),:now)"),{"id":uuid4(),"profile":profile["id"],"tenant":profile["tenant_id"],"metadata":json.dumps({"enrolment_id":str(enrolment_id),"source":body.source}),"now":now});await db.commit()
    return {"success":True,"data":{"id":str(enrolment_id),"status":"NEW","duplicate":False},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/marketplace/profiles/{profile_id}/reviews")
async def submit_marketplace_review(profile_id:UUID,request:Request,body:ReviewCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    if not ctx:return error(request,401,"AUTHENTICATION_REQUIRED","A verified client relationship is required")
    profile=(await db.execute(text("SELECT id,tenant_id FROM external_consultant_public_profiles WHERE id=:id AND status='PUBLISHED'"),{"id":profile_id})).mappings().first()
    if not profile:return error(request,404,"CONSULTANT_NOT_FOUND","Consultant profile was not found")
    eligible=(await db.execute(text("SELECT 1 FROM external_scheduled_appointments WHERE tenant_id=:tenant AND client_id=:client AND status='COMPLETED' LIMIT 1"),{"tenant":profile["tenant_id"],"client":ctx["user_id"]})).first()
    if not eligible:return error(request,403,"REVIEW_NOT_ELIGIBLE","A completed verified engagement is required")
    review_id=uuid4();now=datetime.now(timezone.utc);await db.execute(text("INSERT INTO external_consultant_reviews(id,profile_id,tenant_id,client_id,overall_rating,review_text,communication_rating,professionalism_rating,support_experience_rating,verified_engagement,status,created_at,updated_at) VALUES (:id,:profile,:tenant,:client,:overall,:review,:communication,:professionalism,:support,TRUE,'UNDER_MODERATION',:now,:now)"),{"id":review_id,"profile":profile_id,"tenant":profile["tenant_id"],"client":ctx["user_id"],"overall":body.overall_rating,"review":body.review_text,"communication":body.communication_rating,"professionalism":body.professionalism_rating,"support":body.support_experience_rating,"now":now});await db.execute(text("INSERT INTO external_consultant_review_events(id,review_id,tenant_id,event_type,actor_id,created_at) VALUES (:id,:review,:tenant,'REVIEW_SUBMITTED',:actor,:now)"),{"id":uuid4(),"review":review_id,"tenant":profile["tenant_id"],"actor":ctx["user_id"],"now":now});await db.commit();return {"success":True,"data":{"id":str(review_id),"status":"UNDER_MODERATION"},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/admin/marketplace/reviews/{review_id}/decision")
async def moderate_marketplace_review(review_id:UUID,request:Request,body:AdminDecision,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=_platform_admin(request,ctx)
    if denied:return denied
    action=body.action.upper();status={"PUBLISH_REVIEW":"PUBLISHED","REJECT_REVIEW":"REJECTED","HIDE_REVIEW":"HIDDEN","RESTORE_REVIEW":"PUBLISHED"}.get(action)
    if not status:return error(request,422,"UNKNOWN_REVIEW_ACTION","Review action is not recognised")
    if action in REASON_REQUIRED and not body.reason:return error(request,422,"REASON_REQUIRED","A reason is required")
    row=(await db.execute(text("UPDATE external_consultant_reviews SET status=:status,updated_at=:now WHERE id=:id RETURNING tenant_id"),{"status":status,"now":datetime.now(timezone.utc),"id":review_id})).mappings().first()
    if not row:return error(request,404,"REVIEW_NOT_FOUND","Review was not found")
    await db.execute(text("INSERT INTO external_consultant_review_events(id,review_id,tenant_id,event_type,actor_id,reason,created_at) VALUES (:id,:review,:tenant,:event,:actor,:reason,:now)"),{"id":uuid4(),"review":review_id,"tenant":row["tenant_id"],"event":action,"actor":ctx["user_id"],"reason":body.reason,"now":datetime.now(timezone.utc)});await db.commit();return {"success":True,"data":{"status":status},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/marketplace/reviews/{review_id}/report")
async def report_marketplace_review(review_id:UUID,request:Request,body:ReviewReport,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    profile=await _marketplace_profile(db,ctx)
    if not profile:return error(request,404,"PROFILE_NOT_FOUND","Marketplace profile was not found")
    row=(await db.execute(text("UPDATE external_consultant_reviews SET reported_at=:now,updated_at=:now WHERE id=:id AND profile_id=:profile RETURNING tenant_id"),{"now":datetime.now(timezone.utc),"id":review_id,"profile":profile["id"]})).mappings().first()
    if not row:return error(request,404,"REVIEW_NOT_FOUND","Review was not found")
    await db.execute(text("INSERT INTO external_consultant_review_events(id,review_id,tenant_id,event_type,actor_id,reason,created_at) VALUES (:id,:review,:tenant,'REVIEW_REPORTED',:actor,:reason,:now)"),{"id":uuid4(),"review":review_id,"tenant":row["tenant_id"],"actor":ctx["user_id"],"reason":body.reason,"now":datetime.now(timezone.utc)});await db.commit();return {"success":True,"data":{"reported":True},"error":None,"request_id":request.state.correlation_id}

# P42 provider-neutral external calendar sync. P13 remains appointment authority.
@app.get("/api/v1/practice-operations/calendar-sync")
async def calendar_sync_status(request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"CALENDAR_SYNC_VIEW")
    if denied:return denied
    rows=list((await db.execute(text("SELECT id,provider,status,last_synced_at FROM external_calendar_connections WHERE tenant_id=:tenant AND user_id=:user ORDER BY provider"),{"tenant":ctx["tenant_id"],"user":ctx["user_id"]})).mappings().all())
    found={row["provider"]:dict(row) for row in rows};providers=[]
    for provider in ("GOOGLE","MICROSOFT"):
        row=found.get(provider);providers.append({"provider":provider,"calendarProvider":provider_state(provider,bool(row and row["status"]=='CONNECTED')),"connection":row})
    blocks=[project_busy_block(dict(row)) for row in (await db.execute(text("SELECT id,starts_at,ends_at FROM external_calendar_busy_blocks WHERE tenant_id=:tenant AND active=TRUE AND ends_at>NOW() ORDER BY starts_at LIMIT 250"),{"tenant":ctx["tenant_id"]})).mappings().all()]
    return {"success":True,"data":{"providers":providers,"busyBlocks":blocks,"schedulingAuthority":"P13_INTERNAL"},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/calendar-sync/connections")
async def prepare_calendar_connection(request:Request,body:CalendarConnectionPrepare,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"CALENDAR_SYNC_MANAGE")
    if denied:return denied
    # OAuth handshakes require governed provider configuration; never accept tokens from this API.
    return {"success":True,"data":{"provider":body.provider,"calendarProvider":"NOT_CONFIGURED","oauthTokenExposed":False},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/calendar-sync/connections/{connection_id}/busy-blocks",status_code=201)
async def import_calendar_busy_block(connection_id:UUID,request:Request,body:CalendarBusyBlockImport,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"CALENDAR_SYNC_MANAGE")
    if denied:return denied
    if body.ends_at<=body.starts_at:return error(request,422,"INVALID_BUSY_WINDOW","Busy block must end after it starts")
    connection=(await db.execute(text("SELECT id,tenant_id FROM external_calendar_connections WHERE id=:id AND tenant_id=:tenant AND user_id=:user AND status='CONNECTED'"),{"id":connection_id,"tenant":ctx["tenant_id"],"user":ctx["user_id"]})).mappings().first()
    if not connection:return error(request,409,"CALENDAR_PROVIDER_NOT_CONFIGURED","Calendar provider is not configured")
    digest=hashlib.sha256(body.provider_event_id.encode()).hexdigest();block_id=uuid4();now=datetime.now(timezone.utc)
    await db.execute(text("INSERT INTO external_calendar_busy_blocks(id,connection_id,tenant_id,provider_event_hash,starts_at,ends_at,visibility,active,created_at,updated_at) VALUES (:id,:connection,:tenant,:hash,:start,:end,'BUSY',TRUE,:now,:now) ON CONFLICT(connection_id,provider_event_hash) DO UPDATE SET starts_at=EXCLUDED.starts_at,ends_at=EXCLUDED.ends_at,active=TRUE,updated_at=EXCLUDED.updated_at"),{"id":block_id,"connection":connection_id,"tenant":ctx["tenant_id"],"hash":digest,"start":body.starts_at,"end":body.ends_at,"now":now});await db.commit()
    return {"success":True,"data":{"visibility":"BUSY","providerEventTitle":None},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/calendar-sync/connections/{connection_id}/external-changes",status_code=202)
async def detect_external_calendar_change(connection_id:UUID,request:Request,body:CalendarExternalChange,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"CALENDAR_SYNC_MANAGE")
    if denied:return denied
    connection=(await db.execute(text("SELECT id FROM external_calendar_connections WHERE id=:id AND tenant_id=:tenant AND user_id=:user AND status='CONNECTED'"),{"id":connection_id,"tenant":ctx["tenant_id"],"user":ctx["user_id"]})).first()
    if not connection:return error(request,409,"CALENDAR_PROVIDER_NOT_CONFIGURED","Calendar provider is not configured")
    appointment=(await db.execute(text("SELECT id FROM external_scheduled_appointments WHERE id=:id AND tenant_id=:tenant"),{"id":body.appointment_id,"tenant":ctx["tenant_id"]})).first()
    if not appointment:return error(request,404,"APPOINTMENT_NOT_FOUND","Appointment was not found")
    action=external_change_action(body.change_type);now=datetime.now(timezone.utc)
    await db.execute(text("INSERT INTO external_calendar_sync_events(id,connection_id,tenant_id,appointment_id,event_type,external_change_type,actor_id,metadata,created_at) VALUES (:id,:connection,:tenant,:appointment,'EXTERNAL_CHANGE_DETECTED',:change,:actor,CAST(:metadata AS jsonb),:now)"),{"id":uuid4(),"connection":connection_id,"tenant":ctx["tenant_id"],"appointment":body.appointment_id,"change":body.change_type,"actor":ctx["user_id"],"metadata":json.dumps({"provider_event_hash":hashlib.sha256(body.provider_event_id.encode()).hexdigest(),"action":action}),"now":now});await db.commit()
    return {"success":True,"data":{"action":action,"appointmentChanged":False},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/marketplace/earnings")
async def marketplace_earnings(request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    row=(await db.execute(text("""SELECT COUNT(*) transaction_count,COALESCE(SUM(gross_minor),0) gross_minor,COALESCE(SUM(platform_fee_minor),0) platform_fee_minor,COALESCE(SUM(net_payout_minor),0) net_earnings_minor,MIN(currency) currency FROM external_marketplace_transactions WHERE tenant_id=:tenant AND consultant_user_id=:user"""),{"tenant":ctx["tenant_id"],"user":ctx["user_id"]})).mappings().one()
    payouts=(await db.execute(text("""SELECT COALESCE(SUM(amount_minor) FILTER(WHERE state IN ('PENDING','ELIGIBLE','PROCESSING','ON_HOLD')),0) pending_payout_minor,COALESCE(SUM(amount_minor) FILTER(WHERE state='PAID'),0) paid_payout_minor FROM external_marketplace_payouts WHERE tenant_id=:tenant AND consultant_user_id=:user"""),{"tenant":ctx["tenant_id"],"user":ctx["user_id"]})).mappings().one()
    data={**dict(row),**dict(payouts)};data["state"]="READY" if row["transaction_count"] else "CONFIRMED_EMPTY";return {"success":True,"data":data,"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/admin/marketplace/finance")
async def admin_marketplace_finance(request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=_platform_admin(request,ctx)
    if denied:return denied
    row=(await db.execute(text("""SELECT COUNT(*) transaction_count,COALESCE(SUM(gross_minor),0) gmv_minor,COALESCE(SUM(platform_fee_minor),0) platform_revenue_minor,COALESCE(SUM(net_payout_minor),0) consultant_payable_minor,COALESCE(SUM(CASE WHEN status IN ('REFUNDED','PARTIALLY_REFUNDED') THEN gross_minor ELSE 0 END),0) refunds_minor FROM external_marketplace_transactions"""))).mappings().one()
    pending=(await db.execute(text("SELECT COALESCE(SUM(amount_minor),0) FROM external_marketplace_payouts WHERE state IN ('PENDING','ELIGIBLE','PROCESSING','ON_HOLD')"))).scalar_one()
    return {"success":True,"data":{**dict(row),"pending_settlement_minor":pending,"state":"READY" if row["transaction_count"] else "CONFIRMED_EMPTY","revenueRecognition":"RECORDED_TRANSACTIONS_ONLY"},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/admin/marketplace/commission-rules",status_code=201)
async def create_marketplace_commission_rule(request:Request,body:MarketplaceCommissionRuleCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=_platform_admin(request,ctx)
    if denied:return denied
    if body.scope_type!='PLATFORM_DEFAULT' and not body.scope_id:return error(request,422,"COMMISSION_SCOPE_REQUIRED","This commission scope requires an identifier")
    if body.commission_type=='PERCENTAGE' and body.commission_value>100:return error(request,422,"INVALID_COMMISSION","Percentage cannot exceed 100")
    item_id=uuid4();now=datetime.now(timezone.utc)
    await db.execute(text("INSERT INTO external_marketplace_commission_rules(id,scope_type,scope_id,commission_type,commission_value,currency,active,effective_from,effective_until,created_by,created_at) VALUES (:id,:scope,:scope_id,:kind,:value,:currency,TRUE,:starts,:ends,:actor,:now)"),{"id":item_id,"scope":body.scope_type,"scope_id":body.scope_id,"kind":body.commission_type,"value":body.commission_value,"currency":body.currency,"starts":body.effective_from,"ends":body.effective_until,"actor":ctx["user_id"],"now":now});await db.commit()
    return {"success":True,"data":{"id":str(item_id),"active":True},"error":None,"request_id":request.state.correlation_id}

@app.patch("/api/v1/practice-operations/admin/marketplace/payouts/{payout_id}")
async def update_marketplace_payout(payout_id:UUID,request:Request,body:MarketplacePayoutUpdate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=_platform_admin(request,ctx)
    if denied:return denied
    try:assert_paid_evidence(body.state,body.provider_reference,body.manual_settlement_reference)
    except ValueError as exc:return error(request,422,"SETTLEMENT_EVIDENCE_REQUIRED",str(exc))
    now=datetime.now(timezone.utc);result=await db.execute(text("UPDATE external_marketplace_payouts SET state=:state,provider_reference=:provider,manual_settlement_reference=:manual,settled_at=CASE WHEN :state='PAID' THEN :now ELSE settled_at END,updated_at=:now WHERE id=:id"),{"state":body.state,"provider":body.provider_reference,"manual":body.manual_settlement_reference,"now":now,"id":payout_id})
    if result.rowcount!=1:return error(request,404,"PAYOUT_NOT_FOUND","Payout was not found")
    await db.execute(text("INSERT INTO external_marketplace_financial_ledger(id,payout_id,tenant_id,entry_type,amount_minor,currency,direction,evidence_reference,created_at) SELECT :entry,id,tenant_id,'PAYOUT',amount_minor,currency,'DEBIT',COALESCE(:provider,:manual),:now FROM external_marketplace_payouts WHERE id=:id"),{"entry":uuid4(),"provider":body.provider_reference,"manual":body.manual_settlement_reference,"now":now,"id":payout_id});await db.commit()
    return {"success":True,"data":{"state":body.state,"settlementEvidence":body.state=='PAID'},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/subscription")
async def practice_subscription(request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    row=(await db.execute(text("""SELECT s.id,s.state,s.billing_cycle,s.current_period_start,s.current_period_end,s.trial_ends_at,p.code,p.name,p.monthly_price_minor,p.annual_price_minor,p.currency,p.included_practitioners,p.included_locations,p.storage_bytes,p.feature_entitlements,p.usage_limits FROM external_practice_subscriptions s JOIN external_saas_plans p ON p.id=s.plan_id WHERE s.tenant_id=:tenant"""),{"tenant":ctx["tenant_id"]})).mappings().first()
    if not row:return {"success":True,"data":{"state":"NOT_CONFIGURED","subscriptionPaymentProvider":subscription_provider_status(False),"downgradePolicy":downgrade_policy()},"error":None,"request_id":request.state.correlation_id}
    return {"success":True,"data":{**dict(row),"subscriptionPaymentProvider":subscription_provider_status(False),"downgradePolicy":downgrade_policy(),"entitlementAuthority":"PRODUCT_AND_ROLE_AND_PROFESSION"},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/admin/saas-plans")
async def admin_saas_plans(request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=_platform_admin(request,ctx)
    if denied:return denied
    rows=[dict(row) for row in (await db.execute(text("SELECT id,code,name,monthly_price_minor,annual_price_minor,currency,included_practitioners,included_locations,storage_bytes,feature_entitlements,usage_limits,active FROM external_saas_plans ORDER BY code"))).mappings().all()]
    return {"success":True,"data":{"state":"READY" if rows else "CONFIRMED_EMPTY","items":rows},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/public/consultants/{slug}/promotions/quote")
async def public_promotion_quote(slug:str,request:Request,body:PromotionQuote,db:AsyncSession=Depends(get_db)):
    profile=(await db.execute(text("SELECT id,tenant_id,consultant_user_id FROM external_consultant_public_profiles WHERE slug=:slug AND status='PUBLISHED' AND public_visibility=TRUE AND approval_valid=TRUE AND suspended_at IS NULL"),{"slug":slug})).mappings().first()
    if not profile:return error(request,404,"CONSULTANT_NOT_FOUND","Consultant profile was not found")
    rule=(await db.execute(text("SELECT id,tenant_id,promotion_type,value,valid_from,valid_until,usage_limit,per_user_limit,service_id,consultant_id,minimum_amount_minor,maximum_discount_minor,stackable,active FROM external_promotions WHERE UPPER(code)=UPPER(:code) AND active=TRUE AND (tenant_id IS NULL OR tenant_id=:tenant) ORDER BY tenant_id NULLS LAST,created_at DESC LIMIT 1"),{"code":body.code,"tenant":profile["tenant_id"]})).mappings().first()
    if not rule:return error(request,404,"PROMOTION_NOT_FOUND","Promotion was not found")
    counts=(await db.execute(text("SELECT COUNT(*) total,COUNT(*) FILTER(WHERE user_id=:user) user_total FROM external_promotion_redemptions WHERE promotion_id=:id"),{"user":body.user_reference,"id":rule["id"]})).mappings().one()
    try:validate_rule(dict(rule),now=datetime.now(timezone.utc),tenant_id=profile["tenant_id"],user_id=body.user_reference,service_id=body.service_id,consultant_id=profile["consultant_user_id"],total_uses=counts["total"],user_uses=counts["user_total"],stacked=bool(body.existing_promotion_ids),amount_minor=body.amount_minor);discount=discount_minor(rule["promotion_type"],rule["value"],body.amount_minor,rule["maximum_discount_minor"])
    except ValueError as exc:return error(request,409,"PROMOTION_NOT_APPLICABLE",str(exc))
    return {"success":True,"data":{"promotionId":str(rule["id"]),"discountMinor":discount,"amountAfterMinor":body.amount_minor-discount,"currency":body.currency,"applied":True},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/billing/refunds",status_code=201)
async def create_refund_request(request:Request,body:RefundCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"BILLING_MANAGE")
    if denied:return denied
    invoice=(await db.execute(text("SELECT id,grand_total_minor,currency FROM external_invoices WHERE id=:id AND tenant_id=:tenant AND status<>'DRAFT'"),{"id":body.invoice_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not invoice:return error(request,404,"INVOICE_NOT_FOUND","Issued invoice was not found")
    if invoice["currency"]!=body.currency or body.amount_minor>invoice["grand_total_minor"]:return error(request,422,"INVALID_REFUND_AMOUNT","Refund must be within the issued invoice total and currency")
    item_id=uuid4();now=datetime.now(timezone.utc)
    await db.execute(text("INSERT INTO external_refunds(id,tenant_id,invoice_id,payment_id,appointment_id,amount_minor,currency,state,reason,requested_by,created_at,updated_at) VALUES (:id,:tenant,:invoice,:payment,:appointment,:amount,:currency,'REFUND_REQUESTED',:reason,:actor,:now,:now)"),{"id":item_id,"tenant":ctx["tenant_id"],"invoice":body.invoice_id,"payment":body.payment_id,"appointment":body.appointment_id,"amount":body.amount_minor,"currency":body.currency,"reason":body.reason,"actor":ctx["user_id"],"now":now});await db.execute(text("INSERT INTO external_refund_events(id,refund_id,tenant_id,event_type,resulting_state,actor_id,created_at) VALUES (:id,:refund,:tenant,'REFUND_REQUESTED','REFUND_REQUESTED',:actor,:now)"),{"id":uuid4(),"refund":item_id,"tenant":ctx["tenant_id"],"actor":ctx["user_id"],"now":now});await db.commit()
    return {"success":True,"data":{"id":str(item_id),"state":"REFUND_REQUESTED","invoiceChanged":False},"error":None,"request_id":request.state.correlation_id}

@app.patch("/api/v1/practice-operations/billing/refunds/{refund_id}")
async def transition_refund(refund_id:UUID,request:Request,body:RefundTransition,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied,_=await _team_guard(request,db,ctx,"BILLING_MANAGE")
    if denied:return denied
    row=(await db.execute(text("SELECT id,tenant_id,invoice_id,amount_minor,currency,state FROM external_refunds WHERE id=:id AND tenant_id=:tenant FOR UPDATE"),{"id":refund_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not row:return error(request,404,"REFUND_NOT_FOUND","Refund was not found")
    evidence=body.provider_refund_reference or body.manual_refund_reference
    try:target=refund_transition(row["state"],body.state,evidence)
    except ValueError as exc:return error(request,409,"INVALID_REFUND_TRANSITION",str(exc))
    now=datetime.now(timezone.utc);await db.execute(text("UPDATE external_refunds SET state=:state,provider_refund_reference=:provider,manual_refund_reference=:manual,approved_by=CASE WHEN :state='REFUND_APPROVED' THEN :actor ELSE approved_by END,updated_at=:now WHERE id=:id"),{"state":target,"provider":body.provider_refund_reference,"manual":body.manual_refund_reference,"actor":ctx["user_id"],"now":now,"id":refund_id});await db.execute(text("INSERT INTO external_refund_events(id,refund_id,tenant_id,event_type,previous_state,resulting_state,actor_id,evidence_reference,created_at) VALUES (:id,:refund,:tenant,:event,:previous,:result,:actor,:evidence,:now)"),{"id":uuid4(),"refund":refund_id,"tenant":ctx["tenant_id"],"event":target,"previous":row["state"],"result":target,"actor":ctx["user_id"],"evidence":evidence,"now":now})
    if target=='REFUNDED':
        note_id=uuid4();await db.execute(text("INSERT INTO external_credit_notes(id,tenant_id,invoice_id,refund_id,credit_note_number,amount_minor,currency,reason,status,issued_at,created_by,created_at) SELECT :id,tenant_id,invoice_id,id,:number,amount_minor,currency,reason,'ISSUED',:now,:actor,:now FROM external_refunds WHERE id=:refund"),{"id":note_id,"number":f"CR-{str(note_id)[:8].upper()}","now":now,"actor":ctx["user_id"],"refund":refund_id})
    await db.commit();return {"success":True,"data":{"state":target,"refundEvidence":bool(evidence),"invoiceChanged":False,"creditNoteIssued":target=='REFUNDED'},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/admin/marketplace/finder-config")
async def admin_finder_config(request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=_platform_admin(request,ctx)
    if denied:return denied
    row=(await db.execute(text("SELECT config,updated_by,updated_at FROM external_marketplace_finder_config WHERE config_key='PUBLIC_FINDER'"))).mappings().first()
    return {"success":True,"data":dict(row) if row else {"config":{"support_areas":SUPPORT_TAXONOMY,"questions":["support_area","mode","location","languages","availability","budget","experience"]}},"error":None,"request_id":request.state.correlation_id}

@app.put("/api/v1/practice-operations/admin/marketplace/finder-config")
async def update_admin_finder_config(request:Request,body:dict,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=_platform_admin(request,ctx)
    if denied:return denied
    areas=body.get("support_areas");questions=body.get("questions")
    if not isinstance(areas,dict) or not isinstance(questions,list):return error(request,422,"INVALID_FINDER_CONFIG","Support areas and question order are required")
    allowed_questions={"support_area","mode","location","languages","availability","budget","experience"}
    if not questions or questions[0]!="support_area" or len(questions)!=len(set(questions)) or any(item not in allowed_questions for item in questions):return error(request,422,"INVALID_FINDER_QUESTIONS","Question order must be unique and begin with Support Area")
    active={code:item for code,item in areas.items() if item.get("active",True)};eligible={profession for item in SUPPORT_TAXONOMY.values() for profession in item["professions"]}
    if not active:return error(request,422,"NO_ACTIVE_SUPPORT_AREA","At least one active support area is required")
    if any(not item.get("professions") for item in active.values()):return error(request,422,"UNMAPPED_ACTIVE_SUPPORT_AREA","Every active support area requires a profession mapping")
    if any(len(item.get("professions",[]))!=len(set(item.get("professions",[]))) for item in areas.values()):return error(request,422,"DUPLICATE_MAPPING","Profession mappings must be unique")
    if any(profession not in eligible for item in active.values() for profession in item.get("professions",[])):return error(request,422,"INVALID_PROFESSION","Profession mapping is not marketplace eligible")
    previous=(await db.execute(text("SELECT config FROM external_marketplace_finder_config WHERE config_key='PUBLIC_FINDER'"))).mappings().first();history=list(previous["config"].get("_audit_history",[]) if previous else []);history.append({"event":"FINDER_PROFESSION_MAPPING_UPDATED","actor":ctx["user_id"],"timestamp":datetime.now(timezone.utc).isoformat(),"old":previous["config"] if previous else None,"new":{"support_areas":areas,"questions":questions}})
    config={"support_areas":areas,"questions":questions,"_audit_history":history[-20:]}
    await db.execute(text("INSERT INTO external_marketplace_finder_config(id,config_key,config,active,updated_by,updated_at) VALUES (:id,'PUBLIC_FINDER',CAST(:config AS jsonb),TRUE,:actor,:now) ON CONFLICT(config_key) DO UPDATE SET config=EXCLUDED.config,active=TRUE,updated_by=EXCLUDED.updated_by,updated_at=EXCLUDED.updated_at"),{"id":uuid4(),"config":json.dumps(config),"actor":ctx["user_id"],"now":datetime.now(timezone.utc)});await db.commit()
    return {"success":True,"data":{"config":config},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/admin/marketplace/analytics")
async def admin_marketplace_analytics(request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=_platform_admin(request,ctx)
    if denied:return denied
    summary=(await db.execute(text("SELECT COUNT(*) FILTER(WHERE status='PUBLISHED')::int published_consultants,COUNT(*) FILTER(WHERE status IN ('SUBMITTED_FOR_REVIEW','UNDER_REVIEW'))::int pending_approvals,COUNT(*) FILTER(WHERE status='PUBLISHED' AND accepting_new_clients=TRUE)::int accepting_clients FROM external_consultant_public_profiles"))).mappings().one()
    events=[dict(row) for row in (await db.execute(text("SELECT event_type,COUNT(*)::int count FROM external_consultant_marketplace_events GROUP BY event_type"))).mappings().all()]
    homepage_events=[dict(row) for row in (await db.execute(text("SELECT event_type,COUNT(*)::int count FROM external_marketplace_homepage_events GROUP BY event_type"))).mappings().all()]
    comparison_events=[dict(row) for row in (await db.execute(text("SELECT event_type,COUNT(*)::int count FROM external_marketplace_comparison_events GROUP BY event_type"))).mappings().all()]
    finder_events=[dict(row) for row in (await db.execute(text("SELECT event_type,step,COUNT(*)::int count FROM external_marketplace_finder_events GROUP BY event_type,step"))).mappings().all()]
    return {"success":True,"data":{"state":"READY","summary":dict(summary),"events":events,"homepage_events":homepage_events,"comparison_events":comparison_events,"finder_events":finder_events,"engagement_label":"Marketplace engagement"},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/support/tickets")
async def list_support_tickets(request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    rows=[dict(row) for row in (await db.execute(text("SELECT id,ticket_type,subject,status,priority,owner_id,sla_due_at,safe_context,created_at,updated_at FROM external_support_tickets WHERE tenant_id=:tenant ORDER BY updated_at DESC LIMIT 100"),{"tenant":ctx["tenant_id"]})).mappings().all()]
    return {"success":True,"data":{"state":"READY" if rows else "CONFIRMED_EMPTY","items":rows},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/support/tickets",status_code=201)
async def create_support_ticket(request:Request,body:SupportTicketCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    try: context_data=safe_context(body.context)
    except ValueError as exc:return error(request,422,"UNSAFE_SUPPORT_CONTEXT",str(exc))
    item_id=uuid4();now=datetime.now(timezone.utc)
    await db.execute(text("INSERT INTO external_support_tickets(id,tenant_id,created_by,ticket_type,subject,description,safe_context,created_at,updated_at) VALUES (:id,:tenant,:actor,:type,:subject,:description,CAST(:context AS jsonb),:now,:now)"),{"id":item_id,"tenant":ctx["tenant_id"],"actor":ctx["user_id"],"type":body.ticket_type,"subject":body.subject,"description":body.description,"context":json.dumps(context_data),"now":now})
    await db.execute(text("INSERT INTO external_support_ticket_events(id,ticket_id,tenant_id,event_type,resulting_status,actor_id,metadata,created_at) VALUES (:id,:ticket,:tenant,'CREATED','OPEN',:actor,CAST(:details AS jsonb),:now)"),{"id":uuid4(),"ticket":item_id,"tenant":ctx["tenant_id"],"actor":ctx["user_id"],"details":json.dumps({"ticket_type":body.ticket_type}),"now":now});await db.commit()
    return {"success":True,"data":{"id":str(item_id),"status":"OPEN","context":context_data},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/admin/support/tickets")
async def admin_support_tickets(request:Request,status:str|None=None,priority:str|None=None,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=_platform_admin(request,ctx)
    if denied:return denied
    rows=[dict(row) for row in (await db.execute(text("SELECT id,tenant_id,created_by,ticket_type,subject,status,priority,owner_id,sla_due_at,safe_context,created_at,updated_at FROM external_support_tickets WHERE (CAST(:status AS text) IS NULL OR status=CAST(:status AS text)) AND (CAST(:priority AS text) IS NULL OR priority=CAST(:priority AS text)) ORDER BY priority,created_at LIMIT 250"),{"status":status,"priority":priority})).mappings().all()]
    return {"success":True,"data":{"state":"READY" if rows else "CONFIRMED_EMPTY","items":rows},"error":None,"request_id":request.state.correlation_id}

@app.patch("/api/v1/practice-operations/admin/support/tickets/{ticket_id}")
async def update_support_ticket(ticket_id:UUID,request:Request,body:SupportTicketUpdate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=_platform_admin(request,ctx)
    if denied:return denied
    row=(await db.execute(text("SELECT tenant_id,status,priority,owner_id FROM external_support_tickets WHERE id=:id FOR UPDATE"),{"id":ticket_id})).mappings().first()
    if not row:return error(request,404,"SUPPORT_TICKET_NOT_FOUND","Support ticket was not found")
    priority=body.priority or row["priority"];owner=body.owner_id if body.owner_id is not None else row["owner_id"];now=datetime.now(timezone.utc);hours={"P1":4,"P2":8,"P3":24,"P4":72}[priority]
    await db.execute(text("UPDATE external_support_tickets SET status=:status,priority=:priority,owner_id=:owner,sla_due_at=COALESCE(sla_due_at,:sla),updated_at=:now WHERE id=:id"),{"status":body.status,"priority":priority,"owner":owner,"sla":now+timedelta(hours=hours),"now":now,"id":ticket_id})
    await db.execute(text("INSERT INTO external_support_ticket_events(id,ticket_id,tenant_id,event_type,previous_status,resulting_status,actor_id,message,metadata,created_at) VALUES (:id,:ticket,:tenant,'ADMIN_UPDATED',:previous,:result,:actor,:message,CAST(:details AS jsonb),:now)"),{"id":uuid4(),"ticket":ticket_id,"tenant":row["tenant_id"],"previous":row["status"],"result":body.status,"actor":ctx["user_id"],"message":body.message,"details":json.dumps({"priority":priority,"owner_id":owner}),"now":now});await db.commit()
    return {"success":True,"data":{"id":str(ticket_id),"status":body.status,"priority":priority,"owner_id":owner},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/notification-centre")
async def notification_centre(request:Request,state:str|None=None,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    rows=[dict(row) for row in (await db.execute(text("""SELECT n.id,n.client_id,n.event_type,n.title,n.payload,n.created_at,COALESCE(s.state,'UNREAD') state FROM practice_notifications n LEFT JOIN external_notification_user_states s ON s.notification_id=n.id AND s.tenant_id=n.tenant_id AND s.user_id=:user WHERE n.tenant_id=:tenant AND (CAST(:state AS text) IS NULL OR COALESCE(s.state,'UNREAD')=CAST(:state AS text)) ORDER BY n.created_at DESC LIMIT 100"""),{"user":ctx["user_id"],"tenant":ctx["tenant_id"],"state":state})).mappings().all()]
    for row in rows:row["category"]=notification_category(row["event_type"])
    return {"success":True,"data":{"state":"READY" if rows else "CONFIRMED_EMPTY","items":rows,"source":"CANONICAL_SYSTEM_EVENTS"},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/notification-centre/{notification_id}/{action}")
async def act_notification(notification_id:UUID,action:str,request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    if action not in {'read','archive'}:return error(request,422,"INVALID_NOTIFICATION_ACTION","Notification action must be read or archive")
    exists=(await db.execute(text("SELECT 1 FROM practice_notifications WHERE id=:id AND tenant_id=:tenant"),{"id":notification_id,"tenant":ctx["tenant_id"]})).first()
    if not exists:return error(request,404,"NOTIFICATION_NOT_FOUND","Notification was not found")
    result='READ' if action=='read' else 'ARCHIVED';now=datetime.now(timezone.utc)
    await db.execute(text("INSERT INTO external_notification_user_states(id,tenant_id,user_id,notification_id,state,acted_at) VALUES (:id,:tenant,:user,:notification,:state,:now) ON CONFLICT(tenant_id,user_id,notification_id) DO UPDATE SET state=EXCLUDED.state,acted_at=EXCLUDED.acted_at"),{"id":uuid4(),"tenant":ctx["tenant_id"],"user":ctx["user_id"],"notification":notification_id,"state":result,"now":now});await db.commit()
    return {"success":True,"data":{"state":result,"userAction":True},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/notification-preferences")
async def get_notification_preferences(request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    row=(await db.execute(text("SELECT in_app,email,sms,whatsapp,digest_mode,category_preferences FROM external_notification_preferences WHERE tenant_id=:tenant AND user_id=:user"),{"tenant":ctx["tenant_id"],"user":ctx["user_id"]})).mappings().first()
    return {"success":True,"data":dict(row) if row else {"in_app":True,"email":False,"sms":False,"whatsapp":False,"digest_mode":"IMMEDIATE","category_preferences":{},"providers":{"email":"NOT_CONFIGURED","sms":"NOT_CONFIGURED","whatsapp":"PREPARATION_ONLY"}},"error":None,"request_id":request.state.correlation_id}

@app.put("/api/v1/practice-operations/notification-preferences")
async def update_notification_preferences(request:Request,body:dict,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    try:mode=digest_mode(body.get('digest_mode','IMMEDIATE'))
    except ValueError as exc:return error(request,422,"INVALID_DIGEST_MODE",str(exc))
    now=datetime.now(timezone.utc);values={key:bool(body.get(key,False)) for key in ('in_app','email','sms','whatsapp')};values['in_app']=True
    await db.execute(text("""INSERT INTO external_notification_preferences(id,tenant_id,user_id,in_app,email,sms,whatsapp,digest_mode,category_preferences,updated_at) VALUES (:id,:tenant,:user,:in_app,:email,:sms,:whatsapp,:mode,CAST(:categories AS jsonb),:now) ON CONFLICT(tenant_id,user_id) DO UPDATE SET in_app=EXCLUDED.in_app,email=EXCLUDED.email,sms=EXCLUDED.sms,whatsapp=EXCLUDED.whatsapp,digest_mode=EXCLUDED.digest_mode,category_preferences=EXCLUDED.category_preferences,updated_at=EXCLUDED.updated_at"""),{"id":uuid4(),"tenant":ctx["tenant_id"],"user":ctx["user_id"],**values,"mode":mode,"categories":json.dumps(body.get('category_preferences',{})),"now":now});await db.commit()
    return {"success":True,"data":{**values,"digest_mode":mode,"externalSendAttempted":False,"mandatoryInApp":True},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/global-search")
async def global_search(request:Request,q:str=Query(min_length=2,max_length=120),ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied:return denied
    term=f"%{q.strip()}%";params={"tenant":ctx["tenant_id"],"term":term}
    sql="""SELECT id::text,'LEAD' resource_type,TRIM(first_name||' '||COALESCE(last_name,'')) title,'/dashboard/consultant?view=leads' route,updated_at FROM external_leads WHERE tenant_id=:tenant AND (first_name ILIKE :term OR last_name ILIKE :term OR email ILIKE :term)
    UNION ALL SELECT id::text,'INVOICE',COALESCE(invoice_number,'Draft invoice'),'/dashboard/consultant?view=billing',updated_at FROM external_invoices WHERE tenant_id=:tenant AND (invoice_number ILIKE :term OR client_id ILIKE :term)
    UNION ALL SELECT id::text,'DOCUMENT',title,'/dashboard/consultant?view=documents',updated_at FROM external_documents WHERE tenant_id=:tenant AND visibility<>'PRACTITIONER_PRIVATE' AND title ILIKE :term
    UNION ALL SELECT id::text,'REFERRAL',COALESCE(destination_name,receiving_profession_code),'/dashboard/consultant?view=referrals',updated_at FROM external_referrals WHERE tenant_id=:tenant AND (destination_name ILIKE :term OR receiving_profession_code ILIKE :term)
    UNION ALL SELECT id::text,'SUPPORT',subject,'/dashboard/consultant?view=support',updated_at FROM external_support_tickets WHERE tenant_id=:tenant AND (subject ILIKE :term OR description ILIKE :term)
    ORDER BY updated_at DESC LIMIT 50"""
    rows=[dict(row) for row in (await db.execute(text(sql),params)).mappings().all()]
    return {"success":True,"data":{"state":"READY" if rows else "CONFIRMED_EMPTY","items":rows,"query":q,"authority":"TENANT_AND_RBAC","domains":["clients","leads","appointments","invoices","payments","reports","documents","forms","resources","referrals","consultants","marketplace_enrolments","support_tickets"]},"error":None,"request_id":request.state.correlation_id}

@app.get("/api/v1/practice-operations/recent-work")
async def recent_work(request:Request,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    rows=[dict(row) for row in (await db.execute(text("SELECT resource_type,resource_id,title,route,activity_type,occurred_at FROM external_recent_work WHERE tenant_id=:tenant AND user_id=:user ORDER BY occurred_at DESC LIMIT 30"),{"tenant":ctx["tenant_id"],"user":ctx["user_id"]})).mappings().all()]
    return {"success":True,"data":{"recentlyViewed":[x for x in rows if x['activity_type']=='VIEWED'],"recentlyEdited":[x for x in rows if x['activity_type']=='EDITED'],"continueWorking":rows[:5]},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/recent-work")
async def record_recent_work(request:Request,body:dict,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    if body.get('activity_type') not in {'VIEWED','EDITED'}:return error(request,422,"INVALID_ACTIVITY_TYPE","Activity must be viewed or edited")
    if not str(body.get('route','')).startswith('/dashboard/consultant'):return error(request,422,"UNSAFE_ACTIVITY_ROUTE","Recent work route is outside the authorised workspace")
    now=datetime.now(timezone.utc);await db.execute(text("""INSERT INTO external_recent_work(id,tenant_id,user_id,resource_type,resource_id,title,route,activity_type,occurred_at) VALUES (:id,:tenant,:user,:type,:resource,:title,:route,:activity,:now) ON CONFLICT(tenant_id,user_id,resource_type,resource_id,activity_type) DO UPDATE SET title=EXCLUDED.title,route=EXCLUDED.route,occurred_at=EXCLUDED.occurred_at"""),{"id":uuid4(),"tenant":ctx["tenant_id"],"user":ctx["user_id"],"type":str(body.get('resource_type',''))[:50],"resource":str(body.get('resource_id',''))[:120],"title":str(body.get('title',''))[:240],"route":body['route'][:500],"activity":body['activity_type'],"now":now});await db.commit()
    return {"success":True,"data":{"recorded":True,"privateToUser":True},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/command-palette/resolve")
async def resolve_safe_command(request:Request,body:dict,ctx=Depends(context)):
    try:command=resolve_command(body.get('command',''))
    except ValueError as exc:return error(request,422,"UNKNOWN_SAFE_COMMAND",str(exc))
    return {"success":True,"data":{"command":command,"execution":"CLIENT_NAVIGATION_ONLY","naturalLanguageExecution":False},"error":None,"request_id":request.state.correlation_id}


# Phase 1 intentionally exposes one-segment dynamic CRUD routes for its four
# generic resources. Later phases added literal one-segment collections such
# as /packages, /resources, /automations, and /referrals. Starlette resolves
# routes in registration order, so every explicit P1-P50 path must precede the
# two legacy catch-alls; otherwise the generic handler returns
# RESOURCE_NOT_FOUND (or validates against the wrong request contract) before
# the owning handler can run. Keep the correction centralized and preserve
# every public path and request contract.
def _prefer_literal_practice_collection_routes() -> None:
    prefix = "/api/v1/practice-operations/"
    dynamic_paths = {
        f"{prefix}{{resource}}",
        f"{prefix}{{resource}}/{{item_id}}",
    }
    specific_routes = []
    catch_all_routes = []
    for route in app.router.routes:
        if getattr(route, "path", "") in dynamic_paths:
            catch_all_routes.append(route)
        else:
            specific_routes.append(route)
    if not catch_all_routes:
        return
    app.router.routes[:] = [*specific_routes, *catch_all_routes]


_prefer_literal_practice_collection_routes()
