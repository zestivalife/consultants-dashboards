import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException
from app.db.models.owner_access import UserRole
from app.db.models.role import Role
from app.services.password_service import password_service
from app.services.user_service import CreateUserCommand, user_service


async def _role(session: AsyncSession, name: str) -> Role:
    role = Role(id=uuid.uuid4(), name=name, description=f"{name} role")
    session.add(role)
    await session.flush()
    return role


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "role_name",
    [
        "platform_owner",
        "organization_admin",
        "practitioner",
        "mentor",
        "consultant",
        "corporate_admin",
        "team_member",
        "future_role",
    ],
)
async def test_shared_user_service_creates_identity_for_every_role(session: AsyncSession, role_name: str):
    role = await _role(session, role_name)

    created = await user_service.create_user(
        session,
        CreateUserCommand(
            email=f"{role_name}@identity.test",
            role_name=role.name,
            password="Correct123!Z",
            first_name="Identity",
            status="ACTIVE",
            is_verified=True,
            audit_event_type="TEST_USER_CREATED",
        ),
    )

    assert created.user.email == f"{role_name}@identity.test"
    assert created.user.role_id == role.id
    assert created.user.email_verified is True
    assert created.user.password_changed_at is not None
    assert password_service.verify_password("Correct123!Z", created.user.password_hash)

    user_role = await session.scalar(
        select(UserRole).where(UserRole.user_id == created.user.id, UserRole.role_id == role.id)
    )
    assert user_role is not None
    assert user_role.is_primary is True


@pytest.mark.asyncio
async def test_shared_user_service_rejects_duplicate_email(session: AsyncSession):
    await _role(session, "consultant")
    command = CreateUserCommand(
        email="duplicate@identity.test",
        role_name="consultant",
        password="Correct123!Z",
        status="ACTIVE",
        is_verified=True,
    )
    await user_service.create_user(session, command)

    with pytest.raises(ConflictException, match="already exists"):
        await user_service.create_user(session, command)


@pytest.mark.asyncio
async def test_shared_user_service_generates_temporary_password(session: AsyncSession):
    await _role(session, "mentor")

    created = await user_service.create_user(
        session,
        CreateUserCommand(
            email="mentor.provisioning@identity.test",
            role_name="mentor",
        ),
    )

    assert created.is_temporary_password is True
    assert created.user.status == "ACTIVE"
    assert created.user.email_verified is True
    assert created.user.must_change_password is True
    assert created.user.password_changed_at is None
    assert password_service.verify_password(created.plain_password, created.user.password_hash)
