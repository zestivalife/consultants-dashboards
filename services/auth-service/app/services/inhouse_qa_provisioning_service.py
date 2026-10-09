import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import httpx
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import AppException, ConflictException
from app.db.models.inhouse_qa import InhouseQaProvisioning
from app.db.models.owner_access import Organization, OrganizationMembership
from app.db.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.services.user_service import CreateUserCommand, user_service


QA_CLASSIFICATION = "GOVERNED_QA_INHOUSE"
CANONICAL_TENANT_ID = "00000000-0000-4000-8000-000000000001"
ROLE_MAP = {
    "user": "user",
    "consultant": "consultant",
    "provider": "provider",
    "dietician": "dietician",
    "senior_consultant": "senior_consultant",
    "practitioner": "practitioner",
    "mentor": "mentor",
    "admin": "organization_admin",
    "super_admin": "platform_owner",
    "platform_owner": "platform_owner",
}
TENANT_ROLE_MAP = {
    "user": "CLIENT",
    "consultant": "CONSULTANT",
    "provider": "CONSULTANT",
    "dietician": "CONSULTANT",
    "senior_consultant": "SENIOR_CONSULTANT",
    "practitioner": "CONSULTANT",
    "mentor": "CONSULTANT",
    "admin": "STAFF",
    "super_admin": None,
    "platform_owner": None,
}


@dataclass(slots=True)
class ProvisionInhouseQaCommand:
    fixture_key: str
    canonical_role: str
    email: str
    mobile_number: str
    password: str
    display_name: str
    created_by_reference: str
    organization_id: uuid.UUID | None = None


def _delegation_token(subject: uuid.UUID) -> str:
    settings = get_settings()
    if not settings.fiteatsy_delegation_private_key:
        raise AppException("Governed QA provisioning is not configured.", 503)
    now = datetime.now(timezone.utc)
    payload = {
        "iss": settings.fiteatsy_delegation_issuer,
        "sub": str(subject),
        "aud": settings.fiteatsy_delegation_audience,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=60)).timestamp()),
        "jti": str(uuid.uuid4()),
        "product": "fiteatsy",
        "permissions": ["fiteatsy.qa.identity.create"],
        "purpose": "qa_provisioning",
        "actor_type": "platform_owner",
    }
    return jwt.encode(
        payload,
        settings.fiteatsy_delegation_private_key.replace("\\n", "\n"),
        algorithm="RS256",
        headers={"typ": "Zestiva-Delegated-Authority", "kid": settings.fiteatsy_delegation_key_id},
    )


async def _provision_application_user(user: User, command: ProvisionInhouseQaCommand) -> dict:
    settings = get_settings()
    body = {
        "authIdentityId": str(user.id),
        "fixtureKey": command.fixture_key,
        "name": command.display_name,
        "email": user.email,
        "mobileNumber": command.mobile_number,
        "role": command.canonical_role,
        "reason": "Governed in-house QA role-matrix provisioning",
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            f"{settings.fiteatsy_backend_url.rstrip('/')}/v1/internal/delegated/qa-inhouse-identities/provision",
            headers={
                "x-zestiva-delegation": _delegation_token(user.id),
                "idempotency-key": f"governed-qa-inhouse:{command.fixture_key}",
            },
            json=body,
        )
    if response.status_code not in (200, 201):
        raise AppException("Governed QA application provisioning failed safely.", 503)
    return response.json()


async def provision_inhouse_qa_identity(
    session: AsyncSession, command: ProvisionInhouseQaCommand
) -> InhouseQaProvisioning:
    if not command.fixture_key.startswith("inhouse-"):
        raise AppException("Invalid governed QA fixture key.", 400)
    if command.canonical_role not in ROLE_MAP:
        raise AppException("Unsupported governed QA role.", 400)

    existing = (await session.execute(
        select(InhouseQaProvisioning).where(InhouseQaProvisioning.fixture_key == command.fixture_key)
    )).scalar_one_or_none()
    if existing is not None:
        user = await session.get(User, existing.auth_user_id)
        if user is None or user.account_classification != QA_CLASSIFICATION:
            raise ConflictException("Governed QA fixture lineage is invalid.")
        if existing.canonical_role != command.canonical_role:
            raise ConflictException("Governed QA fixture role cannot be escalated.")
        return existing

    auth_role = ROLE_MAP[command.canonical_role]
    created = await user_service.create_user(session, CreateUserCommand(
        email=command.email,
        mobile=command.mobile_number,
        phone=command.mobile_number,
        role_name=auth_role,
        password=command.password,
        first_name=command.display_name,
        status="ACTIVE",
        is_active=True,
        is_verified=True,
        actor_user_id=None,
        audit_event_type="QA_CREDENTIAL_SETUP",
        must_change_password=False,
    ))
    user = created.user
    user.account_classification = QA_CLASSIFICATION
    ledger = InhouseQaProvisioning(
        fixture_key=command.fixture_key,
        auth_user_id=user.id,
        canonical_role=command.canonical_role,
        status="PENDING",
        created_by_reference=command.created_by_reference,
    )
    session.add(ledger)
    await AuditLogRepository(session).create("QA_IDENTITY_PROVISIONED", user_id=user.id)

    requires_membership = TENANT_ROLE_MAP[command.canonical_role] is not None
    if requires_membership:
        if command.organization_id is None:
            raise AppException("Governed QA organization is required for this role.", 400)
        organization = await session.get(Organization, command.organization_id)
        if organization is None or organization.status != "ACTIVE":
            raise AppException("Governed QA organization is unavailable.", 409)
        membership = (await session.execute(select(OrganizationMembership).where(
            OrganizationMembership.user_id == user.id,
            OrganizationMembership.organization_id == command.organization_id,
        ))).scalar_one_or_none()
        if membership is None:
            session.add(OrganizationMembership(
                user_id=user.id,
                organization_id=command.organization_id,
                status="ACTIVE",
                is_verified=True,
                tags=[QA_CLASSIFICATION],
            ))
            await AuditLogRepository(session).create("QA_TENANT_MEMBERSHIP_CREATED", user_id=user.id)

    await session.flush()
    try:
        result = await _provision_application_user(user, command)
        ledger.fiteatsy_user_id = result["applicationUserId"]
        ledger.status = "READY"
        ledger.last_error_code = None
        await AuditLogRepository(session).create("QA_APPLICATION_USER_LINKED", user_id=user.id)
        await AuditLogRepository(session).create("QA_ROLE_ASSIGNED", user_id=user.id)
        await session.commit()
    except Exception:
        await session.rollback()
        # The Auth transaction is rolled back completely. The backend endpoint is
        # atomic and idempotent, so retry cannot create duplicate active lineage.
        raise
    return ledger
