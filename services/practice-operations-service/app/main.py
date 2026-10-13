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
from app.contracts import ResourceCreate, ResourceUpdate
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
    table=RESOURCE_TABLES.get(resource)
    if not table: return error(request, 404, "RESOURCE_NOT_FOUND", "Practice resource not found")
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
    existing=(await db.execute(text(f"SELECT * FROM {table} WHERE tenant_id=:tenant_id AND idempotency_key=:key"),{"tenant_id":ctx["tenant_id"],"key":idempotency_key})).mappings().first()
    if existing: return {"success":True,"data":dict(existing),"error":None,"request_id":request.state.correlation_id}
    item_id=uuid4(); event_id=uuid4(); now=datetime.now(timezone.utc); event_type=f"{resource.rstrip('s').replace('-','_').upper()}_CREATED"
    params={"id":item_id,"tenant_id":ctx["tenant_id"],"client_id":body.client_id,"type":body.type,"title":body.title,"status":body.status,"due_at":body.due_at,"payload":json.dumps(body.payload),"actor":ctx["user_id"],"key":idempotency_key,"now":now}
    await db.execute(text(f"INSERT INTO {table} (id,tenant_id,client_id,type,title,status,due_at,payload,version,created_by,idempotency_key,created_at,updated_at) VALUES (:id,:tenant_id,:client_id,:type,:title,:status,:due_at,CAST(:payload AS jsonb),1,:actor,:key,:now,:now)"),params)
    await db.execute(text("INSERT INTO service_outbox_events (id,tenant_id,event_type,aggregate_type,aggregate_id,payload,status,created_at) VALUES (:id,:tenant_id,:event_type,:aggregate_type,:aggregate_id,CAST(:payload AS jsonb),'PENDING',:now)"),{"id":event_id,"tenant_id":ctx["tenant_id"],"event_type":event_type,"aggregate_type":resource,"aggregate_id":item_id,"payload":json.dumps({"client_id":body.client_id}),"now":now})
    return {"success":True,"data":{"id":str(item_id),**body.model_dump(),"version":1},"error":None,"request_id":request.state.correlation_id}


@app.patch("/api/v1/practice-operations/{resource}/{item_id}")
async def update_resource(request: Request, resource: str, item_id: UUID, body: ResourceUpdate, ctx=Depends(context), db: AsyncSession=Depends(get_db)):
    denied=external_only(request,ctx)
    if denied: return denied
    table=RESOURCE_TABLES.get(resource)
    if not table: return error(request,404,"RESOURCE_NOT_FOUND","Practice resource not found")
    values=body.model_dump(exclude_none=True); expected=values.pop("version"); values["updated_at"]=datetime.now(timezone.utc)
    if "payload" in values: values["payload"]=json.dumps(values["payload"])
    assignments=[]
    for key in values: assignments.append(f"{key} = CAST(:{key} AS jsonb)" if key=="payload" else f"{key} = :{key}")
    assignments.append("version = version + 1")
    result=await db.execute(text(f"UPDATE {table} SET {', '.join(assignments)} WHERE id=:id AND tenant_id=:tenant_id AND version=:version RETURNING id, version, status, updated_at"),{"id":item_id,"tenant_id":ctx["tenant_id"],"version":expected,**values})
    row=result.mappings().first()
    if not row: return error(request,409,"STALE_WRITE","This record changed. Refresh and retry")
    return {"success":True,"data":dict(row),"error":None,"request_id":request.state.correlation_id}
