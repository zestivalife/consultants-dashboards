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
from app.core.exceptions import AppException, ConflictException
from app.core.mobile_identity import canonical_mobile
from app.core.mobile_otp import send_mobile_otp
from app.core.rate_limit import check_rate_limit
from app.db.models.external_signup import ExternalSignupChallenge, ExternalSignupProvisioning
from app.db.models.role import Role
from app.db.models.user import User
from app.services import auth_service
from app.services.password_service import password_service
from app.schemas.auth import ExternalConsultantRegisterRequest


def _otp_digest(challenge_id: uuid.UUID, code: str) -> str:
    secret = get_settings().jwt_secret_key.encode()
    return hmac.new(secret, f"{challenge_id}:{code}".encode(), hashlib.sha256).hexdigest()


def _new_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _identity_email(mobile: str, supplied: str | None) -> str:
    return supplied.strip().lower() if supplied else f"mobile-{mobile.removeprefix('+')}@identity.invalid"


async def register_without_verification(
    session: AsyncSession, *, body: ExternalConsultantRegisterRequest,
    ip_address: str | None = None, user_agent: str | None = None,
) -> dict:
    mobile = canonical_mobile(body.mobile_number)
    email = str(body.email).strip().lower()
    if not await check_rate_limit(f"external-signup-register:{ip_address or 'unknown'}:{mobile}"):
        raise AppException("Too many registration requests. Please try again later.", 429)
    existing_mobile = (await session.execute(select(User).where(User.mobile == mobile))).scalar_one_or_none()
    existing_email = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
    existing_user = existing_mobile or existing_email
    if existing_mobile and existing_email and existing_mobile.id != existing_email.id:
        raise ConflictException("An account already exists. Sign in to continue.")
    if existing_user:
        provisioning = (await session.execute(
            select(ExternalSignupProvisioning).where(ExternalSignupProvisioning.auth_user_id == existing_user.id)
        )).scalar_one_or_none()
        resumable = (
            provisioning is not None
            and provisioning.status in {"REGISTRATION_ACCEPTED", "PROVISIONING_RETRY"}
            and not existing_user.is_verified
            and existing_user.mobile == mobile
            and existing_user.email == email
        )
        if not resumable:
            raise ConflictException("An account already exists. Sign in to continue.")
        user = existing_user
    else:
        provisioning = None

    role = (await session.execute(select(Role).where(Role.name == "consultant"))).scalar_one_or_none()
    if role is None:
        raise AppException("Consultant role is not configured.", 503)
    now = datetime.now(timezone.utc)
    if provisioning is None:
        request_id = uuid.uuid4()
        audit = ExternalSignupChallenge(
            id=request_id, email_normalized=email, mobile_normalized=mobile,
            otp_hash=_otp_digest(request_id, secrets.token_urlsafe(32)), status="REGISTRATION_ACCEPTED",
            attempt_count=0, resend_count=0, expires_at=now, last_sent_at=now, consumed_at=now,
        )
        user = User(
            email=email, mobile=mobile, phone=mobile,
            password_hash=password_service.hash_password(secrets.token_urlsafe(48)), role_id=role.id,
            first_name=body.full_name.strip(), is_active=True, is_verified=False,
            email_verified=False, mobile_verified=False, status="ACTIVE",
        )
        session.add_all([audit, user])
        await session.flush()
        provisioning = ExternalSignupProvisioning(
            challenge_id=audit.id, auth_user_id=user.id, account_type=body.account_type,
            idempotency_key=f"external-signup-mobile:{mobile}", status="REGISTRATION_ACCEPTED",
        )
        session.add(provisioning)
        await session.commit()

    professional_details = {
        "professionalRole": body.professional_role,
        "yearsExperience": body.years_experience,
        "activeClientRange": body.active_client_range,
        "qualification": body.qualification,
        "specialisation": body.specialisation,
        "registrationNumber": body.registration_number,
        "certification": body.certification,
        "areaOfExpertise": body.area_of_expertise,
        "profession": body.profession,
        "mentoringDomain": body.mentoring_domain,
    }
    try:
        result = await _provision_fiteatsy(
            user,
            {
                "authIdentityId": str(user.id), "name": body.full_name.strip(), "email": email,
                "mobileNumber": mobile, "accountType": body.account_type,
                "professionalTitle": body.professional_role, "speciality": body.specialisation or body.area_of_expertise,
                "practiceName": body.practice_name, "contactVerification": "UNVERIFIED_SIGNUP",
                "professionalDetails": professional_details,
            },
            provisioning.idempotency_key,
        )
    except AppException:
        provisioning.status = "PROVISIONING_RETRY"
        provisioning.last_error_code = "FITEATSY_PROVISIONING_UNAVAILABLE"
        await session.commit()
        raise
    provisioning.status = result["state"]
    provisioning.fiteatsy_user_id = result.get("userId")
    provisioning.tenant_id = result.get("tenantId")
    provisioning.owner_membership_id = result.get("ownerMembershipId")
    provisioning.onboarding_id = result.get("onboardingId")
    login = await auth_service.issue_mobile_otp_session(session, user, ip_address=ip_address, user_agent=user_agent)
    await session.commit()
    return {
        "state": provisioning.status, "tenant_id": provisioning.tenant_id,
        "onboarding_id": provisioning.onboarding_id, "workspace_ready": provisioning.status == "READY",
        "identity_type": "NEW_CONSULTANT", "auth_session": login.model_dump(mode="json"),
    }


async def start(session: AsyncSession, mobile_number: str, ip_address: str | None = None) -> dict:
    mobile = canonical_mobile(mobile_number)
    if not await check_rate_limit(f"external-signup-start:{ip_address or 'unknown'}:{mobile}"):
        raise AppException("Too many verification requests. Please try again later.", 429)
    now = datetime.now(timezone.utc)
    challenge_id, code = uuid.uuid4(), _new_code()
    challenge = ExternalSignupChallenge(
        id=challenge_id, mobile_normalized=mobile, otp_hash=_otp_digest(challenge_id, code),
        status="OTP_PENDING", attempt_count=0, resend_count=0,
        expires_at=now + timedelta(seconds=get_settings().external_signup_otp_ttl_seconds),
        last_sent_at=now,
    )
    session.add(challenge)
    await session.flush()
    try:
        await send_mobile_otp(mobile, code)
    except AppException:
        await session.rollback()
        raise
    return {"challenge_id": challenge.id, "state": "OTP_PENDING", "expires_in": get_settings().external_signup_otp_ttl_seconds}


async def resend(session: AsyncSession, challenge_id: uuid.UUID, ip_address: str | None = None) -> dict:
    challenge = (await session.execute(select(ExternalSignupChallenge).where(ExternalSignupChallenge.id == challenge_id).with_for_update())).scalar_one_or_none()
    if challenge is None or challenge.status != "OTP_PENDING" or not challenge.mobile_normalized:
        raise AppException("Verification cannot be resent.", 409)
    now, settings = datetime.now(timezone.utc), get_settings()
    if (now - challenge.last_sent_at).total_seconds() < settings.external_signup_resend_cooldown_seconds:
        raise AppException("Please wait before requesting another code.", 429)
    if challenge.resend_count >= settings.external_signup_max_resends:
        challenge.status = "BLOCKED"
        await session.commit()
        raise AppException("Verification resend limit reached.", 429)
    if not await check_rate_limit(f"external-signup-resend:{ip_address or 'unknown'}:{challenge.mobile_normalized}"):
        raise AppException("Too many verification requests. Please try again later.", 429)
    code = _new_code()
    challenge.otp_hash = _otp_digest(challenge.id, code)
    challenge.resend_count += 1
    challenge.attempt_count = 0
    challenge.last_sent_at = now
    challenge.expires_at = now + timedelta(seconds=settings.external_signup_otp_ttl_seconds)
    await session.flush()
    await send_mobile_otp(challenge.mobile_normalized, code)
    return {"challenge_id": challenge.id, "state": "OTP_PENDING", "expires_in": settings.external_signup_otp_ttl_seconds}


def _delegation_token(subject: uuid.UUID) -> str:
    settings = get_settings()
    if not settings.fiteatsy_delegation_private_key:
        raise AppException("External signup provisioning is not configured.", 503)
    now = datetime.now(timezone.utc)
    payload = {
        "iss": settings.fiteatsy_delegation_issuer, "sub": str(subject), "aud": settings.fiteatsy_delegation_audience,
        "iat": int(now.timestamp()), "exp": int((now + timedelta(seconds=60)).timestamp()), "jti": str(uuid.uuid4()),
        "product": "fiteatsy", "permissions": ["fiteatsy.external.signup.provision"],
        "purpose": "external_consultant_signup", "actor_type": "consultant_auth_service",
    }
    return jwt.encode(payload, settings.fiteatsy_delegation_private_key.replace("\\n", "\n"), algorithm="RS256", headers={"typ": "Zestiva-Delegated-Authority", "kid": settings.fiteatsy_delegation_key_id})


async def _provision_fiteatsy(user: User, body: dict, idempotency_key: str) -> dict:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            f"{settings.fiteatsy_backend_url.rstrip('/')}/v1/internal/delegated/external-consultant-signups/provision",
            headers={"x-zestiva-delegation": _delegation_token(user.id), "idempotency-key": idempotency_key},
            json={k: v for k, v in body.items() if v is not None},
        )
    if response.status_code not in (200, 201):
        raise AppException("Workspace provisioning is temporarily unavailable. Retry safely.", 503)
    return response.json()


async def _verify_challenge(session: AsyncSession, challenge_id: uuid.UUID, code: str) -> ExternalSignupChallenge:
    challenge = (await session.execute(select(ExternalSignupChallenge).where(ExternalSignupChallenge.id == challenge_id).with_for_update())).scalar_one_or_none()
    if challenge is None or not challenge.mobile_normalized:
        raise AppException("Verification is invalid or expired.", 400)
    if challenge.status == "CONSUMED":
        raise AppException("Verification code has already been used.", 409)
    now, settings = datetime.now(timezone.utc), get_settings()
    if challenge.status != "OTP_PENDING" or challenge.expires_at <= now:
        if challenge.status == "OTP_PENDING":
            challenge.status = "OTP_EXPIRED"
            await session.commit()
        raise AppException("Verification is invalid or expired.", 400)
    if challenge.attempt_count >= settings.external_signup_max_attempts:
        challenge.status = "BLOCKED"
        await session.commit()
        raise AppException("Verification attempt limit reached.", 429)
    if not hmac.compare_digest(challenge.otp_hash, _otp_digest(challenge.id, code)):
        challenge.attempt_count += 1
        if challenge.attempt_count >= settings.external_signup_max_attempts:
            challenge.status = "BLOCKED"
        await session.commit()
        raise AppException("Verification code is incorrect.", 400)
    challenge.status = "MOBILE_VERIFIED"
    await session.flush()
    return challenge


async def verify_and_provision(
    session: AsyncSession, *, challenge_id: uuid.UUID, code: str, name: str, email: str | None,
    account_type: str, professional_title: str | None, speciality: str | None, practice_name: str | None,
    ip_address: str | None = None, user_agent: str | None = None,
) -> dict:
    challenge = await _verify_challenge(session, challenge_id, code)
    mobile = challenge.mobile_normalized
    user = (await session.execute(select(User).where(User.mobile == mobile))).scalar_one_or_none()
    is_new = user is None
    profile_payload = {
        "name": name.strip(), "email": email, "mobileNumber": mobile,
        "accountType": account_type, "professionalTitle": professional_title,
        "speciality": speciality, "practiceName": practice_name,
    }
    if user is None:
        role = (await session.execute(select(Role).where(Role.name == "consultant"))).scalar_one_or_none()
        if role is None:
            raise AppException("Consultant role is not configured.", 503)
        identity_email = _identity_email(mobile, email)
        if email and (await session.execute(select(User).where(User.email == identity_email))).scalar_one_or_none():
            raise ConflictException("An account already exists for this contact email.")
        user = User(
            email=identity_email, mobile=mobile, phone=mobile,
            password_hash=password_service.hash_password(secrets.token_urlsafe(48)),
            role_id=role.id, first_name=name.strip(), is_active=True, is_verified=True,
            email_verified=False, mobile_verified=True, status="ACTIVE",
        )
        session.add(user)
        await session.flush()
        provisioning = ExternalSignupProvisioning(
            challenge_id=challenge.id, auth_user_id=user.id, account_type=account_type,
            idempotency_key=f"external-signup-mobile:{mobile}", status="MOBILE_VERIFIED",
        )
        session.add(provisioning)
        await session.commit()
    else:
        provisioning = (await session.execute(select(ExternalSignupProvisioning).where(ExternalSignupProvisioning.auth_user_id == user.id))).scalar_one_or_none()
        if provisioning is None:
            raise ConflictException("The verified identity is not linked to a Consultant workspace.")

    if provisioning.status in {"MOBILE_VERIFIED", "PROVISIONING_RETRY"} or not provisioning.tenant_id:
        try:
            result = await _provision_fiteatsy(
                user,
                {"authIdentityId": str(user.id), **profile_payload},
                provisioning.idempotency_key,
            )
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
        provisioning.last_error_code = None
        provisioning.last_error_detail = None

    challenge.status = "CONSUMED"
    challenge.consumed_at = datetime.now(timezone.utc)
    login = await auth_service.issue_mobile_otp_session(session, user, ip_address=ip_address, user_agent=user_agent)
    await session.commit()
    return {
        "state": provisioning.status, "tenant_id": provisioning.tenant_id, "onboarding_id": provisioning.onboarding_id,
        "workspace_ready": provisioning.status == "READY",
        "identity_type": "NEW_CONSULTANT" if is_new else "RETURNING_CONSULTANT",
        "auth_session": login.model_dump(mode="json"),
    }
