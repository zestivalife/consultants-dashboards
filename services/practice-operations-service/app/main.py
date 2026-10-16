from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import UUID, uuid4
import json
import structlog
from fastapi import Depends, FastAPI, Header, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from app.contracts import (ConsultationTransition, GoalProgressCreate,
                           MediaReferenceCreate, OutboxDelivery, ResourceCreate,
                           ResourceUpdate, PracticeConfigurationUpdate,
                           CommunicationTemplateCreate, WhatsAppOpenCreate,
                           OnboardingCompletedCreate)
from app.domain import calendar_window, consultation_transition, factual_summary
from app.db import get_db, engine

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
    "CLIENT_CRM", "CLIENT_ONBOARDING", "CONSULTATIONS", "SESSION_NOTES",
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
    "PSYCHOLOGIST": {"CONSULTATIONS","SESSION_NOTES","FOLLOW_UPS","GOALS_PROGRESS","TASKS","CALENDAR","COMMUNICATION","WHATSAPP_SHARING","THERAPY_PLAN","ASSESSMENTS","TEMPLATES","CLIENT_CRM","CLIENT_ONBOARDING"},
    "COUNSELLOR": {"CONSULTATIONS","SESSION_NOTES","FOLLOW_UPS","GOALS_PROGRESS","TASKS","CALENDAR","COMMUNICATION","WHATSAPP_SHARING","THERAPY_PLAN","ASSESSMENTS","TEMPLATES","CLIENT_CRM","CLIENT_ONBOARDING"},
    "PHYSIOTHERAPIST": {"CONSULTATIONS","SESSION_NOTES","FOLLOW_UPS","GOALS_PROGRESS","TASKS","CALENDAR","COMMUNICATION","WHATSAPP_SHARING","REHAB_PLAN","EXERCISE_PLAN","ASSESSMENTS","TEMPLATES","CLIENT_CRM","CLIENT_ONBOARDING"},
    "HEALTH_COACH": {"CONSULTATIONS","SESSION_NOTES","FOLLOW_UPS","GOALS_PROGRESS","TASKS","CALENDAR","COMMUNICATION","WHATSAPP_SHARING","HABIT_PLAN","TEMPLATES","CLIENT_CRM","CLIENT_ONBOARDING"},
}
TERMINOLOGY = {
    "DIETITIAN":{"consultation":"Consultation","plan":"Diet Plan","goal":"Nutrition Goal"},
    "NUTRITIONIST":{"consultation":"Consultation","plan":"Nutrition Plan","goal":"Nutrition Goal"},
    "PSYCHOLOGIST":{"consultation":"Session","plan":"Therapy Plan","goal":"Therapy Goal"},
    "COUNSELLOR":{"consultation":"Session","plan":"Care Plan","goal":"Therapy Goal"},
    "PHYSIOTHERAPIST":{"consultation":"Assessment","plan":"Rehab Plan","goal":"Exercise Goal"},
    "HEALTH_COACH":{"consultation":"Coaching Session","plan":"Habit Plan","goal":"Lifestyle Goal"},
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
    if len(digits) < 10 or len(digits) > 15: return error(request, 400, "INVALID_PHONE", "Enter a valid mobile number with country code")
    if body.shareable_type == "DIET_PLAN_DRAFT": return error(request, 409, "DRAFT_NOT_SHAREABLE", "Publish the plan before sharing")
    item_id, now = uuid4(), datetime.now(timezone.utc)
    metadata = {"phone_last4":digits[-4:],"shareable_type":body.shareable_type,"shareable_id":body.shareable_id}
    await db.execute(text("""INSERT INTO practice_communication_activity
      (id,tenant_id,client_id,channel,event_type,template_code,purpose,metadata,created_by,created_at)
      VALUES (:id,:tenant_id,:client_id,'WHATSAPP','WHATSAPP_OPENED',:template_code,:purpose,CAST(:metadata AS jsonb),:actor,:now)"""), {"id":item_id,"tenant_id":ctx["tenant_id"],"client_id":body.client_id,"template_code":body.template_code,"purpose":body.purpose,"metadata":json.dumps(metadata),"actor":ctx["user_id"],"now":now})
    await db.execute(text("""INSERT INTO practice_timeline_events
      (id,tenant_id,client_id,event_type,source_type,source_id,summary,metadata,occurred_at)
      VALUES (:id,:tenant_id,:client_id,'WHATSAPP_OPENED','COMMUNICATION',:source_id,:summary,CAST(:metadata AS jsonb),:now)
      ON CONFLICT (tenant_id,event_type,source_type,source_id) DO NOTHING"""), {"id":uuid4(),"tenant_id":ctx["tenant_id"],"client_id":body.client_id,"source_id":str(item_id),"summary":f"WhatsApp opened for {body.purpose}","metadata":json.dumps({"template_code":body.template_code}),"now":now})
    return {"success": True, "data": {"id":str(item_id),"event_type":"WHATSAPP_OPENED","phone":digits,"message":body.message}, "error": None, "request_id": request.state.correlation_id}


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
