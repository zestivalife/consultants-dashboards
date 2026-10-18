from contextlib import asynccontextmanager
from datetime import date, datetime, timezone, timedelta
from uuid import UUID, uuid4
import json
import base64
import hashlib
import secrets
import structlog
import httpx
from urllib.parse import urlparse
from cryptography.fernet import Fernet
from fastapi import Depends, FastAPI, Header, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
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
                           ProfessionPlanCreate, ProfessionPlanSave)
from app.contracts import SessionNoteCreate, SessionNoteSave, SessionNoteAmendment, PrivateNoteCreate
from app.contracts import ProgressMetricCreate, ProgressObservationCreate, ProgressTargetCreate, ProgressMilestoneCreate
from app.contracts import TemplateCreate, TemplateUpdate, SessionSuggestionGenerate, SessionSuggestionDecision, EngagementProjectionRequest
from app.contracts import ClientPortalInvitationCreate, ClientPortalDocumentCreate
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
from app.billing import calculate_line
from app.p15 import adherence_summary, homework_transition
from app.p16 import (ACTION_TYPES, CONFIRMATION_ACTIONS, SAFE_ACTIONS,
                     assert_chain_depth, evaluate_condition, idempotency_key)
from app.p17 import PERMISSIONS, ROLE_PERMISSIONS, can_manage_role, resolve_permissions
from app.p18 import MIN_COHORT_SIZE, analytics_window, cohort_result, rate
from app.p19 import ALLOWED_SCOPES, referral_transition, validate_scopes
from app.client_portal import PortalTokenError, issue_portal_token, portal_token_hash, validate_portal_token
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


async def configuration(db: AsyncSession, ctx):
    row = (await db.execute(text("SELECT profession,capabilities,terminology,profile,version FROM practice_tenant_configuration WHERE tenant_id=:tenant_id"), {"tenant_id":ctx["tenant_id"]})).mappings().first()
    if row: return dict(row)
    return {"profession":"OTHER","capabilities":["CLIENT_CRM","CLIENT_ONBOARDING","CONSULTATIONS","FOLLOW_UPS","GOALS_PROGRESS","TASKS","CALENDAR","COMMUNICATION","WHATSAPP_SHARING","TEMPLATES"],"terminology":{"consultation":"Consultation","plan":"Care Plan","goal":"Goal"},"profile":{},"version":0}


async def require_capability(request: Request, db: AsyncSession, ctx, capability: str):
    config = await configuration(db, ctx)
    if capability not in set(config["capabilities"]):
        return error(request, 403, "CAPABILITY_NOT_ENABLED", f"{capability.replace('_',' ').title()} is not enabled for this practice")
    return None


def error(request: Request, status: int, code: str, message: str, retryable: bool = False):
    return JSONResponse(status_code=status, content={"success": False, "error": {"code": code, "safe_message": message, "correlation_id": getattr(request.state, "correlation_id", None), "retryable": retryable}})


def context(x_user_id: str | None = Header(None), x_tenant_id: str | None = Header(None), x_user_role: str | None = Header(None), x_tenant_type: str | None = Header(None), x_user_email: str | None = Header(None)):
    if not x_user_id or not x_tenant_id:
        return None
    return {"user_id": x_user_id, "tenant_id": x_tenant_id, "role": x_user_role or "member", "tenant_type": x_tenant_type, "email": (x_user_email or "").lower()}


def external_only(request: Request, ctx):
    if not ctx:
        return error(request, 401, "AUTHENTICATION_REQUIRED", "Authentication is required")
    if ctx.get("tenant_type") not in {"INDEPENDENT_CONSULTANT", "PRACTICE", "CLINIC"}:
        return error(request, 403, "EXTERNAL_PRACTICE_SCOPE_REQUIRED", "External practice access is required")
    return None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("service_starting", service=get_settings().app_name)
    yield
    await engine().dispose()


app = FastAPI(title="Practice Operations Service", version=get_settings().app_version, lifespan=lifespan)


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
    digits = "".join(ch for ch in body.phone if ch.isdigit())
    if not body.phone.strip().startswith("+") or len(digits) < 10 or len(digits) > 15: return error(request, 400, "INVALID_PHONE", "Enter a valid mobile number with explicit country code")
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
    return {"success": True, "data": {"id":str(item_id),"event_type":"WHATSAPP_OPENED","intent":body.intent,"phone":digits,"message":body.message}, "error": None, "request_id": request.state.correlation_id}


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
    await db.execute(text("UPDATE external_assessment_instances SET status='COMPLETED',completed_at=:now,updated_at=:now WHERE id=:id"),{"id":assessment_id,"now":now});await db.execute(text("INSERT INTO external_assessment_review_events(id,assessment_instance_id,tenant_id,client_id,event_type,notes,actor_id,created_at) VALUES (:event,:id,:tenant,:client,'COMPLETED',:notes,:actor,:now)"),{"event":uuid4(),"id":assessment_id,"tenant":ctx["tenant_id"],"client":instance["client_id"],"notes":body.review_notes,"actor":ctx["user_id"],"now":now});await db.commit()
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
    return {"success":True,"data":{"status":"COMPLETED","completionPercent":100,"submittedAt":now},"error":None,"request_id":request.state.correlation_id}


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
      WHERE cp.tenant_id=:tenant AND (:client IS NULL OR cp.client_id=:client)
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
    item_id,now=uuid4(),datetime.now(timezone.utc)
    await db.execute(text("""INSERT INTO external_availability_rules
      (id,tenant_id,weekday,start_time,end_time,timezone,effective_from,effective_until,active,created_by,created_at,updated_at)
      VALUES (:id,:tenant,:weekday,CAST(:start AS time),CAST(:end AS time),:timezone,:effective_from,:effective_until,TRUE,:actor,:now,:now)"""),{
      "id":item_id,"tenant":ctx["tenant_id"],"weekday":body.weekday,"start":body.start_time,"end":body.end_time,
      "timezone":body.timezone,"effective_from":body.effective_from,"effective_until":body.effective_until,
      "actor":ctx["user_id"],"now":now})
    return {"success":True,"data":{"id":str(item_id)},"error":None,"request_id":request.state.correlation_id}


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
      WHERE a.tenant_id=:tenant AND (:client IS NULL OR a.client_id=:client) ORDER BY a.starts_at"""),
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
      AND (:client IS NULL OR client_id=:client) AND (:status IS NULL OR status=:status)
      AND (:search IS NULL OR invoice_number ILIKE '%'||:search||'%' OR client_id ILIKE '%'||:search||'%')
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
      WHERE p.tenant_id=:tenant AND (:client IS NULL OR p.client_id=:client) ORDER BY p.payment_date DESC,p.created_at DESC"""),
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
      AND (:scope IS NULL OR d.scope=:scope) AND (:type IS NULL OR d.resource_type=:type)
      AND (:active IS NULL OR d.active=:active) ORDER BY d.scope,d.title"""),{
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
    documents = [dict(row) for row in (await db.execute(text("""SELECT id,title,media_type,status,submitted_at
      FROM external_client_portal_documents WHERE tenant_id=:tenant AND client_id=:client
      AND status NOT IN ('REMOVED','QUARANTINED') ORDER BY submitted_at DESC"""), params)).mappings().all()]
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
    return {"success": True, "data": {
        "clientId": scope["client_id"], "tasks": tasks, "appointments": appointments,
        "goals": goals, "plans": plans, "assessments": assessments,
        "instructions": instructions, "progress": progress, "documents": documents,
        "resources": resources, "homework": homework, "notifications": [], "packages": packages, "invoices": invoices, "receipts": receipts,
        "referralConsents": referral_consents,
    }, "error": None, "request_id": request.state.correlation_id}


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
      WHERE d.tenant_id=:tenant AND (:state IS NULL OR (:state='ACTIVE' AND d.enabled) OR (:state='DISABLED' AND NOT d.enabled) OR v.status=:state)
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
      c.status consent_status,c.allowed_data_scopes,c.expires_at FROM external_referrals r
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
