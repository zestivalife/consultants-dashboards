import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, ForbiddenException
from app.db.models.owner_access import AuditEvent, Permission, RolePermission, UserRole, UserStatusHistory
from app.db.models.role import Role
from app.db.models.user import PasswordHistory, User
from app.schemas.auth import UserResponse
from app.schemas.people_access import BulkActionRequest, ManagedUserCreateRequest
from app.services import people_access_service
from app.services.password_service import password_service


async def _create_role(session: AsyncSession, name: str, description: str = "") -> Role:
    role = Role(id=uuid.uuid4(), name=name, description=description or name.title())
    session.add(role)
    await session.flush()
    return role


async def _create_user(session: AsyncSession, role: Role, email: str, **overrides) -> User:
    user = User(
        id=uuid.uuid4(),
        email=email,
        password_hash=password_service.hash_password(overrides.pop("password", "Correct123!Ok")),
        role_id=role.id,
        is_verified=True,
        is_active=True,
        status="ACTIVE",
        **overrides,
    )
    session.add(user)
    await session.flush()
    return user


def _actor_from_user(user: User, permissions: list[str] | None = None) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        is_verified=user.is_verified,
        role=user.role.name if user.role else "member",
        company_name=user.company_name,
        company_id=user.company_id,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        permissions=permissions or [],
        must_change_password=user.must_change_password,
        created_at=user.created_at,
    )


@pytest.mark.asyncio
async def test_resolve_user_permissions_merges_role_and_user_permissions(session: AsyncSession):
    owner_role = await _create_role(session, "platform_owner")
    read_permission = Permission(id=uuid.uuid4(), key="users.read", module="users", label="Read users")
    edit_permission = Permission(id=uuid.uuid4(), key="users.edit", module="users", label="Edit users")
    session.add_all([read_permission, edit_permission])
    await session.flush()
    session.add(RolePermission(role_id=owner_role.id, permission_id=read_permission.id))
    await session.flush()

    owner = await _create_user(session, owner_role, "owner@nuetra.in", permissions=["users.edit"])

    permissions = await people_access_service.resolve_user_permissions(session, owner)
    assert permissions == ["users.read", "users.edit"]


@pytest.mark.asyncio
async def test_ensure_owner_access_allows_required_permission(session: AsyncSession):
    owner_role = await _create_role(session, "platform_owner")
    owner = await _create_user(session, owner_role, "owner@zestiva.in")
    actor = _actor_from_user(owner, permissions=["packages.manage"])

    await people_access_service.ensure_owner_access(session, actor, {"packages.manage"})


@pytest.mark.asyncio
async def test_ensure_owner_access_rejects_missing_permission(session: AsyncSession):
    owner_role = await _create_role(session, "platform_owner")
    owner = await _create_user(session, owner_role, "owner@zestiva.in")
    actor = _actor_from_user(owner, permissions=["users.read"])

    with pytest.raises(ForbiddenException):
        await people_access_service.ensure_owner_access(session, actor, {"packages.manage"})


@pytest.mark.asyncio
async def test_create_user_generates_temporary_credentials_and_primary_role(session: AsyncSession):
    owner_role = await _create_role(session, "platform_owner")
    consultant_role = await _create_role(session, "consultant")
    owner = await _create_user(session, owner_role, "owner@nuetra.in", first_name="Owner")
    actor = _actor_from_user(owner, permissions=["users.create", "users.read", "users.edit"])

    detail = await people_access_service.create_user(
        session,
        ManagedUserCreateRequest(
            email="consultant@nuetra.in",
            first_name="Aarav",
            last_name="Joshi",
            role="consultant",
            permissions=["reports.view"],
        ),
        actor=actor,
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id="req-people-create",
    )

    assert detail.email == "consultant@nuetra.in"
    assert detail.role == "consultant"
    assert detail.status == "ACTIVE"
    assert detail.must_change_password is True
    assert detail.temporary_credentials.username == "consultant@nuetra.in"
    assert detail.temporary_credentials.temporary_password

    created_user = await session.scalar(select(User).where(User.email == "consultant@nuetra.in"))
    assert created_user is not None
    assert created_user.status == "ACTIVE"
    assert created_user.is_active is True
    assert created_user.is_verified is True
    assert created_user.must_change_password is True
    assert password_service.verify_password(detail.temporary_credentials.temporary_password, created_user.password_hash)

    password_history = await session.scalar(
        select(PasswordHistory).where(
            PasswordHistory.user_id == created_user.id,
            PasswordHistory.source == "temporary_user_creation",
        )
    )
    assert password_history is not None
    assert password_history.password_hash == created_user.password_hash

    user_role = await session.scalar(
        select(UserRole).where(UserRole.user_id == detail.id, UserRole.role_id == consultant_role.id)
    )
    assert user_role is not None
    assert user_role.is_primary is True

    status_history = await session.scalar(
        select(UserStatusHistory).where(UserStatusHistory.user_id == created_user.id)
    )
    assert status_history is not None
    assert status_history.new_status == "ACTIVE"

    audit_event = await session.scalar(
        select(AuditEvent).where(
            AuditEvent.entity_id == str(created_user.id),
            AuditEvent.action == "PASSWORD_RESET_BY_ADMIN",
        )
    )
    assert audit_event is not None
    assert audit_event.after_state["temporary_password_returned_once"] is True
    assert detail.temporary_credentials.temporary_password not in str(audit_event.after_state)


@pytest.mark.asyncio
async def test_create_user_rejects_duplicate_email(session: AsyncSession):
    owner_role = await _create_role(session, "platform_owner")
    consultant_role = await _create_role(session, "consultant")
    owner = await _create_user(session, owner_role, "owner@nuetra.in")
    await _create_user(session, consultant_role, "existing@nuetra.in")
    actor = _actor_from_user(owner, permissions=["users.create"])

    with pytest.raises(ConflictException):
        await people_access_service.create_user(
            session,
            ManagedUserCreateRequest(email="existing@nuetra.in", role="consultant"),
            actor=actor,
            ip_address="127.0.0.1",
            user_agent="pytest",
            request_id="req-duplicate",
        )


@pytest.mark.asyncio
async def test_reset_user_password_returns_new_temporary_password_and_audits(session: AsyncSession):
    owner_role = await _create_role(session, "platform_owner")
    mentor_role = await _create_role(session, "mentor")
    owner = await _create_user(session, owner_role, "owner@nuetra.in")
    mentor = await _create_user(session, mentor_role, "mentor@nuetra.in", must_change_password=False)
    actor = _actor_from_user(owner, permissions=["users.edit"])
    original_hash = mentor.password_hash

    result = await people_access_service.reset_user_password(
        session,
        mentor.id,
        actor=actor,
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id="req-reset-password",
    )

    assert result.username == mentor.email
    assert result.temporary_password
    assert result.must_change_password is True
    assert mentor.must_change_password is True
    assert mentor.password_hash != original_hash
    assert password_service.verify_password(result.temporary_password, mentor.password_hash)

    password_history = await session.scalar(
        select(PasswordHistory).where(
            PasswordHistory.user_id == mentor.id,
            PasswordHistory.source == "admin_password_reset",
        )
    )
    assert password_history is not None

    audit_event = await session.scalar(
        select(AuditEvent).where(
            AuditEvent.entity_id == str(mentor.id),
            AuditEvent.action == "PASSWORD_RESET_BY_ADMIN",
            AuditEvent.request_id == "req-reset-password",
        )
    )
    assert audit_event is not None
    assert audit_event.after_state["must_change_password"] is True


@pytest.mark.asyncio
async def test_bulk_action_updates_status_and_audit(session: AsyncSession):
    owner_role = await _create_role(session, "platform_owner")
    consultant_role = await _create_role(session, "consultant")
    owner = await _create_user(session, owner_role, "owner@nuetra.in")
    consultant = await _create_user(session, consultant_role, "consultant@nuetra.in")
    actor = _actor_from_user(owner, permissions=["users.edit"])

    result = await people_access_service.bulk_action(
        session,
        action="suspend",
        user_ids=[consultant.id],
        actor=actor,
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id="req-bulk-suspend",
    )

    assert result.processed == 1
    assert result.affected_ids == [consultant.id]
    assert consultant.status == "SUSPENDED"
    assert consultant.is_active is False

    audit_event = await session.scalar(
        select(AuditEvent).where(
            AuditEvent.entity_id == str(consultant.id),
            AuditEvent.action == "users.bulk.suspend",
            AuditEvent.request_id == "req-bulk-suspend",
        )
    )
    assert audit_event is not None


@pytest.mark.asyncio
async def test_bulk_action_request_defaults_to_empty_user_ids():
    request = BulkActionRequest(action="activate")
    assert request.user_ids == []
