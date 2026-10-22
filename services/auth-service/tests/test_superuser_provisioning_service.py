import uuid

import pytest
from sqlalchemy import func, select

from app.core.exceptions import ConflictException, ForbiddenException
from app.db.models import (
    AuditEvent,
    AuthAuditLog,
    InternalPrivilegedInvitation,
    OrganizationMembership,
    PasswordHistory,
    Role,
    User,
    UserProductAccess,
    UserRole,
)
from app.services import superuser_provisioning_service as service
from app.services.superuser_provisioning_service import ProvisionSuperuserCommand


async def _seed_authority_and_invitation(session):
    role = Role(id=uuid.uuid4(), name="superuser", description="Canonical superuser")
    session.add(role)
    await session.flush()
    priyanshi = User(
        id=uuid.uuid4(),
        email="priyanshi@example.test",
        password_hash="unused",
        role_id=role.id,
        is_active=True,
        is_verified=True,
    )
    lalit = User(
        id=uuid.uuid4(),
        email="lalit@example.test",
        password_hash="unused",
        role_id=role.id,
        is_active=True,
        is_verified=True,
    )
    session.add_all((priyanshi, lalit))
    await session.flush()
    invitation = InternalPrivilegedInvitation(
        id=uuid.uuid4(),
        email="amitsaini19@gmail.com",
        phone="+919225534789",
        first_name="Amit",
        last_name="Saini",
        role_name="internal_super_admin",
        initiated_by_user_id=priyanshi.id,
        status="PENDING_APPROVAL",
    )
    session.add(invitation)
    await session.commit()
    return role, priyanshi, lalit, invitation


@pytest.mark.asyncio
async def test_provisions_exact_superuser_without_product_or_tenant_access(session, monkeypatch):
    role, priyanshi, lalit, invitation = await _seed_authority_and_invitation(session)
    monkeypatch.setattr(service, "require_bootstrap_authority", lambda actor_id, approver=False: None)

    result = await service.provision_authorized_superuser(
        session,
        ProvisionSuperuserCommand(
            operator_user_id=lalit.id,
            invitation_id=invitation.id,
            email="amitsaini19@gmail.com",
            mobile="+91 92255 34789",
            first_name="Amit",
            last_name="Saini",
        ),
    )

    amit = await session.scalar(select(User).where(User.id == result.user_id))
    assert amit is not None
    assert amit.role_id == role.id
    assert amit.permissions == []
    assert amit.status == "PASSWORD_CHANGE_REQUIRED"
    assert amit.must_change_password is True
    assert amit.credential_status == "TEMPORARY"
    assert amit.temporary_password_expires_at is not None
    assert amit.account_classification == "PRODUCTION_USER"
    assert amit.mfa_enabled is False
    assert result.role == "superuser"
    assert result.invitation_status == "REVOKED"

    assignment = await session.scalar(select(UserRole).where(UserRole.user_id == amit.id))
    assert assignment is not None
    assert assignment.role_id == role.id
    assert assignment.assigned_by_user_id == lalit.id
    assert assignment.is_primary is True
    assert await session.scalar(
        select(func.count()).select_from(UserProductAccess).where(UserProductAccess.user_id == amit.id)
    ) == 0
    assert await session.scalar(
        select(func.count()).select_from(OrganizationMembership).where(
            OrganizationMembership.user_id == amit.id
        )
    ) == 0
    assert await session.scalar(
        select(func.count()).select_from(PasswordHistory).where(PasswordHistory.user_id == amit.id)
    ) == 1

    reconciled = await session.get(InternalPrivilegedInvitation, invitation.id)
    assert reconciled is not None
    assert reconciled.user_id == amit.id
    assert reconciled.approved_by_user_id == lalit.id
    assert reconciled.status == "REVOKED"
    assert reconciled.token_hash is None
    assert reconciled.activation_hash is None

    audit = await session.scalar(
        select(AuditEvent).where(
            AuditEvent.entity_id == str(amit.id),
            AuditEvent.action == "GOVERNED_SUPERUSER_PROVISIONED",
        )
    )
    assert audit is not None
    assert audit.actor_user_id == lalit.id
    assert audit.after_state["product_entitlements"] == 0
    auth_audit = await session.scalar(
        select(AuthAuditLog).where(
            AuthAuditLog.user_id == amit.id,
            AuthAuditLog.event_type == "GOVERNED_SUPERUSER_PROVISIONED",
        )
    )
    assert auth_audit is not None
    assert str(lalit.id) in (auth_audit.user_agent or "")

    assert (await session.get(User, lalit.id)).role_id == role.id
    assert (await session.get(User, priyanshi.id)).role_id == role.id

    with pytest.raises(ConflictException, match="Account already exists"):
        await service.provision_authorized_superuser(
            session,
            ProvisionSuperuserCommand(
                operator_user_id=lalit.id,
                invitation_id=invitation.id,
                email="amitsaini19@gmail.com",
                mobile="+919225534789",
                first_name="Amit",
                last_name="Saini",
            ),
        )
    assert await session.scalar(
        select(func.count()).select_from(User).where(User.email == "amitsaini19@gmail.com")
    ) == 1


@pytest.mark.asyncio
async def test_requires_configured_active_superuser_approver(session, monkeypatch):
    operator_id = uuid.uuid4()

    def reject(_actor_id, *, approver=False):
        assert approver is True
        raise ForbiddenException("Designated Internal IAM bootstrap authority required")

    monkeypatch.setattr(service, "require_bootstrap_authority", reject)
    with pytest.raises(ForbiddenException, match="bootstrap authority"):
        await service.provision_authorized_superuser(
            session,
            ProvisionSuperuserCommand(
                operator_user_id=operator_id,
                invitation_id=uuid.uuid4(),
                email="different-amit@example.test",
                mobile="+919000000001",
                first_name="Amit",
                last_name="Saini",
            ),
        )
