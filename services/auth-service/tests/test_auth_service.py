import uuid
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, ForbiddenException, UnauthorizedException
from app.core.password_policy import WeakPasswordException
from app.core.security import hash_password
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
    from app.db.models.audit_log import AuthAuditLog
    from sqlalchemy import select

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
