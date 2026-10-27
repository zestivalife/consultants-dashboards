"""External Consultant <-> Fiteatsy connection domain.

The mobile-facing endpoints trust only a short-lived asymmetric assertion
issued by Fiteatsy. A caller supplied user id is never treated as identity.
"""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import hmac
import json
import secrets
import httpx
from uuid import uuid4

import jwt
from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import Response
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_db

PIN_ALPHABET = "0123456789"
ALLOWED_SCOPES = {"PROFILE", "HEALTH_SUMMARY", "MEASUREMENTS", "BIOMARKERS", "DIET_PLANS", "APPOINTMENTS"}


def generate_connection_pin(length: int = 6) -> str:
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


def create_fiteatsy_delegation(connection, permission: str, purpose: str) -> str:
    settings = get_settings(); now = datetime.now(timezone.utc)
    claims = {
        "iss": settings.external_fiteatsy_outbound_issuer,
        "sub": str(connection["consultant_id"]),
        "aud": settings.external_fiteatsy_outbound_audience,
        "iat": int(now.timestamp()), "exp": int((now + timedelta(seconds=60)).timestamp()), "jti": str(uuid4()),
        "product": "fiteatsy", "permissions": [permission], "purpose": purpose,
        "actor_type": "EXTERNAL_CONSULTANT", "tenant_id": str(connection["tenant_id"]),
        "connection_id": str(connection["id"]), "fiteatsy_user_id": str(connection["fiteatsy_user_id"]),
        "scopes": list(connection["consented_scopes"] or []),
    }
    key = (settings.external_fiteatsy_outbound_private_key or "").replace("\\n", "\n")
    return jwt.encode(claims, key, algorithm="RS256", headers={"typ": "Zestiva-Delegated-Authority", "kid": settings.external_fiteatsy_outbound_key_id})


class InvitationCreate(BaseModel):
    client_id: str | None = Field(default=None, max_length=120)
    expires_in_hours: int = Field(default=72, ge=1, le=168)
    scopes: list[str] = Field(default_factory=lambda: ["PROFILE", "HEALTH_SUMMARY", "DIET_PLANS", "APPOINTMENTS"])


class PinRedeem(BaseModel):
    pin: str = Field(min_length=6, max_length=32)
    consent_version: str = Field(min_length=1, max_length=40)
    accepted_scopes: list[str]


def public_consultant_projection(row):
    if not row:
        return None
    source = dict(row.get("projection") or {})
    return {
        "id": str(row["profile_id"]),
        "slug": row.get("slug"),
        "display_name": source.get("display_name"),
        "headline": source.get("headline"),
        "profession_code": source.get("profession_code"),
        "specialisations": source.get("specialisations") or [],
        "languages": source.get("languages") or [],
        "profile_photo_url": source.get("profile_photo_url"),
        "verified_qualifications": int(row.get("verified_qualifications") or 0),
    }


async def consultant_projection(db, tenant_id, consultant_id, include_contact=False):
    row = (await db.execute(text("""SELECT p.id::text profile_id,p.slug,v.projection,
      COALESCE(q.verified_qualifications,0)::int verified_qualifications,
      CASE WHEN :include_contact THEN cp.phone_e164 ELSE NULL END phone_e164
      FROM external_consultant_public_profiles p
      JOIN external_consultant_public_profile_versions v ON v.profile_id=p.id AND v.version=p.current_published_version
      LEFT JOIN (SELECT profile_id,COUNT(*) FILTER(WHERE verification_status='VERIFIED' AND (expiry_date IS NULL OR expiry_date>=CURRENT_DATE)) verified_qualifications FROM external_consultant_qualifications GROUP BY profile_id) q ON q.profile_id=p.id
      LEFT JOIN external_consultant_contact_profiles cp ON cp.tenant_id=p.tenant_id AND cp.consultant_user_id=p.consultant_user_id
      WHERE p.tenant_id=:tenant AND p.consultant_user_id=:consultant AND p.status='PUBLISHED'
        AND p.approval_valid=TRUE AND p.suspended_at IS NULL"""), {
          "tenant": tenant_id, "consultant": consultant_id, "include_contact": include_contact
      })).mappings().first()
    result = public_consultant_projection(row)
    if result is not None and include_contact:
        result["phone_e164"] = row.get("phone_e164")
    return result


def pin_status_error(request, error, invitation, now):
    if not invitation:
        return error(request, 404, "CONNECTION_PIN_INVALID", "The Connection PIN is invalid")
    if invitation["status"] == "REDEEMED":
        return error(request, 409, "CONNECTION_PIN_ALREADY_USED", "This Connection PIN has already been used")
    if invitation["status"] == "REVOKED":
        return error(request, 410, "CONNECTION_PIN_REVOKED", "This Connection PIN was revoked by the consultant")
    if invitation["status"] == "EXPIRED" or invitation["expires_at"] <= now:
        return error(request, 410, "CONNECTION_PIN_EXPIRED", "This Connection PIN has expired")
    if invitation["attempt_count"] >= invitation["max_attempts"]:
        return error(request, 429, "CONNECTION_PIN_LOCKED", "This Connection PIN is temporarily unavailable")
    return None


class PinPreview(BaseModel):
    pin: str = Field(min_length=6, max_length=32)


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


class ActivePlanSelection(BaseModel):
    publication_id: str = Field(min_length=1, max_length=120)


class AppointmentPublication(BaseModel):
    appointment_id: str = Field(min_length=1, max_length=120)
    idempotency_key: str = Field(min_length=8, max_length=120)


def validate_canonical_plan_content(content: dict) -> None:
    required = {"nutritionSnapshot", "dailyTargets", "mealPlan", "hydrationRhythm", "weeklySuccessGuide", "smartSubstitutions", "supplementsAndClinicalNotes"}
    meal_keys = {"earlyMorning", "breakfast", "midMorningSnack", "lunch", "eveningSnack", "dinner", "bedtimeNutrition"}
    if not required <= set(content) or not isinstance(content.get("mealPlan"), dict) or set(content["mealPlan"]) != meal_keys:
        raise ValueError("Plan content does not satisfy the canonical Fiteatsy nutrition contract")
    for key in meal_keys:
        section = content["mealPlan"][key]
        if not isinstance(section, dict) or not isinstance(section.get("options"), list):
            raise ValueError(f"Canonical meal section {key} is invalid")
        for option in section["options"]:
            if not isinstance(option, dict) or not option.get("id") or not option.get("meal"):
                raise ValueError(f"Canonical meal option in {key} is invalid")
            components = option.get("components")
            if not isinstance(components, list) or not components or any(not isinstance(item, dict) or not item.get("foodId") for item in components):
                raise ValueError(f"Canonical meal option in {key} must reference verified Fiteatsy catalogue foods")


async def send_plan_to_fiteatsy(connection, body: PlanPublication, consultant: dict | None):
    settings = get_settings()
    token = create_fiteatsy_delegation(connection, "fiteatsy.external.diet.write", "external_consultant_diet_plan")
    url = f"{settings.external_fiteatsy_backend_url.rstrip('/')}/v1/internal/external-consultant-access/{connection['fiteatsy_user_id']}/diet-plans"
    payload = {
        "externalPlanId": body.plan_id, "externalVersion": str(body.plan_version),
        "consultantId": str(connection["consultant_id"]),
        "consultantName": (consultant or {}).get("display_name") or "External consultant",
        "practiceName": (consultant or {}).get("headline") or "Zestiva 360",
        "publishedAtISO": datetime.now(timezone.utc).isoformat(), "content": body.content,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        result = await client.post(url, json=payload, headers={"x-zestiva-delegation": token})
    result.raise_for_status()
    return result.json()


async def select_plan_in_fiteatsy(connection, external_plan_id: str):
    settings = get_settings()
    token = create_fiteatsy_delegation(connection, "fiteatsy.external.diet.select", "external_consultant_diet_plan_selection")
    url = f"{settings.external_fiteatsy_backend_url.rstrip('/')}/v1/internal/external-consultant-access/{connection['fiteatsy_user_id']}/diet-plans/active"
    async with httpx.AsyncClient(timeout=15.0) as client:
        result = await client.put(url, json={"externalPlanId": external_plan_id}, headers={"x-zestiva-delegation": token})
    result.raise_for_status()
    return result.json()


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
        settings = get_settings(); now = datetime.now(timezone.utc)
        pin = None; invitation_id = None
        # Six numeric digits intentionally have a small keyspace. Let the
        # database's unique verifier constraint arbitrate concurrent issuers
        # and retry without ever exposing a colliding PIN.
        for _ in range(12):
            candidate = generate_connection_pin(); candidate_id = uuid4()
            inserted = (await db.execute(text("""INSERT INTO external_fiteatsy_connection_invitations(id,tenant_id,consultant_id,intended_client_id,pin_verifier,pin_hint,status,attempt_count,max_attempts,expires_at,requested_scopes,created_at,updated_at)
                VALUES(:id,:tenant,:consultant,:client,:verifier,:hint,'PENDING',0,8,:expires,CAST(:scopes AS JSONB),:now,:now)
                ON CONFLICT(pin_verifier) DO NOTHING RETURNING id"""), {"id": candidate_id, "tenant": ctx["tenant_id"], "consultant": ctx["user_id"], "client": body.client_id, "verifier": pin_verifier(candidate, settings.external_fiteatsy_pin_pepper or ""), "hint": candidate[-2:], "expires": now + timedelta(hours=body.expires_in_hours), "scopes": json.dumps(scopes), "now": now})).scalar_one_or_none()
            if inserted:
                pin = candidate; invitation_id = candidate_id
                break
        if pin is None or invitation_id is None:
            await db.rollback()
            return error(request, 503, "CONNECTION_PIN_UNAVAILABLE", "A unique Connection PIN could not be issued. Please retry.")
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

    async def active_health_connection(connection_id, ctx, db):
        return (await db.execute(text("SELECT id::text,tenant_id,consultant_id,fiteatsy_user_id,consented_scopes FROM external_fiteatsy_connections WHERE id=:id AND tenant_id=:tenant AND consultant_id=:consultant AND state='ACTIVE'"), {"id": connection_id, "tenant": ctx["tenant_id"], "consultant": ctx["user_id"]})).mappings().first()

    @router.get("/api/v1/practice-operations/fiteatsy-connections/{connection_id}/health-context")
    async def health_context(connection_id: str, request: Request, ctx=Depends(context_dependency), db: AsyncSession=Depends(get_db)):
        denied = external_only(request, ctx) or enabled(request)
        if denied: return denied
        settings = get_settings()
        if not settings.external_fiteatsy_health_access_enabled: return error(request, 404, "FEATURE_DISABLED", "Fiteatsy health access is not enabled")
        connection = await active_health_connection(connection_id, ctx, db)
        if not connection: return error(request, 404, "CONNECTION_NOT_FOUND", "An active Fiteatsy connection could not be found")
        if not set(connection["consented_scopes"] or []) & {"PROFILE", "HEALTH_SUMMARY", "MEASUREMENTS", "BIOMARKERS"}: return error(request, 403, "HEALTH_CONSENT_REQUIRED", "The client has not consented to health access")
        token = create_fiteatsy_delegation(connection, "fiteatsy.external.health.read", "external_consultant_health")
        url = f"{settings.external_fiteatsy_backend_url.rstrip('/')}/v1/internal/external-consultant-access/{connection['fiteatsy_user_id']}/health-context"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client: upstream = await client.get(url, headers={"x-zestiva-delegation": token})
        except httpx.RequestError: return error(request, 503, "FITEATSY_UNAVAILABLE", "Fiteatsy health data is temporarily unavailable")
        if upstream.status_code != 200:
            safe = upstream.json() if upstream.headers.get("content-type", "").startswith("application/json") else {}
            return error(request, upstream.status_code, safe.get("error", "FITEATSY_REQUEST_FAILED"), safe.get("message", "Fiteatsy health data could not be retrieved"))
        data = upstream.json()
        for report in data.get("reports", []):
            report["file_path"] = f"/api/v1/practice-operations/fiteatsy-connections/{connection_id}/reports/{report['id']}/file"
        return response(request, data)

    @router.get("/api/v1/practice-operations/fiteatsy-connections/{connection_id}/reports/{report_id}/file")
    async def health_report_file(connection_id: str, report_id: str, request: Request, ctx=Depends(context_dependency), db: AsyncSession=Depends(get_db)):
        denied = external_only(request, ctx) or enabled(request)
        if denied: return denied
        settings = get_settings()
        if not settings.external_fiteatsy_health_access_enabled: return error(request, 404, "FEATURE_DISABLED", "Fiteatsy health access is not enabled")
        connection = await active_health_connection(connection_id, ctx, db)
        if not connection or "HEALTH_SUMMARY" not in (connection["consented_scopes"] or []): return error(request, 403, "REPORT_ACCESS_DENIED", "An active consented report connection is required")
        token = create_fiteatsy_delegation(connection, "fiteatsy.external.report.read", "external_consultant_report")
        url = f"{settings.external_fiteatsy_backend_url.rstrip('/')}/v1/internal/external-consultant-access/{connection['fiteatsy_user_id']}/reports/{report_id}/file"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client: upstream = await client.get(url, headers={"x-zestiva-delegation": token})
        except httpx.RequestError: return error(request, 503, "FITEATSY_UNAVAILABLE", "The report file is temporarily unavailable")
        if upstream.status_code != 200: return error(request, upstream.status_code, "REPORT_FILE_UNAVAILABLE", "The report file could not be retrieved")
        headers = {key: value for key, value in upstream.headers.items() if key.lower() in {"content-type", "content-length", "content-disposition"}}
        headers["Cache-Control"] = "no-store, private"
        return Response(content=upstream.content, status_code=200, headers=headers)

    @router.post("/api/v1/fiteatsy-connections/redeem")
    async def redeem_invitation(request: Request, body: PinRedeem, authorization: str | None = Header(None), idempotency_key: str | None = Header(None), db: AsyncSession=Depends(get_db)):
        denied = enabled(request)
        if denied: return denied
        identity, denied = fiteatsy_identity(request, authorization)
        if denied: return denied
        try: accepted = clean_scopes(body.accepted_scopes)
        except ValueError as exc: return error(request, 422, "INVALID_CONNECTION_SCOPE", str(exc))
        verifier = pin_verifier(body.pin, get_settings().external_fiteatsy_pin_pepper or ""); now = datetime.now(timezone.utc)
        invitation = (await db.execute(text("SELECT * FROM external_fiteatsy_connection_invitations WHERE pin_verifier=:verifier FOR UPDATE"), {"verifier": verifier})).mappings().first()
        if invitation and invitation["status"] == "REDEEMED" and idempotency_key and str(invitation.get("redemption_idempotency_key")) == idempotency_key and invitation["redeemed_by_fiteatsy_user_id"] == identity["sub"]:
            existing = (await db.execute(text("SELECT id::text,state,consented_scopes FROM external_fiteatsy_connections WHERE tenant_id=:tenant AND consultant_id=:consultant AND fiteatsy_user_id=:user"), {"tenant": invitation["tenant_id"], "consultant": invitation["consultant_id"], "user": identity["sub"]})).mappings().first()
            if existing: return response(request, dict(existing), 200)
        denied = pin_status_error(request, error, invitation, now)
        if denied: return denied
        if not set(accepted) <= set(invitation["requested_scopes"] or []):
            return error(request, 422, "CONSENT_SCOPE_EXCEEDS_INVITATION", "Accepted consent exceeds the invited access")
        connection_id = uuid4()
        await db.execute(text("""INSERT INTO external_fiteatsy_connections(id,tenant_id,consultant_id,fiteatsy_user_id,consultant_client_id,state,consent_version,consented_scopes,programme_status,connected_at,updated_at)
            VALUES(:id,:tenant,:consultant,:user,:client,'ACTIVE',:version,CAST(:scopes AS JSONB),'NOT_ENROLLED',:now,:now)
            ON CONFLICT(tenant_id,consultant_id,fiteatsy_user_id) DO UPDATE SET state='ACTIVE',consent_version=EXCLUDED.consent_version,consented_scopes=EXCLUDED.consented_scopes,connected_at=EXCLUDED.connected_at,disconnected_at=NULL,updated_at=EXCLUDED.updated_at RETURNING id"""), {"id": connection_id, "tenant": invitation["tenant_id"], "consultant": invitation["consultant_id"], "user": identity["sub"], "client": invitation["intended_client_id"], "version": body.consent_version, "scopes": json.dumps(accepted), "now": now})
        await db.execute(text("UPDATE external_fiteatsy_connection_invitations SET status='REDEEMED',redeemed_by_fiteatsy_user_id=:user,redemption_idempotency_key=CAST(:key AS UUID),redeemed_at=:now,updated_at=:now WHERE id=:id"), {"user": identity["sub"], "key": idempotency_key, "now": now, "id": invitation["id"]})
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
        row = (await db.execute(text("SELECT pin_hint,requested_scopes,expires_at,status,attempt_count,max_attempts,tenant_id,consultant_id FROM external_fiteatsy_connection_invitations WHERE pin_verifier=:verifier"), {"verifier": verifier})).mappings().first()
        denied = pin_status_error(request, error, row, datetime.now(timezone.utc))
        if denied: return denied
        consultant = await consultant_projection(db, row["tenant_id"], row["consultant_id"])
        return response(request, {"pin_hint": row["pin_hint"], "requested_scopes": row["requested_scopes"], "expires_at": row["expires_at"], "consent_required": True, "consultant": consultant})

    @router.get("/api/v1/fiteatsy-connections")
    async def mobile_connections(request: Request, authorization: str | None = Header(None), db: AsyncSession=Depends(get_db)):
        denied = enabled(request)
        if denied: return denied
        identity, denied = fiteatsy_identity(request, authorization)
        if denied: return denied
        rows = []
        for row in (await db.execute(text("SELECT id::text,tenant_id,consultant_id,state,consented_scopes,programme_status,connected_at,disconnected_at FROM external_fiteatsy_connections WHERE fiteatsy_user_id=:user ORDER BY connected_at DESC"), {"user": identity["sub"]})).mappings().all():
            item = dict(row); item["consultant"] = await consultant_projection(db, row["tenant_id"], row["consultant_id"], True); item.pop("tenant_id", None); item.pop("consultant_id", None); rows.append(item)
        return response(request, {"connections": rows})

    @router.get("/api/v1/fiteatsy-connections/{connection_id}")
    async def mobile_connection_details(connection_id: str, request: Request, authorization: str | None = Header(None), db: AsyncSession=Depends(get_db)):
        denied = enabled(request)
        if denied: return denied
        identity, denied = fiteatsy_identity(request, authorization)
        if denied: return denied
        row = (await db.execute(text("SELECT id::text,tenant_id,consultant_id,state,consented_scopes,programme_status,connected_at,disconnected_at FROM external_fiteatsy_connections WHERE id=:id AND fiteatsy_user_id=:user"), {"id": connection_id, "user": identity["sub"]})).mappings().first()
        if not row: return error(request, 404, "CONNECTION_NOT_FOUND", "The consultant connection could not be found")
        item = dict(row); item["consultant"] = await consultant_projection(db, row["tenant_id"], row["consultant_id"], True); item.pop("tenant_id", None); item.pop("consultant_id", None)
        return response(request, {"connection": item})

    @router.get("/api/v1/fiteatsy-connections/{connection_id}/diet-plans")
    async def mobile_plans(connection_id: str, request: Request, authorization: str | None = Header(None), db: AsyncSession=Depends(get_db)):
        denied = enabled(request)
        if denied: return denied
        identity, denied = fiteatsy_identity(request, authorization)
        if denied: return denied
        rows = [dict(item) for item in (await db.execute(text("""SELECT p.id::text,p.plan_id,p.plan_version,p.title,p.content,p.status,p.published_at,
          (selection.publication_id=p.id) AS is_active
          FROM external_fiteatsy_plan_publications p
          JOIN external_fiteatsy_connections c ON c.id=p.connection_id
          LEFT JOIN external_fiteatsy_active_plan_selections selection ON selection.fiteatsy_user_id=c.fiteatsy_user_id
          WHERE c.id=:id AND c.fiteatsy_user_id=:user AND c.state='ACTIVE' AND c.consented_scopes ? 'DIET_PLANS'
          ORDER BY p.published_at DESC"""), {"id": connection_id, "user": identity["sub"]})).mappings().all()]
        return response(request, {"plans": rows})

    @router.put("/api/v1/fiteatsy-connections/{connection_id}/diet-plans/active")
    async def select_mobile_plan(connection_id: str, request: Request, body: ActivePlanSelection, authorization: str | None = Header(None), db: AsyncSession=Depends(get_db)):
        denied = enabled(request)
        if denied: return denied
        identity, denied = fiteatsy_identity(request, authorization)
        if denied: return denied
        publication = (await db.execute(text("""SELECT p.id publication_id,p.plan_id,c.* FROM external_fiteatsy_plan_publications p
          JOIN external_fiteatsy_connections c ON c.id=p.connection_id
          WHERE p.id=:publication AND c.id=:connection AND c.fiteatsy_user_id=:user
            AND c.state='ACTIVE' AND c.consented_scopes ? 'DIET_PLANS' AND p.status='PUBLISHED'"""), {
          "publication": body.publication_id, "connection": connection_id, "user": identity["sub"]
        })).mappings().first()
        if not publication: return error(request, 404, "DIET_PLAN_NOT_AVAILABLE", "The published diet plan is not available through this active connection")
        try:
            await select_plan_in_fiteatsy(publication, publication["plan_id"])
        except httpx.HTTPError:
            await db.rollback()
            return error(request, 502, "FITEATSY_CANONICAL_SELECTION_FAILED", "Fiteatsy did not accept the active diet plan selection")
        now = datetime.now(timezone.utc)
        await db.execute(text("""INSERT INTO external_fiteatsy_active_plan_selections(fiteatsy_user_id,publication_id,selected_at,updated_at)
          VALUES(:user,:publication,:now,:now)
          ON CONFLICT(fiteatsy_user_id) DO UPDATE SET publication_id=EXCLUDED.publication_id,selected_at=EXCLUDED.selected_at,updated_at=EXCLUDED.updated_at"""), {
          "user": identity["sub"], "publication": publication["publication_id"], "now": now
        })
        await db.commit()
        return response(request, {"publication_id": str(publication["publication_id"]), "active": True, "selected_at": now})

    @router.get("/api/v1/fiteatsy-connections/{connection_id}/appointments")
    async def mobile_appointments(connection_id: str, request: Request, authorization: str | None = Header(None), db: AsyncSession=Depends(get_db)):
        denied = enabled(request)
        if denied: return denied
        identity, denied = fiteatsy_identity(request, authorization)
        if denied: return denied
        rows = [dict(item) for item in (await db.execute(text("""SELECT link.id::text,a.id::text appointment_id,t.name title,a.starts_at,a.ends_at,a.status,a.attendance_status,a.cancellation_reason,a.updated_at
          FROM external_fiteatsy_appointment_links link
          JOIN external_fiteatsy_connections c ON c.id=link.connection_id
          JOIN external_scheduled_appointments a ON a.id=link.appointment_id AND a.tenant_id=link.tenant_id
          JOIN external_appointment_types t ON t.id=a.appointment_type_id AND t.tenant_id=a.tenant_id
          WHERE c.id=:id AND c.fiteatsy_user_id=:user AND c.state='ACTIVE' AND c.consented_scopes ? 'APPOINTMENTS'
          ORDER BY a.starts_at"""), {"id": connection_id, "user": identity["sub"]})).mappings().all()]
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
        connection = (await db.execute(text("SELECT * FROM external_fiteatsy_connections WHERE id=:id AND tenant_id=:tenant AND consultant_id=:consultant AND state='ACTIVE' AND consented_scopes ? 'DIET_PLANS'"), {"id": connection_id, "tenant": ctx["tenant_id"], "consultant": ctx["user_id"]})).mappings().first()
        if not connection: return error(request, 404, "CONNECTION_NOT_FOUND", "An active, consented connection could not be found")
        try:
            validate_canonical_plan_content(body.content)
            consultant = await consultant_projection(db, connection["tenant_id"], connection["consultant_id"])
            await send_plan_to_fiteatsy(connection, body, consultant)
        except ValueError as exc:
            return error(request, 422, "INVALID_CANONICAL_DIET_PLAN", str(exc))
        except httpx.HTTPError:
            await db.rollback()
            return error(request, 502, "FITEATSY_CANONICAL_INGESTION_FAILED", "Fiteatsy did not accept the canonical diet plan")
        publication_id = uuid4(); now = datetime.now(timezone.utc)
        row = (await db.execute(text("""INSERT INTO external_fiteatsy_plan_publications(id,connection_id,tenant_id,consultant_id,plan_id,plan_version,title,content,idempotency_key,status,published_at)
            VALUES(:id,:connection,:tenant,:consultant,:plan,:version,:title,CAST(:content AS JSONB),:key,'PUBLISHED',:now) ON CONFLICT(connection_id,idempotency_key) DO UPDATE SET id=external_fiteatsy_plan_publications.id RETURNING id,status,published_at"""), {"id": publication_id, "connection": connection_id, "tenant": ctx["tenant_id"], "consultant": ctx["user_id"], "plan": body.plan_id, "version": body.plan_version, "title": body.title, "content": json.dumps(body.content), "key": body.idempotency_key, "now": now})).mappings().one()
        await db.commit(); return response(request, dict(row), 201)

    @router.post("/api/v1/practice-operations/fiteatsy-connections/{connection_id}/appointments")
    async def publish_appointment(connection_id: str, request: Request, body: AppointmentPublication, ctx=Depends(context_dependency), db: AsyncSession=Depends(get_db)):
        denied = external_only(request, ctx) or enabled(request)
        if denied: return denied
        if not get_settings().external_fiteatsy_scheduling_enabled: return error(request, 404, "FEATURE_DISABLED", "Fiteatsy scheduling is not enabled")
        connection = (await db.execute(text("SELECT * FROM external_fiteatsy_connections WHERE id=:id AND tenant_id=:tenant AND consultant_id=:consultant AND state='ACTIVE' AND consented_scopes ? 'APPOINTMENTS'"), {"id": connection_id, "tenant": ctx["tenant_id"], "consultant": ctx["user_id"]})).mappings().first()
        if not connection: return error(request, 404, "CONNECTION_NOT_FOUND", "An active, consented connection could not be found")
        if not connection["consultant_client_id"]:
            return error(request, 409, "CONNECTION_CLIENT_NOT_LINKED", "The connection must be linked to the consultant client before scheduling")
        appointment = (await db.execute(text("""SELECT a.id,a.status,a.starts_at,a.ends_at FROM external_scheduled_appointments a
          WHERE a.id=CAST(:appointment AS uuid) AND a.tenant_id=:tenant AND a.client_id=:client AND a.created_by=:consultant"""), {
          "appointment": body.appointment_id, "tenant": ctx["tenant_id"], "client": connection["consultant_client_id"], "consultant": ctx["user_id"]
        })).mappings().first()
        if not appointment: return error(request, 404, "CANONICAL_APPOINTMENT_NOT_FOUND", "The canonical appointment was not found for this connected client")
        row = (await db.execute(text("""INSERT INTO external_fiteatsy_appointment_links(id,connection_id,tenant_id,appointment_id,idempotency_key,created_at)
            VALUES(:id,:connection,:tenant,:appointment,:key,:now) ON CONFLICT(connection_id,idempotency_key) DO UPDATE SET id=external_fiteatsy_appointment_links.id RETURNING id,created_at"""), {"id": uuid4(), "connection": connection_id, "tenant": ctx["tenant_id"], "appointment": body.appointment_id, "key": body.idempotency_key, "now": datetime.now(timezone.utc)})).mappings().one()
        await db.commit(); return response(request, dict(row), 201)

    return router
