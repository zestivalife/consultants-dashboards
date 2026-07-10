import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.email import get_email_service
from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException
from app.core.security import hash_password
from app.db.models.owner_access import (
    AuditEvent,
    LoginSession,
    Organization,
    Permission,
    UserInvitation,
    UserNote,
    UserStatusHistory,
)
from app.db.models.user import User
from app.repositories.people_access_repository import PeopleAccessRepository
from app.schemas.auth import UserResponse
from app.schemas.people_access import (
    BulkActionResponse,
    ManagedUserCreateRequest,
    ManagedUserUpdateRequest,
    OrganizationCreateRequest,
    OrganizationResponse,
    PeopleAccessAuditItem,
    PeopleAccessDistributionItem,
    PeopleAccessInvitationItem,
    PeopleAccessMetadataResponse,
    PeopleAccessSummaryMetric,
    PeopleAccessSummaryResponse,
    PeopleAccessUserRow,
    PeopleAccessUsersResponse,
    PermissionCatalogItem,
    RolePermissionMatrixRow,
    UserAttachmentItem,
    UserNoteCreateRequest,
    UserNoteItem,
    UserProfileDetail,
    UserRoleAssignment,
    UserStatusHistoryItem,
    LoginSessionItem,
    MembershipSummary,
)


OWNER_ROLE_NAMES = {"superuser", "platform_owner"}
MANAGEABLE_STATUSES = {"INVITED", "PENDING_VERIFICATION", "ACTIVE", "INACTIVE", "LOCKED", "SUSPENDED", "DELETED"}
ROLE_ALIASES = {
    "platform owner": "platform_owner",
    "organization admin": "organization_admin",
    "corporate admin": "corporate_admin",
    "senior consultant": "senior_consultant",
    "support admin": "support_admin",
}


def normalize_role_name(role_name: str) -> str:
    compact = role_name.strip().lower().replace("-", "_").replace(" ", "_")
    return ROLE_ALIASES.get(compact, compact)


def _display_name(user: User | None) -> str:
    if not user:
        return "System"
    name = " ".join(value for value in [user.first_name, user.last_name] if value)
    return name or user.email


def _normalize_status(status: str | None) -> str:
    normalized = (status or "ACTIVE").strip().upper()
    if normalized not in MANAGEABLE_STATUSES:
        raise ForbiddenException(f"Unsupported user status '{status}'")
    return normalized


def _browser_from_user_agent(user_agent: str | None) -> tuple[str | None, str | None]:
    if not user_agent:
        return None, None
    browser = "Unknown"
    if "Chrome" in user_agent:
        browser = "Chrome"
    elif "Safari" in user_agent:
        browser = "Safari"
    elif "Firefox" in user_agent:
        browser = "Firefox"

    platform = "Unknown"
    if "Mac OS X" in user_agent or "Macintosh" in user_agent:
        platform = "macOS"
    elif "Windows" in user_agent:
        platform = "Windows"
    elif "Linux" in user_agent:
        platform = "Linux"
    elif "Android" in user_agent:
        platform = "Android"
    elif "iPhone" in user_agent or "iPad" in user_agent:
        platform = "iOS"
    return browser, platform


async def resolve_user_permissions(session: AsyncSession, user: User) -> list[str]:
    repo = PeopleAccessRepository(session)
    role_permissions = await repo.get_role_permissions([user.role_id])
    permissions = list(role_permissions.get(user.role_id, []))
    for permission in user.permissions or []:
        if permission not in permissions:
            permissions.append(permission)
    return permissions


async def ensure_owner_access(session: AsyncSession, current_user: UserResponse) -> None:
    role_name = (current_user.role or "").lower()
    if role_name in OWNER_ROLE_NAMES:
        return
    permission_set = set(current_user.permissions or [])
    if "users.read" not in permission_set and "users.create" not in permission_set:
        raise ForbiddenException("Platform owner access is required")


def _membership_to_summary(membership) -> MembershipSummary:
    return MembershipSummary(
        id=membership.id,
        organization_id=membership.organization_id,
        organization=membership.organization.name if membership.organization else "Unassigned",
        department_id=membership.department_id,
        department=membership.department.name if membership.department else None,
        employee_id=membership.employee_id,
        package=membership.package_name,
        practitioner_id=membership.assigned_practitioner_id,
        practitioner=_display_name(membership.assigned_practitioner),
        mentor_id=membership.assigned_mentor_id,
        mentor=_display_name(membership.assigned_mentor),
        consultant_id=membership.assigned_consultant_id,
        consultant=_display_name(membership.assigned_consultant),
        status=membership.status,
        verification="Verified" if membership.is_verified else "Pending verification",
        tags=membership.tags or [],
        joined_at=membership.joined_at,
    )


def _user_to_row(user: User) -> PeopleAccessUserRow:
    membership = user.organization_memberships[0] if user.organization_memberships else None
    return PeopleAccessUserRow(
        id=user.id,
        avatar=user.avatar_url,
        name=_display_name(user),
        email=user.email,
        phone=user.phone,
        employee_id=membership.employee_id if membership else None,
        organization=membership.organization.name if membership and membership.organization else None,
        department=membership.department.name if membership and membership.department else None,
        role=user.role.name if user.role else "member",
        status=user.status,
        verification="Verified" if user.is_verified else "Pending verification",
        package=membership.package_name if membership else None,
        practitioner=_display_name(membership.assigned_practitioner) if membership else None,
        mentor=_display_name(membership.assigned_mentor) if membership else None,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
        tags=membership.tags if membership else [],
    )


async def get_summary(session: AsyncSession) -> PeopleAccessSummaryResponse:
    repo = PeopleAccessRepository(session)
    counts = await repo.get_summary_counts()
    pending_invitations = await repo.pending_invitations()
    recent_events = await repo.recent_audit_events()
    role_distribution = await repo.role_distribution()
    org_distribution = await repo.organization_distribution()

    return PeopleAccessSummaryResponse(
        metrics=[
            PeopleAccessSummaryMetric(label="People", value=counts["users"]),
            PeopleAccessSummaryMetric(label="Organizations", value=counts["organizations"]),
            PeopleAccessSummaryMetric(label="Invited", value=counts["invited"]),
            PeopleAccessSummaryMetric(label="Suspended", value=counts["suspended"]),
            PeopleAccessSummaryMetric(label="Pending approvals", value=counts["pending_invitations"]),
        ],
        role_distribution=[
            PeopleAccessDistributionItem(label=name.replace("_", " ").title(), value=value)
            for name, value in role_distribution
        ],
        organization_distribution=[
            PeopleAccessDistributionItem(label=name, value=value)
            for name, value in org_distribution
        ],
        pending_invitations=[
            PeopleAccessInvitationItem(
                id=invite.id,
                email=invite.email,
                role=invite.role.name if invite.role else None,
                organization=invite.organization.name if invite.organization else None,
                status=invite.status,
                created_at=invite.created_at,
                expires_at=invite.expires_at,
            )
            for invite in pending_invitations
        ],
        recent_activity=[
            PeopleAccessAuditItem(
                id=event.id,
                actor="Platform action" if event.actor_user_id else "System",
                action=event.action,
                entity_type=event.entity_type,
                entity_id=event.entity_id,
                created_at=event.created_at,
                request_id=event.request_id,
            )
            for event in recent_events
        ],
    )


async def list_users(
    session: AsyncSession,
    *,
    search: str | None = None,
    role: str | None = None,
    organization_id: uuid.UUID | None = None,
    department_id: uuid.UUID | None = None,
    status: str | None = None,
    verification: str | None = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> PeopleAccessUsersResponse:
    repo = PeopleAccessRepository(session)
    users, total = await repo.list_users(
        search=search,
        role=normalize_role_name(role) if role else None,
        organization_id=organization_id,
        department_id=department_id,
        status=_normalize_status(status) if status else None,
        verification=verification,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return PeopleAccessUsersResponse(
        items=[_user_to_row(user) for user in users],
        pagination=repo.build_pagination(page, page_size, total),
    )


async def get_metadata(session: AsyncSession) -> PeopleAccessMetadataResponse:
    repo = PeopleAccessRepository(session)
    roles_with_counts = await repo.list_roles_with_counts()
    role_permissions = await repo.get_role_permissions([role.id for role, _ in roles_with_counts])
    permissions = await repo.list_permissions()
    organizations = await repo.list_organizations()
    departments = await repo.list_departments()
    practitioners = await repo.list_assignable_users(["practitioner", "consultant", "senior_consultant"])
    mentors = await repo.list_assignable_users(["mentor", "support_admin"])
    consultants = await repo.list_assignable_users(["consultant", "senior_consultant"])

    return PeopleAccessMetadataResponse(
        roles=[
            RolePermissionMatrixRow(
                id=role.id,
                name=role.name.replace("_", " ").title(),
                description=role.description,
                users=user_count,
                cloneable=role.name not in {"superuser", "platform_owner"},
                permissions=role_permissions.get(role.id, []),
            )
            for role, user_count in roles_with_counts
        ],
        permissions=[
            PermissionCatalogItem(
                id=permission.id,
                key=permission.key,
                module=permission.module,
                label=permission.label,
                description=permission.description,
            )
            for permission in permissions
        ],
        organizations=[
            {"id": org.id, "name": org.name, "status": org.status}
            for org in organizations
        ],
        departments=[
            {"id": department.id, "organization_id": department.organization_id, "name": department.name}
            for department in departments
        ],
        practitioners=[_user_to_row(user) for user in practitioners],
        mentors=[_user_to_row(user) for user in mentors],
        consultants=[_user_to_row(user) for user in consultants],
    )


async def get_user_detail(session: AsyncSession, user_id: uuid.UUID) -> UserProfileDetail:
    repo = PeopleAccessRepository(session)
    user = await repo.get_user_detail(user_id)
    if user is None:
        raise NotFoundException("User not found")

    return UserProfileDetail(
        id=user.id,
        avatar=user.avatar_url,
        first_name=user.first_name,
        last_name=user.last_name,
        name=_display_name(user),
        email=user.email,
        phone=user.phone,
        role=user.role.name if user.role else "member",
        roles=[
            UserRoleAssignment(
                id=user_role.role.id,
                name=user_role.role.name.replace("_", " ").title(),
                description=user_role.role.description,
                is_primary=user_role.is_primary,
            )
            for user_role in user.user_roles
        ],
        permissions=await resolve_user_permissions(session, user),
        professional_title=user.industry,
        status=user.status,
        verification="Verified" if user.is_verified else "Pending verification",
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        memberships=[_membership_to_summary(membership) for membership in user.organization_memberships],
        sessions=[
            LoginSessionItem(
                id=session_item.id,
                browser=session_item.browser,
                platform=session_item.platform,
                ip_address=session_item.ip_address,
                status=session_item.status,
                created_at=session_item.created_at,
                last_seen_at=session_item.last_seen_at,
                revoked_at=session_item.revoked_at,
            )
            for session_item in sorted(user.login_sessions, key=lambda item: item.created_at, reverse=True)
        ],
        notes=[
            UserNoteItem(
                id=note.id,
                body=note.body,
                author=_display_name(note.author),
                created_at=note.created_at,
                updated_at=note.updated_at,
            )
            for note in sorted(user.notes, key=lambda item: item.created_at, reverse=True)
        ],
        attachments=[
            UserAttachmentItem(
                id=attachment.id,
                file_name=attachment.file_name,
                file_url=attachment.file_url,
                content_type=attachment.content_type,
                created_at=attachment.created_at,
            )
            for attachment in sorted(user.attachments, key=lambda item: item.created_at, reverse=True)
        ],
        status_history=[
            UserStatusHistoryItem(
                id=history.id,
                previous_status=history.previous_status,
                new_status=history.new_status,
                reason=history.reason,
                changed_by=_display_name(history.changed_by),
                created_at=history.created_at,
            )
            for history in sorted(user.status_history, key=lambda item: item.created_at, reverse=True)
        ],
    )


async def create_user(
    session: AsyncSession,
    payload: ManagedUserCreateRequest,
    *,
    actor: UserResponse,
    ip_address: str | None,
    user_agent: str | None,
    request_id: str | None,
) -> UserProfileDetail:
    repo = PeopleAccessRepository(session)
    email = payload.email.lower().strip()
    if await repo.get_user_by_email(email):
        raise ConflictException("A user with this email already exists")

    role_name = normalize_role_name(payload.role)
    role = await repo.get_role_by_name(role_name)
    if role is None:
        raise NotFoundException(f"Role '{payload.role}' not found")

    organization = None
    if payload.organization_id:
        organization = await repo.get_organization(payload.organization_id)
        if organization is None:
            raise NotFoundException("Organization not found")

    if payload.department_id:
        department = await repo.get_department(payload.department_id)
        if department is None:
            raise NotFoundException("Department not found")

    status = _normalize_status(payload.status)
    temp_password = f"Nuetra@{secrets.token_hex(4)}"
    user = User(
        email=email,
        password_hash=hash_password(temp_password),
        role_id=role.id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        phone=payload.phone,
        industry=role.name.replace("_", " ").title(),
        permissions=payload.permissions,
        is_active=status not in {"INACTIVE", "SUSPENDED", "DELETED"},
        is_verified=status not in {"INVITED", "PENDING_VERIFICATION"},
        status=status,
    )
    await repo.create_user(user)
    await repo.clear_primary_roles(user.id)
    await repo.ensure_user_role(user.id, role.id, actor.id, is_primary=True)

    if payload.organization_id:
        await repo.upsert_primary_membership(
            user.id,
            {
                "organization_id": payload.organization_id,
                "department_id": payload.department_id,
                "employee_id": payload.employee_id,
                "package_name": payload.package_name,
                "assigned_practitioner_id": payload.assigned_practitioner_id,
                "assigned_mentor_id": payload.assigned_mentor_id,
                "assigned_consultant_id": payload.assigned_consultant_id,
                "status": status,
                "is_verified": status not in {"INVITED", "PENDING_VERIFICATION"},
                "tags": payload.tags,
                "created_by_user_id": actor.id,
            },
        )

    invitation = UserInvitation(
        email=user.email,
        invited_role_id=role.id,
        organization_id=payload.organization_id,
        department_id=payload.department_id,
        invited_by_user_id=actor.id,
        status="INVITED",
        token=secrets.token_urlsafe(24),
        expires_at=payload.invite_expires_at or (datetime.now(timezone.utc) + timedelta(days=7)),
    )
    await repo.create_invitation(invitation)

    await repo.add_status_history(
        UserStatusHistory(
            user_id=user.id,
            previous_status=None,
            new_status=status,
            reason="User created from People & Access module",
            changed_by_user_id=actor.id,
        )
    )
    if payload.note:
        await repo.add_note(UserNote(user_id=user.id, author_user_id=actor.id, body=payload.note))

    await repo.add_audit_event(
        AuditEvent(
            actor_user_id=actor.id,
            entity_type="user",
            entity_id=str(user.id),
            action="users.create",
            before_state=None,
            after_state={"email": user.email, "role": role.name, "status": status},
            ip_address=ip_address,
            browser=user_agent,
            request_id=request_id,
        )
    )

    try:
        get_email_service().send_invitation(user.email, temp_password, role.name)
    except Exception:
        pass

    return await get_user_detail(session, user.id)


async def update_user(
    session: AsyncSession,
    user_id: uuid.UUID,
    payload: ManagedUserUpdateRequest,
    *,
    actor: UserResponse,
    ip_address: str | None,
    user_agent: str | None,
    request_id: str | None,
) -> UserProfileDetail:
    repo = PeopleAccessRepository(session)
    user = await repo.get_user_detail(user_id)
    if user is None:
        raise NotFoundException("User not found")

    before_state = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": user.phone,
        "status": user.status,
        "role": user.role.name if user.role else None,
        "permissions": await resolve_user_permissions(session, user),
    }

    if payload.first_name is not None:
        user.first_name = payload.first_name
    if payload.last_name is not None:
        user.last_name = payload.last_name
    if payload.phone is not None:
        user.phone = payload.phone
    if payload.permissions is not None:
        user.permissions = payload.permissions

    if payload.status is not None:
        next_status = _normalize_status(payload.status)
        if user.status != next_status:
            previous_status = user.status
            user.status = next_status
            user.is_active = next_status not in {"INACTIVE", "SUSPENDED", "DELETED"}
            await repo.add_status_history(
                UserStatusHistory(
                    user_id=user.id,
                    previous_status=previous_status,
                    new_status=next_status,
                    reason="Status updated from People & Access",
                    changed_by_user_id=actor.id,
                )
            )

    if payload.role:
        role = await repo.get_role_by_name(normalize_role_name(payload.role))
        if role is None:
            raise NotFoundException(f"Role '{payload.role}' not found")
        user.role_id = role.id
        await repo.clear_primary_roles(user.id)
        await repo.ensure_user_role(user.id, role.id, actor.id, is_primary=True)

    if any(
        value is not None
        for value in [
            payload.organization_id,
            payload.department_id,
            payload.employee_id,
            payload.package_name,
            payload.assigned_practitioner_id,
            payload.assigned_mentor_id,
            payload.assigned_consultant_id,
            payload.tags,
            payload.status,
        ]
    ):
        org_id = payload.organization_id or (user.organization_memberships[0].organization_id if user.organization_memberships else None)
        if org_id:
            await repo.upsert_primary_membership(
                user.id,
                {
                    "organization_id": org_id,
                    "department_id": payload.department_id or (user.organization_memberships[0].department_id if user.organization_memberships else None),
                    "employee_id": payload.employee_id if payload.employee_id is not None else (user.organization_memberships[0].employee_id if user.organization_memberships else None),
                    "package_name": payload.package_name if payload.package_name is not None else (user.organization_memberships[0].package_name if user.organization_memberships else None),
                    "assigned_practitioner_id": payload.assigned_practitioner_id if payload.assigned_practitioner_id is not None else (user.organization_memberships[0].assigned_practitioner_id if user.organization_memberships else None),
                    "assigned_mentor_id": payload.assigned_mentor_id if payload.assigned_mentor_id is not None else (user.organization_memberships[0].assigned_mentor_id if user.organization_memberships else None),
                    "assigned_consultant_id": payload.assigned_consultant_id if payload.assigned_consultant_id is not None else (user.organization_memberships[0].assigned_consultant_id if user.organization_memberships else None),
                    "status": user.status,
                    "is_verified": user.is_verified,
                    "tags": payload.tags if payload.tags is not None else (user.organization_memberships[0].tags if user.organization_memberships else []),
                    "created_by_user_id": actor.id,
                },
            )

    if payload.note:
        await repo.add_note(UserNote(user_id=user.id, author_user_id=actor.id, body=payload.note))

    after_state = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": user.phone,
        "status": user.status,
        "role_id": str(user.role_id),
        "permissions": user.permissions or [],
    }
    await repo.add_audit_event(
        AuditEvent(
            actor_user_id=actor.id,
            entity_type="user",
            entity_id=str(user.id),
            action="users.edit",
            before_state=before_state,
            after_state=after_state,
            ip_address=ip_address,
            browser=user_agent,
            request_id=request_id,
        )
    )
    return await get_user_detail(session, user.id)


async def add_note(
    session: AsyncSession,
    user_id: uuid.UUID,
    payload: UserNoteCreateRequest,
    *,
    actor: UserResponse,
    ip_address: str | None,
    user_agent: str | None,
    request_id: str | None,
) -> list[UserNoteItem]:
    repo = PeopleAccessRepository(session)
    user = await repo.get_user_detail(user_id)
    if user is None:
        raise NotFoundException("User not found")
    await repo.add_note(UserNote(user_id=user.id, author_user_id=actor.id, body=payload.body))
    await repo.add_audit_event(
        AuditEvent(
            actor_user_id=actor.id,
            entity_type="user_note",
            entity_id=str(user.id),
            action="users.edit",
            before_state=None,
            after_state={"body": payload.body},
            ip_address=ip_address,
            browser=user_agent,
            request_id=request_id,
        )
    )
    detail = await get_user_detail(session, user.id)
    return detail.notes


async def bulk_action(
    session: AsyncSession,
    *,
    action: str,
    user_ids: list[uuid.UUID],
    actor: UserResponse,
    organization_id: uuid.UUID | None = None,
    department_id: uuid.UUID | None = None,
    role_name: str | None = None,
    package_name: str | None = None,
    status: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    request_id: str | None = None,
) -> BulkActionResponse:
    repo = PeopleAccessRepository(session)
    normalized_action = action.strip().lower()
    affected_ids: list[uuid.UUID] = []
    target_role = await repo.get_role_by_name(normalize_role_name(role_name)) if role_name else None

    for user_id in user_ids:
        user = await repo.get_user_detail(user_id)
        if user is None:
            continue

        if normalized_action in {"activate", "deactivate", "suspend", "delete"}:
            next_status = {
                "activate": "ACTIVE",
                "deactivate": "INACTIVE",
                "suspend": "SUSPENDED",
                "delete": "DELETED",
            }[normalized_action]
            previous_status = user.status
            user.status = next_status
            user.is_active = next_status not in {"INACTIVE", "SUSPENDED", "DELETED"}
            await repo.add_status_history(
                UserStatusHistory(
                    user_id=user.id,
                    previous_status=previous_status,
                    new_status=next_status,
                    reason=f"Bulk action: {normalized_action}",
                    changed_by_user_id=actor.id,
                )
            )
        elif normalized_action == "assign_role" and target_role:
            user.role_id = target_role.id
            await repo.clear_primary_roles(user.id)
            await repo.ensure_user_role(user.id, target_role.id, actor.id, is_primary=True)

        if normalized_action in {"assign_organization", "assign_department", "assign_package"}:
            org_id = organization_id or (user.organization_memberships[0].organization_id if user.organization_memberships else None)
            if org_id:
                await repo.upsert_primary_membership(
                    user.id,
                    {
                        "organization_id": org_id,
                        "department_id": department_id or (user.organization_memberships[0].department_id if user.organization_memberships else None),
                        "employee_id": user.organization_memberships[0].employee_id if user.organization_memberships else None,
                        "package_name": package_name if package_name is not None else (user.organization_memberships[0].package_name if user.organization_memberships else None),
                        "assigned_practitioner_id": user.organization_memberships[0].assigned_practitioner_id if user.organization_memberships else None,
                        "assigned_mentor_id": user.organization_memberships[0].assigned_mentor_id if user.organization_memberships else None,
                        "assigned_consultant_id": user.organization_memberships[0].assigned_consultant_id if user.organization_memberships else None,
                        "status": status or user.status,
                        "is_verified": user.is_verified,
                        "tags": user.organization_memberships[0].tags if user.organization_memberships else [],
                        "created_by_user_id": actor.id,
                    },
                )

        await repo.add_audit_event(
            AuditEvent(
                actor_user_id=actor.id,
                entity_type="user",
                entity_id=str(user.id),
                action=f"users.bulk.{normalized_action}",
                before_state=None,
                after_state={"status": user.status, "role_id": str(user.role_id)},
                ip_address=ip_address,
                browser=user_agent,
                request_id=request_id,
            )
        )
        affected_ids.append(user.id)

    return BulkActionResponse(action=normalized_action, processed=len(affected_ids), affected_ids=affected_ids)


async def create_organization(
    session: AsyncSession,
    payload: OrganizationCreateRequest,
    *,
    actor: UserResponse,
    ip_address: str | None,
    user_agent: str | None,
    request_id: str | None,
) -> OrganizationResponse:
    repo = PeopleAccessRepository(session)
    organization = Organization(
        name=payload.name,
        industry=payload.industry,
        company_size=payload.company_size,
        gst_number=payload.gst_number,
        address=payload.address,
        timezone_name=payload.timezone_name,
        country=payload.country,
        subscription_name=payload.subscription_name,
        renewal_date=payload.renewal_date,
        primary_contact_name=payload.primary_contact_name,
        primary_contact_email=payload.primary_contact_email,
        status=_normalize_status(payload.status),
        created_by_user_id=actor.id,
    )
    await repo.create_organization(organization)
    await repo.add_audit_event(
        AuditEvent(
            actor_user_id=actor.id,
            entity_type="organization",
            entity_id=str(organization.id),
            action="organizations.manage",
            before_state=None,
            after_state={"name": organization.name, "status": organization.status},
            ip_address=ip_address,
            browser=user_agent,
            request_id=request_id,
        )
    )
    return OrganizationResponse(
        id=organization.id,
        name=organization.name,
        industry=organization.industry,
        company_size=organization.company_size,
        gst_number=organization.gst_number,
        address=organization.address,
        timezone_name=organization.timezone_name,
        country=organization.country,
        subscription_name=organization.subscription_name,
        renewal_date=organization.renewal_date,
        primary_contact_name=organization.primary_contact_name,
        primary_contact_email=organization.primary_contact_email,
        status=organization.status,
        created_at=organization.created_at,
    )


async def register_login_session(
    session: AsyncSession,
    user: User,
    refresh_token_id: uuid.UUID,
    ip_address: str | None,
    user_agent: str | None,
) -> None:
    repo = PeopleAccessRepository(session)
    browser, platform = _browser_from_user_agent(user_agent)
    await repo.add_login_session(
        LoginSession(
            user_id=user.id,
            refresh_token_id=refresh_token_id,
            ip_address=ip_address,
            user_agent=user_agent,
            browser=browser,
            platform=platform,
            status="ACTIVE",
        )
    )


async def refresh_login_session(
    session: AsyncSession,
    user: User,
    refresh_token_id: uuid.UUID,
    ip_address: str | None,
    user_agent: str | None,
) -> None:
    await register_login_session(session, user, refresh_token_id, ip_address, user_agent)


async def revoke_login_session(session: AsyncSession, refresh_token_id: uuid.UUID) -> None:
    repo = PeopleAccessRepository(session)
    await repo.revoke_login_session_by_refresh_token(refresh_token_id)
