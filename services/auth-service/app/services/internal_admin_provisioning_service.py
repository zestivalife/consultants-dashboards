"""Governed, single-use bootstrap for the first Internal Super Admin."""

import base64
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException
from app.core.mobile_identity import canonical_mobile
from app.db.models.internal_privileged_invitation import InternalPrivilegedInvitation
from app.db.models.owner_access import Permission, RolePermission, UserProductAccess, UserRole
from app.db.models.role import Role
from app.db.models.user import PasswordHistory, User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.user_repository import UserRepository
from app.services.iam_lifecycle import CREDENTIAL_TEMPORARY, STATUS_PASSWORD_CHANGE_REQUIRED, temporary_password_expiry
from app.services.password_service import password_service

INTERNAL_SUPER_ADMIN_PERMISSIONS = {
    "internal.audit.view", "internal.invitations.manage", "internal.operations.manage",
    "internal.roles.assign", "internal.users.manage", "internal.users.read",
    "internal.verification.manage",
}


@dataclass(frozen=True, slots=True)
class ProvisionInternalSuperAdminCommand:
    email: str
    first_name: str
    last_name: str
    phone: str
    temporary_password: str
    authorization_grant: str


def _decode(value: str) -> bytes:
    try:
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except Exception as exc:
        raise ForbiddenException("Bootstrap authorization grant is malformed") from exc


def _verify_grant(token: str, *, invitation: InternalPrivilegedInvitation, email: str, phone: str) -> dict:
    settings = get_settings()
    if not settings.internal_first_admin_authority_public_key or not settings.internal_first_admin_release_sha:
        raise ForbiddenException("First-administrator trust anchor is not configured")
    try:
        encoded_payload, encoded_signature = token.strip().split(".", 1)
        key_data = settings.internal_first_admin_authority_public_key.replace("\\n", "\n").encode()
        public_key = serialization.load_pem_public_key(key_data)
        if not isinstance(public_key, Ed25519PublicKey):
            raise TypeError("Ed25519 key required")
        public_key.verify(_decode(encoded_signature), encoded_payload.encode())
        claims = json.loads(_decode(encoded_payload))
    except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError, InvalidSignature) as exc:
        raise ForbiddenException("Bootstrap authorization grant is invalid") from exc

    now = int(datetime.now(timezone.utc).timestamp())
    required = {
        "iss": settings.internal_first_admin_authority_issuer,
        "aud": settings.internal_first_admin_authority_audience,
        "invitation_id": str(invitation.id), "email": email, "phone": phone,
        "role": "internal_super_admin", "release_sha": settings.internal_first_admin_release_sha,
    }
    if any(claims.get(key) != value for key, value in required.items()):
        raise ForbiddenException("Bootstrap authorization grant scope does not match")
    if not isinstance(claims.get("jti"), str) or not claims["jti"]:
        raise ForbiddenException("Bootstrap authorization grant has no one-time identifier")
    if not isinstance(claims.get("authorizing_principal"), str) or not claims["authorizing_principal"]:
        raise ForbiddenException("Bootstrap authorizing principal is missing")
    if claims["authorizing_principal"].strip().lower() == email:
        raise ForbiddenException("Bootstrap authority must be distinct from the target identity")
    if not isinstance(claims.get("iat"), int) or not isinstance(claims.get("exp"), int):
        raise ForbiddenException("Bootstrap authorization grant lifetime is invalid")
    if claims["iat"] > now + 60 or claims["exp"] <= now or claims["exp"] - claims["iat"] > 900:
        raise ForbiddenException("Bootstrap authorization grant is expired or exceeds 15 minutes")
    return claims


async def provision_internal_super_admin(session: AsyncSession, command: ProvisionInternalSuperAdminCommand) -> User:
    """Create exactly the first Internal Super Admin under an offline-signed grant."""
    user_repo = UserRepository(session)
    email = command.email.strip().lower()
    phone = canonical_mobile(command.phone)
    role = (await session.execute(select(Role).where(Role.name == "internal_super_admin").with_for_update())).scalar_one_or_none()
    if role is None:
        raise NotFoundException("internal_super_admin role is not configured")

    # Locking the singleton role serializes this check even while the user count is zero.
    existing_admins = await session.scalar(select(func.count(User.id)).where(User.role_id == role.id))
    if existing_admins:
        raise ConflictException("First-administrator bootstrap is permanently disabled")
    if await user_repo.get_by_email(email):
        raise ConflictException("Identity already exists; credentials were not changed")

    invitation = (await session.execute(
        select(InternalPrivilegedInvitation).where(InternalPrivilegedInvitation.email == email)
        .order_by(InternalPrivilegedInvitation.created_at.desc()).limit(1).with_for_update()
    )).scalar_one_or_none()
    if invitation is None:
        raise NotFoundException("A governed Internal Super Admin invitation is required")
    if invitation.status != "PENDING_APPROVAL" or invitation.user_id is not None:
        raise ForbiddenException("Invitation is not eligible for first-administrator bootstrap")
    if (invitation.role_name != "internal_super_admin"
            or invitation.first_name.strip() != command.first_name.strip()
            or invitation.last_name.strip() != command.last_name.strip()
            or canonical_mobile(invitation.phone) != phone):
        raise ConflictException("Provisioning identity does not match the pending invitation")
    if await user_repo.get_by_mobile(phone):
        raise ConflictException("Telephone identity already exists; credentials were not changed")

    claims = _verify_grant(command.authorization_grant, invitation=invitation, email=email, phone=phone)
    grant_hash = hashlib.sha256(claims["jti"].encode()).hexdigest()
    replay = await session.scalar(select(InternalPrivilegedInvitation.id).where(
        InternalPrivilegedInvitation.bootstrap_grant_hash == grant_hash
    ))
    if replay is not None:
        raise ForbiddenException("Bootstrap authorization grant has already been consumed")

    permission_keys = list((await session.execute(
        select(Permission.key).join(RolePermission, RolePermission.permission_id == Permission.id)
        .where(RolePermission.role_id == role.id).order_by(Permission.key)
    )).scalars())
    if set(permission_keys) != INTERNAL_SUPER_ADMIN_PERMISSIONS:
        raise ForbiddenException("Internal Super Admin role must contain exactly the governed permissions")

    password_service.validate_new_password(command.temporary_password)
    password_hash = password_service.hash_password(command.temporary_password)
    now = datetime.now(timezone.utc)
    user = User(
        email=email, password_hash=password_hash, first_name=command.first_name.strip(),
        last_name=command.last_name.strip(), phone=phone, mobile=phone, role_id=role.id,
        role=role, is_active=True, is_verified=True, email_verified=False,
        status=STATUS_PASSWORD_CHANGE_REQUIRED, permissions=permission_keys,
        must_change_password=True, credential_status=CREDENTIAL_TEMPORARY,
        account_classification="INTERNAL_PRIVILEGED", temporary_password_created_at=now,
        temporary_password_expires_at=temporary_password_expiry(now), mfa_enabled=False,
        mfa_secret_encrypted=None,
    )
    await user_repo.create(user)
    session.add(UserRole(user_id=user.id, role_id=role.id, assigned_by_user_id=None, is_primary=True))
    session.add(PasswordHistory(user_id=user.id, password_hash=password_hash,
                                source="governed_first_internal_admin_bootstrap"))
    principal = claims["authorizing_principal"].strip()
    await AuditLogRepository(session).create(
        "FIRST_INTERNAL_SUPER_ADMIN_BOOTSTRAPPED_PASSWORD_CHANGE_REQUIRED",
        user_id=user.id, user_agent=f"authority={principal}; grant={grant_hash[:16]}",
    )
    external_access = await session.scalar(select(UserProductAccess.id).where(
        UserProductAccess.user_id == user.id).limit(1))
    if external_access is not None:
        raise ForbiddenException("Internal privileged identity received an external entitlement")

    invitation.user_id = user.id
    invitation.approved_at = now
    invitation.accepted_at = now
    invitation.activated_at = now
    invitation.status = "ACTIVE"
    invitation.token_hash = None
    invitation.activation_hash = None
    invitation.bootstrap_authority_principal = principal
    invitation.bootstrap_grant_hash = grant_hash
    await session.flush()
    return user
