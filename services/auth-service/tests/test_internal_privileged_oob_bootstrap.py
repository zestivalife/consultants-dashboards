import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import ConflictException, ForbiddenException
from app.services import internal_privileged_iam_service as service


class _Audit:
    def __init__(self, _session):
        pass

    create = AsyncMock()


def _record(*, actor_id: uuid.UUID, status: str = "PENDING_APPROVAL"):
    return SimpleNamespace(
        id=uuid.uuid4(),
        initiated_by_user_id=actor_id,
        email="amitsaini19@gmail.com",
        phone="+919225534789",
        status=status,
        token_hash=None,
        approved_by_user_id=None,
        approved_at=None,
        expires_at=None,
        delivery_channel="EMAIL",
        administrative_identity_verified_at=None,
        administrative_identity_verified_by_user_id=None,
        administrative_verification_reason=None,
    )


@pytest.mark.asyncio
async def test_oob_approval_is_two_person_single_use_and_audited(monkeypatch):
    initiator, approver = uuid.uuid4(), uuid.uuid4()
    record = _record(actor_id=initiator)
    session = SimpleNamespace(get=AsyncMock(return_value=record), commit=AsyncMock())
    monkeypatch.setattr(service, "require_bootstrap_authority", lambda actor_id, approver=False: None)
    monkeypatch.setattr(service, "AuditLogRepository", _Audit)
    monkeypatch.setattr(service, "get_settings", lambda: SimpleNamespace(internal_privileged_invitation_ttl_minutes=10))

    approved, token = await service.approve_out_of_band(
        session,
        actor_id=approver,
        invitation_id=record.id,
        confirmed_email=record.email,
        confirmed_phone=record.phone,
        reason="Identity checked by authorised operator",
    )

    assert len(token) >= 40
    assert approved.token_hash and token not in approved.token_hash
    assert approved.status == "APPROVED"
    assert approved.delivery_channel == "SECURE_OUT_OF_BAND"
    assert approved.administrative_identity_verified_by_user_id == approver
    assert approved.administrative_verification_reason == "Identity checked by authorised operator"
    session.commit.assert_awaited_once()

    with pytest.raises(ConflictException):
        await service.approve_out_of_band(
            session,
            actor_id=approver,
            invitation_id=record.id,
            confirmed_email=record.email,
            confirmed_phone=record.phone,
            reason="Identity checked by authorised operator",
        )


@pytest.mark.asyncio
async def test_oob_approval_rejects_same_operator_and_unapproved_identity(monkeypatch):
    initiator, approver = uuid.uuid4(), uuid.uuid4()
    record = _record(actor_id=initiator)
    session = SimpleNamespace(get=AsyncMock(return_value=record), commit=AsyncMock())
    monkeypatch.setattr(service, "require_bootstrap_authority", lambda actor_id, approver=False: None)

    with pytest.raises(ForbiddenException, match="Two-person"):
        await service.approve_out_of_band(
            session, actor_id=initiator, invitation_id=record.id,
            confirmed_email=record.email, confirmed_phone=record.phone,
            reason="Identity checked by authorised operator",
        )

    with pytest.raises(ForbiddenException, match="not authorised"):
        await service.approve_out_of_band(
            session, actor_id=approver, invitation_id=record.id,
            confirmed_email="other@example.com", confirmed_phone=record.phone,
            reason="Identity checked by authorised operator",
        )


def test_oob_contract_never_marks_email_verified_and_never_sends_email():
    source = open("app/services/internal_privileged_iam_service.py").read()
    route = open("app/api/v1/routes/internal_privileged_iam.py").read()
    assert 'email_verified=record.delivery_channel == "EMAIL"' in source
    oob_route = route.split('approve-out-of-band', 1)[1].split('@router.post', 1)[0]
    assert "get_email_service" not in oob_route
    assert 'response.headers["Cache-Control"] = "no-store"' in oob_route
    assert "enrolment_token" in oob_route
