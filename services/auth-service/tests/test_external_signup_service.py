import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import delete, select

from app.core.exceptions import AppException
from app.db.models.external_signup import ExternalSignupChallenge, ExternalSignupProvisioning
from app.db.models.owner_access import LoginSession
from app.db.models.refresh_token import RefreshToken
from app.db.models.role import Role
from app.db.models.user import User
from app.services import external_signup_service
from app.schemas.auth import ExternalConsultantRegisterRequest


async def _challenge(session, *, code="123456", expires_delta=timedelta(minutes=5)):
    challenge_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    challenge = ExternalSignupChallenge(
        id=challenge_id,
        mobile_normalized=f"+919{str(challenge_id.int)[-9:]}",
        otp_hash=external_signup_service._otp_digest(challenge_id, code),
        status="OTP_PENDING",
        attempt_count=0,
        resend_count=0,
        expires_at=now + expires_delta,
        last_sent_at=now,
    )
    session.add(challenge)
    await session.flush()
    return challenge


@pytest.mark.asyncio
async def test_provisioning_uses_internal_delegated_authority_route(monkeypatch):
    captured = {}

    class Response:
        status_code = 200

        @staticmethod
        def json():
            return {"state": "ONBOARDING_IN_PROGRESS"}

    class Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def post(self, url, **kwargs):
            captured["url"] = url
            captured["headers"] = kwargs["headers"]
            captured["json"] = kwargs["json"]
            return Response()

    monkeypatch.setattr(external_signup_service.httpx, "AsyncClient", lambda **_kwargs: Client())
    monkeypatch.setattr(external_signup_service, "_delegation_token", lambda _subject: "signed-token")

    user = type("UserIdentity", (), {"id": uuid.uuid4()})()
    result = await external_signup_service._provision_fiteatsy(
        user,
        {"name": "External Owner", "practiceName": None, "speciality": None},
        "external-signup:challenge",
    )

    assert captured["url"].endswith("/v1/internal/delegated/external-consultant-signups/provision")
    assert captured["headers"] == {
        "x-zestiva-delegation": "signed-token",
        "idempotency-key": "external-signup:challenge",
    }
    assert captured["json"] == {"name": "External Owner"}
    assert result == {"state": "ONBOARDING_IN_PROGRESS"}


@pytest.mark.asyncio
async def test_provisioning_maps_backend_identity_conflict_to_non_retryable_conflict(monkeypatch):
    class Response:
        status_code = 409

    class Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def post(self, *_args, **_kwargs):
            return Response()

    monkeypatch.setattr(external_signup_service.httpx, "AsyncClient", lambda **_kwargs: Client())
    monkeypatch.setattr(external_signup_service, "_delegation_token", lambda _subject: "signed-token")

    user = type("UserIdentity", (), {"id": uuid.uuid4()})()
    with pytest.raises(AppException) as error:
        await external_signup_service._provision_fiteatsy(user, {"name": "Existing Account"}, "signup-conflict")

    assert error.value.status_code == 409
    assert error.value.message == "An account already exists. Sign in to continue."


@pytest.mark.asyncio
async def test_wrong_otp_is_persisted_and_fails_closed(session):
    challenge = await _challenge(session)
    with pytest.raises(AppException) as error:
        await external_signup_service.verify_and_provision(
            session,
            challenge_id=challenge.id,
            code="654321",
            name="External Owner",
            email=None,
            account_type="INDEPENDENT_CONSULTANT",
            professional_title=None,
            speciality=None,
            practice_name=None,
        )
    assert error.value.status_code == 400
    await session.refresh(challenge)
    assert challenge.attempt_count == 1
    assert challenge.status == "OTP_PENDING"


@pytest.mark.asyncio
async def test_expired_otp_is_single_use_and_fails_closed(session):
    challenge = await _challenge(session, expires_delta=timedelta(seconds=-1))
    with pytest.raises(AppException) as error:
        await external_signup_service.verify_and_provision(
            session,
            challenge_id=challenge.id,
            code="123456",
            name="External Owner",
            email=None,
            account_type="INDEPENDENT_CONSULTANT",
            professional_title=None,
            speciality=None,
            practice_name=None,
        )
    assert error.value.status_code == 400
    await session.refresh(challenge)
    assert challenge.status == "OTP_EXPIRED"


@pytest.mark.asyncio
async def test_successful_verify_is_single_use_and_does_not_duplicate_identity(session, monkeypatch):
    role = (await session.execute(select(Role).where(Role.name == "consultant"))).scalar_one_or_none()
    created_role = role is None
    if role is None:
        role = Role(name="consultant", description="External Consultant")
        session.add(role)
        await session.flush()
    challenge = await _challenge(session)
    calls = 0

    async def provision(user, body, idempotency_key):
        nonlocal calls
        calls += 1
        return {
            "state": "ONBOARDING_IN_PROGRESS",
            "userId": f"ext_{user.id}",
            "tenantId": str(uuid.uuid4()),
            "ownerMembershipId": str(uuid.uuid4()),
            "onboardingId": str(uuid.uuid4()),
            "workspaceReady": False,
        }

    monkeypatch.setattr(external_signup_service, "_provision_fiteatsy", provision)
    kwargs = dict(
        challenge_id=challenge.id,
        code="123456",
        name="External Owner",
        email=None,
        account_type="INDEPENDENT_CONSULTANT",
        professional_title="Dietitian",
        speciality="Nutrition",
        practice_name=None,
    )
    first = await external_signup_service.verify_and_provision(session, **kwargs)
    with pytest.raises(AppException) as replay:
        await external_signup_service.verify_and_provision(session, **kwargs)
    assert replay.value.status_code == 409
    assert first["identity_type"] == "NEW_CONSULTANT"
    assert calls == 1
    users = (await session.execute(select(User).where(User.mobile == challenge.mobile_normalized))).scalars().all()
    provisions = (await session.execute(select(ExternalSignupProvisioning).where(ExternalSignupProvisioning.challenge_id == challenge.id))).scalars().all()
    assert len(users) == 1
    assert len(provisions) == 1
    assert challenge.status == "CONSUMED"
    await session.execute(delete(LoginSession).where(LoginSession.user_id == users[0].id))
    await session.execute(delete(RefreshToken).where(RefreshToken.user_id == users[0].id))
    await session.delete(provisions[0])
    await session.delete(users[0])
    await session.delete(challenge)
    if created_role:
        await session.delete(role)
    await session.commit()


@pytest.mark.asyncio
async def test_direct_registration_provisions_unverified_identity_and_resumes_without_duplicates(session, monkeypatch):
    role = (await session.execute(select(Role).where(Role.name == "consultant"))).scalar_one_or_none()
    created_role = role is None
    if role is None:
        role = Role(name="consultant", description="External Consultant")
        session.add(role)
        await session.flush()
    calls = 0

    async def provision(user, body, _idempotency_key):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise AppException("temporary", 503)
        assert body["contactVerification"] == "UNVERIFIED_SIGNUP"
        assert body["mobileNumber"] == "+919762006688"
        return {
            "state": "ONBOARDING_IN_PROGRESS", "userId": f"ext_{user.id}",
            "tenantId": str(uuid.uuid4()), "ownerMembershipId": str(uuid.uuid4()),
            "onboardingId": str(uuid.uuid4()), "workspaceReady": False,
        }

    class SessionResult:
        def model_dump(self, **_kwargs):
            return {"tokens": {"access_token": "redacted", "refresh_token": "redacted"}}

    async def issue_session(*_args, **_kwargs): return SessionResult()
    async def allow_rate_limit(*_args, **_kwargs): return True
    monkeypatch.setattr(external_signup_service, "_provision_fiteatsy", provision)
    monkeypatch.setattr(external_signup_service.auth_service, "issue_direct_registration_session", issue_session)
    monkeypatch.setattr(external_signup_service, "check_rate_limit", allow_rate_limit)
    body = ExternalConsultantRegisterRequest(
        full_name="QA Consultant", mobile_number="+91 97620 06688", email="qa-direct@example.com",
        account_type="INDEPENDENT_CONSULTANT", professional_role="DIETITIAN_NUTRITIONIST",
        years_experience=5, active_client_range="0", qualification="MSc Nutrition",
        password="QaDirect#2026Strong", confirm_password="QaDirect#2026Strong",
        specialisation="Clinical Nutrition", recaptcha_token="test-recaptcha-token",
    )
    with pytest.raises(AppException, match="temporary"):
        await external_signup_service.register_without_verification(session, body=body)
    users = (await session.execute(select(User).where(User.mobile == "+919762006688"))).scalars().all()
    original_password_hash = users[0].password_hash
    retry_body = body.model_copy(update={
        "password": "Different#2026Strong",
        "confirm_password": "Different#2026Strong",
    })
    result = await external_signup_service.register_without_verification(session, body=retry_body)
    assert result["state"] == "ONBOARDING_IN_PROGRESS"
    users = (await session.execute(select(User).where(User.mobile == "+919762006688"))).scalars().all()
    provisions = (await session.execute(select(ExternalSignupProvisioning).where(ExternalSignupProvisioning.auth_user_id == users[0].id))).scalars().all()
    assert len(users) == 1
    assert len(provisions) == 1
    assert users[0].is_verified is False
    assert users[0].email_verified is False
    assert users[0].mobile_verified is False
    assert users[0].password_hash == original_password_hash
    assert external_signup_service.password_service.verify_password("QaDirect#2026Strong", users[0].password_hash)
    assert not external_signup_service.password_service.verify_password("Different#2026Strong", users[0].password_hash)
    await session.delete(provisions[0])
    challenge = (await session.execute(select(ExternalSignupChallenge).where(ExternalSignupChallenge.id == provisions[0].challenge_id))).scalar_one()
    await session.delete(challenge)
    await session.delete(users[0])
    if created_role: await session.delete(role)
    await session.commit()


@pytest.mark.asyncio
async def test_duplicate_direct_signup_cannot_replace_existing_identity_password(session, monkeypatch):
    role = (await session.execute(select(Role).where(Role.name == "consultant"))).scalar_one_or_none()
    if role is None:
        role = Role(name="consultant", description="External Consultant")
        session.add(role)
        await session.flush()
    original_hash = external_signup_service.password_service.hash_password("Original#2026Strong")
    user = User(
        email="existing-direct@example.com", mobile="+919762006687", phone="+919762006687",
        password_hash=original_hash, role_id=role.id, first_name="Existing QA",
        is_active=True, is_verified=False, email_verified=False, mobile_verified=False, status="ACTIVE",
    )
    session.add(user)
    await session.flush()

    async def allow_rate_limit(*_args, **_kwargs): return True
    monkeypatch.setattr(external_signup_service, "check_rate_limit", allow_rate_limit)
    body = ExternalConsultantRegisterRequest(
        full_name="Existing QA", mobile_number="+91 97620 06687", email="existing-direct@example.com",
        account_type="INDEPENDENT_CONSULTANT", professional_role="DIETITIAN_NUTRITIONIST",
        years_experience=5, active_client_range="0", qualification="MSc Nutrition",
        password="Replacement#2026Strong", confirm_password="Replacement#2026Strong",
        recaptcha_token="test-recaptcha-token",
    )

    with pytest.raises(AppException, match="account already exists"):
        await external_signup_service.register_without_verification(session, body=body)

    assert user.password_hash == original_hash
    assert external_signup_service.password_service.verify_password("Original#2026Strong", user.password_hash)
    assert not external_signup_service.password_service.verify_password("Replacement#2026Strong", user.password_hash)
