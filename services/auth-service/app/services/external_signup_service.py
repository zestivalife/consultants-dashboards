import asyncio
import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import httpx
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.email import get_email_service
from app.core.exceptions import AppException, ConflictException
from app.core.rate_limit import check_rate_limit
from app.db.models.external_signup import ExternalSignupChallenge, ExternalSignupProvisioning
from app.db.models.role import Role
from app.db.models.user import User
from app.services.password_service import password_service


def canonical_email(value: str) -> str:
    return value.strip().lower()


def _otp_digest(challenge_id: uuid.UUID, code: str) -> str:
    secret = get_settings().jwt_secret_key.encode("utf-8")
    return hmac.new(secret, f"{challenge_id}:{code}".encode("utf-8"), hashlib.sha256).hexdigest()


def _new_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


async def _send_code(email: str, code: str) -> None:
    html = f"<p>Your Fiteatsy Consultant verification code is <strong>{code}</strong>.</p><p>It expires in 5 minutes. If you did not request this, ignore this email.</p>"
    await asyncio.to_thread(get_email_service().send, email, "Verify your Fiteatsy Consultant account", html)


async def start(session: AsyncSession, email: str, ip_address: str | None = None) -> dict:
    normalized = canonical_email(email)
    if not await check_rate_limit(f"external-signup-start:{ip_address or 'unknown'}:{normalized}"):
        raise AppException("Too many verification requests. Please try again later.", 429)
    now = datetime.now(timezone.utc)
    challenge_id = uuid.uuid4()
    code = _new_code()
    challenge = ExternalSignupChallenge(
        id=challenge_id,
        email_normalized=normalized,
        otp_hash=_otp_digest(challenge_id, code),
        status="PENDING",
        attempt_count=0,
        resend_count=0,
        expires_at=now + timedelta(seconds=get_settings().external_signup_otp_ttl_seconds),
        last_sent_at=now,
    )
    session.add(challenge)
    await session.flush()
    await _send_code(normalized, code)
    return {"challenge_id": challenge.id, "state": "VERIFICATION_PENDING", "expires_in": get_settings().external_signup_otp_ttl_seconds}


async def resend(session: AsyncSession, challenge_id: uuid.UUID, ip_address: str | None = None) -> dict:
    challenge = (await session.execute(select(ExternalSignupChallenge).where(ExternalSignupChallenge.id == challenge_id).with_for_update())).scalar_one_or_none()
    if challenge is None or challenge.status != "PENDING":
        raise AppException("Verification cannot be resent.", 409)
    now = datetime.now(timezone.utc)
    settings = get_settings()
    if (now - challenge.last_sent_at).total_seconds() < settings.external_signup_resend_cooldown_seconds:
        raise AppException("Please wait before requesting another code.", 429)
    if challenge.resend_count >= settings.external_signup_max_resends:
        challenge.status = "BLOCKED"
        await session.commit()
        raise AppException("Verification resend limit reached.", 429)
    if not await check_rate_limit(f"external-signup-resend:{ip_address or 'unknown'}:{challenge.email_normalized}"):
        raise AppException("Too many verification requests. Please try again later.", 429)
    code = _new_code()
    challenge.otp_hash = _otp_digest(challenge.id, code)
    challenge.resend_count += 1
    challenge.attempt_count = 0
    challenge.last_sent_at = now
    challenge.expires_at = now + timedelta(seconds=settings.external_signup_otp_ttl_seconds)
    await session.flush()
    await _send_code(challenge.email_normalized, code)
    return {"challenge_id": challenge.id, "state": "VERIFICATION_PENDING", "expires_in": settings.external_signup_otp_ttl_seconds}


def _delegation_token(subject: uuid.UUID) -> str:
    settings = get_settings()
    if not settings.fiteatsy_delegation_private_key:
        raise AppException("External signup provisioning is not configured.", 503)
    now = datetime.now(timezone.utc)
    payload = {
        "iss": settings.fiteatsy_delegation_issuer,
        "sub": str(subject),
        "aud": settings.fiteatsy_delegation_audience,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=60)).timestamp()),
        "jti": str(uuid.uuid4()),
        "product": "fiteatsy",
        "permissions": ["fiteatsy.external.signup.provision"],
        "purpose": "external_consultant_signup",
        "actor_type": "consultant_auth_service",
    }
    return jwt.encode(payload, settings.fiteatsy_delegation_private_key.replace("\\n", "\n"), algorithm="RS256", headers={"typ": "Zestiva-Delegated-Authority", "kid": settings.fiteatsy_delegation_key_id})


async def _provision_fiteatsy(user: User, body: dict, idempotency_key: str) -> dict:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            f"{settings.fiteatsy_backend_url.rstrip('/')}/v1/admin/delegated/external-consultant-signups/provision",
            headers={"x-zestiva-delegation": _delegation_token(user.id), "idempotency-key": idempotency_key},
            json=body,
        )
    if response.status_code not in (200, 201):
        raise AppException("Workspace provisioning is temporarily unavailable. Retry safely.", 503)
    return response.json()


async def verify_and_provision(session: AsyncSession, *, challenge_id: uuid.UUID, code: str, password: str, name: str, account_type: str, professional_title: str | None, speciality: str | None, practice_name: str | None) -> dict:
    challenge = (await session.execute(select(ExternalSignupChallenge).where(ExternalSignupChallenge.id == challenge_id).with_for_update())).scalar_one_or_none()
    if challenge is None:
        raise AppException("Verification is invalid or expired.", 400)
    existing_provisioning = (await session.execute(select(ExternalSignupProvisioning).where(ExternalSignupProvisioning.challenge_id == challenge.id))).scalar_one_or_none()
    if challenge.status == "CONSUMED" and existing_provisioning:
        return {"state": existing_provisioning.status, "tenant_id": existing_provisioning.tenant_id, "onboarding_id": existing_provisioning.onboarding_id, "workspace_ready": existing_provisioning.status == "READY"}
    now = datetime.now(timezone.utc)
    if challenge.status not in {"PENDING", "VERIFIED"} or (challenge.status == "PENDING" and challenge.expires_at <= now):
        challenge.status = "EXPIRED" if challenge.status == "PENDING" and challenge.expires_at <= now else challenge.status
        await session.commit()
        raise AppException("Verification is invalid or expired.", 400)
    if challenge.status == "PENDING" and challenge.attempt_count >= get_settings().external_signup_max_attempts:
        challenge.status = "BLOCKED"
        await session.commit()
        raise AppException("Verification attempt limit reached.", 429)
    if challenge.status == "PENDING" and not hmac.compare_digest(challenge.otp_hash, _otp_digest(challenge.id, code)):
        challenge.attempt_count += 1
        if challenge.attempt_count >= get_settings().external_signup_max_attempts:
            challenge.status = "BLOCKED"
        await session.commit()
        raise AppException("Verification code is incorrect.", 400)

    if existing_provisioning is None:
        existing_user = (await session.execute(select(User).where(User.email == challenge.email_normalized))).scalar_one_or_none()
        if existing_user is not None:
            raise ConflictException("An account already exists for this verified identity.")
        role = (await session.execute(select(Role).where(Role.name == "consultant"))).scalar_one_or_none()
        if role is None:
            raise AppException("Consultant role is not configured.", 503)
        password_service.validate_new_password(password)
        user = User(
            email=challenge.email_normalized,
            password_hash=password_service.hash_password(password),
            role_id=role.id,
            first_name=name.strip(),
            is_active=True,
            is_verified=True,
            email_verified=True,
            status="ACTIVE",
        )
        session.add(user)
        await session.flush()
        idempotency_key = f"external-signup:{challenge.id}"
        provisioning = ExternalSignupProvisioning(challenge_id=challenge.id, auth_user_id=user.id, account_type=account_type, idempotency_key=idempotency_key)
        session.add(provisioning)
        challenge.status = "VERIFIED"
        await session.commit()
    else:
        provisioning = existing_provisioning
        user = (await session.execute(select(User).where(User.id == provisioning.auth_user_id))).scalar_one()

    try:
        result = await _provision_fiteatsy(user, {
            "authIdentityId": str(user.id),
            "name": name.strip(),
            "email": challenge.email_normalized,
            "accountType": account_type,
            "professionalTitle": professional_title,
            "speciality": speciality,
            "practiceName": practice_name,
        }, provisioning.idempotency_key)
    except AppException:
        provisioning.status = "PROVISIONING_RETRY"
        provisioning.last_error_code = "FITEATSY_PROVISIONING_UNAVAILABLE"
        provisioning.last_error_detail = "Retryable downstream provisioning failure"
        await session.commit()
        raise
    provisioning.status = result["state"]
    provisioning.fiteatsy_user_id = result.get("userId")
    provisioning.tenant_id = result.get("tenantId")
    provisioning.owner_membership_id = result.get("ownerMembershipId")
    provisioning.onboarding_id = result.get("onboardingId")
    challenge.status = "CONSUMED"
    challenge.consumed_at = now
    await session.commit()
    return {"state": provisioning.status, "tenant_id": provisioning.tenant_id, "onboarding_id": provisioning.onboarding_id, "workspace_ready": result.get("workspaceReady", False)}
