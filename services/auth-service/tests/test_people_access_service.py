import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.owner_access import Permission, RolePermission, UserInvitation, UserRole
from app.db.models.role import Role
from app.db.models.user import User
from app.core.exceptions import ForbiddenException
from app.schemas.auth import UserResponse
from app.schemas.people_access import ManagedUserCreateRequest, ManagedUserUpdateRequest
from app.services import people_access_service


async def _create_role(session: AsyncSession, name: str, description: str = "") -> Role:
    role = Role(id=uuid.uuid4(), name=name, description=description or name.title())
    session.add(role)
    await session.flush()
    return role


async def _create_user(session: AsyncSession, role: Role, email: str, **overrides) -> User:
    user = User(
        id=uuid.uuid4(),
        email=email,
        password_hash="hashed-password",
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

    owner = await _create_user(
        session,
        owner_role,
        "owner@nuetra.in",
        permissions=["users.edit"],
    )

    permissions = await people_access_service.resolve_user_permissions(session, owner)
    assert permissions == ["users.read", "users.edit"]


@pytest.mark.asyncio
async def test_ensure_owner_access_allows_required_permission(session: AsyncSession):
    owner_role = await _create_role(session, "platform_owner")
    owner = await _create_user(session, owner_role, "owner@zestiva.in")
    actor = _actor_from_user(owner, permissions=["packages.manage"])

    await people_access_service.ensure_owner_access(
        session,
        actor,
        {"packages.manage"},
    )


@pytest.mark.asyncio
async def test_ensure_owner_access_rejects_role_without_required_permission(session: AsyncSession):
    owner_role = await _create_role(session, "platform_owner")
    owner = await _create_user(session, owner_role, "owner@zestiva.in")
    actor = _actor_from_user(owner, permissions=["users.read"])

    with pytest.raises(ForbiddenException):
        await people_access_service.ensure_owner_access(
            session,
            actor,
            {"packages.manage"},
        )


@pytest.mark.asyncio
async def test_ensure_owner_access_allows_any_permission_match(session: AsyncSession):
    owner_role = await _create_role(session, "platform_owner")
    owner = await _create_user(session, owner_role, "owner@zestiva.in")
    actor = _actor_from_user(owner, permissions=["users.invite"])

    await people_access_service.ensure_owner_access(
        session,
        actor,
        {"users.edit", "users.invite"},
    )


@pytest.mark.asyncio
async def test_create_user_creates_invitation_and_primary_role(session: AsyncSession):
    owner_role = await _create_role(session, "platform_owner")
    consultant_role = await _create_role(session, "consultant")
    owner = await _create_user(session, owner_role, "owner@nuetra.in", first_name="Owner")
    actor = _actor_from_user(owner, permissions=["users.create", "users.read", "users.edit"])

    payload = ManagedUserCreateRequest(
        email="consultant@nuetra.in",
        first_name="Aarav",
        last_name="Joshi",
        role="consultant",
        status="INVITED",
        permissions=["reports.view"],
    )

    detail = await people_access_service.create_user(
        session,
        payload,
        actor=actor,
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id="req-people-create",
    )

    assert detail.email == "consultant@nuetra.in"
    assert detail.role == "consultant"

    invitation = await session.scalar(select(UserInvitation).where(UserInvitation.email == "consultant@nuetra.in"))
    assert invitation is not None
    assert invitation.status == "INVITED"

    user_role = await session.scalar(
        select(UserRole)
        .where(UserRole.user_id == detail.id, UserRole.role_id == consultant_role.id)
    )
    assert user_role is not None
    assert user_role.is_primary is True


@pytest.mark.asyncio
async def test_update_user_changes_status_and_role(session: AsyncSession):
    owner_role = await _create_role(session, "platform_owner")
    consultant_role = await _create_role(session, "consultant")
    mentor_role = await _create_role(session, "mentor")
    owner = await _create_user(session, owner_role, "owner@nuetra.in", first_name="Owner")
    managed_user = await _create_user(session, consultant_role, "person@nuetra.in", first_name="Person")
    actor = _actor_from_user(owner, permissions=["users.edit", "users.read"])

    payload = ManagedUserUpdateRequest(role="mentor", status="SUSPENDED", permissions=["users.read"])
    detail = await people_access_service.update_user(
        session,
        managed_user.id,
        payload,
        actor=actor,
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id="req-people-update",
    )

    assert detail.role == "mentor"
    assert detail.status == "SUSPENDED"
    assert "users.read" in detail.permissions or detail.permissions == ["users.read"]

    user_role = await session.scalar(
        select(UserRole)
        .where(UserRole.user_id == managed_user.id, UserRole.role_id == mentor_role.id)
    )
    assert user_role is not None
    assert user_role.is_primary is True
