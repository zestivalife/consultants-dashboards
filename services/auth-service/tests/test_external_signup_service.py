import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.core.exceptions import AppException
from app.db.models.external_signup import ExternalSignupChallenge, ExternalSignupProvisioning
from app.db.models.role import Role
from app.db.models.user import User
from app.services import external_signup_service


async def _challenge(session, *, code="123456", expires_delta=timedelta(minutes=5)):
    challenge_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    challenge = ExternalSignupChallenge(
        id=challenge_id,
        email_normalized=f"external-{challenge_id}@example.test",
        otp_hash=external_signup_service._otp_digest(challenge_id, code),
        status="PENDING",
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
async def test_wrong_otp_is_persisted_and_fails_closed(session):
    challenge = await _challenge(session)
    with pytest.raises(AppException) as error:
        await external_signup_service.verify_and_provision(
            session,
            challenge_id=challenge.id,
            code="654321",
            password="StrongPassword123!",
            name="External Owner",
            account_type="INDEPENDENT_CONSULTANT",
            professional_title=None,
            speciality=None,
            practice_name=None,
        )
    assert error.value.status_code == 400
    await session.refresh(challenge)
    assert challenge.attempt_count == 1
    assert challenge.status == "PENDING"


@pytest.mark.asyncio
async def test_expired_otp_is_single_use_and_fails_closed(session):
    challenge = await _challenge(session, expires_delta=timedelta(seconds=-1))
    with pytest.raises(AppException) as error:
        await external_signup_service.verify_and_provision(
            session,
            challenge_id=challenge.id,
            code="123456",
            password="StrongPassword123!",
            name="External Owner",
            account_type="INDEPENDENT_CONSULTANT",
            professional_title=None,
            speciality=None,
            practice_name=None,
        )
    assert error.value.status_code == 400
    await session.refresh(challenge)
    assert challenge.status == "EXPIRED"


@pytest.mark.asyncio
async def test_successful_verify_is_idempotent_and_does_not_duplicate_identity(session, monkeypatch):
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
        password="StrongPassword123!",
        name="External Owner",
        account_type="INDEPENDENT_CONSULTANT",
        professional_title="Dietitian",
        speciality="Nutrition",
        practice_name=None,
    )
    first = await external_signup_service.verify_and_provision(session, **kwargs)
    second = await external_signup_service.verify_and_provision(session, **kwargs)
    assert first == second
    assert calls == 1
    users = (await session.execute(select(User).where(User.email == challenge.email_normalized))).scalars().all()
    provisions = (await session.execute(select(ExternalSignupProvisioning).where(ExternalSignupProvisioning.challenge_id == challenge.id))).scalars().all()
    assert len(users) == 1
    assert len(provisions) == 1
    assert challenge.status == "CONSUMED"
    await session.delete(provisions[0])
    await session.delete(users[0])
    await session.delete(challenge)
    if created_role:
        await session.delete(role)
    await session.commit()
