import base64
import hashlib
import hmac
import secrets
import struct
import time
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

from cryptography.fernet import Fernet, InvalidToken
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

def _fernet() -> Fernet:
    key = get_settings().internal_iam_mfa_encryption_key
    if not key:
        raise ForbiddenException("Internal privileged MFA is not configured")
    try: return Fernet(key.encode())
    except (ValueError, TypeError) as exc: raise ForbiddenException("Internal privileged MFA configuration is invalid") from exc

def _totp_step(now: int | None = None) -> int:
    return int(now or time.time()) // 30

def _totp(secret: str, step: int) -> str:
    key = base64.b32decode(secret + "=" * ((8 - len(secret) % 8) % 8), casefold=True)
    digest = hmac.new(key, struct.pack(">Q", step), hashlib.sha1).digest()
    offset = digest[-1] & 15
    value = (struct.unpack(">I", digest[offset:offset+4])[0] & 0x7fffffff) % 1_000_000
    return f"{value:06d}"

def verify_totp(user: User, code: str) -> int:
    if not user.mfa_secret_encrypted or not user.mfa_enabled:
        raise ForbiddenException("Privileged MFA enrolment required")
    try: secret = _fernet().decrypt(user.mfa_secret_encrypted.encode()).decode()
    except InvalidToken as exc: raise ForbiddenException("Privileged MFA credential unavailable") from exc
    current = _totp_step()
    for step in (current - 1, current, current + 1):
        if hmac.compare_digest(_totp(secret, step), str(code or "")):
            if user.mfa_last_accepted_step is not None and step <= user.mfa_last_accepted_step:
                raise ForbiddenException("MFA code has already been used")
            return step
    raise ForbiddenException("Invalid MFA code")

async def initiate(session: AsyncSession, *, actor_id: uuid.UUID, email: str, phone: str, first_name: str, last_name: str):
    require_bootstrap_authority(actor_id)
    email = email.strip().lower()
    repo=UserRepository(session); existing_user=await repo.get_by_email(email)
    if existing_user and (not existing_user.role or existing_user.role.name != ROLE or existing_user.is_active):
        raise ConflictException("Identity already exists")
    phone_value=canonical_mobile(phone)
    phone_owner=await repo.get_by_mobile(phone_value)
    if phone_owner and (not existing_user or phone_owner.id != existing_user.id): raise ConflictException("Telephone identity already exists")
    existing = await session.scalar(select(InternalPrivilegedInvitation).where(InternalPrivilegedInvitation.email == email, InternalPrivilegedInvitation.status.in_(["PENDING_APPROVAL","APPROVED","ENROLLING_MFA","ACTIVE"])))
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

async def accept(session: AsyncSession, *, token: str, password: str) -> tuple[str, str]:
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
        user=existing; user.password_hash=password_service.hash_password(password,validate=False); user.first_name=record.first_name; user.last_name=record.last_name; user.phone=record.phone; user.mobile=record.phone; user.is_verified=True; user.email_verified=True; user.status="PENDING_MFA"; user.mfa_enabled=False; user.mfa_last_accepted_step=None
    else:
        user=User(email=record.email,mobile=record.phone,phone=record.phone,password_hash=password_service.hash_password(password,validate=False),first_name=record.first_name,last_name=record.last_name,role_id=role.id,is_active=False,is_verified=True,email_verified=True,status="PENDING_MFA",account_classification="INTERNAL_PRIVILEGED",mfa_enabled=False)
        session.add(user)
    await session.flush()
    activation=secrets.token_urlsafe(48); secret=base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")
    user.mfa_secret_encrypted=_fernet().encrypt(secret.encode()).decode(); record.activation_hash=hash_token(activation); record.token_hash=None; record.user_id=user.id; record.accepted_at=now; record.status="ENROLLING_MFA"; record.expires_at=now+timedelta(minutes=15)
    await AuditLogRepository(session).create("INTERNAL_PRIVILEGED_EMAIL_VERIFIED", user_id=user.id); await session.commit()
    uri=f"otpauth://totp/{quote('Zestiva Internal:'+record.email)}?secret={secret}&issuer=Zestiva%20Internal&algorithm=SHA1&digits=6&period=30"
    return activation, uri

async def confirm_mfa(session: AsyncSession, *, activation_token: str, code: str, expected_user_id: uuid.UUID | None = None) -> User:
    now=datetime.now(timezone.utc); digest=hash_token(activation_token)
    record=await session.scalar(select(InternalPrivilegedInvitation).where(InternalPrivilegedInvitation.activation_hash==digest))
    if not record or record.status!="ENROLLING_MFA" or not record.user_id: raise ForbiddenException("Invalid activation session")
    if expected_user_id is not None and record.user_id != expected_user_id: raise ForbiddenException("MFA activation does not belong to this identity")
    if not record.expires_at or record.expires_at < now: raise ForbiddenException("Activation session expired")
    user=await UserRepository(session).get_by_id(record.user_id)
    if not user: raise NotFoundException("Identity not found")
    user.mfa_enabled=True
    # Temporarily enable verification helper, then persist the single-use step.
    step=verify_totp(user,code); user.mfa_last_accepted_step=step; user.is_active=True; user.status="ACTIVE"
    record.activation_hash=None; record.activated_at=now; record.status="ACTIVE"
    await AuditLogRepository(session).create("INTERNAL_PRIVILEGED_MFA_ENROLLED", user_id=user.id)
    await AuditLogRepository(session).create("INTERNAL_PRIVILEGED_ACCOUNT_ACTIVATED", user_id=user.id)
    await session.commit(); return user

async def begin_first_admin_mfa_enrolment(session: AsyncSession, *, user_id: uuid.UUID) -> tuple[str, str]:
    """Start MFA only after the bootstrap password has been permanently replaced."""
    user = await UserRepository(session).get_by_id(user_id)
    if not user or not user.role or user.role.name != ROLE:
        raise NotFoundException("Internal privileged identity not found")
    if user.must_change_password or user.credential_status == "TEMPORARY":
        raise ForbiddenException("Permanent password replacement is required before MFA enrolment")
    if user.mfa_enabled:
        raise ConflictException("Privileged MFA is already enrolled")
    if user.status != "PENDING_MFA":
        raise ForbiddenException("Identity is not awaiting MFA enrolment")
    record = await session.scalar(
        select(InternalPrivilegedInvitation).where(
            InternalPrivilegedInvitation.user_id == user.id,
            InternalPrivilegedInvitation.role_name == ROLE,
        ).with_for_update()
    )
    if not record or not record.bootstrap_grant_hash:
        raise ForbiddenException("Governed first-administrator evidence is unavailable")
    now = datetime.now(timezone.utc)
    activation = secrets.token_urlsafe(48)
    secret = base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")
    user.mfa_secret_encrypted = _fernet().encrypt(secret.encode()).decode()
    user.mfa_enabled = False
    user.mfa_last_accepted_step = None
    record.activation_hash = hash_token(activation)
    record.status = "ENROLLING_MFA"
    record.expires_at = now + timedelta(minutes=15)
    await AuditLogRepository(session).create("FIRST_INTERNAL_ADMIN_MFA_ENROLMENT_STARTED", user_id=user.id)
    await session.commit()
    uri = f"otpauth://totp/{quote('Zestiva Internal:'+record.email)}?secret={secret}&issuer=Zestiva%20Internal&algorithm=SHA1&digits=6&period=30"
    return activation, uri

async def assert_no_external_entitlement(session: AsyncSession, user_id: uuid.UUID) -> None:
    count = await session.scalar(select(UserProductAccess.id).where(UserProductAccess.user_id==user_id).limit(1))
    if count is not None: raise ForbiddenException("Internal privileged identity must not have product entitlements")

async def revoke(session: AsyncSession, *, actor_id: uuid.UUID, user_id: uuid.UUID) -> None:
    require_bootstrap_authority(actor_id, approver=True)
    if actor_id == user_id: raise ForbiddenException("Privileged users cannot revoke themselves")
    user=await UserRepository(session).get_by_id(user_id)
    if not user or not user.role or user.role.name != ROLE: raise NotFoundException("Internal privileged identity not found")
    user.is_active=False; user.status="REVOKED"; user.mfa_enabled=False; user.mfa_secret_encrypted=None; user.mfa_last_accepted_step=None; user.current_session_version += 1; user.refresh_token_version += 1
    await AuditLogRepository(session).create("INTERNAL_PRIVILEGED_ACCESS_REVOKED",user_id=user.id); await session.commit()
