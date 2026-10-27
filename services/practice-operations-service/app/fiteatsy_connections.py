"""External Consultant <-> Fiteatsy connection domain.

The mobile-facing endpoints trust only a short-lived asymmetric assertion
issued by Fiteatsy. A caller supplied user id is never treated as identity.
"""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import hmac
import json
import secrets
from uuid import uuid4

import jwt
from fastapi import APIRouter, Depends, Header, Request
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_db

PIN_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
ALLOWED_SCOPES = {"PROFILE", "HEALTH_SUMMARY", "MEASUREMENTS", "BIOMARKERS", "DIET_PLANS", "APPOINTMENTS"}


def generate_connection_pin(length: int = 8) -> str:
    return "".join(secrets.choice(PIN_ALPHABET) for _ in range(length))


def pin_verifier(pin: str, pepper: str) -> str:
    normalized = "".join(pin.upper().split())
    return hmac.new(pepper.encode(), normalized.encode(), sha256).hexdigest()


def verify_pin(pin: str, verifier: str, pepper: str) -> bool:
    return hmac.compare_digest(pin_verifier(pin, pepper), verifier)


def decode_fiteatsy_identity(token: str, public_key: str, issuer: str, audience: str) -> dict:
    claims = jwt.decode(token, public_key, algorithms=["RS256"], issuer=issuer, audience=audience, options={"require": ["exp", "iat", "iss", "aud", "sub"]})
    if claims.get("actor_type") != "FITEATSY_USER":
        raise jwt.InvalidTokenError("unexpected actor type")
    return claims


class InvitationCreate(BaseModel):
    client_id: str | None = Field(default=None, max_length=120)
    expires_in_hours: int = Field(default=72, ge=1, le=168)
    scopes: list[str] = Field(default_factory=lambda: ["PROFILE", "HEALTH_SUMMARY", "DIET_PLANS", "APPOINTMENTS"])


class PinRedeem(BaseModel):
    pin: str = Field(min_length=8, max_length=32)
    consent_version: str = Field(min_length=1, max_length=40)
    accepted_scopes: list[str]


class PinPreview(BaseModel):
    pin: str = Field(min_length=8, max_length=32)


class ConnectionAction(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class ProgrammeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=240)
    starts_on: datetime | None = None
    ends_on: datetime | None = None


class ProgrammeAction(BaseModel):
    action: str = Field(pattern="^(INVITE|ACTIVATE|PAUSE|COMPLETE|CANCEL)$")


class PlanPublication(BaseModel):
    plan_id: str = Field(min_length=1, max_length=120)
    plan_version: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=240)
    content: dict
    idempotency_key: str = Field(min_length=8, max_length=120)


class AppointmentPublication(BaseModel):
    appointment_id: str = Field(min_length=1, max_length=120)
    starts_at: datetime
    ends_at: datetime
    title: str = Field(min_length=1, max_length=240)
    idempotency_key: str = Field(min_length=8, max_length=120)


def build_router(context_dependency, external_only, error):
    router = APIRouter()

    def response(request, data, status_code=200):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"success": True, "data": data, "error": None, "request_id": getattr(request.state, "correlation_id", None)}))

    def enabled(request):
        if not get_settings().external_fiteatsy_connection_enabled:
            return error(request, 404, "FEATURE_DISABLED", "Fiteatsy connections are not enabled for this environment")

    def clean_scopes(values):
        scopes = {str(value).upper() for value in values}
        if not scopes or not scopes <= ALLOWED_SCOPES:
            raise ValueError("Connection scopes are invalid")
        return sorted(scopes)

    def fiteatsy_identity(request: Request, authorization: str | None):
        if not authorization or not authorization.startswith("Bearer "):
            return None, error(request, 401, "FITEATSY_IDENTITY_REQUIRED", "A verified Fiteatsy identity is required")
        settings = get_settings()
        try:
            return decode_fiteatsy_identity(authorization[7:], settings.external_fiteatsy_inbound_public_key or "", settings.external_fiteatsy_inbound_issuer, settings.external_fiteatsy_inbound_audience), None
        except jwt.PyJWTError:
            return None, error(request, 401, "FITEATSY_IDENTITY_INVALID", "The Fiteatsy identity assertion is invalid or expired")

    @router.post("/api/v1/practice-operations/fiteatsy-connections/invitations")
    async def create_invitation(request: Request, body: InvitationCreate, ctx=Depends(context_dependency), db: AsyncSession=Depends(get_db)):
        denied = external_only(request, ctx) or enabled(request)
        if denied: return denied
        try: scopes = clean_scopes(body.scopes)
        except ValueError as exc: return error(request, 422, "INVALID_CONNECTION_SCOPE", str(exc))
        settings = get_settings(); pin = generate_connection_pin(); now = datetime.now(timezone.utc); invitation_id = uuid4()
        await db.execute(text("""INSERT INTO external_fiteatsy_connection_invitations(id,tenant_id,consultant_id,intended_client_id,pin_verifier,pin_hint,status,attempt_count,max_attempts,expires_at,requested_scopes,created_at,updated_at)
            VALUES(:id,:tenant,:consultant,:client,:verifier,:hint,'PENDING',0,8,:expires,CAST(:scopes AS JSONB),:now,:now)"""), {"id": invitation_id, "tenant": ctx["tenant_id"], "consultant": ctx["user_id"], "client": body.client_id, "verifier": pin_verifier(pin, settings.external_fiteatsy_pin_pepper or ""), "hint": pin[-2:], "expires": now + timedelta(hours=body.expires_in_hours), "scopes": json.dumps(scopes), "now": now})
        await db.execute(text("INSERT INTO external_fiteatsy_connection_events(id,tenant_id,invitation_id,event_type,actor_type,actor_id,event_data,created_at) VALUES(:id,:tenant,:invitation,'INVITATION_CREATED','CONSULTANT',:actor,CAST(:data AS JSONB),:now)"), {"id": uuid4(), "tenant": ctx["tenant_id"], "invitation": invitation_id, "actor": ctx["user_id"], "data": json.dumps({"scopes": scopes}), "now": now})
        await db.commit()
        return response(request, {"invitation_id": str(invitation_id), "connection_pin": pin, "expires_at": (now + timedelta(hours=body.expires_in_hours)).isoformat(), "scopes": scopes, "display_once": True}, 201)

    @router.get("/api/v1/practice-operations/fiteatsy-connections")
    async def list_connections(request: Request, ctx=Depends(context_dependency), db: AsyncSession=Depends(get_db)):
        denied = external_only(request, ctx) or enabled(request)
        if denied: return denied
        connections = [dict(row) for row in (await db.execute(text("SELECT id::text,consultant_client_id,state,consent_version,consented_scopes,programme_status,connected_at,disconnected_at FROM external_fiteatsy_connections WHERE tenant_id=:tenant AND consultant_id=:consultant ORDER BY connected_at DESC"), {"tenant": ctx["tenant_id"], "consultant": ctx["user_id"]})).mappings().all()]
        invitations = [dict(row) for row in (await db.execute(text("SELECT id::text,intended_client_id,pin_hint,status,expires_at,requested_scopes,created_at FROM external_fiteatsy_connection_invitations WHERE tenant_id=:tenant AND consultant_id=:consultant ORDER BY created_at DESC LIMIT 100"), {"tenant": ctx["tenant_id"], "consultant": ctx["user_id"]})).mappings().all()]
        return response(request, {"connections": connections, "invitations": invitations})

    @router.get("/api/v1/practice-operations/fiteatsy-connections/{connection_id}")
    async def connection_details(connection_id: str, request: Request, ctx=Depends(context_dependency), db: AsyncSession=Depends(get_db)):
        denied = external_only(request, ctx) or enabled(request)
        if denied: return denied
        row = (await db.execute(text("SELECT id::text,consultant_client_id,state,consent_version,consented_scopes,programme_status,connected_at,disconnected_at FROM external_fiteatsy_connections WHERE id=:id AND tenant_id=:tenant AND consultant_id=:consultant"), {"id": connection_id, "tenant": ctx["tenant_id"], "consultant": ctx["user_id"]})).mappings().first()
        if not row: return error(request, 404, "CONNECTION_NOT_FOUND", "The Fiteatsy connection could not be found")
        programmes = [dict(item) for item in (await db.execute(text("SELECT id::text,name,status,starts_on,ends_on,created_at,updated_at FROM external_fiteatsy_programmes WHERE connection_id=:id ORDER BY created_at DESC"), {"id": connection_id})).mappings().all()]
        return response(request, {"connection": dict(row), "programmes": programmes})

    @router.post("/api/v1/practice-operations/fiteatsy-connections/invitations/{invitation_id}/revoke")
    async def revoke_invitation(invitation_id: str, request: Request, body: ConnectionAction, ctx=Depends(context_dependency), db: AsyncSession=Depends(get_db)):
        denied = external_only(request, ctx) or enabled(request)
        if denied: return denied
        now = datetime.now(timezone.utc)
        row = (await db.execute(text("UPDATE external_fiteatsy_connection_invitations SET status='REVOKED',updated_at=:now WHERE id=:id AND tenant_id=:tenant AND consultant_id=:consultant AND status='PENDING' RETURNING id"), {"id": invitation_id, "tenant": ctx["tenant_id"], "consultant": ctx["user_id"], "now": now})).first()
        if not row: return error(request, 404, "INVITATION_NOT_FOUND", "The pending invitation could not be found")
        await db.execute(text("INSERT INTO external_fiteatsy_connection_events(id,tenant_id,invitation_id,event_type,actor_type,actor_id,event_data,created_at) VALUES(:id,:tenant,:invitation,'INVITATION_REVOKED','CONSULTANT',:actor,CAST(:data AS JSONB),:now)"), {"id": uuid4(), "tenant": ctx["tenant_id"], "invitation": invitation_id, "actor": ctx["user_id"], "data": json.dumps({"reason": body.reason}), "now": now})
        await db.commit(); return response(request, {"invitation_id": invitation_id, "status": "REVOKED"})

    @router.post("/api/v1/practice-operations/fiteatsy-connections/{connection_id}/programmes")
    async def create_programme(connection_id: str, request: Request, body: ProgrammeCreate, ctx=Depends(context_dependency), db: AsyncSession=Depends(get_db)):
        denied = external_only(request, ctx) or enabled(request)
        if denied: return denied
        if body.starts_on and body.ends_on and body.ends_on <= body.starts_on: return error(request, 422, "INVALID_PROGRAMME_WINDOW", "Programme end must be after its start")
        connection = (await db.execute(text("SELECT id FROM external_fiteatsy_connections WHERE id=:id AND tenant_id=:tenant AND consultant_id=:consultant AND state='ACTIVE'"), {"id": connection_id, "tenant": ctx["tenant_id"], "consultant": ctx["user_id"]})).first()
        if not connection: return error(request, 404, "CONNECTION_NOT_FOUND", "An active Fiteatsy connection could not be found")
        now = datetime.now(timezone.utc); programme_id = uuid4()
        await db.execute(text("INSERT INTO external_fiteatsy_programmes(id,connection_id,tenant_id,consultant_id,name,status,starts_on,ends_on,created_at,updated_at) VALUES(:id,:connection,:tenant,:consultant,:name,'DRAFT',:starts,:ends,:now,:now)"), {"id": programme_id, "connection": connection_id, "tenant": ctx["tenant_id"], "consultant": ctx["user_id"], "name": body.name, "starts": body.starts_on.date() if body.starts_on else None, "ends": body.ends_on.date() if body.ends_on else None, "now": now})
        await db.commit(); return response(request, {"programme_id": str(programme_id), "status": "DRAFT"}, 201)

    @router.post("/api/v1/practice-operations/fiteatsy-connections/{connection_id}/programmes/{programme_id}/action")
    async def programme_action(connection_id: str, programme_id: str, request: Request, body: ProgrammeAction, ctx=Depends(context_dependency), db: AsyncSession=Depends(get_db)):
        denied = external_only(request, ctx) or enabled(request)
        if denied: return denied
        target = {"INVITE":"INVITED","ACTIVATE":"ACTIVE","PAUSE":"PAUSED","COMPLETE":"COMPLETED","CANCEL":"CANCELLED"}[body.action]
        row = (await db.execute(text("UPDATE external_fiteatsy_programmes SET status=:status,updated_at=:now WHERE id=:id AND connection_id=:connection AND tenant_id=:tenant AND consultant_id=:consultant RETURNING id"), {"status": target, "now": datetime.now(timezone.utc), "id": programme_id, "connection": connection_id, "tenant": ctx["tenant_id"], "consultant": ctx["user_id"]})).first()
        if not row: return error(request, 404, "PROGRAMME_NOT_FOUND", "The programme could not be found")
        await db.execute(text("UPDATE external_fiteatsy_connections SET programme_status=:status,updated_at=:now WHERE id=:id"), {"status": target, "now": datetime.now(timezone.utc), "id": connection_id})
        await db.commit(); return response(request, {"programme_id": programme_id, "status": target})

    @router.post("/api/v1/practice-operations/fiteatsy-connections/{connection_id}/revoke")
    async def revoke_connection(connection_id: str, request: Request, body: ConnectionAction, ctx=Depends(context_dependency), db: AsyncSession=Depends(get_db)):
        denied = external_only(request, ctx) or enabled(request)
        if denied: return denied
        row = (await db.execute(text("UPDATE external_fiteatsy_connections SET state='REVOKED',disconnected_at=:now,updated_at=:now WHERE id=:id AND tenant_id=:tenant AND consultant_id=:consultant AND state='ACTIVE' RETURNING id"), {"id": connection_id, "tenant": ctx["tenant_id"], "consultant": ctx["user_id"], "now": datetime.now(timezone.utc)})).first()
        if not row: return error(request, 404, "CONNECTION_NOT_FOUND", "The active Fiteatsy connection could not be found")
        await db.execute(text("INSERT INTO external_fiteatsy_connection_events(id,tenant_id,connection_id,event_type,actor_type,actor_id,event_data,created_at) VALUES(:id,:tenant,:connection,'CONNECTION_REVOKED','CONSULTANT',:actor,CAST(:data AS JSONB),:now)"), {"id": uuid4(), "tenant": ctx["tenant_id"], "connection": connection_id, "actor": ctx["user_id"], "data": json.dumps({"reason": body.reason}), "now": datetime.now(timezone.utc)})
        await db.commit(); return response(request, {"connection_id": connection_id, "state": "REVOKED"})

    @router.post("/api/v1/fiteatsy-connections/redeem")
    async def redeem_invitation(request: Request, body: PinRedeem, authorization: str | None = Header(None), db: AsyncSession=Depends(get_db)):
        denied = enabled(request)
        if denied: return denied
        identity, denied = fiteatsy_identity(request, authorization)
        if denied: return denied
        try: accepted = clean_scopes(body.accepted_scopes)
        except ValueError as exc: return error(request, 422, "INVALID_CONNECTION_SCOPE", str(exc))
        verifier = pin_verifier(body.pin, get_settings().external_fiteatsy_pin_pepper or ""); now = datetime.now(timezone.utc)
        invitation = (await db.execute(text("SELECT * FROM external_fiteatsy_connection_invitations WHERE pin_verifier=:verifier FOR UPDATE"), {"verifier": verifier})).mappings().first()
        if not invitation or invitation["status"] != "PENDING" or invitation["expires_at"] <= now or invitation["attempt_count"] >= invitation["max_attempts"]:
            return error(request, 404, "CONNECTION_PIN_INVALID", "The Connection PIN is invalid or no longer available")
        if not set(accepted) <= set(invitation["requested_scopes"] or []):
            return error(request, 422, "CONSENT_SCOPE_EXCEEDS_INVITATION", "Accepted consent exceeds the invited access")
        connection_id = uuid4()
        await db.execute(text("""INSERT INTO external_fiteatsy_connections(id,tenant_id,consultant_id,fiteatsy_user_id,consultant_client_id,state,consent_version,consented_scopes,programme_status,connected_at,updated_at)
            VALUES(:id,:tenant,:consultant,:user,:client,'ACTIVE',:version,CAST(:scopes AS JSONB),'NOT_ENROLLED',:now,:now)
            ON CONFLICT(tenant_id,consultant_id,fiteatsy_user_id) DO UPDATE SET state='ACTIVE',consent_version=EXCLUDED.consent_version,consented_scopes=EXCLUDED.consented_scopes,connected_at=EXCLUDED.connected_at,disconnected_at=NULL,updated_at=EXCLUDED.updated_at RETURNING id"""), {"id": connection_id, "tenant": invitation["tenant_id"], "consultant": invitation["consultant_id"], "user": identity["sub"], "client": invitation["intended_client_id"], "version": body.consent_version, "scopes": json.dumps(accepted), "now": now})
        await db.execute(text("UPDATE external_fiteatsy_connection_invitations SET status='REDEEMED',redeemed_by_fiteatsy_user_id=:user,redeemed_at=:now,updated_at=:now WHERE id=:id"), {"user": identity["sub"], "now": now, "id": invitation["id"]})
        actual = (await db.execute(text("SELECT id FROM external_fiteatsy_connections WHERE tenant_id=:tenant AND consultant_id=:consultant AND fiteatsy_user_id=:user"), {"tenant": invitation["tenant_id"], "consultant": invitation["consultant_id"], "user": identity["sub"]})).scalar_one()
        await db.execute(text("INSERT INTO external_fiteatsy_consents(id,connection_id,consent_version,scopes,decision,actor_fiteatsy_user_id,created_at) VALUES(:id,:connection,:version,CAST(:scopes AS JSONB),'GRANTED',:user,:now)"), {"id": uuid4(), "connection": actual, "version": body.consent_version, "scopes": json.dumps(accepted), "user": identity["sub"], "now": now})
        await db.commit(); return response(request, {"connection_id": str(actual), "state": "ACTIVE", "consented_scopes": accepted}, 201)

    @router.post("/api/v1/fiteatsy-connections/preview")
    async def preview_invitation(request: Request, body: PinPreview, authorization: str | None = Header(None), db: AsyncSession=Depends(get_db)):
        denied = enabled(request)
        if denied: return denied
        _, denied = fiteatsy_identity(request, authorization)
        if denied: return denied
        verifier = pin_verifier(body.pin, get_settings().external_fiteatsy_pin_pepper or "")
        row = (await db.execute(text("SELECT pin_hint,requested_scopes,expires_at,status FROM external_fiteatsy_connection_invitations WHERE pin_verifier=:verifier"), {"verifier": verifier})).mappings().first()
        if not row or row["status"] != "PENDING" or row["expires_at"] <= datetime.now(timezone.utc): return error(request, 404, "CONNECTION_PIN_INVALID", "The Connection PIN is invalid or no longer available")
        return response(request, {"pin_hint": row["pin_hint"], "requested_scopes": row["requested_scopes"], "expires_at": row["expires_at"], "consent_required": True})

    @router.get("/api/v1/fiteatsy-connections")
    async def mobile_connections(request: Request, authorization: str | None = Header(None), db: AsyncSession=Depends(get_db)):
        denied = enabled(request)
        if denied: return denied
        identity, denied = fiteatsy_identity(request, authorization)
        if denied: return denied
        rows = [dict(row) for row in (await db.execute(text("SELECT id::text,state,consented_scopes,programme_status,connected_at,disconnected_at FROM external_fiteatsy_connections WHERE fiteatsy_user_id=:user ORDER BY connected_at DESC"), {"user": identity["sub"]})).mappings().all()]
        return response(request, {"connections": rows})

    @router.get("/api/v1/fiteatsy-connections/{connection_id}")
    async def mobile_connection_details(connection_id: str, request: Request, authorization: str | None = Header(None), db: AsyncSession=Depends(get_db)):
        denied = enabled(request)
        if denied: return denied
        identity, denied = fiteatsy_identity(request, authorization)
        if denied: return denied
        row = (await db.execute(text("SELECT id::text,state,consented_scopes,programme_status,connected_at,disconnected_at FROM external_fiteatsy_connections WHERE id=:id AND fiteatsy_user_id=:user"), {"id": connection_id, "user": identity["sub"]})).mappings().first()
        if not row: return error(request, 404, "CONNECTION_NOT_FOUND", "The consultant connection could not be found")
        return response(request, {"connection": dict(row)})

    @router.get("/api/v1/fiteatsy-connections/{connection_id}/diet-plans")
    async def mobile_plans(connection_id: str, request: Request, authorization: str | None = Header(None), db: AsyncSession=Depends(get_db)):
        denied = enabled(request)
        if denied: return denied
        identity, denied = fiteatsy_identity(request, authorization)
        if denied: return denied
        rows = [dict(item) for item in (await db.execute(text("SELECT p.id::text,p.plan_id,p.plan_version,p.title,p.content,p.status,p.published_at FROM external_fiteatsy_plan_publications p JOIN external_fiteatsy_connections c ON c.id=p.connection_id WHERE c.id=:id AND c.fiteatsy_user_id=:user AND c.state='ACTIVE' AND c.consented_scopes ? 'DIET_PLANS' ORDER BY p.published_at DESC"), {"id": connection_id, "user": identity["sub"]})).mappings().all()]
        return response(request, {"plans": rows})

    @router.get("/api/v1/fiteatsy-connections/{connection_id}/appointments")
    async def mobile_appointments(connection_id: str, request: Request, authorization: str | None = Header(None), db: AsyncSession=Depends(get_db)):
        denied = enabled(request)
        if denied: return denied
        identity, denied = fiteatsy_identity(request, authorization)
        if denied: return denied
        rows = [dict(item) for item in (await db.execute(text("SELECT a.id::text,a.appointment_id,a.title,a.starts_at,a.ends_at,a.status,a.created_at FROM external_fiteatsy_appointments a JOIN external_fiteatsy_connections c ON c.id=a.connection_id WHERE c.id=:id AND c.fiteatsy_user_id=:user AND c.state='ACTIVE' AND c.consented_scopes ? 'APPOINTMENTS' ORDER BY a.starts_at"), {"id": connection_id, "user": identity["sub"]})).mappings().all()]
        return response(request, {"appointments": rows})

    @router.delete("/api/v1/fiteatsy-connections/{connection_id}")
    async def mobile_disconnect(connection_id: str, request: Request, authorization: str | None = Header(None), db: AsyncSession=Depends(get_db)):
        denied = enabled(request)
        if denied: return denied
        identity, denied = fiteatsy_identity(request, authorization)
        if denied: return denied
        row = (await db.execute(text("UPDATE external_fiteatsy_connections SET state='DISCONNECTED',disconnected_at=:now,updated_at=:now WHERE id=:id AND fiteatsy_user_id=:user AND state='ACTIVE' RETURNING id"), {"id": connection_id, "user": identity["sub"], "now": datetime.now(timezone.utc)})).first()
        if not row: return error(request, 404, "CONNECTION_NOT_FOUND", "The active consultant connection could not be found")
        await db.commit(); return response(request, {"connection_id": connection_id, "state": "DISCONNECTED"})

    @router.post("/api/v1/practice-operations/fiteatsy-connections/{connection_id}/diet-plans")
    async def publish_plan(connection_id: str, request: Request, body: PlanPublication, ctx=Depends(context_dependency), db: AsyncSession=Depends(get_db)):
        denied = external_only(request, ctx) or enabled(request)
        if denied: return denied
        if not get_settings().external_fiteatsy_diet_publish_enabled: return error(request, 404, "FEATURE_DISABLED", "Fiteatsy Diet Plan delivery is not enabled")
        connection = (await db.execute(text("SELECT id FROM external_fiteatsy_connections WHERE id=:id AND tenant_id=:tenant AND consultant_id=:consultant AND state='ACTIVE' AND consented_scopes ? 'DIET_PLANS'"), {"id": connection_id, "tenant": ctx["tenant_id"], "consultant": ctx["user_id"]})).first()
        if not connection: return error(request, 404, "CONNECTION_NOT_FOUND", "An active, consented connection could not be found")
        publication_id = uuid4(); now = datetime.now(timezone.utc)
        row = (await db.execute(text("""INSERT INTO external_fiteatsy_plan_publications(id,connection_id,tenant_id,consultant_id,plan_id,plan_version,title,content,idempotency_key,status,published_at)
            VALUES(:id,:connection,:tenant,:consultant,:plan,:version,:title,CAST(:content AS JSONB),:key,'PUBLISHED',:now) ON CONFLICT(connection_id,idempotency_key) DO UPDATE SET id=external_fiteatsy_plan_publications.id RETURNING id,status,published_at"""), {"id": publication_id, "connection": connection_id, "tenant": ctx["tenant_id"], "consultant": ctx["user_id"], "plan": body.plan_id, "version": body.plan_version, "title": body.title, "content": json.dumps(body.content), "key": body.idempotency_key, "now": now})).mappings().one()
        await db.commit(); return response(request, dict(row), 201)

    @router.post("/api/v1/practice-operations/fiteatsy-connections/{connection_id}/appointments")
    async def publish_appointment(connection_id: str, request: Request, body: AppointmentPublication, ctx=Depends(context_dependency), db: AsyncSession=Depends(get_db)):
        denied = external_only(request, ctx) or enabled(request)
        if denied: return denied
        if not get_settings().external_fiteatsy_scheduling_enabled: return error(request, 404, "FEATURE_DISABLED", "Fiteatsy scheduling is not enabled")
        if body.ends_at <= body.starts_at: return error(request, 422, "INVALID_APPOINTMENT_WINDOW", "Appointment end must be after its start")
        connection = (await db.execute(text("SELECT id FROM external_fiteatsy_connections WHERE id=:id AND tenant_id=:tenant AND consultant_id=:consultant AND state='ACTIVE' AND consented_scopes ? 'APPOINTMENTS'"), {"id": connection_id, "tenant": ctx["tenant_id"], "consultant": ctx["user_id"]})).first()
        if not connection: return error(request, 404, "CONNECTION_NOT_FOUND", "An active, consented connection could not be found")
        row = (await db.execute(text("""INSERT INTO external_fiteatsy_appointments(id,connection_id,tenant_id,consultant_id,appointment_id,title,starts_at,ends_at,idempotency_key,status,created_at)
            VALUES(:id,:connection,:tenant,:consultant,:appointment,:title,:starts,:ends,:key,'SCHEDULED',:now) ON CONFLICT(connection_id,idempotency_key) DO UPDATE SET id=external_fiteatsy_appointments.id RETURNING id,status,created_at"""), {"id": uuid4(), "connection": connection_id, "tenant": ctx["tenant_id"], "consultant": ctx["user_id"], "appointment": body.appointment_id, "title": body.title, "starts": body.starts_at, "ends": body.ends_at, "key": body.idempotency_key, "now": datetime.now(timezone.utc)})).mappings().one()
        await db.commit(); return response(request, dict(row), 201)

    return router
