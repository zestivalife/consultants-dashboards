from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from uuid import UUID, uuid4
import json
import base64
import hashlib
import structlog
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
from app.domain import calendar_window, consultation_transition, factual_summary
from app.db import get_db, engine
from app.profession_intake import (FROZEN_PROFESSIONS, SUPPORTED_PROFESSIONS,
                                   IntakeTokenError, issue_token, token_hash,
                                   validate_token)

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
    "RENEWALS", "ANALYTICS", "CLIENT_PORTAL",
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


def context(x_user_id: str | None = Header(None), x_tenant_id: str | None = Header(None), x_user_role: str | None = Header(None), x_tenant_type: str | None = Header(None)):
    if not x_user_id or not x_tenant_id:
        return None
    return {"user_id": x_user_id, "tenant_id": x_tenant_id, "role": x_user_role or "member", "tenant_type": x_tenant_type}


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
    denied = external_only(request, ctx)
    if denied: return denied
    try: start, end = calendar_window(view.upper(), anchor or datetime.now(timezone.utc))
    except ValueError: return error(request, 400, "INVALID_CALENDAR_VIEW", "View must be AGENDA, DAY, WEEK, or MONTH")
    params = {"tenant_id": ctx["tenant_id"], "start": start, "end": end, "client_id": client_id}
    rows = (await db.execute(text("""SELECT id,client_id,title,status,due_at AS starts_at,'CONSULTATION' AS source_type FROM practice_consultations WHERE tenant_id=:tenant_id AND due_at>=:start AND due_at<:end AND (CAST(:client_id AS text) IS NULL OR client_id=CAST(:client_id AS text))
      UNION ALL SELECT id,client_id,title,status,due_at,'FOLLOW_UP' FROM practice_follow_ups WHERE tenant_id=:tenant_id AND due_at>=:start AND due_at<:end AND (CAST(:client_id AS text) IS NULL OR client_id=CAST(:client_id AS text))
      UNION ALL SELECT id,client_id,title,status,due_at,'TASK' FROM practice_tasks WHERE tenant_id=:tenant_id AND due_at>=:start AND due_at<:end AND (CAST(:client_id AS text) IS NULL OR client_id=CAST(:client_id AS text))
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
    if denied:return denied
    rows=(await db.execute(text("SELECT id,consultation_id,note_type,title,status,current_version,created_at,updated_at FROM external_session_notes WHERE tenant_id=:tenant AND client_id=:client ORDER BY updated_at DESC"),{"tenant":ctx["tenant_id"],"client":client_id})).mappings().all()
    return {"success":True,"data":{"items":[dict(row) for row in rows]},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/session-notes",status_code=201)
async def create_session_note(request:Request,body:SessionNoteCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx) or await require_capability(request,db,ctx,"SESSION_NOTES")
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
    rows=(await db.execute(text("SELECT id,encrypted_content,created_by,created_at,updated_at FROM external_session_private_notes WHERE note_id=:note AND tenant_id=:tenant ORDER BY created_at DESC"),{"note":note_id,"tenant":ctx["tenant_id"]})).mappings().all();cipher=_private_note_cipher()
    return {"success":True,"data":{"items":[{"id":row["id"],"content":cipher.decrypt(row["encrypted_content"].encode()).decode(),"created_by":row["created_by"],"created_at":row["created_at"],"updated_at":row["updated_at"]} for row in rows]},"error":None,"request_id":request.state.correlation_id}

@app.post("/api/v1/practice-operations/session-notes/{note_id}/private",status_code=201)
async def create_private_note(request:Request,note_id:UUID,body:PrivateNoteCreate,ctx=Depends(context),db:AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx) or await require_capability(request,db,ctx,"PRIVATE_NOTES")
    if denied:return denied
    note=(await db.execute(text("SELECT client_id FROM external_session_notes WHERE id=:id AND tenant_id=:tenant"),{"id":note_id,"tenant":ctx["tenant_id"]})).mappings().first()
    if not note:return error(request,404,"SESSION_NOTE_NOT_FOUND","Session note not found")
    item_id=uuid4();now=datetime.now(timezone.utc);encrypted=_private_note_cipher().encrypt(body.content.encode()).decode()
    await db.execute(text("INSERT INTO external_session_private_notes(id,note_id,tenant_id,client_id,encrypted_content,created_by,created_at,updated_at) VALUES (:id,:note,:tenant,:client,:content,:actor,:now,:now)"),{"id":item_id,"note":note_id,"tenant":ctx["tenant_id"],"client":note["client_id"],"content":encrypted,"actor":ctx["user_id"],"now":now});await db.commit();return {"success":True,"data":{"id":str(item_id)},"error":None,"request_id":request.state.correlation_id}

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
