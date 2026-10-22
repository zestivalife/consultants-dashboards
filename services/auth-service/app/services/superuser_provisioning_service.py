from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException
from app.core.mobile_identity import canonical_mobile
from app.db.models.internal_privileged_invitation import InternalPrivilegedInvitation
from app.db.models.owner_access import (
    AuditEvent,
    OrganizationMembership,
    UserProductAccess,
    UserRole,
)
from app.db.models.role import Role
from app.db.models.user import PasswordHistory, User
from app.repositories.audit_log_repository import AuditLogRepository
from app.services.iam_lifecycle import (
    CREDENTIAL_TEMPORARY,
    STATUS_PASSWORD_CHANGE_REQUIRED,
    temporary_password_expiry,
)
from app.services.internal_privileged_iam_service import require_bootstrap_authority
from app.services.password_service import password_service


SUPERUSER_ROLE = "superuser"
ACCOUNT_CLASSIFICATION = "PRODUCTION_USER"


@dataclass(frozen=True, slots=True)
class ProvisionSuperuserCommand:
    operator_user_id: uuid.UUID
    invitation_id: uuid.UUID
    email: str
    mobile: str
    first_name: str
    last_name: str


@dataclass(frozen=True, slots=True)
class ProvisionSuperuserResult:
    user_id: uuid.UUID
    email: str
    mobile: str
    role: str
    status: str
    must_change_password: bool
    invitation_status: str


async def _assert_operator(session: AsyncSession, operator_user_id: uuid.UUID) -> User:
    # This reuses the independently configured Internal IAM approver allow-list;
    # possession of a generic superuser session alone is deliberately insufficient.
    require_bootstrap_authority(operator_user_id, approver=True)
    operator = await session.scalar(
        select(User)
        .join(Role, Role.id == User.role_id)
        .where(
            User.id == operator_user_id,
            User.is_active.is_(True),
            User.deleted_at.is_(None),
            Role.name == SUPERUSER_ROLE,
        )
    )
    if operator is None:
        raise ForbiddenException("Active configured superuser approver required")
    return operator


async def provision_authorized_superuser(
    session: AsyncSession,
    command: ProvisionSuperuserCommand,
) -> ProvisionSuperuserResult:
    operator = await _assert_operator(session, command.operator_user_id)
    email = command.email.strip().lower()
    mobile = canonical_mobile(command.mobile)
    first_name = command.first_name.strip()
    last_name = command.last_name.strip()
    if not first_name or not last_name:
        raise ConflictException("First and last name are required")

    invitation = await session.scalar(
        select(InternalPrivilegedInvitation)
        .where(InternalPrivilegedInvitation.id == command.invitation_id)
        .with_for_update()
    )
    if invitation is None:
        raise NotFoundException("Existing privileged invitation not found")
    if invitation.email.strip().lower() != email or canonical_mobile(invitation.phone) != mobile:
        raise ConflictException("Invitation identity does not match the authorised account")
    if invitation.status not in {"PENDING_APPROVAL", "REVOKED"}:
        raise ConflictException("Invitation is not eligible for direct provisioning reconciliation")

    existing = await session.scalar(
        select(User).where(func.lower(User.email) == email).with_for_update()
    )
    mobile_owner = await session.scalar(
        select(User).where(User.mobile == mobile).with_for_update()
    )
    if existing is not None or mobile_owner is not None:
        raise ConflictException("Account already exists; no duplicate was created")

    role = await session.scalar(select(Role).where(Role.name == SUPERUSER_ROLE))
    if role is None:
        raise ForbiddenException("Canonical superuser role is unavailable")

    now = datetime.now(timezone.utc)
    generated_password = password_service.generate_temporary_password()
    password_hash = password_service.hash_password(generated_password)
    # The generated value is intentionally discarded. Lalit must use the existing
    # governed admin reset flow, which returns a fresh temporary password once.
    del generated_password

    user = User(
        email=email,
        mobile=mobile,
        phone=mobile,
        password_hash=password_hash,
        first_name=first_name,
        last_name=last_name,
        role_id=role.id,
        is_active=True,
        is_verified=True,
        email_verified=True,
        mobile_verified=False,
        status=STATUS_PASSWORD_CHANGE_REQUIRED,
        permissions=[],
        must_change_password=True,
        credential_status=CREDENTIAL_TEMPORARY,
        account_classification=ACCOUNT_CLASSIFICATION,
        temporary_password_created_at=now,
        temporary_password_expires_at=temporary_password_expiry(now),
        mfa_enabled=False,
    )
    session.add(user)
    await session.flush()

    session.add(
        UserRole(
            user_id=user.id,
            role_id=role.id,
            assigned_by_user_id=operator.id,
            is_primary=True,
        )
    )
    session.add(
        PasswordHistory(
            user_id=user.id,
            password_hash=password_hash,
            source="governed_superuser_provisioning",
        )
    )

    invitation.user_id = user.id
    invitation.approved_by_user_id = operator.id
    invitation.approved_at = now
    invitation.revoked_at = now
    invitation.status = "REVOKED"
    invitation.token_hash = None
    invitation.activation_hash = None
    invitation.expires_at = None

    # Explicitly prove that provisioning did not attach a tenant or product.
    product_access = await session.scalar(
        select(UserProductAccess.id).where(UserProductAccess.user_id == user.id).limit(1)
    )
    membership = await session.scalar(
        select(OrganizationMembership.id)
        .where(OrganizationMembership.user_id == user.id)
        .limit(1)
    )
    if product_access is not None or membership is not None:
        raise ForbiddenException("Provisioned superuser must not receive product or tenant entitlements")

    session.add(
        AuditEvent(
            actor_user_id=operator.id,
            entity_type="user",
            entity_id=str(user.id),
            action="GOVERNED_SUPERUSER_PROVISIONED",
            before_state={"invitation_id": str(invitation.id), "status": "PENDING_APPROVAL"},
            after_state={
                "role": SUPERUSER_ROLE,
                "status": STATUS_PASSWORD_CHANGE_REQUIRED,
                "direct_permissions": [],
                "product_entitlements": 0,
                "organization_memberships": 0,
                "must_change_password": True,
                "invitation_status": "REVOKED",
            },
        )
    )
    await AuditLogRepository(session).create(
        "GOVERNED_SUPERUSER_PROVISIONED",
        user_id=user.id,
        user_agent=f"authorised_by:{operator.id}",
    )
    await session.commit()
    await session.refresh(user)

    return ProvisionSuperuserResult(
        user_id=user.id,
        email=user.email,
        mobile=user.mobile or "",
        role=SUPERUSER_ROLE,
        status=user.status,
        must_change_password=user.must_change_password,
        invitation_status=invitation.status,
    )
