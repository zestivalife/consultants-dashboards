import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, ForbiddenException
from app.core.security import hash_token
from app.core.password_policy import WeakPasswordException
from app.db.models.owner_access import AuditEvent, InvitationEmailOutbox, Permission, RolePermission, UserInvitation, UserRole
from app.db.models.role import Role
from app.db.models.user import PasswordHistory, User
from app.schemas.auth import UserResponse
from app.schemas.people_access import CredentialCreateRequest, InvitationCreateRequest, ManagedUserCreateRequest, ManagedUserUpdateRequest
from app.services import people_access_service
from app.services.password_service import password_service


@pytest.fixture(autouse=True)
def fake_invitation_email_service(monkeypatch):
    sent_messages: list[dict] = []

    class FakeEmailService:
        def send_invitation_link(self, **kwargs):
            sent_messages.append(kwargs)

    monkeypatch.setattr(people_access_service, "get_email_service", lambda: FakeEmailService())
    return sent_messages


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


async def _accepted_invitation(session: AsyncSession, email: str = "credential.consultant@zestiva.in") -> tuple[UserInvitation, str]:
    owner_role = await _create_role(session, f"platform_owner_{uuid.uuid4().hex[:8]}")
    consultant_role = await _create_role(session, f"consultant_{uuid.uuid4().hex[:8]}")
    owner = await _create_user(session, owner_role, f"owner-{uuid.uuid4().hex[:8]}@zestiva.in", first_name="Owner")
    actor = _actor_from_user(owner, permissions=["users.invite"])

    invitation = await people_access_service.create_invitation(
        session,
        InvitationCreateRequest(email=email, role=consultant_role.name),
        actor=actor,
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id=f"req-invite-create-{uuid.uuid4().hex[:8]}",
    )
    raw_token = "test-invitation-token-" + uuid.uuid4().hex + uuid.uuid4().hex
    invitation_row = await session.scalar(select(UserInvitation).where(UserInvitation.id == invitation.id))
    invitation_row.token_hash = hash_token(raw_token)
    invitation_row.token_fingerprint = invitation_row.token_hash[:12]
    invitation_row.token = f"redacted:{invitation_row.id}"

    await people_access_service.accept_invitation(
        session,
        raw_token,
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id=f"req-invite-accept-{uuid.uuid4().hex[:8]}",
    )
    return invitation_row, raw_token


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
async def test_create_user_generates_temporary_credentials_and_primary_role(session: AsyncSession):
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
    assert detail.status == "ACTIVE"
    assert detail.must_change_password is True
    assert detail.temporary_credentials.username == "consultant@nuetra.in"
    assert detail.temporary_credentials.temporary_password

    invitation = await session.scalar(select(UserInvitation).where(UserInvitation.email == "consultant@nuetra.in"))
    assert invitation is None

    created_user = await session.scalar(select(User).where(User.email == "consultant@nuetra.in"))
    assert created_user is not None
    assert created_user.status == "ACTIVE"
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
        select(UserRole)
        .where(UserRole.user_id == detail.id, UserRole.role_id == consultant_role.id)
    )
    assert user_role is not None
    assert user_role.is_primary is True

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
async def test_create_invitation_hashes_token_and_queues_email_event(session: AsyncSession):
    owner_role = await _create_role(session, "platform_owner")
    consultant_role = await _create_role(session, "consultant")
    owner = await _create_user(session, owner_role, "owner@nuetra.in", first_name="Owner")
    actor = _actor_from_user(owner, permissions=["users.invite"])

    invitation = await people_access_service.create_invitation(
        session,
        InvitationCreateRequest(
            email="new.consultant@zestiva.in",
            role="consultant",
            first_name="Nisha",
            last_name="Rao",
            country_code="+91",
            mobile_number="9876543210",
        ),
        actor=actor,
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id="req-invite-create",
    )

    invitation_row = await session.scalar(select(UserInvitation).where(UserInvitation.id == invitation.id))
    assert invitation_row is not None
    assert invitation_row.invited_role_id == consultant_role.id
    assert invitation.first_name == "Nisha"
    assert invitation.last_name == "Rao"
    assert invitation.mobile_number == "9876543210"
    assert invitation.country_code == "+91"
    assert invitation.invitation_url.endswith(f"/invite/{invitation.invitation_url.rsplit('/', 1)[-1]}")
    assert invitation_row.first_name == "Nisha"
    assert invitation_row.last_name == "Rao"
    assert invitation_row.mobile_number == "9876543210"
    assert invitation_row.country_code == "+91"
    assert invitation_row.token.startswith("redacted:")
    assert invitation_row.token_hash
    assert invitation_row.token_hash != invitation_row.token
    assert invitation_row.token_fingerprint == invitation_row.token_hash[:12]
    assert invitation.token_fingerprint == invitation_row.token_fingerprint
    assert invitation.invitation_url
    assert invitation_row.token_hash not in invitation.invitation_url

    outbox = await session.scalar(
        select(InvitationEmailOutbox).where(
            InvitationEmailOutbox.invitation_id == invitation_row.id,
            InvitationEmailOutbox.event_type == "INVITATION_CREATED",
        )
    )
    assert outbox is not None
    assert outbox.email == "new.consultant@zestiva.in"
    assert outbox.event_type == "INVITATION_CREATED"
    assert outbox.status == "SENT"
    assert outbox.sent_at is not None
    assert outbox.attempts == 1
    assert "token" not in outbox.payload

    whatsapp_outbox = await session.scalar(
        select(InvitationEmailOutbox).where(
            InvitationEmailOutbox.invitation_id == invitation_row.id,
            InvitationEmailOutbox.event_type == "INVITATION_CREATED_WHATSAPP",
        )
    )
    assert whatsapp_outbox is not None
    assert whatsapp_outbox.status == "PENDING"
    assert whatsapp_outbox.payload["delivery_channel"] == "WHATSAPP"
    assert whatsapp_outbox.payload["requires_phone_number"] is True
    assert "token" not in whatsapp_outbox.payload


@pytest.mark.asyncio
async def test_regenerate_invitation_link_rotates_hash_and_returns_transient_url(session: AsyncSession):
    owner_role = await _create_role(session, "platform_owner")
    await _create_role(session, "consultant")
    owner = await _create_user(session, owner_role, "owner@nuetra.in", first_name="Owner")
    actor = _actor_from_user(owner, permissions=["users.invite"])

    invitation = await people_access_service.create_invitation(
        session,
        InvitationCreateRequest(email="regenerate.consultant@zestiva.in", role="consultant"),
        actor=actor,
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id="req-invite-regenerate-create",
    )
    invitation_row = await session.scalar(select(UserInvitation).where(UserInvitation.id == invitation.id))
    original_hash = invitation_row.token_hash
    original_fingerprint = invitation_row.token_fingerprint

    regenerated = await people_access_service.regenerate_invitation_link(
        session,
        invitation.id,
        actor=actor,
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id="req-invite-regenerate",
    )

    assert regenerated.status == "INVITED"
    assert regenerated.invitation_url
    assert regenerated.invitation_url.startswith("http")
    assert invitation_row.token.startswith("redacted:")
    assert invitation_row.token_hash != original_hash
    assert invitation_row.token_fingerprint != original_fingerprint
    assert invitation_row.token_fingerprint == invitation_row.token_hash[:12]
    assert invitation_row.token_hash not in regenerated.invitation_url

    outbox_event = await session.scalar(
        select(InvitationEmailOutbox).where(
            InvitationEmailOutbox.invitation_id == invitation.id,
            InvitationEmailOutbox.event_type == "INVITATION_LINK_REGENERATED",
        )
    )
    assert outbox_event is not None
    assert outbox_event.status == "PENDING"
    assert "token" not in outbox_event.payload

    audit_event = await session.scalar(
        select(AuditEvent)
        .where(
            AuditEvent.entity_type == "user_invitation",
            AuditEvent.entity_id == str(invitation.id),
            AuditEvent.action == "INVITATION_LINK_REGENERATED",
            AuditEvent.request_id == "req-invite-regenerate",
        )
    )
    assert audit_event is not None
    assert audit_event.after_state["token_fingerprint"] == invitation_row.token_fingerprint


@pytest.mark.asyncio
async def test_create_invitation_rejects_duplicate_open_invitation(session: AsyncSession):
    owner_role = await _create_role(session, "platform_owner")
    await _create_role(session, "consultant")
    owner = await _create_user(session, owner_role, "owner@nuetra.in", first_name="Owner")
    actor = _actor_from_user(owner, permissions=["users.invite"])
    payload = InvitationCreateRequest(email="duplicate@zestiva.in", role="consultant")

    await people_access_service.create_invitation(
        session,
        payload,
        actor=actor,
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id="req-invite-duplicate-1",
    )

    with pytest.raises(ConflictException):
        await people_access_service.create_invitation(
            session,
            payload,
            actor=actor,
            ip_address="127.0.0.1",
            user_agent="pytest",
            request_id="req-invite-duplicate-2",
        )


@pytest.mark.asyncio
async def test_resend_invitation_rotates_token_hash_and_queues_outbox(session: AsyncSession):
    owner_role = await _create_role(session, "platform_owner")
    await _create_role(session, "consultant")
    owner = await _create_user(session, owner_role, "owner@nuetra.in", first_name="Owner")
    actor = _actor_from_user(owner, permissions=["users.invite"])

    invitation = await people_access_service.create_invitation(
        session,
        InvitationCreateRequest(email="resend.consultant@zestiva.in", role="consultant"),
        actor=actor,
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id="req-invite-resend-create",
    )
    invitation_row = await session.scalar(select(UserInvitation).where(UserInvitation.id == invitation.id))
    original_hash = invitation_row.token_hash

    resent = await people_access_service.resend_invitation(
        session,
        invitation.id,
        actor=actor,
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id="req-invite-resend",
    )

    assert resent.status == "INVITED"
    assert invitation_row.token.startswith("redacted:")
    assert invitation_row.token_hash != original_hash
    assert invitation_row.token_fingerprint == invitation_row.token_hash[:12]
    assert resent.invitation_url
    assert invitation_row.token_hash not in resent.invitation_url

    outbox_events = (
        await session.scalars(
            select(InvitationEmailOutbox)
            .where(InvitationEmailOutbox.invitation_id == invitation.id)
            .order_by(InvitationEmailOutbox.created_at)
        )
    ).all()
    assert sorted(event.event_type for event in outbox_events) == sorted([
        "INVITATION_CREATED",
        "INVITATION_CREATED_WHATSAPP",
        "INVITATION_RESENT",
        "INVITATION_RESENT_WHATSAPP",
    ])
    statuses_by_type = {event.event_type: event.status for event in outbox_events}
    assert statuses_by_type["INVITATION_CREATED"] == "SENT"
    assert statuses_by_type["INVITATION_CREATED_WHATSAPP"] == "PENDING"
    assert statuses_by_type["INVITATION_RESENT"] == "SENT"
    assert statuses_by_type["INVITATION_RESENT_WHATSAPP"] == "PENDING"


@pytest.mark.asyncio
async def test_expire_invitation_updates_status_and_audit(session: AsyncSession):
    owner_role = await _create_role(session, "platform_owner")
    await _create_role(session, "consultant")
    owner = await _create_user(session, owner_role, "owner@nuetra.in", first_name="Owner")
    actor = _actor_from_user(owner, permissions=["users.invite"])

    invitation = await people_access_service.create_invitation(
        session,
        InvitationCreateRequest(email="expire.consultant@zestiva.in", role="consultant"),
        actor=actor,
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id="req-invite-expire-create",
    )

    expired = await people_access_service.expire_invitation(
        session,
        invitation.id,
        actor=actor,
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id="req-invite-expire",
    )

    assert expired.status == "EXPIRED"
    invitation_row = await session.scalar(select(UserInvitation).where(UserInvitation.id == invitation.id))
    assert invitation_row.status == "EXPIRED"
    assert invitation_row.expires_at is not None

    audit_event = await session.scalar(
        select(AuditEvent)
        .where(
            AuditEvent.entity_type == "user_invitation",
            AuditEvent.entity_id == str(invitation.id),
            AuditEvent.action == "INVITATION_EXPIRED",
            AuditEvent.request_id == "req-invite-expire",
        )
    )
    assert audit_event is not None
    assert audit_event.after_state["status"] == "EXPIRED"


@pytest.mark.asyncio
async def test_cancel_invitation_updates_status_and_audit(session: AsyncSession):
    owner_role = await _create_role(session, "platform_owner")
    await _create_role(session, "consultant")
    owner = await _create_user(session, owner_role, "owner@nuetra.in", first_name="Owner")
    actor = _actor_from_user(owner, permissions=["users.invite"])

    invitation = await people_access_service.create_invitation(
        session,
        InvitationCreateRequest(email="cancel.consultant@zestiva.in", role="consultant"),
        actor=actor,
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id="req-invite-cancel-create",
    )

    cancelled = await people_access_service.cancel_invitation(
        session,
        invitation.id,
        actor=actor,
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id="req-invite-cancel",
    )

    assert cancelled.status == "CANCELLED"
    invitation_row = await session.scalar(select(UserInvitation).where(UserInvitation.id == invitation.id))
    assert invitation_row.status == "CANCELLED"
    assert invitation_row.cancelled_at is not None

    audit_event = await session.scalar(
        select(AuditEvent)
        .where(
            AuditEvent.entity_type == "user_invitation",
            AuditEvent.entity_id == str(invitation.id),
            AuditEvent.action == "INVITATION_CANCELLED",
            AuditEvent.request_id == "req-invite-cancel",
        )
    )
    assert audit_event is not None
    assert audit_event.after_state["status"] == "CANCELLED"

    revoked_event = await session.scalar(
        select(AuditEvent)
        .where(
            AuditEvent.entity_type == "user_invitation",
            AuditEvent.entity_id == str(invitation.id),
            AuditEvent.action == "INVITATION_REVOKED",
            AuditEvent.request_id == "req-invite-cancel",
        )
    )
    assert revoked_event is not None

    outbox_event = await session.scalar(
        select(InvitationEmailOutbox).where(
            InvitationEmailOutbox.invitation_id == invitation.id,
            InvitationEmailOutbox.event_type == "INVITATION_REVOKED",
        )
    )
    assert outbox_event is not None
    assert outbox_event.status == "PENDING"


@pytest.mark.asyncio
async def test_validate_invitation_token_uses_hash_lookup(session: AsyncSession):
    owner_role = await _create_role(session, "platform_owner")
    await _create_role(session, "consultant")
    owner = await _create_user(session, owner_role, "owner@nuetra.in", first_name="Owner")
    actor = _actor_from_user(owner, permissions=["users.invite"])

    invitation = await people_access_service.create_invitation(
        session,
        InvitationCreateRequest(email="validate.consultant@zestiva.in", role="consultant"),
        actor=actor,
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id="req-invite-validate-create",
    )
    raw_token = "test-invitation-token-" + "x" * 48
    invitation_row = await session.scalar(select(UserInvitation).where(UserInvitation.id == invitation.id))
    invitation_row.token = f"redacted:{invitation_row.id}"
    invitation_row.token_hash = hash_token(raw_token)
    invitation_row.token_fingerprint = invitation_row.token_hash[:12]

    validated = await people_access_service.validate_invitation_token(
        session,
        raw_token,
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id="req-invite-validate-open",
    )

    assert validated.invitation_id == invitation.id
    assert validated.email == "validate.consultant@zestiva.in"
    assert validated.role == "consultant"
    assert validated.next_step == "ACCEPT_INVITATION"
    assert validated.redirect_url == "/onboarding/password/setup"

    audit_event = await session.scalar(
        select(AuditEvent).where(
            AuditEvent.entity_id == str(invitation.id),
            AuditEvent.action == "INVITATION_OPENED",
            AuditEvent.request_id == "req-invite-validate-open",
        )
    )
    assert audit_event is not None
    assert audit_event.after_state["token_fingerprint"] == invitation_row.token_fingerprint


@pytest.mark.asyncio
async def test_accept_invitation_creates_pending_user_and_audit(session: AsyncSession):
    owner_role = await _create_role(session, "platform_owner")
    consultant_role = await _create_role(session, "consultant")
    owner = await _create_user(session, owner_role, "owner@nuetra.in", first_name="Owner")
    actor = _actor_from_user(owner, permissions=["users.invite"])

    invitation = await people_access_service.create_invitation(
        session,
        InvitationCreateRequest(email="accept.consultant@zestiva.in", role="consultant"),
        actor=actor,
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id="req-invite-accept-create",
    )
    raw_token = "test-invitation-token-" + "y" * 48
    invitation_row = await session.scalar(select(UserInvitation).where(UserInvitation.id == invitation.id))
    invitation_row.token_hash = hash_token(raw_token)
    invitation_row.token_fingerprint = invitation_row.token_hash[:12]

    accepted = await people_access_service.accept_invitation(
        session,
        raw_token,
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id="req-invite-accept",
    )

    assert accepted.email == "accept.consultant@zestiva.in"
    assert accepted.status == "ACCEPTED"
    assert accepted.next_step == "PASSWORD_SETUP"
    assert accepted.redirect_url == "/onboarding/password/setup"
    assert invitation_row.status == "ACCEPTED"
    assert invitation_row.accepted_at is not None

    user = await session.scalar(select(User).where(User.email == "accept.consultant@zestiva.in"))
    assert user is not None
    assert user.id == accepted.user_id
    assert user.role_id == consultant_role.id
    assert user.status == "PENDING_VERIFICATION"
    assert user.is_active is False
    assert user.is_verified is False

    audit_event = await session.scalar(
        select(AuditEvent)
        .where(
            AuditEvent.entity_type == "user_invitation",
            AuditEvent.entity_id == str(invitation.id),
            AuditEvent.action == "INVITATION_ACCEPTED",
            AuditEvent.request_id == "req-invite-accept",
        )
    )
    assert audit_event is not None
    assert audit_event.after_state["next_step"] == "PASSWORD_SETUP"

    outbox_event = await session.scalar(
        select(InvitationEmailOutbox).where(
            InvitationEmailOutbox.invitation_id == invitation.id,
            InvitationEmailOutbox.event_type == "INVITATION_ACCEPTED",
        )
    )
    assert outbox_event is not None
    assert outbox_event.status == "PENDING"
    assert outbox_event.payload["token_fingerprint"] == invitation_row.token_fingerprint

    with pytest.raises(ConflictException, match="already been accepted"):
        await people_access_service.accept_invitation(
            session,
            raw_token,
            ip_address="127.0.0.1",
            user_agent="pytest",
            request_id="req-invite-accept-replay",
        )


@pytest.mark.asyncio
async def test_validate_invitation_token_expires_and_audits(session: AsyncSession):
    owner_role = await _create_role(session, "platform_owner")
    await _create_role(session, "consultant")
    owner = await _create_user(session, owner_role, "owner@nuetra.in", first_name="Owner")
    actor = _actor_from_user(owner, permissions=["users.invite"])

    invitation = await people_access_service.create_invitation(
        session,
        InvitationCreateRequest(email="expired.consultant@zestiva.in", role="consultant"),
        actor=actor,
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id="req-invite-expired-create",
    )
    raw_token = "test-invitation-token-" + "e" * 48
    invitation_row = await session.scalar(select(UserInvitation).where(UserInvitation.id == invitation.id))
    invitation_row.token_hash = hash_token(raw_token)
    invitation_row.token_fingerprint = invitation_row.token_hash[:12]
    invitation_row.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)

    with pytest.raises(ConflictException, match="expired"):
        await people_access_service.validate_invitation_token(
            session,
            raw_token,
            ip_address="127.0.0.1",
            user_agent="pytest",
            request_id="req-invite-expired-validate",
        )

    assert invitation_row.status == "EXPIRED"
    audit_event = await session.scalar(
        select(AuditEvent).where(
            AuditEvent.entity_id == str(invitation.id),
            AuditEvent.action == "INVITATION_EXPIRED",
            AuditEvent.request_id == "req-invite-expired-validate",
        )
    )
    assert audit_event is not None


@pytest.mark.asyncio
async def test_password_setup_initiation_requires_accepted_invitation(session: AsyncSession):
    owner_role = await _create_role(session, "platform_owner")
    await _create_role(session, "consultant")
    owner = await _create_user(session, owner_role, "owner@nuetra.in", first_name="Owner")
    actor = _actor_from_user(owner, permissions=["users.invite"])

    invitation = await people_access_service.create_invitation(
        session,
        InvitationCreateRequest(email="password.consultant@zestiva.in", role="consultant"),
        actor=actor,
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id="req-invite-password-create",
    )
    raw_token = "test-invitation-token-" + "z" * 48
    invitation_row = await session.scalar(select(UserInvitation).where(UserInvitation.id == invitation.id))
    invitation_row.token_hash = hash_token(raw_token)
    invitation_row.token_fingerprint = invitation_row.token_hash[:12]

    with pytest.raises(ConflictException):
        await people_access_service.initiate_password_setup(
            session,
            raw_token,
            ip_address="127.0.0.1",
            user_agent="pytest",
            request_id="req-invite-password-early",
        )

    accepted = await people_access_service.accept_invitation(
        session,
        raw_token,
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id="req-invite-password-accept",
    )
    initiated = await people_access_service.initiate_password_setup(
        session,
        raw_token,
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id="req-invite-password-init",
    )

    assert initiated.user_id == accepted.user_id
    assert initiated.next_step == "PASSWORD_CREATE"

    audit_event = await session.scalar(
        select(AuditEvent)
        .where(
            AuditEvent.entity_type == "user_invitation",
            AuditEvent.entity_id == str(invitation.id),
            AuditEvent.action == "PASSWORD_SETUP_INITIATED",
            AuditEvent.request_id == "req-invite-password-init",
        )
    )
    assert audit_event is not None


@pytest.mark.asyncio
async def test_create_credentials_persists_password_history_outbox_and_audit(session: AsyncSession):
    invitation, raw_token = await _accepted_invitation(session, "credential.success@zestiva.in")

    result = await people_access_service.create_credentials(
        session,
        CredentialCreateRequest(
            token=raw_token,
            password="CredentialPass123!",
            confirm_password="CredentialPass123!",
        ),
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id="req-credential-create",
    )

    user = await session.scalar(select(User).where(User.id == result.user_id))
    assert result.invitation_id == invitation.id
    assert result.email == "credential.success@zestiva.in"
    assert result.status == "PASSWORD_CREATED"
    assert result.next_step == "LOGIN"
    assert result.redirect_url == "/login"
    assert invitation.status == "PASSWORD_CREATED"
    assert user is not None
    assert password_service.verify_password("CredentialPass123!", user.password_hash)
    assert user.password_changed_at is not None
    assert user.status == "PENDING_PROFILE"
    assert user.is_active is False
    assert user.is_verified is False

    history = await session.scalar(
        select(PasswordHistory).where(
            PasswordHistory.user_id == user.id,
            PasswordHistory.source == "credential_creation",
        )
    )
    assert history is not None
    assert password_service.verify_password("CredentialPass123!", history.password_hash)

    outbox_event = await session.scalar(
        select(InvitationEmailOutbox).where(
            InvitationEmailOutbox.invitation_id == invitation.id,
            InvitationEmailOutbox.event_type == "PASSWORD_CREATED",
        )
    )
    assert outbox_event is not None
    assert outbox_event.status == "PENDING"
    assert outbox_event.payload["next_step"] == "LOGIN"

    consumed_audit = await session.scalar(
        select(AuditEvent).where(
            AuditEvent.entity_id == str(invitation.id),
            AuditEvent.action == "INVITATION_CONSUMED",
            AuditEvent.request_id == "req-credential-create",
        )
    )
    assert consumed_audit is not None

    password_audit = await session.scalar(
        select(AuditEvent).where(
            AuditEvent.entity_id == str(user.id),
            AuditEvent.action == "PASSWORD_CREATED",
            AuditEvent.request_id == "req-credential-create",
        )
    )
    assert password_audit is not None
    assert password_audit.after_state["token_fingerprint"] == invitation.token_fingerprint


@pytest.mark.asyncio
async def test_create_credentials_rejects_confirmation_mismatch_and_audits(session: AsyncSession):
    invitation, raw_token = await _accepted_invitation(session, "credential.mismatch@zestiva.in")

    with pytest.raises(WeakPasswordException, match="confirmation"):
        await people_access_service.create_credentials(
            session,
            CredentialCreateRequest(
                token=raw_token,
                password="CredentialPass123!",
                confirm_password="CredentialPass124!",
            ),
            ip_address="127.0.0.1",
            user_agent="pytest",
            request_id="req-credential-mismatch",
        )

    audit_event = await session.scalar(
        select(AuditEvent).where(
            AuditEvent.entity_id == str(invitation.id),
            AuditEvent.action == "PASSWORD_VALIDATION_FAILED",
            AuditEvent.request_id == "req-credential-mismatch",
        )
    )
    assert audit_event is not None
    assert "confirmation" in audit_event.after_state["reason"]
    assert invitation.status == "ACCEPTED"


@pytest.mark.asyncio
async def test_create_credentials_rejects_reused_password(session: AsyncSession):
    invitation, raw_token = await _accepted_invitation(session, "credential.reuse@zestiva.in")
    user = await session.scalar(select(User).where(User.id == invitation.user_id))
    reused_hash = password_service.hash_password("CredentialPass123!")
    user.password_hash = reused_hash
    session.add(
        PasswordHistory(
            user_id=user.id,
            password_hash=reused_hash,
            source="previous_password",
        )
    )
    await session.flush()

    with pytest.raises(WeakPasswordException, match="last 5 passwords"):
        await people_access_service.create_credentials(
            session,
            CredentialCreateRequest(
                token=raw_token,
                password="CredentialPass123!",
                confirm_password="CredentialPass123!",
            ),
            ip_address="127.0.0.1",
            user_agent="pytest",
            request_id="req-credential-reuse",
        )

    audit_event = await session.scalar(
        select(AuditEvent).where(
            AuditEvent.entity_id == str(invitation.id),
            AuditEvent.action == "PASSWORD_VALIDATION_FAILED",
            AuditEvent.request_id == "req-credential-reuse",
        )
    )
    assert audit_event is not None
    assert "last 5 passwords" in audit_event.after_state["reason"]
    assert invitation.status == "ACCEPTED"


@pytest.mark.asyncio
async def test_create_credentials_rejects_replay_after_password_created(session: AsyncSession):
    invitation, raw_token = await _accepted_invitation(session, "credential.replay@zestiva.in")

    await people_access_service.create_credentials(
        session,
        CredentialCreateRequest(
            token=raw_token,
            password="CredentialPass123!",
            confirm_password="CredentialPass123!",
        ),
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id="req-credential-replay-first",
    )

    with pytest.raises(ConflictException):
        await people_access_service.create_credentials(
            session,
            CredentialCreateRequest(
                token=raw_token,
                password="AnotherPass123!",
                confirm_password="AnotherPass123!",
            ),
            ip_address="127.0.0.1",
            user_agent="pytest",
            request_id="req-credential-replay-second",
        )


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
