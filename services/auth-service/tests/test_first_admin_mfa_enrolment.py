import base64
from types import SimpleNamespace

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import delete

from app.core.exceptions import ForbiddenException
from app.db.models.audit_log import AuthAuditLog
from app.db.models.internal_privileged_invitation import InternalPrivilegedInvitation
from app.db.models.role import Role
from app.db.models.user import User
from app.services import internal_privileged_iam_service as service


@pytest.mark.asyncio
async def test_first_admin_mfa_enrolment_confirms_and_rejects_replay(session, monkeypatch):
    role = Role(name="internal_super_admin")
    session.add(role)
    await session.flush()
    user = User(
        email="first-admin-mfa@nuetra.test", password_hash="not-used", role_id=role.id,
        role=role, is_active=True, is_verified=True, status="PENDING_MFA",
        credential_status="PERMANENT", must_change_password=False, permissions=["internal.users.read"],
    )
    session.add(user)
    await session.flush()
    invitation = InternalPrivilegedInvitation(
        email=user.email, phone="+919225534789", first_name="First", last_name="Admin",
        role_name="internal_super_admin", initiated_by_user_id=__import__("uuid").uuid4(),
        user_id=user.id, status="ACTIVE", bootstrap_grant_hash="a" * 64,
    )
    session.add(invitation)
    await session.flush()
    key = Fernet.generate_key().decode()
    monkeypatch.setattr(service, "get_settings", lambda: SimpleNamespace(internal_iam_mfa_encryption_key=key))

    activation, uri = await service.begin_first_admin_mfa_enrolment(session, user_id=user.id)
    secret = uri.split("secret=", 1)[1].split("&", 1)[0]
    code = service._totp(secret, service._totp_step())
    confirmed = await service.confirm_mfa(
        session, activation_token=activation, code=code, expected_user_id=user.id,
    )
    assert confirmed.mfa_enabled is True
    assert confirmed.status == "ACTIVE"
    assert invitation.status == "ACTIVE"
    assert invitation.activation_hash is None

    with pytest.raises(ForbiddenException, match="Invalid activation session"):
        await service.confirm_mfa(session, activation_token=activation, code=code, expected_user_id=user.id)

    # The service commits by design. Remove this test's committed records so the
    # session-scoped SQLite engine remains isolated for the rest of the suite.
    await session.execute(delete(AuthAuditLog).where(AuthAuditLog.user_id == user.id))
    await session.delete(invitation)
    await session.delete(user)
    await session.flush()
    await session.delete(role)
    await session.commit()


def test_totp_rejects_expired_and_replayed_codes(monkeypatch):
    secret = base64.b32encode(b"01234567890123456789").decode().rstrip("=")
    key = Fernet.generate_key().decode()
    now = 1_800_000_000
    user = SimpleNamespace(
        mfa_secret_encrypted=Fernet(key.encode()).encrypt(secret.encode()).decode(),
        mfa_enabled=True, mfa_last_accepted_step=None,
    )
    monkeypatch.setattr(service, "get_settings", lambda: SimpleNamespace(internal_iam_mfa_encryption_key=key))
    monkeypatch.setattr(service.time, "time", lambda: now)
    expired = service._totp(secret, service._totp_step(now) - 2)
    with pytest.raises(ForbiddenException, match="Invalid MFA code"):
        service.verify_totp(user, expired)
    current_step = service._totp_step(now)
    current = service._totp(secret, current_step)
    assert service.verify_totp(user, current) == current_step
    user.mfa_last_accepted_step = current_step
    with pytest.raises(ForbiddenException, match="already been used"):
        service.verify_totp(user, current)
