"""Read-only Zestiva projection of canonical Fiteatsy client identities."""
from datetime import datetime, timezone
import hashlib
import json
from typing import Literal
from uuid import UUID, uuid4

import jwt
from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_db


class DirectoryRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fiteatsy_user_id: UUID
    fiteatsy_client_id: str | None = Field(default=None, max_length=120)
    display_name: str = Field(min_length=1, max_length=240)
    mobile_number_normalized: str | None = Field(default=None, max_length=32)
    email_normalized: str | None = Field(default=None, max_length=320)
    account_status: str = Field(min_length=1, max_length=30)
    mobile_verified: bool
    registration_status: Literal["PENDING", "COMPLETED"]
    registered_at: datetime
    source_updated_at: datetime
    deleted_at: datetime | None = None


class DirectoryEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: UUID
    event_type: Literal[
        "FITEATSY_USER_REGISTERED", "FITEATSY_USER_VERIFIED", "FITEATSY_USER_PROFILE_UPDATED",
        "FITEATSY_USER_STATUS_CHANGED", "FITEATSY_USER_DEACTIVATED", "FITEATSY_USER_DELETED",
    ]
    fiteatsy_user_id: UUID
    source_version: int = Field(gt=0)
    schema_version: Literal[1]
    occurred_at: datetime
    data: DirectoryRecord


def decode_directory_assertion(token: str) -> dict:
    settings = get_settings()
    claims = jwt.decode(
        token,
        (settings.external_fiteatsy_inbound_public_key or "").replace("\\n", "\n"),
        algorithms=["RS256"], issuer=settings.external_fiteatsy_inbound_issuer,
        audience=settings.external_fiteatsy_inbound_audience,
        options={"require": ["exp", "iat", "iss", "aud", "sub", "jti"]},
    )
    if claims.get("actor_type") != "FITEATSY_SERVICE" or claims.get("purpose") != "client_directory_sync":
        raise jwt.InvalidTokenError("unexpected directory assertion purpose")
    return claims


def build_router(context_dependency, error):
    router = APIRouter()

    @router.post("/api/v1/internal/fiteatsy-client-directory/events")
    async def apply_event(
        request: Request, body: DirectoryEvent, authorization: str | None = Header(default=None),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
        db: AsyncSession = Depends(get_db),
    ):
        if not authorization or not authorization.startswith("Bearer "):
            return error(request, 401, "DIRECTORY_ASSERTION_REQUIRED", "A signed directory assertion is required")
        try:
            decode_directory_assertion(authorization[7:])
        except jwt.PyJWTError:
            return error(request, 401, "DIRECTORY_ASSERTION_INVALID", "The directory assertion is invalid or expired")
        if idempotency_key != str(body.event_id) or body.data.fiteatsy_user_id != body.fiteatsy_user_id:
            return error(request, 422, "DIRECTORY_EVENT_INVALID", "The directory event identity is inconsistent")

        payload_sha256 = hashlib.sha256(json.dumps(body.model_dump(mode="json"), sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        await db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:event))"), {"event": str(body.event_id)})
        existing = (await db.execute(text(
            "SELECT disposition,payload_sha256 FROM fiteatsy_client_directory_events WHERE event_id=:event"
        ), {"event": body.event_id})).mappings().one_or_none()
        if existing:
            if existing["payload_sha256"] != payload_sha256:
                return error(request, 409, "DIRECTORY_IDEMPOTENCY_CONFLICT", "The event identifier was already used for different content")
            return {"success": True, "data": {"event_id": str(body.event_id), "disposition": "DUPLICATE"}, "error": None, "request_id": getattr(request.state, "correlation_id", None)}

        current_version = (await db.execute(text(
            "SELECT source_version FROM fiteatsy_client_directory WHERE fiteatsy_user_id=:user FOR UPDATE"
        ), {"user": body.fiteatsy_user_id})).scalar_one_or_none()
        disposition = "STALE" if current_version is not None and int(current_version) >= body.source_version else "APPLIED"
        now = datetime.now(timezone.utc)
        if disposition == "APPLIED":
            data = body.data
            await db.execute(text("""INSERT INTO fiteatsy_client_directory(
              id,fiteatsy_user_id,fiteatsy_client_id,display_name,mobile_number_normalized,email_normalized,
              account_status,mobile_verified,registration_status,registered_at,source_updated_at,source_version,
              last_synced_at,sync_status,deleted_at,created_at,updated_at
            ) VALUES(:id,:user,:client,:name,:mobile,:email,:status,:verified,:registration,:registered,:source_updated,
                     :version,:now,'CURRENT',:deleted,:now,:now)
            ON CONFLICT(fiteatsy_user_id) DO UPDATE SET
              fiteatsy_client_id=excluded.fiteatsy_client_id,display_name=excluded.display_name,
              mobile_number_normalized=excluded.mobile_number_normalized,email_normalized=excluded.email_normalized,
              account_status=excluded.account_status,mobile_verified=excluded.mobile_verified,
              registration_status=excluded.registration_status,registered_at=excluded.registered_at,
              source_updated_at=excluded.source_updated_at,source_version=excluded.source_version,
              last_synced_at=excluded.last_synced_at,sync_status='CURRENT',deleted_at=excluded.deleted_at,updated_at=excluded.updated_at
            WHERE fiteatsy_client_directory.source_version < excluded.source_version"""), {
                "id": uuid4(), "user": body.fiteatsy_user_id, "client": data.fiteatsy_client_id,
                "name": data.display_name, "mobile": data.mobile_number_normalized, "email": data.email_normalized,
                "status": data.account_status, "verified": data.mobile_verified, "registration": data.registration_status,
                "registered": data.registered_at, "source_updated": data.source_updated_at, "version": body.source_version,
                "deleted": data.deleted_at, "now": now,
            })
        await db.execute(text("""INSERT INTO fiteatsy_client_directory_events(
          event_id,event_type,fiteatsy_user_id,source_version,schema_version,payload_sha256,occurred_at,processed_at,disposition
        ) VALUES(:event,:type,:user,:version,:schema,:payload_sha256,:occurred,:processed,:disposition)"""), {
            "event": body.event_id, "type": body.event_type, "user": body.fiteatsy_user_id,
            "version": body.source_version, "schema": body.schema_version, "payload_sha256": payload_sha256, "occurred": body.occurred_at,
            "processed": now, "disposition": disposition,
        })
        await db.commit()
        return JSONResponse(status_code=202, content={"success": True, "data": {"event_id": str(body.event_id), "disposition": disposition}, "error": None, "request_id": getattr(request.state, "correlation_id", None)})

    @router.get("/api/v1/practice-operations/fiteatsy-client-directory")
    async def list_directory(
        request: Request, q: str = Query(default="", max_length=120),
        status: Literal["all", "active", "inactive"] = "all",
        order: Literal["asc", "desc"] = "desc", page: int = Query(default=1, ge=1),
        page_size: int = Query(default=25, ge=1, le=100),
        ctx=Depends(context_dependency), db: AsyncSession = Depends(get_db),
    ):
        if not ctx:
            return error(request, 401, "AUTHENTICATION_REQUIRED", "Authentication is required")
        if ctx.get("role") not in {"SUPER_ADMIN", "SUPERUSER", "PLATFORM_OWNER"}:
            return error(request, 403, "PLATFORM_OWNER_REQUIRED", "Platform Owner access is required")
        mobile = "".join(char for char in q if char.isdigit())
        if len(mobile) == 12 and mobile.startswith("91"):
            mobile = mobile[2:]
        filters = {"q": q.strip(), "mobile": mobile, "status": status, "limit": page_size, "offset": (page - 1) * page_size}
        where = """deleted_at IS NULL AND registration_status='COMPLETED' AND mobile_verified=TRUE
          AND (:status='all' OR lower(account_status)=:status)
          AND (:q='' OR lower(display_name) LIKE '%'||lower(:q)||'%' OR lower(coalesce(email_normalized,'')) LIKE '%'||lower(:q)||'%'
               OR (:mobile<>'' AND right(regexp_replace(coalesce(mobile_number_normalized,''),'[^0-9]','','g'),10) LIKE '%'||:mobile||'%'))"""
        direction = "ASC" if order == "asc" else "DESC"
        rows = (await db.execute(text(f"""SELECT fiteatsy_user_id::text,fiteatsy_client_id,display_name,
          mobile_number_normalized,email_normalized,account_status,mobile_verified,registration_status,registered_at,
          source_updated_at,last_synced_at,sync_status FROM fiteatsy_client_directory WHERE {where}
          ORDER BY registered_at {direction},fiteatsy_user_id {direction} LIMIT :limit OFFSET :offset"""), filters)).mappings().all()
        total = (await db.execute(text(f"SELECT count(*)::int FROM fiteatsy_client_directory WHERE {where}"), filters)).scalar_one()
        return {"success": True, "data": {"clients": [dict(row) for row in rows], "pagination": {"total": total, "page": page, "page_size": page_size}}, "error": None, "request_id": getattr(request.state, "correlation_id", None)}

    return router
