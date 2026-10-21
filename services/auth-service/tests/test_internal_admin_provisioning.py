import base64
import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import select

from app.core.exceptions import ConflictException, ForbiddenException
from app.db.models.audit_log import AuthAuditLog
from app.db.models.internal_privileged_invitation import InternalPrivilegedInvitation
from app.db.models.owner_access import Permission, RolePermission
from app.db.models.role import Role
from app.services.internal_admin_provisioning_service import (
    INTERNAL_SUPER_ADMIN_PERMISSIONS,
    ProvisionInternalSuperAdminCommand,
    provision_internal_super_admin,
)


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _grant(private_key, invitation, *, overrides=None):
    now = int(datetime.now(timezone.utc).timestamp())
    claims = {
        "iss": "test-security-authority",
        "aud": "test-first-admin",
        "jti": "single-use-grant-001",
        "authorizing_principal": "security-approver@nuetra.test",
        "invitation_id": str(invitation.id),
        "email": invitation.email,
        "phone": invitation.phone,
        "role": "internal_super_admin",
        "release_sha": "candidate-sha",
        "iat": now,
        "exp": now + 600,
    }
    claims.update(overrides or {})
    payload = _encode(json.dumps(claims, separators=(",", ":"), sort_keys=True).encode())
    return f"{payload}.{_encode(private_key.sign(payload.encode()))}"


@pytest.mark.asyncio
async def test_first_admin_bootstrap_is_scoped_audited_and_single_use(session, monkeypatch):
    role = Role(name="internal_super_admin")
    session.add(role)
    await session.flush()
    permissions = [Permission(key=key, module="internal", label=key)
                   for key in sorted(INTERNAL_SUPER_ADMIN_PERMISSIONS)]
    session.add_all(permissions)
    await session.flush()
    session.add_all(RolePermission(role_id=role.id, permission_id=item.id) for item in permissions)
    invitation = InternalPrivilegedInvitation(
        email="amitsaini19@gmail.com", phone="+919225534789", first_name="Amit",
        last_name="Saini", role_name="internal_super_admin",
        initiated_by_user_id=__import__("uuid").uuid4(), status="PENDING_APPROVAL",
    )
    session.add(invitation)
    await session.flush()
    private_key = Ed25519PrivateKey.generate()
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    monkeypatch.setattr(
        "app.services.internal_admin_provisioning_service.get_settings",
        lambda: SimpleNamespace(
            internal_first_admin_authority_public_key=public_pem,
            internal_first_admin_release_sha="candidate-sha",
            internal_first_admin_authority_issuer="test-security-authority",
            internal_first_admin_authority_audience="test-first-admin",
        ),
    )
    command = ProvisionInternalSuperAdminCommand(
        email="amitsaini19@gmail.com", first_name="Amit", last_name="Saini",
        phone="+919225534789", temporary_password="A_Strong-Temporary9!Pass",
        authorization_grant=_grant(private_key, invitation),
    )
    created = await provision_internal_super_admin(session, command)
    assert created.role.name == "internal_super_admin"
    assert set(created.permissions) == INTERNAL_SUPER_ADMIN_PERMISSIONS
    assert len(created.permissions) == 7
    assert created.must_change_password is True
    assert created.credential_status == "TEMPORARY"
    assert invitation.status == "ACTIVE"
    assert invitation.bootstrap_authority_principal == "security-approver@nuetra.test"
    assert invitation.bootstrap_grant_hash
    audit = (await session.execute(select(AuthAuditLog).where(
        AuthAuditLog.user_id == created.id))).scalar_one()
    assert audit.event_type == "FIRST_INTERNAL_SUPER_ADMIN_BOOTSTRAPPED_PASSWORD_CHANGE_REQUIRED"
    assert "security-approver@nuetra.test" in audit.user_agent

    with pytest.raises(ConflictException, match="permanently disabled"):
        await provision_internal_super_admin(session, command)


@pytest.mark.asyncio
async def test_first_admin_bootstrap_rejects_wrong_scope(session, monkeypatch):
    role = Role(name="internal_super_admin")
    session.add(role)
    await session.flush()
    invitation = InternalPrivilegedInvitation(
        email="target@example.test", phone="+919225534780", first_name="Target",
        last_name="Admin", role_name="internal_super_admin",
        initiated_by_user_id=__import__("uuid").uuid4(), status="PENDING_APPROVAL",
    )
    session.add(invitation)
    await session.flush()
    private_key = Ed25519PrivateKey.generate()
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    monkeypatch.setattr(
        "app.services.internal_admin_provisioning_service.get_settings",
        lambda: SimpleNamespace(
            internal_first_admin_authority_public_key=public_pem,
            internal_first_admin_release_sha="candidate-sha",
            internal_first_admin_authority_issuer="test-security-authority",
            internal_first_admin_authority_audience="test-first-admin",
        ),
    )
    command = ProvisionInternalSuperAdminCommand(
        email=invitation.email, first_name="Target", last_name="Admin",
        phone=invitation.phone, temporary_password="A_Strong-Temporary9!Pass",
        authorization_grant=_grant(private_key, invitation, overrides={"role": "platform_owner"}),
    )
    with pytest.raises(ForbiddenException, match="scope does not match"):
        await provision_internal_super_admin(session, command)


def test_provisioning_script_uses_hidden_inputs_only():
    source = open("scripts/provision_internal_super_admin.py", encoding="utf-8").read()
    assert source.count("getpass(") == 3
    assert 'add_argument("--password"' not in source
    assert 'add_argument("--authorization-grant"' not in source
