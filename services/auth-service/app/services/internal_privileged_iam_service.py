import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException
from app.core.mobile_identity import canonical_mobile
from app.core.security import hash_token
from app.db.models.internal_privileged_invitation import InternalPrivilegedInvitation
from app.db.models.owner_access import UserProductAccess
from app.db.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.services.iam_lifecycle import CREDENTIAL_TEMPORARY, STATUS_PASSWORD_CHANGE_REQUIRED, temporary_password_expiry
from app.services.password_service import password_service

ROLE = "internal_super_admin"

def _allowlist(value: str) -> set[uuid.UUID]:
    result = set()
    for item in value.split(","):
        try: result.add(uuid.UUID(item.strip()))
        except ValueError: pass
    return result

def require_bootstrap_authority(actor_id: uuid.UUID, *, approver: bool = False) -> None:
    settings = get_settings()
    configured = settings.internal_iam_approver_user_ids if approver else settings.internal_iam_initiator_user_ids
    if actor_id not in _allowlist(configured):
        raise ForbiddenException("Designated Internal IAM bootstrap authority required")

async def initiate(session: AsyncSession, *, actor_id: uuid.UUID, email: str, phone: str, first_name: str, last_name: str):
    require_bootstrap_authority(actor_id)
    email = email.strip().lower()
    repo=UserRepository(session); existing_user=await repo.get_by_email(email)
    if existing_user and (not existing_user.role or existing_user.role.name != ROLE or existing_user.is_active):
        raise ConflictException("Identity already exists")
    phone_value=canonical_mobile(phone)
    phone_owner=await repo.get_by_mobile(phone_value)
    if phone_owner and (not existing_user or phone_owner.id != existing_user.id): raise ConflictException("Telephone identity already exists")
    existing = await session.scalar(select(InternalPrivilegedInvitation).where(InternalPrivilegedInvitation.email == email, InternalPrivilegedInvitation.status.in_(["PENDING_APPROVAL","APPROVED","ACTIVE"])))
    if existing: raise ConflictException("Privileged invitation already exists")
    record = InternalPrivilegedInvitation(email=email, phone=phone_value, first_name=first_name.strip(), last_name=last_name.strip(), role_name=ROLE, initiated_by_user_id=actor_id, user_id=existing_user.id if existing_user else None, status="PENDING_APPROVAL")
    session.add(record); await AuditLogRepository(session).create("INTERNAL_PRIVILEGED_INVITATION_REQUESTED", user_id=actor_id); await session.commit(); await session.refresh(record)
    return record

async def approve(session: AsyncSession, *, actor_id: uuid.UUID, invitation_id: uuid.UUID) -> tuple[InternalPrivilegedInvitation, str]:
    require_bootstrap_authority(actor_id, approver=True)
    record = await session.get(InternalPrivilegedInvitation, invitation_id)
    if not record: raise NotFoundException("Invitation not found")
    if record.initiated_by_user_id == actor_id: raise ForbiddenException("Two-person approval is required")
    if record.status != "PENDING_APPROVAL": raise ConflictException("Invitation is not pending approval")
    token = secrets.token_urlsafe(48); now = datetime.now(timezone.utc)
    record.token_hash=hash_token(token); record.approved_by_user_id=actor_id; record.approved_at=now; record.expires_at=now+timedelta(minutes=get_settings().internal_privileged_invitation_ttl_minutes); record.status="APPROVED"
    await AuditLogRepository(session).create("INTERNAL_PRIVILEGED_INVITATION_APPROVED", user_id=actor_id); await session.commit()
    return record, token

async def accept(session: AsyncSession, *, token: str, password: str) -> User:
    now=datetime.now(timezone.utc); digest=hash_token(token)
    record=await session.scalar(select(InternalPrivilegedInvitation).where(InternalPrivilegedInvitation.token_hash==digest))
    if not record or record.status!="APPROVED": raise ForbiddenException("Invalid or consumed invitation")
    if not record.expires_at or record.expires_at < now:
        record.status="EXPIRED"; record.token_hash=None; await session.commit(); raise ForbiddenException("Invitation has expired")
    existing=await UserRepository(session).get_by_email(record.email)
    if existing and (record.user_id != existing.id or not existing.role or existing.role.name != ROLE or existing.is_active): raise ConflictException("Identity already exists")
    role=await RoleRepository(session).get_by_name(ROLE)
    if not role: raise ForbiddenException("Internal Super Admin role is unavailable")
    password_service.validate_new_password(password)
    if existing:
        user=existing; user.password_hash=password_service.hash_password(password,validate=False); user.first_name=record.first_name; user.last_name=record.last_name; user.phone=record.phone; user.mobile=record.phone; user.is_verified=True; user.email_verified=True
    else:
        user=User(email=record.email,mobile=record.phone,phone=record.phone,password_hash=password_service.hash_password(password,validate=False),first_name=record.first_name,last_name=record.last_name,role_id=role.id,is_active=True,is_verified=True,email_verified=True,status=STATUS_PASSWORD_CHANGE_REQUIRED,account_classification="INTERNAL_PRIVILEGED")
        session.add(user)
    await session.flush()
    user.is_active=True; user.status=STATUS_PASSWORD_CHANGE_REQUIRED; user.must_change_password=True; user.credential_status=CREDENTIAL_TEMPORARY; user.temporary_password_created_at=now; user.temporary_password_expires_at=temporary_password_expiry(now); user.temporary_password_consumed_at=None
    record.activation_hash=None; record.token_hash=None; record.user_id=user.id; record.accepted_at=now; record.activated_at=now; record.status="ACTIVE"
    await AuditLogRepository(session).create("INTERNAL_PRIVILEGED_EMAIL_VERIFIED", user_id=user.id)
    await AuditLogRepository(session).create("INTERNAL_PRIVILEGED_ACCOUNT_ACTIVATED", user_id=user.id)
    await session.commit(); return user

async def assert_no_external_entitlement(session: AsyncSession, user_id: uuid.UUID) -> None:
    count = await session.scalar(select(UserProductAccess.id).where(UserProductAccess.user_id==user_id).limit(1))
    if count is not None: raise ForbiddenException("Internal privileged identity must not have product entitlements")

async def revoke(session: AsyncSession, *, actor_id: uuid.UUID, user_id: uuid.UUID) -> None:
    require_bootstrap_authority(actor_id, approver=True)
    if actor_id == user_id: raise ForbiddenException("Privileged users cannot revoke themselves")
    user=await UserRepository(session).get_by_id(user_id)
    if not user or not user.role or user.role.name != ROLE: raise NotFoundException("Internal privileged identity not found")
    user.is_active=False; user.status="REVOKED"; user.current_session_version += 1; user.refresh_token_version += 1
    await AuditLogRepository(session).create("INTERNAL_PRIVILEGED_ACCESS_REVOKED",user_id=user.id); await session.commit()
