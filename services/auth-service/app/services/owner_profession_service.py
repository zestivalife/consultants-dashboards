import uuid
from datetime import datetime, timedelta, timezone

import httpx
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import AppException
from app.db.models.external_qa import ExternalQaPracticeProvisioning
from app.db.models.external_signup import ExternalSignupProvisioning
from app.repositories.audit_log_repository import AuditLogRepository


async def _tenant_for_user(session: AsyncSession, user_id: uuid.UUID) -> str:
    qa = (await session.execute(select(ExternalQaPracticeProvisioning.tenant_id).where(
        ExternalQaPracticeProvisioning.auth_user_id == user_id,
        ExternalQaPracticeProvisioning.status.in_(("WORKSPACE_READY", "READY")),
    ))).scalar_one_or_none()
    signup = (await session.execute(select(ExternalSignupProvisioning.tenant_id).where(
        ExternalSignupProvisioning.auth_user_id == user_id,
    ))).scalar_one_or_none()
    tenants = {value for value in (qa, signup) if value}
    if not tenants:
        raise AppException("This user has no governed Practice Operations tenant linkage.", 422)
    if len(tenants) != 1:
        raise AppException("This user has ambiguous Practice Operations tenant linkage.", 409)
    return tenants.pop()


def _token(actor_id: uuid.UUID, target_user_id: uuid.UUID, tenant_id: str) -> str:
    settings = get_settings()
    if not settings.fiteatsy_delegation_private_key:
        raise AppException("Owner profession configuration is not configured.", 503)
    now = datetime.now(timezone.utc)
    return jwt.encode({"iss": settings.fiteatsy_delegation_issuer, "sub": str(actor_id),
        "aud": settings.practice_qa_delegation_audience, "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=60)).timestamp()), "jti": str(uuid.uuid4()),
        "permissions": ["practice.owner.profession.manage"], "purpose": "owner_profession_configuration",
        "actor_type": "platform_owner", "target_user_id": str(target_user_id), "tenant_id": tenant_id},
        settings.fiteatsy_delegation_private_key.replace("\\n", "\n"), algorithm="RS256",
        headers={"typ": "Zestiva-Delegated-Authority", "kid": settings.fiteatsy_delegation_key_id})


async def get_profession(session: AsyncSession, actor_id: uuid.UUID, target_user_id: uuid.UUID) -> dict:
    tenant_id = await _tenant_for_user(session, target_user_id)
    return await _request("GET", actor_id, target_user_id, tenant_id)


async def update_profession(session: AsyncSession, actor_id: uuid.UUID, target_user_id: uuid.UUID,
                            profession: str, expected_version: int) -> dict:
    tenant_id = await _tenant_for_user(session, target_user_id)
    result = await _request("PUT", actor_id, target_user_id, tenant_id,
                            {"profession": profession, "expected_version": expected_version})
    await AuditLogRepository(session).create("OWNER_PROFESSION_UPDATED", user_id=target_user_id)
    await session.commit()
    return result


async def _request(method: str, actor_id: uuid.UUID, target_user_id: uuid.UUID,
                   tenant_id: str, body: dict | None = None) -> dict:
    settings = get_settings()
    url = f"{settings.practice_operations_service_url.rstrip('/')}/internal/owner/users/{target_user_id}/profession"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.request(method, url, headers={"x-owner-delegation": _token(actor_id, target_user_id, tenant_id)}, json=body)
    payload = response.json()
    if response.status_code >= 400:
        message = payload.get("error", {}).get("safe_message", "Profession configuration failed safely.")
        raise AppException(message, response.status_code)
    if not payload.get("success") or not isinstance(payload.get("data"), dict):
        raise AppException("Profession configuration returned an invalid response.", 503)
    return payload["data"]
