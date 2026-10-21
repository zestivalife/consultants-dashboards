import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.core.exceptions import ConflictException
from app.db.models.audit_log import AuthAuditLog
from app.db.models.owner_access import Permission, RolePermission
from app.db.models.internal_privileged_invitation import InternalPrivilegedInvitation
from app.db.models.role import Role
from app.db.models.user import User
from app.services.internal_admin_provisioning_service import (
    INTERNAL_SUPER_ADMIN_PERMISSIONS,
    ProvisionInternalSuperAdminCommand,
    provision_internal_super_admin,
)


@pytest.mark.asyncio
async def test_provisioning_creates_isolated_temporary_internal_admin(session, monkeypatch):
    role = Role(name="internal_super_admin")
    session.add(role)
    await session.flush()
    permissions = [
        Permission(key=key, module="internal", label=key)
        for key in sorted(INTERNAL_SUPER_ADMIN_PERMISSIONS)
    ]
    session.add_all(permissions)
    await session.flush()
    session.add_all(
        RolePermission(role_id=role.id, permission_id=permission.id)
        for permission in permissions
    )
    operator = User(
        email="operator@nuetra.test",
        password_hash="not-used",
        role_id=role.id,
        role=role,
        permissions=["internal.users.manage"],
        is_active=True,
        is_verified=True,
    )
    session.add(operator)
    await session.flush()
    initiator = User(
        email="initiator@nuetra.test",
        password_hash="not-used",
        role_id=role.id,
        role=role,
        permissions=["internal.invitations.manage"],
        is_active=True,
        is_verified=True,
    )
    session.add(initiator)
    await session.flush()
    invitation = InternalPrivilegedInvitation(
        email="amit.saini@example.test",
        phone="+919225534789",
        first_name="Amit",
        last_name="Saini",
        role_name="internal_super_admin",
        initiated_by_user_id=initiator.id,
        approved_by_user_id=operator.id,
        status="APPROVED",
        approved_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
    )
    session.add(invitation)
    await session.flush()
    monkeypatch.setattr(
        "app.services.internal_admin_provisioning_service.require_bootstrap_authority",
        lambda actor_id, approver=False: None,
    )

    created = await provision_internal_super_admin(
        session,
        ProvisionInternalSuperAdminCommand(
            email="Amit.Saini@example.test",
            first_name="Amit",
            last_name="Saini",
            phone="+919225534789",
            temporary_password="A_Strong-Temporary9!Pass",
            operator_user_id=operator.id,
        ),
    )

    assert created.email == "amit.saini@example.test"
    assert created.role.name == "internal_super_admin"
    assert set(created.permissions) == INTERNAL_SUPER_ADMIN_PERMISSIONS
    assert len(created.permissions) == 7
    assert created.must_change_password is True
    assert created.credential_status == "TEMPORARY"
    assert created.mfa_enabled is False
    assert created.mfa_secret_encrypted is None
    assert created.mobile == "+919225534789"
    assert invitation.status == "ACTIVE"
    assert invitation.user_id == created.id
    audit = (
        await session.execute(
            select(AuthAuditLog).where(AuthAuditLog.user_id == created.id)
        )
    ).scalar_one()
    assert audit.event_type == "INTERNAL_SUPER_ADMIN_PROVISIONED_PASSWORD_CHANGE_REQUIRED"

    with pytest.raises(ConflictException, match="credentials were not changed"):
        await provision_internal_super_admin(
            session,
            ProvisionInternalSuperAdminCommand(
                email=created.email,
                first_name="Amit",
                last_name="Saini",
                phone="+919225534789",
                temporary_password="Another_Strong9!Pass",
                operator_user_id=operator.id,
            ),
        )


def test_provisioning_script_never_accepts_password_as_argument():
    source = open("scripts/provision_internal_super_admin.py", encoding="utf-8").read()
    assert "getpass(" in source
    assert 'add_argument("--password"' not in source
