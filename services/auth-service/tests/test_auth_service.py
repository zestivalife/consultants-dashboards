import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException, UnauthorizedException
from app.core.password_policy import WeakPasswordException
from app.core.security import hash_password, verify_password
from app.db.models.audit_log import AuthAuditLog
from app.db.models.refresh_token import RefreshToken
from app.db.models.role import Role
from app.db.models.user import User
from app.services import auth_service

RATE_LIMIT_PATCH = "app.services.auth_service.check_rate_limit"
STORE_OTP_PATCH = "app.services.auth_service.store_otp"
SEND_OTP_PATCH = "app.services.auth_service.get_email_service"


def _always_allow_rate():
    return patch(RATE_LIMIT_PATCH, new_callable=AsyncMock, return_value=True)


def _mock_email():
    return patch(SEND_OTP_PATCH)


async def _create_role_user(
    session: AsyncSession,
    role_name: str,
    *,
    email: str | None = None,
    password: str = "Correct123!",
    is_active: bool = True,
    is_verified: bool = True,
    status: str = "ACTIVE",
    lock_until=None,
    deleted_at=None,
) -> User:
    role = Role(id=uuid.uuid4(), name=role_name, description=f"{role_name} role")
    user = User(
        id=uuid.uuid4(),
        email=email or f"{role_name}@nuetra.test",
        password_hash=hash_password(password),
        role_id=role.id,
        is_active=is_active,
        is_verified=is_verified,
        status=status,
        lock_until=lock_until,
        deleted_at=deleted_at,
    )
    session.add(role)
    await session.flush()
    session.add(user)
    await session.flush()
    return user


# ──────────────────────────────────────────────
#  Login Success
# ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_success(session: AsyncSession, seed_user: User):
    with _always_allow_rate():
        result = await auth_service.login(session, "test@nuetra.com", "Correct123!")
    assert result.tokens.access_token
    assert result.tokens.refresh_token
    assert result.tokens.token_type == "bearer"
    assert result.user.email == "test@nuetra.com"


# ──────────────────────────────────────────────
#  Login Failure — wrong password
# ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_wrong_password(session: AsyncSession, seed_user: User):
    with _always_allow_rate():
        with pytest.raises(UnauthorizedException, match="Invalid credentials"):
            await auth_service.login(session, "test@nuetra.com", "WrongPassword!")


# ──────────────────────────────────────────────
#  Login Failure — account lockout after 5 attempts
# ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_lockout(session: AsyncSession, seed_role: Role):
    user = User(
        id=uuid.uuid4(),
        email="lockout@nuetra.com",
        password_hash=hash_password("GoodPass1!"),
        role_id=seed_role.id,
        is_verified=True,
    )
    session.add(user)
    await session.flush()

    with _always_allow_rate():
        for _ in range(5):
            with pytest.raises(UnauthorizedException):
                await auth_service.login(session, "lockout@nuetra.com", "BadPass!")

        with pytest.raises(ForbiddenException, match="Account locked"):
            await auth_service.login(session, "lockout@nuetra.com", "GoodPass1!")


# ──────────────────────────────────────────────
#  Token Refresh
# ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_refresh_token(session: AsyncSession, seed_user: User):
    with _always_allow_rate():
        login_result = await auth_service.login(session, "test@nuetra.com", "Correct123!")
    raw_refresh = login_result.tokens.refresh_token

    new_tokens = await auth_service.refresh(session, raw_refresh)
    assert new_tokens.access_token
    assert new_tokens.refresh_token
    assert new_tokens.refresh_token != raw_refresh

    with pytest.raises(UnauthorizedException, match="Invalid or expired refresh token"):
        await auth_service.refresh(session, raw_refresh)


# ──────────────────────────────────────────────
#  Role-neutral auth lifecycle
# ──────────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "role_name",
    [
        "platform_owner",
        "organization_admin",
        "practitioner",
        "mentor",
        "consultant",
        "corporate_admin",
        "team_member",
        "future_role",
    ],
)
async def test_auth_lifecycle_is_identical_for_every_role(session: AsyncSession, role_name: str):
    user = await _create_role_user(
        session,
        role_name,
        email=f"{role_name}@zestiva.test",
    )

    with _always_allow_rate():
        login_result = await auth_service.login(
            session,
            user.email,
            "Correct123!",
            ip_address="127.0.0.1",
            user_agent="pytest role lifecycle",
        )

    assert login_result.user.email == user.email
    assert login_result.user.role == role_name
    assert login_result.tokens.access_token
    assert login_result.tokens.refresh_token

    restored_user = await auth_service.get_current_user(session, user.id)
    assert restored_user.email == user.email
    assert restored_user.role == role_name

    first_refresh = login_result.tokens.refresh_token
    second_tokens = await auth_service.refresh(
        session,
        first_refresh,
        ip_address="127.0.0.1",
        user_agent="pytest role lifecycle",
    )
    assert second_tokens.access_token
    assert second_tokens.refresh_token != first_refresh

    with pytest.raises(UnauthorizedException, match="Invalid or expired refresh token"):
        await auth_service.refresh(session, first_refresh)

    await auth_service.logout(
        session,
        second_tokens.refresh_token,
        user_id=user.id,
        ip_address="127.0.0.1",
        user_agent="pytest role lifecycle",
    )
    with pytest.raises(UnauthorizedException, match="Invalid or expired refresh token"):
        await auth_service.refresh(session, second_tokens.refresh_token)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("state_name", "user_kwargs", "expected_message"),
    [
        ("inactive", {"is_active": False}, "Account is inactive"),
        ("unverified", {"is_verified": False}, "Email not verified"),
        (
            "locked",
            {"lock_until": datetime.now(timezone.utc) + timedelta(minutes=10)},
            "Account locked",
        ),
        (
            "deleted_status",
            {"status": "DELETED"},
            "Account is deleted",
        ),
        (
            "deleted_timestamp",
            {"deleted_at": datetime.now(timezone.utc)},
            "Account is deleted",
        ),
    ],
)
async def test_login_rejects_non_authenticatable_users(
    session: AsyncSession,
    state_name: str,
    user_kwargs: dict,
    expected_message: str,
):
    user = await _create_role_user(
        session,
        f"{state_name}_role",
        email=f"{state_name}@zestiva.test",
        **user_kwargs,
    )

    with _always_allow_rate():
        with pytest.raises(ForbiddenException, match=expected_message):
            await auth_service.login(session, user.email, "Correct123!")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("state_name", "mutate", "expected_message"),
    [
        ("inactive", lambda user: setattr(user, "is_active", False), "Account is inactive"),
        ("unverified", lambda user: setattr(user, "is_verified", False), "Email not verified"),
        (
            "locked",
            lambda user: setattr(user, "lock_until", datetime.now(timezone.utc) + timedelta(minutes=10)),
            "Account locked",
        ),
        ("deleted_status", lambda user: setattr(user, "status", "DELETED"), "Account is deleted"),
        (
            "deleted_timestamp",
            lambda user: setattr(user, "deleted_at", datetime.now(timezone.utc)),
            "Account is deleted",
        ),
    ],
)
async def test_existing_sessions_are_rejected_after_account_state_changes(
    session: AsyncSession,
    state_name: str,
    mutate,
    expected_message: str,
):
    user = await _create_role_user(
        session,
        f"{state_name}_session_role",
        email=f"{state_name}.session@zestiva.test",
    )
    with _always_allow_rate():
        login_result = await auth_service.login(session, user.email, "Correct123!")

    mutate(user)
    await session.flush()

    with pytest.raises(ForbiddenException, match=expected_message):
        await auth_service.get_current_user(session, user.id)

    with pytest.raises(ForbiddenException, match=expected_message):
        await auth_service.refresh(session, login_result.tokens.refresh_token)


@pytest.mark.asyncio
async def test_get_current_user_rejects_missing_user(session: AsyncSession):
    with pytest.raises(NotFoundException, match="User not found"):
        await auth_service.get_current_user(session, uuid.uuid4())


# ──────────────────────────────────────────────
#  Register — duplicate email
# ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_duplicate_email(session: AsyncSession, seed_user: User):
    with patch(STORE_OTP_PATCH, new_callable=AsyncMock), _mock_email():
        with pytest.raises(ConflictException, match="already exists"):
            await auth_service.register(session, "test@nuetra.com", "AnyPass123!")


# ──────────────────────────────────────────────
#  Register — success
# ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_success(session: AsyncSession, seed_role: Role):
    with patch(STORE_OTP_PATCH, new_callable=AsyncMock) as mock_otp, _mock_email():
        result = await auth_service.register(session, "new@nuetra.com", "StrongP4ss")
        assert "user_id" in result
        mock_otp.assert_awaited_once()

    stmt = select(AuthAuditLog).where(AuthAuditLog.event_type == "USER_REGISTERED")
    rows = (await session.execute(stmt)).scalars().all()
    assert rows


# ──────────────────────────────────────────────
#  Password Policy
# ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_weak_password_no_uppercase(session: AsyncSession, seed_role: Role):
    with patch(STORE_OTP_PATCH, new_callable=AsyncMock), _mock_email():
        with pytest.raises(WeakPasswordException, match="uppercase"):
            await auth_service.register(session, "weak1@nuetra.com", "alllower1")


@pytest.mark.asyncio
async def test_register_weak_password_no_digit(session: AsyncSession, seed_role: Role):
    with patch(STORE_OTP_PATCH, new_callable=AsyncMock), _mock_email():
        with pytest.raises(WeakPasswordException, match="digit"):
            await auth_service.register(session, "weak2@nuetra.com", "NoDigitHere")


@pytest.mark.asyncio
async def test_register_weak_password_too_short(session: AsyncSession, seed_role: Role):
    with patch(STORE_OTP_PATCH, new_callable=AsyncMock), _mock_email():
        with pytest.raises(WeakPasswordException, match="8 characters"):
            await auth_service.register(session, "weak3@nuetra.com", "Ab1")


# ──────────────────────────────────────────────
#  Audit log entries created on login
# ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_creates_audit_log(session: AsyncSession, seed_user: User):
    with _always_allow_rate():
        await auth_service.login(
            session, "test@nuetra.com", "Correct123!",
            ip_address="127.0.0.1", user_agent="pytest",
        )

    stmt = select(AuthAuditLog).where(AuthAuditLog.event_type == "LOGIN_SUCCESS")
    result = await session.execute(stmt)
    logs = result.scalars().all()
    assert len(logs) >= 1
    assert logs[-1].ip_address == "127.0.0.1"


@pytest.mark.asyncio
async def test_refresh_token_rotation_updates_login_session(session: AsyncSession, seed_user: User):
    from app.db.models.owner_access import LoginSession

    with _always_allow_rate():
        login_result = await auth_service.login(
            session,
            "test@nuetra.com",
            "Correct123!",
            ip_address="127.0.0.1",
            user_agent="pytest/browser",
        )

    initial_sessions = (
        await session.execute(select(LoginSession).where(LoginSession.user_id == seed_user.id))
    ).scalars().all()
    assert len(initial_sessions) == 1
    assert initial_sessions[0].status == "ACTIVE"

    await auth_service.refresh(
        session,
        login_result.tokens.refresh_token,
        ip_address="127.0.0.1",
        user_agent="pytest/browser",
    )

    sessions = (
        await session.execute(select(LoginSession).where(LoginSession.user_id == seed_user.id))
    ).scalars().all()
    assert {item.status for item in sessions} == {"ACTIVE", "REVOKED"}


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token_and_login_session(session: AsyncSession, seed_user: User):
    from app.db.models.owner_access import LoginSession

    with _always_allow_rate():
        login_result = await auth_service.login(session, "test@nuetra.com", "Correct123!")

    await auth_service.logout(session, login_result.tokens.refresh_token, user_id=seed_user.id)

    refresh_tokens = (
        await session.execute(select(RefreshToken).where(RefreshToken.user_id == seed_user.id))
    ).scalars().all()
    assert refresh_tokens
    assert all(token.revoked_at is not None for token in refresh_tokens)

    sessions = (
        await session.execute(select(LoginSession).where(LoginSession.user_id == seed_user.id))
    ).scalars().all()
    assert sessions
    assert all(item.status == "REVOKED" for item in sessions)


def test_password_hashing_has_single_production_implementation():
    service_root = Path(__file__).resolve().parents[1]
    allowed = {service_root / "app" / "core" / "security.py"}
    offenders = []
    for path in [*service_root.joinpath("app").rglob("*.py"), *service_root.joinpath("alembic").rglob("*.py")]:
        if path in allowed:
            continue
        text = path.read_text()
        if "import bcrypt" in text or "bcrypt.hashpw" in text or "DEFAULT_PASSWORD_HASH" in text:
            offenders.append(str(path.relative_to(service_root)))

    assert offenders == []


def test_shared_password_hash_verifies_admin_and_seeded_passwords():
    assert verify_password("PeopleAccess@123", hash_password("PeopleAccess@123"))
    assert verify_password("Temporary123!", hash_password("Temporary123!"))
