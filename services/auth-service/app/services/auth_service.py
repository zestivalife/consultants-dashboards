import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import (
    AppException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
)
from app.core.logging import get_logger
from app.core.password_policy import WeakPasswordException
from app.core.rate_limit import check_rate_limit
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_token,
)
from app.db.models.owner_access import UserStatusHistory
from app.db.models.refresh_token import RefreshToken
from app.db.models.user import PasswordHistory, User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.people_access_repository import PeopleAccessRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    AccessOrganization,
    AccessProduct,
    AccessProfile,
    AccessWorkspace,
    LoginResponse,
    RoleResponse,
    TokenResponse,
    UserResponse,
)
from app.services.password_service import password_service
from app.services import people_access_service
from app.services.iam_lifecycle import (
    AUTHENTICATABLE_STATUSES,
    CREDENTIAL_PERMANENT,
    CREDENTIAL_TEMPORARY,
    DASHBOARD_ELIGIBLE_STATUSES,
    STATUS_ACTIVE,
    STATUS_APPROVED,
    STATUS_EXPIRED,
    STATUS_FIRST_LOGIN,
    STATUS_INVITED,
    STATUS_PASSWORD_CHANGE_REQUIRED,
    is_temporary_password_expired,
    next_action_for_user,
    normalize_status,
)

logger = get_logger(__name__)

PLATFORM_OPERATIONS_PERMISSIONS = {
    "audit.view",
    "notifications.manage",
    "packages.manage",
    "services.manage",
    "settings.manage",
    "subscriptions.manage",
}
ORGANIZATION_OPERATIONS_PERMISSIONS = {
    "organizations.manage",
    "users.create",
    "users.edit",
    "users.export",
    "users.invite",
}
CARE_SUPERVISION_MARKERS = {"mentor", "team_lead"}
CARE_DELIVERY_PERMISSIONS = {"reports.view", "users.read"}


# ── helpers ───────────────────────────────────────────


def _normalize_key(value: object | None) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _active_membership(user: User):
    memberships = list(getattr(user, "organization_memberships", []) or [])
    active = [item for item in memberships if _normalize_key(getattr(item, "status", "")) == "active"]
    return (active or memberships or [None])[0]


def _active_product_access(user: User):
    product_access = list(getattr(user, "product_access", []) or [])
    active = [item for item in product_access if _normalize_key(getattr(item, "status", "")) == "active"]
    primary = [item for item in active if getattr(item, "is_primary", False)]
    return (primary or active or product_access or [None])[0]


def _resolve_workspace(
    *,
    role: str,
    permissions: list[str],
    active_product: AccessProduct | None,
) -> AccessWorkspace:
    permission_set = {permission for permission in permissions if permission}
    role_key = _normalize_key(role)

    if permission_set & PLATFORM_OPERATIONS_PERMISSIONS:
        return AccessWorkspace(
            id="platform-operations",
            label="Platform Operations",
            landing_page="/dashboard/owner",
            required_permissions=sorted(permission_set & PLATFORM_OPERATIONS_PERMISSIONS),
        )

    if permission_set & ORGANIZATION_OPERATIONS_PERMISSIONS:
        return AccessWorkspace(
            id="organization-operations",
            label="Organization Operations",
            landing_page="/dashboard/corporate-admin",
            required_permissions=sorted(permission_set & ORGANIZATION_OPERATIONS_PERMISSIONS),
        )

    if role_key in CARE_SUPERVISION_MARKERS:
        return AccessWorkspace(
            id="care-supervision",
            label="Care Supervision",
            landing_page="/dashboard/team-lead",
            required_permissions=sorted(permission_set & CARE_DELIVERY_PERMISSIONS),
        )

    if active_product is not None or permission_set & CARE_DELIVERY_PERMISSIONS:
        landing_page = "/dashboard/provider"
        if role_key == "senior_consultant":
            landing_page = "/dashboard/senior-consultant"
        return AccessWorkspace(
            id="care-delivery",
            label="Care Delivery",
            landing_page=landing_page,
            required_permissions=sorted(permission_set & CARE_DELIVERY_PERMISSIONS),
        )

    return AccessWorkspace(
        id="member-workspace",
        label="Member Workspace",
        landing_page="/dashboard/team-member",
        required_permissions=[],
    )


async def _access_profile(
    session: AsyncSession,
    user: User,
    permissions: list[str],
) -> AccessProfile:
    detail = await PeopleAccessRepository(session).get_user_detail(user.id)
    access_user = detail or user
    membership = _active_membership(access_user)
    product_access = _active_product_access(access_user)

    active_organization = None
    if membership is not None and getattr(membership, "organization", None) is not None:
        active_organization = AccessOrganization(
            id=membership.organization_id,
            name=membership.organization.name,
            department_id=getattr(membership, "department_id", None),
            department=getattr(getattr(membership, "department", None), "name", None),
            status=getattr(membership, "status", "ACTIVE"),
        )

    active_product = None
    if product_access is not None and getattr(product_access, "product", None) is not None:
        product_role = getattr(product_access, "role", None)
        active_product = AccessProduct(
            id=product_access.product_id,
            name=product_access.product.name,
            role=getattr(product_role, "name", None),
            status=getattr(product_access, "status", "ACTIVE"),
            is_primary=bool(getattr(product_access, "is_primary", False)),
        )

    role_name = (
        getattr(getattr(product_access, "role", None), "name", None)
        or getattr(getattr(access_user, "role", None), "name", None)
        or "member"
    )
    capabilities = sorted(set(permissions or []) | set(getattr(product_access, "permissions", []) or []))
    workspace = _resolve_workspace(
        role=role_name,
        permissions=capabilities,
        active_product=active_product,
    )
    return AccessProfile(
        persona=workspace.id,
        role=role_name,
        permissions=permissions or [],
        capabilities=capabilities,
        active_organization=active_organization,
        active_product=active_product,
        workspace=workspace,
    )


async def _user_response(
    session: AsyncSession,
    user: User,
    permissions: list[str] | None = None,
) -> UserResponse:
    permission_list = permissions if permissions is not None else (user.permissions or [])
    next_action = next_action_for_user(user)
    return UserResponse(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        is_verified=user.is_verified,
        status=normalize_status(user.status),
        credential_status=getattr(user, "credential_status", CREDENTIAL_PERMANENT) or CREDENTIAL_PERMANENT,
        role=user.role.name if user.role else "member",
        company_name=user.company_name,
        company_id=user.company_id,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        permissions=permission_list,
        access_profile=await _access_profile(session, user, permission_list),
        must_change_password=user.must_change_password,
        temporary_password_expires_at=getattr(user, "temporary_password_expires_at", None),
        next_action={
            "type": next_action.type,
            "route": next_action.route,
            "reason": next_action.reason,
        },
        created_at=user.created_at,
    )


def _build_tokens(user: User, raw_refresh: str, permissions: list[str] | None = None) -> TokenResponse:
    settings = get_settings()
    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={
            "role": user.role.name if user.role else "member",
            "status": normalize_status(user.status),
            "credential_status": getattr(user, "credential_status", CREDENTIAL_PERMANENT) or CREDENTIAL_PERMANENT,
            "permissions": permissions if permissions is not None else (user.permissions or []),
        },
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        token_type="bearer",
        expires_in=settings.jwt_access_expiry_minutes * 60,
    )


def _ensure_authenticatable_user(user: User, *, now: datetime | None = None) -> None:
    current_time = now or datetime.now(timezone.utc)
    status = str(user.status or "").upper()
    if user.deleted_at is not None or status == "DELETED":
        logger.warning("auth_blocked_deleted", email=user.email, user_id=str(user.id))
        raise ForbiddenException("Account is deleted. Please contact support.")

    if status not in AUTHENTICATABLE_STATUSES:
        logger.warning("auth_blocked_status", email=user.email, user_id=str(user.id), status=status)
        raise ForbiddenException(f"Account status {status} is not allowed to sign in.")

    if (
        getattr(user, "credential_status", CREDENTIAL_PERMANENT) == CREDENTIAL_TEMPORARY
        and is_temporary_password_expired(user, current_time)
    ):
        logger.warning("auth_blocked_temporary_password_expired", email=user.email, user_id=str(user.id))
        raise ForbiddenException("Temporary password has expired. Please contact your administrator.")

    if user.lock_until and user.lock_until > current_time:
        remaining = int((user.lock_until - current_time).total_seconds())
        raise ForbiddenException(
            f"Account locked. Try again in {remaining} seconds."
        )

    if not user.is_active:
        logger.warning("auth_blocked_inactive", email=user.email, user_id=str(user.id))
        raise ForbiddenException("Account is inactive. Please contact support.")

    if not user.is_verified:
        logger.warning("auth_blocked_unverified", email=user.email, user_id=str(user.id))
        raise ForbiddenException(
            "Account is not verified. Please contact your administrator."
        )


async def login(
    session: AsyncSession,
    email: str,
    password: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> LoginResponse:
    settings = get_settings()
    user_repo = UserRepository(session)
    refresh_repo = RefreshTokenRepository(session)
    audit_repo = AuditLogRepository(session)

    rate_key = f"login:{ip_address or 'unknown'}:{email}"
    if not await check_rate_limit(rate_key):
        raise AppException(message="Too many login attempts. Please try again later.", status_code=429)

    user = await user_repo.get_by_email(email)
    if user is None:
        await audit_repo.create("LOGIN_FAILED", ip_address=ip_address, user_agent=user_agent)
        raise UnauthorizedException("Invalid credentials")

    now = datetime.now(timezone.utc)
    if user.deleted_at is not None or str(user.status or "").upper() == "DELETED":
        logger.warning("login_blocked_deleted", email=email, user_id=str(user.id))
        await audit_repo.create(
            "LOGIN_BLOCKED_DELETED", user_id=user.id, ip_address=ip_address, user_agent=user_agent,
        )
        raise ForbiddenException("Account is deleted. Please contact support.")

    if (
        getattr(user, "credential_status", CREDENTIAL_PERMANENT) == CREDENTIAL_TEMPORARY
        and is_temporary_password_expired(user, now)
    ):
        previous_status = normalize_status(user.status)
        user.status = STATUS_EXPIRED
        user.is_active = False
        await user_repo.update(user)
        session.add(
            UserStatusHistory(
                user_id=user.id,
                previous_status=previous_status,
                new_status=STATUS_EXPIRED,
                reason="Temporary password expired before login",
            )
        )
        await audit_repo.create(
            "LOGIN_BLOCKED_TEMPORARY_PASSWORD_EXPIRED",
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        raise ForbiddenException("Temporary password has expired. Please contact your administrator.")

    if user.lock_until and user.lock_until > now:
        await audit_repo.create(
            "LOGIN_BLOCKED_LOCKED", user_id=user.id, ip_address=ip_address, user_agent=user_agent,
        )
        _ensure_authenticatable_user(user, now=now)

    if not user.is_active:
        await audit_repo.create(
            "LOGIN_BLOCKED_INACTIVE", user_id=user.id, ip_address=ip_address, user_agent=user_agent,
        )
        _ensure_authenticatable_user(user, now=now)

    if not password_service.verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.max_failed_login_attempts:
            user.lock_until = now + timedelta(minutes=settings.account_lock_minutes)
            await audit_repo.create(
                "ACCOUNT_LOCKED", user_id=user.id, ip_address=ip_address, user_agent=user_agent,
            )
            logger.warning("account_locked", user_id=str(user.id))
        await user_repo.update(user)
        await audit_repo.create(
            "LOGIN_FAILED", user_id=user.id, ip_address=ip_address, user_agent=user_agent,
        )
        raise UnauthorizedException("Invalid credentials")

    user.failed_login_attempts = 0
    user.lock_until = None
    user.last_login_at = now
    user.last_login = now
    previous_status = normalize_status(user.status)
    if previous_status == STATUS_INVITED:
        user.status = STATUS_FIRST_LOGIN
    await user_repo.update(user)
    if previous_status == STATUS_INVITED:
        session.add(
            UserStatusHistory(
                user_id=user.id,
                previous_status=previous_status,
                new_status=STATUS_FIRST_LOGIN,
                reason="First successful login with temporary password",
            )
        )
        await audit_repo.create(
            "ACCOUNT_FIRST_LOGIN",
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    # ── Enforce email verification ─────────────────────────────────
    if not user.is_verified:
        await audit_repo.create(
            "LOGIN_BLOCKED_UNVERIFIED", user_id=user.id, ip_address=ip_address, user_agent=user_agent,
        )
        _ensure_authenticatable_user(user, now=now)

    raw_refresh = generate_refresh_token()
    refresh_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(raw_refresh),
        expires_at=now + timedelta(days=settings.jwt_refresh_expiry_days),
    )
    await refresh_repo.create(refresh_record)
    await people_access_service.register_login_session(
        session,
        user,
        refresh_record.id,
        ip_address,
        user_agent,
    )

    await audit_repo.create(
        "LOGIN_SUCCESS", user_id=user.id, ip_address=ip_address, user_agent=user_agent,
    )

    permission_claims = await people_access_service.resolve_user_permissions(session, user)
    tokens = _build_tokens(user, raw_refresh, permission_claims)
    user_data = await _user_response(session, user, permission_claims)

    logger.info("user_logged_in", user_id=str(user.id))
    return LoginResponse(tokens=tokens, user=user_data)


async def refresh(
    session: AsyncSession,
    raw_token: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> TokenResponse:
    settings = get_settings()
    refresh_repo = RefreshTokenRepository(session)
    user_repo = UserRepository(session)
    audit_repo = AuditLogRepository(session)

    token_record = await refresh_repo.get_valid_by_hash(hash_token(raw_token))
    if token_record is None:
        raise UnauthorizedException("Invalid or expired refresh token")

    await refresh_repo.revoke(token_record.id)

    user = await user_repo.get_by_id(token_record.user_id)
    if user is None:
        raise UnauthorizedException("User not found")

    now = datetime.now(timezone.utc)
    if user.deleted_at is not None or str(user.status or "").upper() == "DELETED":
        await audit_repo.create(
            "TOKEN_REFRESH_BLOCKED_DELETED",
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        _ensure_authenticatable_user(user, now=now)

    if user.lock_until and user.lock_until > now:
        await audit_repo.create(
            "TOKEN_REFRESH_BLOCKED_LOCKED",
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        _ensure_authenticatable_user(user, now=now)

    if not user.is_active:
        await audit_repo.create(
            "TOKEN_REFRESH_BLOCKED_INACTIVE",
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        _ensure_authenticatable_user(user, now=now)

    if not user.is_verified:
        await audit_repo.create(
            "TOKEN_REFRESH_BLOCKED_UNVERIFIED",
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        _ensure_authenticatable_user(user, now=now)

    new_raw = generate_refresh_token()
    new_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(new_raw),
        expires_at=now + timedelta(days=settings.jwt_refresh_expiry_days),
    )
    await refresh_repo.create(new_record)
    await people_access_service.refresh_login_session(
        session,
        user,
        token_record.id,
        new_record.id,
        ip_address,
        user_agent,
    )

    await audit_repo.create(
        "TOKEN_REFRESH", user_id=user.id, ip_address=ip_address, user_agent=user_agent,
    )

    permissions = await people_access_service.resolve_user_permissions(session, user)
    return _build_tokens(user, new_raw, permissions)


async def logout(
    session: AsyncSession,
    raw_token: str,
    user_id: uuid.UUID | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> dict:
    refresh_repo = RefreshTokenRepository(session)
    audit_repo = AuditLogRepository(session)

    token_hash = hash_token(raw_token)
    token_record = await refresh_repo.get_valid_by_hash(token_hash)
    await refresh_repo.revoke_by_hash(token_hash)
    if token_record is not None:
        await people_access_service.revoke_login_session(session, token_record.id)

    await audit_repo.create(
        "LOGOUT", user_id=user_id, ip_address=ip_address, user_agent=user_agent,
    )

    return {"message": "Logged out successfully"}


async def _recent_password_hashes(session: AsyncSession, user_id: uuid.UUID, limit: int = 5) -> list[str]:
    result = await session.execute(
        select(PasswordHistory.password_hash)
        .where(PasswordHistory.user_id == user_id)
        .order_by(PasswordHistory.created_at.desc())
        .limit(limit)
    )
    return [value for value in result.scalars().all()]


async def change_password(
    session: AsyncSession,
    user_id: uuid.UUID,
    current_password: str,
    new_password: str,
    confirm_password: str,
    *,
    temporary_only: bool = False,
    issue_new_session: bool = False,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> dict | LoginResponse:
    settings = get_settings()
    user_repo = UserRepository(session)
    refresh_repo = RefreshTokenRepository(session)
    audit_repo = AuditLogRepository(session)
    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise NotFoundException("User not found")

    _ensure_authenticatable_user(user)
    current_status = normalize_status(user.status)
    if temporary_only and not user.must_change_password and current_status not in {
        STATUS_APPROVED,
        STATUS_PASSWORD_CHANGE_REQUIRED,
    }:
        raise ConflictException("Temporary password change is not required for this account")

    if not password_service.verify_password(current_password, user.password_hash):
        await audit_repo.create(
            "PASSWORD_CHANGE_FAILED",
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        raise UnauthorizedException("Current password is incorrect")

    if new_password != confirm_password:
        await audit_repo.create(
            "PASSWORD_VALIDATION_FAILED",
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        raise WeakPasswordException(["password and confirmation must match"])

    previous_hashes = [user.password_hash, *(await _recent_password_hashes(session, user.id, limit=5))]
    try:
        password_service.validate_new_password(new_password)
        password_service.ensure_not_reused(new_password, previous_hashes)
    except WeakPasswordException:
        await audit_repo.create(
            "PASSWORD_VALIDATION_FAILED",
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        raise

    new_hash = password_service.hash_password(new_password)
    now = datetime.now(timezone.utc)
    user.password_hash = new_hash
    user.password_changed_at = now
    user.must_change_password = False
    user.credential_status = CREDENTIAL_PERMANENT
    user.temporary_password_consumed_at = now
    user.temporary_password_expires_at = None
    user.failed_login_attempts = 0
    user.lock_until = None
    if temporary_only and current_status in {
        STATUS_FIRST_LOGIN,
        STATUS_APPROVED,
        STATUS_PASSWORD_CHANGE_REQUIRED,
    }:
        user.status = STATUS_ACTIVE
    await user_repo.update(user)
    session.add(
        PasswordHistory(
            user_id=user.id,
            password_hash=new_hash,
            source="temporary_password_change" if temporary_only else "profile_password_change",
        )
    )
    await session.flush()

    audit_event = "USER_CHANGED_TEMPORARY_PASSWORD" if temporary_only else "PASSWORD_CHANGED"
    await audit_repo.create(
        audit_event,
        user_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    if not issue_new_session:
        return {"message": "Password changed successfully", "must_change_password": False}

    raw_refresh = generate_refresh_token()
    refresh_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(raw_refresh),
        expires_at=now + timedelta(days=settings.jwt_refresh_expiry_days),
    )
    await refresh_repo.create(refresh_record)
    await people_access_service.register_login_session(
        session,
        user,
        refresh_record.id,
        ip_address,
        user_agent,
    )
    permissions = await people_access_service.resolve_user_permissions(session, user)
    return LoginResponse(
        tokens=_build_tokens(user, raw_refresh, permissions),
        user=await _user_response(session, user, permissions),
    )


async def get_current_user(session: AsyncSession, user_id: uuid.UUID) -> UserResponse:
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise NotFoundException("User not found")
    _ensure_authenticatable_user(user)
    permissions = await people_access_service.resolve_user_permissions(session, user)
    return await _user_response(session, user, permissions)


async def list_roles(session: AsyncSession) -> list[RoleResponse]:
    role_repo = RoleRepository(session)
    roles = await role_repo.get_all()
    return [
        RoleResponse(id=r.id, name=r.name, description=r.description)
        for r in roles
    ]
