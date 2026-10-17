import uuid
import hashlib
import json
from datetime import datetime, timedelta, timezone
import httpx
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from app.core.exceptions import AppException, ConflictException
from app.db.models.external_qa import ExternalQaPracticeProvisioning
from app.db.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.people_access import ExternalQaPracticeCreateRequest
from app.services.user_service import CreateUserCommand, user_service

QA_CLASSIFICATION = "GOVERNED_QA_EXTERNAL"


def _fixture_key(profession: str) -> str:
    return f"external-qa-{profession.lower().replace('_', '-')}"


def _input_fingerprint(body: ExternalQaPracticeCreateRequest) -> str:
    canonical = body.model_dump(mode="json", exclude_none=True)
    return hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _validate_qa(body: ExternalQaPracticeCreateRequest) -> None:
    email = str(body.consultant_email).lower()
    if not (email.endswith("@zestiva.test") and (email.startswith("qa+") or email.startswith("qa-"))):
        raise AppException("A qa+ or qa- identity on zestiva.test is required.", 422)
    if not any(marker in body.tenant_name.lower().split() for marker in ("qa", "test")):
        raise AppException("The External QA tenant must be clearly labelled QA or Test.", 422)


def _delegation_token(actor_id: uuid.UUID, audience: str, permission: str, **scope: str) -> str:
    settings = get_settings()
    if not settings.fiteatsy_delegation_private_key:
        raise AppException("Governed External QA provisioning is not configured.", 503)
    now = datetime.now(timezone.utc)
    return jwt.encode({"iss": settings.fiteatsy_delegation_issuer, "sub": str(actor_id), "aud": audience,
        "iat": int(now.timestamp()), "exp": int((now + timedelta(seconds=60)).timestamp()), "jti": str(uuid.uuid4()),
        "product": "fiteatsy", "permissions": [permission], "purpose": "qa_external_practice", "actor_type": "platform_owner", **scope},
        settings.fiteatsy_delegation_private_key.replace("\\n", "\n"), algorithm="RS256",
        headers={"typ": "Zestiva-Delegated-Authority", "kid": settings.fiteatsy_delegation_key_id})


async def _provision_workspace(actor_id: uuid.UUID, user: User, ledger: ExternalQaPracticeProvisioning, body: ExternalQaPracticeCreateRequest) -> dict:
    settings = get_settings()
    payload = {"fixtureKey": ledger.fixture_key, "authIdentityId": str(user.id), "professionCode": body.profession_code,
        "tenantName": body.tenant_name, "consultantDisplayName": body.consultant_display_name,
        "consultantEmail": str(body.consultant_email), "clientCount": body.client_count,
        "specialisation": body.specialisation, "seedProfile": body.seed_profile}
    token = _delegation_token(actor_id, settings.fiteatsy_delegation_audience, "fiteatsy.qa.external_practice.create")
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(f"{settings.fiteatsy_backend_url.rstrip('/')}/v1/internal/delegated/qa-external-practices",
            headers={"x-zestiva-delegation": token, "idempotency-key": f"governed:{ledger.fixture_key}"},
            json={key: value for key, value in payload.items() if value is not None})
    if response.status_code not in (200, 201):
        raise AppException("Canonical External QA workspace provisioning failed safely.", 503)
    return response.json()


async def _configure_profession(actor_id: uuid.UUID, user_id: uuid.UUID, tenant_id: str, body: ExternalQaPracticeCreateRequest) -> dict:
    settings = get_settings()
    token = _delegation_token(actor_id, settings.practice_qa_delegation_audience, "practice.qa.external.configure",
        target_user_id=str(user_id), tenant_id=tenant_id, profession_code=body.profession_code)
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.put(f"{settings.practice_operations_service_url.rstrip('/')}/internal/qa/external-practice/configuration",
            headers={"x-qa-delegation": token}, json={"profession": body.profession_code, "capabilities": [], "profile": body.seed_profile or {}})
    if response.status_code != 200:
        raise AppException("Profession configuration failed safely.", 503)
    payload = response.json()
    if not payload.get("success") or payload.get("data", {}).get("profession") != body.profession_code:
        raise AppException("Profession configuration could not be verified.", 503)
    return payload["data"]


async def provision_external_qa_practice(session: AsyncSession, body: ExternalQaPracticeCreateRequest, actor_id: uuid.UUID) -> dict:
    _validate_qa(body)
    fixture = _fixture_key(body.profession_code)
    fingerprint = _input_fingerprint(body)
    ledger = (await session.execute(select(ExternalQaPracticeProvisioning).where(ExternalQaPracticeProvisioning.fixture_key == fixture))).scalar_one_or_none()
    if ledger is None:
        collision = (await session.execute(select(User).where(User.email == str(body.consultant_email).lower()))).scalar_one_or_none()
        if collision is not None:
            raise ConflictException("The requested QA email is already assigned and cannot be reused.")
        created = await user_service.create_user(session, CreateUserCommand(email=str(body.consultant_email), role_name="consultant",
            first_name=body.consultant_display_name, status="ACTIVE", is_active=True, is_verified=True,
            actor_user_id=actor_id, audit_event_type="QA_EXTERNAL_CREDENTIAL_SETUP"))
        created.user.account_classification = QA_CLASSIFICATION
        ledger = ExternalQaPracticeProvisioning(fixture_key=fixture, auth_user_id=created.user.id,
            profession_code=body.profession_code, tenant_name=body.tenant_name, input_fingerprint=fingerprint, client_count=body.client_count,
            status="PENDING", created_by_reference=str(actor_id))
        session.add(ledger)
        await AuditLogRepository(session).create("QA_EXTERNAL_PRACTICE_REQUESTED", user_id=created.user.id)
        await session.commit()
    elif ledger.input_fingerprint != fingerprint or ledger.status == "DEACTIVATED":
        raise ConflictException("The governed QA fixture binding cannot be changed or reactivated.")
    user = await session.get(User, ledger.auth_user_id)
    if user is None or user.account_classification != QA_CLASSIFICATION:
        raise ConflictException("The governed QA identity lineage is invalid.")
    config = None
    try:
        if ledger.status == "PENDING":
            workspace = await _provision_workspace(actor_id, user, ledger, body)
            ledger.fiteatsy_user_id, ledger.tenant_id = workspace["userId"], workspace["tenantId"]
            ledger.client_ids, ledger.status = workspace["clientIds"], "WORKSPACE_READY"
            ledger.last_error_code = None
            await session.commit()
        if ledger.status == "WORKSPACE_READY":
            config = await _configure_profession(actor_id, user.id, str(ledger.tenant_id), body)
            ledger.status, ledger.last_error_code, ledger.updated_at = "READY", None, datetime.now(timezone.utc)
            await AuditLogRepository(session).create("QA_EXTERNAL_PRACTICE_PROVISIONED", user_id=user.id)
            await session.commit()
    except Exception:
        await session.rollback()
        current = await session.get(ExternalQaPracticeProvisioning, ledger.id)
        if current:
            current.last_error_code = "DOWNSTREAM_PROVISIONING_FAILED"
            await session.commit()
        raise
    return {"fixture_key": ledger.fixture_key, "auth_user_id": str(user.id), "fiteatsy_user_id": ledger.fiteatsy_user_id,
        "tenant_id": ledger.tenant_id, "profession_code": ledger.profession_code, "client_ids": ledger.client_ids,
        "status": ledger.status, "credential_delivery": "USE_GOVERNED_OWNER_PASSWORD_RESET", "configuration": config}


async def deactivate_external_qa_practice(session: AsyncSession, profession_code: str, reason: str, actor_id: uuid.UUID) -> dict:
    fixture = _fixture_key(profession_code)
    ledger = (await session.execute(select(ExternalQaPracticeProvisioning).where(ExternalQaPracticeProvisioning.fixture_key == fixture))).scalar_one_or_none()
    if ledger is None:
        raise AppException("Governed External QA practice was not found.", 404)
    settings = get_settings()
    token = _delegation_token(actor_id, settings.fiteatsy_delegation_audience, "fiteatsy.qa.external_practice.deactivate")
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(f"{settings.fiteatsy_backend_url.rstrip('/')}/v1/internal/delegated/qa-external-practices/{fixture}/deactivate",
            headers={"x-zestiva-delegation": token, "idempotency-key": f"deactivate:{fixture}"}, json={"reason": reason})
    if response.status_code != 200:
        raise AppException("Canonical QA tenant deactivation failed safely.", 503)
    user = await session.get(User, ledger.auth_user_id)
    if user:
        user.is_active, user.status = False, "DEACTIVATED"
        user.current_session_version += 1
        user.refresh_token_version += 1
    ledger.status, ledger.deactivation_reason = "DEACTIVATED", reason
    ledger.deactivated_at = ledger.updated_at = datetime.now(timezone.utc)
    await AuditLogRepository(session).create("QA_EXTERNAL_PRACTICE_DEACTIVATED", user_id=ledger.auth_user_id)
    await session.commit()
    return {"fixture_key": fixture, "tenant_id": ledger.tenant_id, "status": ledger.status}
