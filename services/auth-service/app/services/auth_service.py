import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.email import get_email_service
from app.core.exceptions import (
    AppException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
)
from app.core.logging import get_logger
from app.core.otp import generate_otp, store_otp, verify_and_delete_otp
from app.core.password_policy import validate_password
from app.core.rate_limit import check_rate_limit
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.db.models.otp_verification import OTPVerification
from app.db.models.refresh_token import RefreshToken
from app.db.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginResponse, RoleResponse, TokenResponse, UserResponse
from app.services import people_access_service

logger = get_logger(__name__)


# ── background task helpers ───────────────────────────

def _send_otp_email_background(email: str, otp_code: str) -> None:
    """Send OTP email (background task). Never raises exceptions."""
    try:
        get_email_service().send_otp(email, otp_code)
        logger.info("otp_email_sent_background", email=email)
    except Exception as exc:
        logger.error(
            "otp_email_failed_background",
            email=email,
            error=str(exc),
            note="Email sending failed but API response continues",
        )
        # ERROR: Never re-raise from background tasks - API should not fail


def _send_invitation_email_background(email: str, temp_password: str, role: str) -> None:
    """Send invitation email (background task). Never raises exceptions."""
    try:
        get_email_service().send_invitation(email, temp_password, role)
        logger.info("invitation_email_sent_background", email=email, role=role)
    except Exception as exc:
        logger.error(
            "invitation_email_failed_background",
            email=email,
            error=str(exc),
            note="Email sending failed but API response continues",
        )
        # ERROR: Never re-raise from background tasks - API should not fail


# ── helpers ───────────────────────────────────────────

def _user_response(user: User, permissions: list[str] | None = None) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        is_verified=user.is_verified,
        role=user.role.name if user.role else "member",
        company_name=user.company_name,
        company_id=user.company_id,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        permissions=permissions if permissions is not None else (user.permissions or []),
        created_at=user.created_at,
    )


def _build_tokens(user: User, raw_refresh: str, permissions: list[str] | None = None) -> TokenResponse:
    settings = get_settings()
    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={
            "role": user.role.name if user.role else "member",
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
            "Email not verified. Please check your inbox for the OTP and verify your email first."
        )


# ── public API ────────────────────────────────────────

async def register(
    session: AsyncSession,
    email: str,
    password: str,
    role_name: str | None = None,
    company_name: str | None = None,
    location: str | None = None,
    employees: int | None = None,
    industry: str | None = None,
) -> dict:
    validate_password(password)

    user_repo = UserRepository(session)
    role_repo = RoleRepository(session)
    audit_repo = AuditLogRepository(session)

    existing = await user_repo.get_by_email(email)
    if existing:
        raise ConflictException("A user with this email already exists")

    assigned_role_name = role_name if role_name else "member"
    role = await role_repo.get_by_name(assigned_role_name)
    if role is None:
        raise NotFoundException(f"Role '{assigned_role_name}' not found. Run migrations first.")

    user = User(
        email=email,
        password_hash=hash_password(password),
        role_id=role.id,
        company_name=company_name,
        location=location,
        employees=employees,
        industry=industry,
    )
    await user_repo.create(user)

    otp_code = generate_otp()
    await store_otp(email, otp_code)

    settings = get_settings()
    # Always log OTP — visible in `docker compose logs auth-service`
    # In production, remove this line and ensure SMTP is configured.
    logger.info(
        "OTP_FOR_VERIFICATION",
        email=email,
        otp=otp_code,
        note="DEV ONLY — remove in production",
    )
    if settings.app_env == "development":
        print(f"\n{'='*60}\n[DEV] OTP for {email}: {otp_code}\n{'='*60}\n", flush=True)

    otp_record = OTPVerification(user_id=user.id, purpose="email_verification")
    session.add(otp_record)
    await session.flush()
    await audit_repo.create("USER_REGISTERED", user_id=user.id)

    # Note: Email will be sent in background. API returns success regardless of email status
    # This prevents 504 timeouts due to SMTP/SendGrid delays

    logger.info("user_registered", user_id=str(user.id), email=email)

    return {
        "user_id": str(user.id),
        "otp_code": otp_code,
        "message": "Registration successful. Please verify your email with the OTP sent.",
        "email_sending": "background",
    }


async def verify_otp_action(session: AsyncSession, email: str, otp: str) -> dict:
    user_repo = UserRepository(session)

    user = await user_repo.get_by_email(email)
    if user is None:
        raise NotFoundException("User not found")

    if user.is_verified:
        return {"message": "Email already verified"}

    valid = await verify_and_delete_otp(email, otp)
    if not valid:
        raise UnauthorizedException("Invalid or expired OTP")

    user.is_verified = True
    await user_repo.update(user)

    logger.info("user_verified", user_id=str(user.id))
    return {"message": "Email verified successfully"}


async def resend_otp(session: AsyncSession, email: str) -> dict:
    user_repo = UserRepository(session)

    user = await user_repo.get_by_email(email)
    if user is None:
        raise NotFoundException("User not found")

    if user.is_verified:
        return {"message": "Email already verified. Please login."}

    otp_code = generate_otp()
    await store_otp(email, otp_code)

    settings = get_settings()
    logger.info("OTP_RESENT", email=email, otp=otp_code, note="DEV ONLY — remove in production")
    if settings.app_env == "development":
        print(f"\n{'='*60}\n[DEV] RESENT OTP for {email}: {otp_code}\n{'='*60}\n", flush=True)

    # Note: Email will be sent in background. API returns success regardless of email status
    # This prevents 504 timeouts due to SMTP/SendGrid delays

    return {"message": "OTP resent. Please check your email.", "otp_code": otp_code}


async def forgot_password(session: AsyncSession, email: str) -> dict:
    """Generate an OTP for password reset. Public endpoint."""
    user_repo = UserRepository(session)

    user = await user_repo.get_by_email(email)
    if user is None:
        # For security: don't reveal if email exists
        return {"message": "If this email exists, you will receive an OTP to reset your password.", "otp_code": None}

    otp_code = generate_otp()
    await store_otp(email, otp_code)

    settings = get_settings()
    logger.info("password_reset_otp_generated", email=email, otp=otp_code)
    if settings.app_env == "development":
        print(f"\n{'='*60}\n[DEV] PASSWORD RESET OTP for {email}: {otp_code}\n{'='*60}\n", flush=True)

    return {"message": "OTP sent to your email for password reset.", "otp_code": otp_code}


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

    if not verify_password(password, user.password_hash):
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
    await user_repo.update(user)

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
    user_data = _user_response(user, permission_claims)

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


async def get_current_user(session: AsyncSession, user_id: uuid.UUID) -> UserResponse:
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise NotFoundException("User not found")
    _ensure_authenticatable_user(user)
    permissions = await people_access_service.resolve_user_permissions(session, user)
    return _user_response(user, permissions)


async def list_roles(session: AsyncSession) -> list[RoleResponse]:
    role_repo = RoleRepository(session)
    roles = await role_repo.get_all()
    return [
        RoleResponse(id=r.id, name=r.name, description=r.description)
        for r in roles
    ]
