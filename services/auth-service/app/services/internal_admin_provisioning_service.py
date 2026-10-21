"""Governed local provisioning for a new Internal Super Admin identity."""

from dataclasses import dataclass
from datetime import datetime, timezone
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException
from app.db.models.owner_access import Permission, RolePermission, UserRole
from app.db.models.internal_privileged_invitation import InternalPrivilegedInvitation
from app.db.models.role import Role
from app.db.models.user import PasswordHistory, User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.user_repository import UserRepository
from app.services.iam_lifecycle import (
    CREDENTIAL_TEMPORARY,
    STATUS_PASSWORD_CHANGE_REQUIRED,
    temporary_password_expiry,
)
from app.services.password_service import password_service
from app.services.internal_privileged_iam_service import require_bootstrap_authority
from app.core.mobile_identity import canonical_mobile

INTERNAL_SUPER_ADMIN_PERMISSIONS = {
    "internal.audit.view",
    "internal.invitations.manage",
    "internal.operations.manage",
    "internal.roles.assign",
    "internal.users.manage",
    "internal.users.read",
    "internal.verification.manage",
}


@dataclass(frozen=True, slots=True)
class ProvisionInternalSuperAdminCommand:
    email: str
    first_name: str
    last_name: str
    phone: str
    temporary_password: str
    operator_user_id: uuid.UUID


async def provision_internal_super_admin(
    session: AsyncSession,
    command: ProvisionInternalSuperAdminCommand,
) -> User:
    """Create one isolated Internal Super Admin; existing identities are never changed."""
    user_repo = UserRepository(session)
    require_bootstrap_authority(command.operator_user_id, approver=True)
    operator = await user_repo.get_by_id(command.operator_user_id)
    if (
        operator is None
        or not operator.is_active
        or not operator.role
        or operator.role.name != "internal_super_admin"
        or "internal.users.manage" not in set(operator.permissions or [])
    ):
        raise ForbiddenException("An active Internal Super Admin operator is required")

    email = command.email.strip().lower()
    if await user_repo.get_by_email(email):
        raise ConflictException("Identity already exists; credentials were not changed")

    invitation = (
        await session.execute(
            select(InternalPrivilegedInvitation)
            .where(InternalPrivilegedInvitation.email == email)
            .order_by(InternalPrivilegedInvitation.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if invitation is None:
        raise NotFoundException("A governed Internal Super Admin invitation is required")
    if invitation.status != "APPROVED" or invitation.approved_by_user_id != operator.id:
        raise ForbiddenException("The invitation requires independent governed approval")
    if invitation.initiated_by_user_id == operator.id:
        raise ForbiddenException("Two-person approval is required")
    if invitation.expires_at is None or invitation.expires_at <= now:
        raise ForbiddenException("The approved invitation has expired")

    phone = canonical_mobile(command.phone)
    if (
        invitation.role_name != "internal_super_admin"
        or invitation.first_name.strip() != command.first_name.strip()
        or invitation.last_name.strip() != command.last_name.strip()
        or canonical_mobile(invitation.phone) != phone
    ):
        raise ConflictException("Provisioning identity does not match the approved invitation")
    phone_owner = await user_repo.get_by_mobile(phone)
    if phone_owner is not None:
        raise ConflictException("Telephone identity already exists; credentials were not changed")

    role = (
        await session.execute(select(Role).where(Role.name == "internal_super_admin"))
    ).scalar_one_or_none()
    if role is None:
        raise NotFoundException("internal_super_admin role is not configured")

    permission_keys = list(
        (
            await session.execute(
                select(Permission.key)
                .join(RolePermission, RolePermission.permission_id == Permission.id)
                .where(RolePermission.role_id == role.id)
                .order_by(Permission.key)
            )
        ).scalars()
    )
    if set(permission_keys) != INTERNAL_SUPER_ADMIN_PERMISSIONS:
        raise ForbiddenException("Internal Super Admin role must contain exactly the governed permissions")

    password_service.validate_new_password(command.temporary_password)
    password_hash = password_service.hash_password(command.temporary_password)
    user = User(
        email=email,
        password_hash=password_hash,
        first_name=command.first_name.strip(),
        last_name=command.last_name.strip(),
        phone=phone,
        mobile=phone,
        role_id=role.id,
        role=role,
        is_active=True,
        is_verified=True,
        email_verified=False,
        status=STATUS_PASSWORD_CHANGE_REQUIRED,
        permissions=permission_keys,
        must_change_password=True,
        credential_status=CREDENTIAL_TEMPORARY,
        account_classification="INTERNAL_PRIVILEGED",
        temporary_password_created_at=now,
        temporary_password_expires_at=temporary_password_expiry(now),
        mfa_enabled=False,
        mfa_secret_encrypted=None,
    )
    await user_repo.create(user)
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
            source="governed_local_internal_admin_provisioning",
        )
    )
    await AuditLogRepository(session).create(
        "INTERNAL_SUPER_ADMIN_PROVISIONED_PASSWORD_CHANGE_REQUIRED",
        user_id=user.id,
        user_agent=f"local-provisioner operator={operator.id}",
    )
    invitation.user_id = user.id
    invitation.token_hash = None
    invitation.activation_hash = None
    invitation.accepted_at = now
    invitation.activated_at = now
    invitation.status = "ACTIVE"
    await session.flush()
    return user
