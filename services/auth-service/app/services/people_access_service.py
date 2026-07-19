import uuid
from datetime import datetime, timezone
from io import StringIO
import csv

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException, ConflictException, ForbiddenException, NotFoundException
from app.core.logging import get_logger
from app.db.models.owner_access import (
    AuditEvent,
    LoginSession,
    Organization,
    PackageCatalog,
    Permission,
    Product,
    ServiceCatalog,
    UserNote,
    UserAttachment,
    UserPackageAssignment,
    UserProductAccess,
    UserServiceAssignment,
    UserStatusHistory,
)
from app.db.models.user import PasswordHistory, User
from app.repositories.people_access_repository import PeopleAccessRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.db.models.role import Role
from app.schemas.auth import UserResponse
from app.schemas.people_access import (
    BulkActionResponse,
    CsvImportRequest,
    CsvImportResponse,
    CustomRoleCreateRequest,
    AdminPasswordResetResponse,
    ManagedUserCreateRequest,
    ManagedUserCreateResponse,
    ManagedUserUpdateRequest,
    OrganizationCreateRequest,
    OrganizationResponse,
    PeopleAccessAuditItem,
    PeopleAccessDistributionItem,
    PeopleAccessMetadataResponse,
    PeopleAccessSummaryMetric,
    PeopleAccessSummaryResponse,
    PeopleAccessUserRow,
    PeopleAccessUsersResponse,
    ProductOption,
    PermissionCatalogItem,
    RoleCloneRequest,
    RolePermissionUpdateRequest,
    RolePermissionMatrixRow,
    TemporaryCredentialResponse,
    UserAttachmentItem,
    UserAttachmentCreateRequest,
    UserPackageAssignmentItem,
    UserProductAccessItem,
    UserNoteCreateRequest,
    UserNoteItem,
    UserProfileDetail,
    UserPackageAssignmentRequest,
    UserProductAssignmentRequest,
    UserRoleAssignment,
    UserServiceAssignmentItem,
    UserServiceAssignmentRequest,
    UserStatusHistoryItem,
    LoginSessionItem,
    MembershipSummary,
    PackageCatalogItem,
    PaginationMeta,
    ServiceCatalogItem,
)
from app.services.password_service import password_service
from app.services.user_service import CreateUserCommand, user_service


logger = get_logger(__name__)

MANAGEABLE_STATUSES = {
    "PENDING_VERIFICATION",
    "PENDING_PROFILE",
    "ACTIVE",
    "INACTIVE",
    "LOCKED",
    "SUSPENDED",
    "DELETED",
}
PROTECTED_PLATFORM_OWNER_ROLES = {"platform_owner", "superuser"}
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


def _is_platform_owner(user: User) -> bool:
    role_name = str(user.role.name if user.role else "").lower()
    return role_name in PROTECTED_PLATFORM_OWNER_ROLES


def _ensure_tenant_provisioning_allowed(user: User, operation: str) -> None:
    if _is_platform_owner(user):
        raise ForbiddenException(
            f"Platform Owner accounts cannot be modified by tenant provisioning ({operation})."
        )


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


async def ensure_owner_access(
    session: AsyncSession,
    current_user: UserResponse,
    required_permissions: set[str] | None = None,
) -> None:
    permission_set = set(current_user.permissions or [])
    if not required_permissions:
        required_permissions = {"users.read"}

    if permission_set & required_permissions:
        return

    raise ForbiddenException("You do not have permission to access this resource")


def _membership_to_summary(membership) -> MembershipSummary:
    return MembershipSummary(
        id=membership.id,
        organization_id=membership.organization_id,
        organization=membership.organization.name if membership.organization else "Unassigned",
        department_id=membership.department_id,
        department=membership.department.name if membership.department else None,
        primary_product_id=membership.primary_product_id,
        primary_product=membership.primary_product.name if membership.primary_product else None,
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


def _serialize_audit_event(event: AuditEvent) -> PeopleAccessAuditItem:
    return PeopleAccessAuditItem(
        id=event.id,
        actor="Platform action" if event.actor_user_id else "System",
        action=event.action,
        entity_type=event.entity_type,
        entity_id=event.entity_id,
        product=event.product.name if getattr(event, "product", None) else None,
        created_at=event.created_at,
        request_id=event.request_id,
    )


def _serialize_product_access(access: UserProductAccess) -> UserProductAccessItem:
    return UserProductAccessItem(
        id=access.id,
        product_id=access.product_id,
        product=access.product.name if access.product else "Unknown",
        organization_id=access.organization_id,
        organization=access.organization.name if access.organization else None,
        role_id=access.role_id,
        role=access.role.name if access.role else None,
        status=access.status,
        is_primary=access.is_primary,
        permissions=access.permissions or [],
        created_at=access.created_at,
    )


def _serialize_package_assignment(assignment: UserPackageAssignment) -> UserPackageAssignmentItem:
    return UserPackageAssignmentItem(
        id=assignment.id,
        product_id=assignment.product_id,
        product=assignment.product.name if assignment.product else assignment.package.product.name,
        package_id=assignment.package_id,
        package=assignment.package.name if assignment.package else "Unknown",
        organization_id=assignment.organization_id,
        organization=assignment.organization.name if assignment.organization else None,
        status=assignment.status,
        notes=assignment.notes,
        started_at=assignment.started_at,
        ended_at=assignment.ended_at,
    )


def _serialize_service_assignment(assignment: UserServiceAssignment) -> UserServiceAssignmentItem:
    return UserServiceAssignmentItem(
        id=assignment.id,
        product_id=assignment.product_id,
        product=assignment.product.name if assignment.product else assignment.service.product.name,
        service_id=assignment.service_id,
        service=assignment.service.name if assignment.service else "Unknown",
        organization_id=assignment.organization_id,
        organization=assignment.organization.name if assignment.organization else None,
        status=assignment.status,
        notes=assignment.notes,
        started_at=assignment.started_at,
        ended_at=assignment.ended_at,
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
        consultant=_display_name(membership.assigned_consultant) if membership else None,
        products=[access.product.name for access in user.product_access if getattr(access, "product", None)],
        created_at=user.created_at,
        last_login_at=user.last_login_at,
        tags=membership.tags if membership else [],
    )


async def get_summary(session: AsyncSession) -> PeopleAccessSummaryResponse:
    repo = PeopleAccessRepository(session)
    counts = await repo.get_summary_counts()
    recent_events = await repo.recent_audit_events()
    role_distribution = await repo.role_distribution()
    org_distribution = await repo.organization_distribution()

    return PeopleAccessSummaryResponse(
        metrics=[
            PeopleAccessSummaryMetric(label="People", value=counts["users"]),
            PeopleAccessSummaryMetric(label="Organizations", value=counts["organizations"]),
            PeopleAccessSummaryMetric(label="Pending credentials", value=counts["pending_credentials"]),
            PeopleAccessSummaryMetric(label="Suspended", value=counts["suspended"]),
            PeopleAccessSummaryMetric(label="Pending approvals", value=counts["pending_profiles"]),
        ],
        role_distribution=[
            PeopleAccessDistributionItem(label=name.replace("_", " ").title(), value=value)
            for name, value in role_distribution
        ],
        organization_distribution=[
            PeopleAccessDistributionItem(label=name, value=value)
            for name, value in org_distribution
        ],
        recent_activity=[_serialize_audit_event(event) for event in recent_events],
    )


async def list_users(
    session: AsyncSession,
    *,
    search: str | None = None,
    role: str | None = None,
    organization_id: uuid.UUID | None = None,
    department_id: uuid.UUID | None = None,
    product_id: uuid.UUID | None = None,
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
        product_id=product_id,
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
    products = await repo.list_products()
    packages = await repo.list_packages()
    services = await repo.list_services()
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
        products=[
            ProductOption(id=product.id, key=product.key, name=product.name, status=product.status)
            for product in products
        ],
        packages=[
            PackageCatalogItem(
                id=package.id,
                product_id=package.product_id,
                product=package.product.name if package.product else "Unknown",
                code=package.code,
                name=package.name,
                category=package.category,
                status=package.status,
                description=package.description,
            )
            for package in packages
        ],
        services=[
            ServiceCatalogItem(
                id=service.id,
                product_id=service.product_id,
                product=service.product.name if service.product else "Unknown",
                code=service.code,
                name=service.name,
                category=service.category,
                provider_type=service.provider_type,
                status=service.status,
                description=service.description,
            )
            for service in services
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
    audit_events = await repo.list_user_audit_events(user.id)

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
        must_change_password=user.must_change_password,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        memberships=[_membership_to_summary(membership) for membership in user.organization_memberships],
        product_access=[_serialize_product_access(access) for access in user.product_access],
        package_assignments=[_serialize_package_assignment(item) for item in user.package_assignments],
        service_assignments=[_serialize_service_assignment(item) for item in user.service_assignments],
        sessions=[
            LoginSessionItem(
                id=session_item.id,
                browser=session_item.browser,
                platform=session_item.platform,
                device_label=session_item.device_label,
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
                attachment_type=attachment.attachment_type,
                note=attachment.note,
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
        audit_events=[_serialize_audit_event(event) for event in audit_events],
    )


async def _sync_product_scoped_assignments(
    session: AsyncSession,
    user: User,
    repo: PeopleAccessRepository,
    *,
    actor: UserResponse,
    organization_id: uuid.UUID | None,
    product_ids: list[uuid.UUID],
    primary_product_id: uuid.UUID | None,
    package_ids: list[uuid.UUID],
    service_ids: list[uuid.UUID],
) -> None:
    await repo.clear_user_product_access(user.id)
    await repo.clear_user_package_assignments(user.id)
    await repo.clear_user_service_assignments(user.id)

    for product_id in product_ids:
        product = await repo.get_product(product_id)
        if product is None:
            raise NotFoundException("Product not found")
        if organization_id:
            await repo.ensure_organization_product(organization_id, product_id)
        await repo.add_user_product_access(
            UserProductAccess(
                user_id=user.id,
                product_id=product_id,
                organization_id=organization_id,
                role_id=user.role_id,
                status="ACTIVE",
                is_primary=product_id == primary_product_id,
                permissions=user.permissions or [],
                assigned_by_user_id=actor.id,
            )
        )

    for package_id in package_ids:
        package = await repo.get_package(package_id)
        if package is None:
            raise NotFoundException("Package not found")
        if organization_id:
            await repo.ensure_organization_product(organization_id, package.product_id)
        await repo.add_user_package_assignment(
            UserPackageAssignment(
                user_id=user.id,
                package_id=package.id,
                organization_id=organization_id,
                product_id=package.product_id,
                status="ACTIVE",
                assigned_by_user_id=actor.id,
            )
        )

    for service_id in service_ids:
        service = await repo.get_service(service_id)
        if service is None:
            raise NotFoundException("Service not found")
        if organization_id:
            await repo.ensure_organization_product(organization_id, service.product_id)
        await repo.add_user_service_assignment(
            UserServiceAssignment(
                user_id=user.id,
                service_id=service.id,
                organization_id=organization_id,
                product_id=service.product_id,
                status="ACTIVE",
                assigned_by_user_id=actor.id,
            )
        )


async def create_user(
    session: AsyncSession,
    payload: ManagedUserCreateRequest,
    *,
    actor: UserResponse,
    ip_address: str | None,
    user_agent: str | None,
    request_id: str | None,
) -> ManagedUserCreateResponse:
    repo = PeopleAccessRepository(session)
    email = payload.email.lower().strip()
    if await repo.get_user_by_email(email):
        raise ConflictException("A user with this email already exists")

    role_name = normalize_role_name(payload.role)
    if role_name in PROTECTED_PLATFORM_OWNER_ROLES:
        raise ForbiddenException("Platform Owner accounts cannot be created through tenant provisioning.")

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
    created = await user_service.create_user(
        session,
        CreateUserCommand(
            email=email,
            role_name=role.name,
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone=payload.phone,
            industry=role.name.replace("_", " ").title(),
            permissions=payload.permissions,
            status=status,
            is_active=status not in {"INACTIVE", "SUSPENDED", "DELETED"},
            is_verified=status != "PENDING_VERIFICATION",
            actor_user_id=actor.id,
            audit_event_type="PEOPLE_ACCESS_USER_CREATED",
            must_change_password=True,
        ),
    )
    user = created.user
    await repo.clear_primary_roles(user.id)
    await repo.ensure_user_role(user.id, role.id, actor.id, is_primary=True)

    if payload.organization_id:
        await repo.upsert_primary_membership(
            user.id,
            {
                "organization_id": payload.organization_id,
                "department_id": payload.department_id,
                "primary_product_id": payload.primary_product_id,
                "employee_id": payload.employee_id,
                "package_name": payload.package_name,
                "assigned_practitioner_id": payload.assigned_practitioner_id,
                "assigned_mentor_id": payload.assigned_mentor_id,
                "assigned_consultant_id": payload.assigned_consultant_id,
                "status": status,
                "is_verified": status != "PENDING_VERIFICATION",
                "tags": payload.tags,
                "created_by_user_id": actor.id,
            },
        )

    await _sync_product_scoped_assignments(
        session,
        user,
        repo,
        actor=actor,
        organization_id=payload.organization_id,
        product_ids=payload.product_ids or ([payload.primary_product_id] if payload.primary_product_id else []),
        primary_product_id=payload.primary_product_id,
        package_ids=payload.package_ids,
        service_ids=payload.service_ids,
    )

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
            after_state={
                "email": user.email,
                "role": role.name,
                "status": status,
                "must_change_password": True,
                "temporary_password_returned_once": True,
            },
            ip_address=ip_address,
            browser=user_agent,
            request_id=request_id,
        )
    )
    await repo.add_audit_event(
        AuditEvent(
            actor_user_id=actor.id,
            entity_type="user",
            entity_id=str(user.id),
            action="PASSWORD_RESET_BY_ADMIN",
            before_state=None,
            after_state={"email": user.email, "temporary_password_returned_once": True},
            ip_address=ip_address,
            browser=user_agent,
            request_id=request_id,
        )
    )

    user_detail = await get_user_detail(session, user.id)
    return ManagedUserCreateResponse(
        **user_detail.model_dump(),
        temporary_credentials=TemporaryCredentialResponse(
            username=user.email,
            temporary_password=created.plain_password,
            must_change_password=True,
        ),
    )


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
    _ensure_tenant_provisioning_allowed(user, "update_user")

    before_state = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": user.phone,
        "status": user.status,
        "role": user.role.name if user.role else None,
        "permissions": await resolve_user_permissions(session, user),
    }
    current_membership = user.organization_memberships[0] if user.organization_memberships else None

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
            payload.primary_product_id,
            payload.employee_id,
            payload.package_name,
            payload.assigned_practitioner_id,
            payload.assigned_mentor_id,
            payload.assigned_consultant_id,
            payload.tags,
            payload.status,
        ]
    ):
        org_id = payload.organization_id or (current_membership.organization_id if current_membership else None)
        if org_id:
            await repo.upsert_primary_membership(
                user.id,
                {
                    "organization_id": org_id,
                    "department_id": payload.department_id or (current_membership.department_id if current_membership else None),
                    "primary_product_id": payload.primary_product_id or (current_membership.primary_product_id if current_membership else None),
                    "employee_id": payload.employee_id if payload.employee_id is not None else (current_membership.employee_id if current_membership else None),
                    "package_name": payload.package_name if payload.package_name is not None else (current_membership.package_name if current_membership else None),
                    "assigned_practitioner_id": payload.assigned_practitioner_id if payload.assigned_practitioner_id is not None else (current_membership.assigned_practitioner_id if current_membership else None),
                    "assigned_mentor_id": payload.assigned_mentor_id if payload.assigned_mentor_id is not None else (current_membership.assigned_mentor_id if current_membership else None),
                    "assigned_consultant_id": payload.assigned_consultant_id if payload.assigned_consultant_id is not None else (current_membership.assigned_consultant_id if current_membership else None),
                    "status": user.status,
                    "is_verified": user.is_verified,
                    "tags": payload.tags if payload.tags is not None else (current_membership.tags if current_membership else []),
                    "created_by_user_id": actor.id,
                },
            )

    await _sync_product_scoped_assignments(
        session,
        user,
        repo,
        actor=actor,
        organization_id=payload.organization_id or (current_membership.organization_id if current_membership else None),
        product_ids=payload.product_ids if payload.product_ids is not None else [access.product_id for access in user.product_access],
        primary_product_id=payload.primary_product_id or (current_membership.primary_product_id if current_membership else None),
        package_ids=payload.package_ids if payload.package_ids is not None else [assignment.package_id for assignment in user.package_assignments],
        service_ids=payload.service_ids if payload.service_ids is not None else [assignment.service_id for assignment in user.service_assignments],
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
    await session.flush()
    await session.refresh(user, attribute_names=["role"])
    return await get_user_detail(session, user.id)


async def reset_user_password(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    actor: UserResponse,
    ip_address: str | None,
    user_agent: str | None,
    request_id: str | None,
) -> AdminPasswordResetResponse:
    repo = PeopleAccessRepository(session)
    user = await repo.get_user(user_id)
    if user is None or user.deleted_at is not None or str(user.status or "").upper() == "DELETED":
        raise NotFoundException("User not found")

    temporary_password = password_service.generate_temporary_password()
    is_platform_owner = _is_platform_owner(user)
    user.password_hash = password_service.hash_password(temporary_password)
    user.must_change_password = True
    user.password_changed_at = None
    user.failed_login_attempts = 0
    user.lock_until = None
    if is_platform_owner:
        user.status = "ACTIVE"
        user.is_active = True
        user.is_verified = True
        user.email_verified = True
    elif str(user.status or "").upper() == "PENDING_VERIFICATION":
        user.status = "ACTIVE"
        user.is_active = True
        user.is_verified = True
        user.email_verified = True
    await repo.add_password_history(
        PasswordHistory(
            user_id=user.id,
            password_hash=user.password_hash,
            source="admin_password_reset",
        )
    )
    await repo.add_audit_event(
        AuditEvent(
            actor_user_id=actor.id,
            entity_type="user",
            entity_id=str(user.id),
            action="PASSWORD_RESET_BY_ADMIN",
            before_state=None,
            after_state={
                "email": user.email,
                "must_change_password": True,
                "temporary_password_returned_once": True,
            },
            ip_address=ip_address,
            browser=user_agent,
            request_id=request_id,
        )
    )
    return AdminPasswordResetResponse(
        user_id=user.id,
        username=user.email,
        temporary_password=temporary_password,
        must_change_password=True,
    )


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


async def add_attachment(
    session: AsyncSession,
    user_id: uuid.UUID,
    payload: UserAttachmentCreateRequest,
    *,
    actor: UserResponse,
    ip_address: str | None,
    user_agent: str | None,
    request_id: str | None,
) -> list[UserAttachmentItem]:
    repo = PeopleAccessRepository(session)
    user = await repo.get_user_detail(user_id)
    if user is None:
        raise NotFoundException("User not found")
    await repo.add_attachment(
        UserAttachment(
            user_id=user.id,
            uploaded_by_user_id=actor.id,
            file_name=payload.file_name,
            file_url=payload.file_url,
            content_type=payload.content_type,
            attachment_type=payload.attachment_type,
            note=payload.note,
        )
    )
    await repo.add_audit_event(
        AuditEvent(
            actor_user_id=actor.id,
            entity_type="user_attachment",
            entity_id=str(user.id),
            action="users.edit",
            before_state=None,
            after_state={"file_name": payload.file_name, "attachment_type": payload.attachment_type},
            ip_address=ip_address,
            browser=user_agent,
            request_id=request_id,
        )
    )
    detail = await get_user_detail(session, user.id)
    return detail.attachments


async def update_role_permissions(
    session: AsyncSession,
    role_id: uuid.UUID,
    payload: RolePermissionUpdateRequest,
    *,
    actor: UserResponse,
    ip_address: str | None,
    user_agent: str | None,
    request_id: str | None,
) -> RolePermissionMatrixRow:
    repo = PeopleAccessRepository(session)
    role = await repo.get_role_by_id(role_id)
    if role is None:
        raise NotFoundException("Role not found")
    permissions = await repo.get_permission_by_keys(payload.permission_keys)
    await repo.replace_role_permissions(role.id, [permission.id for permission in permissions])
    await repo.add_audit_event(
        AuditEvent(
            actor_user_id=actor.id,
            entity_type="role",
            entity_id=str(role.id),
            action="settings.manage",
            before_state=None,
            after_state={"permission_keys": payload.permission_keys},
            ip_address=ip_address,
            browser=user_agent,
            request_id=request_id,
        )
    )
    roles = await get_metadata(session)
    return next(item for item in roles.roles if item.id == role.id)


async def create_custom_role(
    session: AsyncSession,
    payload: CustomRoleCreateRequest,
    *,
    actor: UserResponse,
    ip_address: str | None,
    user_agent: str | None,
    request_id: str | None,
) -> RolePermissionMatrixRow:
    repo = PeopleAccessRepository(session)
    role_name = normalize_role_name(payload.name)
    if await repo.get_role_by_name(role_name):
        raise ConflictException("Role already exists")
    role = await repo.create_role(Role(name=role_name, description=payload.description))
    permissions = await repo.get_permission_by_keys(payload.permission_keys)
    await repo.replace_role_permissions(role.id, [permission.id for permission in permissions])
    await repo.add_audit_event(
        AuditEvent(
            actor_user_id=actor.id,
            entity_type="role",
            entity_id=str(role.id),
            action="settings.manage",
            before_state=None,
            after_state={"name": role.name},
            ip_address=ip_address,
            browser=user_agent,
            request_id=request_id,
        )
    )
    roles = await get_metadata(session)
    return next(item for item in roles.roles if item.id == role.id)


async def clone_role(
    session: AsyncSession,
    role_id: uuid.UUID,
    payload: RoleCloneRequest,
    *,
    actor: UserResponse,
    ip_address: str | None,
    user_agent: str | None,
    request_id: str | None,
) -> RolePermissionMatrixRow:
    repo = PeopleAccessRepository(session)
    source_role = await repo.get_role_by_id(role_id)
    if source_role is None:
        raise NotFoundException("Role not found")
    existing = await repo.get_role_by_name(normalize_role_name(payload.name))
    if existing:
        raise ConflictException("Role already exists")
    new_role = await repo.create_role(Role(name=normalize_role_name(payload.name), description=payload.description or source_role.description))
    permissions_map = await repo.get_role_permissions([source_role.id])
    permissions = await repo.get_permission_by_keys(permissions_map.get(source_role.id, []))
    await repo.replace_role_permissions(new_role.id, [permission.id for permission in permissions])
    await repo.add_audit_event(
        AuditEvent(
            actor_user_id=actor.id,
            entity_type="role",
            entity_id=str(new_role.id),
            action="settings.manage",
            before_state={"source_role_id": str(source_role.id)},
            after_state={"name": new_role.name},
            ip_address=ip_address,
            browser=user_agent,
            request_id=request_id,
        )
    )
    roles = await get_metadata(session)
    return next(item for item in roles.roles if item.id == new_role.id)


async def assign_products(
    session: AsyncSession,
    user_id: uuid.UUID,
    assignments: list[UserProductAssignmentRequest],
    *,
    actor: UserResponse,
    ip_address: str | None,
    user_agent: str | None,
    request_id: str | None,
) -> list[UserProductAccessItem]:
    repo = PeopleAccessRepository(session)
    user = await repo.get_user_detail(user_id)
    if user is None:
        raise NotFoundException("User not found")
    _ensure_tenant_provisioning_allowed(user, "assign_products")
    await repo.clear_user_product_access(user.id)
    for assignment in assignments:
        product = await repo.get_product(assignment.product_id)
        if product is None:
            raise NotFoundException("Product not found")
        if assignment.organization_id:
            await repo.ensure_organization_product(assignment.organization_id, assignment.product_id)
        await repo.add_user_product_access(
            UserProductAccess(
                user_id=user.id,
                product_id=assignment.product_id,
                organization_id=assignment.organization_id,
                role_id=assignment.role_id or user.role_id,
                status=_normalize_status(assignment.status),
                is_primary=assignment.is_primary,
                permissions=assignment.permissions,
                assigned_by_user_id=actor.id,
            )
        )
    await repo.add_audit_event(
        AuditEvent(
            actor_user_id=actor.id,
            entity_type="user_product_access",
            entity_id=str(user.id),
            action="users.edit",
            before_state=None,
            after_state={"product_ids": [str(item.product_id) for item in assignments]},
            ip_address=ip_address,
            browser=user_agent,
            request_id=request_id,
        )
    )
    detail = await get_user_detail(session, user.id)
    return detail.product_access


async def assign_packages(
    session: AsyncSession,
    user_id: uuid.UUID,
    assignments: list[UserPackageAssignmentRequest],
    *,
    actor: UserResponse,
    ip_address: str | None,
    user_agent: str | None,
    request_id: str | None,
) -> list[UserPackageAssignmentItem]:
    repo = PeopleAccessRepository(session)
    user = await repo.get_user_detail(user_id)
    if user is None:
        raise NotFoundException("User not found")
    _ensure_tenant_provisioning_allowed(user, "assign_packages")
    await repo.clear_user_package_assignments(user.id)
    for assignment in assignments:
        package = await repo.get_package(assignment.package_id)
        if package is None:
            raise NotFoundException("Package not found")
        if assignment.organization_id:
            await repo.ensure_organization_product(assignment.organization_id, package.product_id)
        await repo.add_user_package_assignment(
            UserPackageAssignment(
                user_id=user.id,
                package_id=assignment.package_id,
                organization_id=assignment.organization_id,
                product_id=package.product_id,
                status=_normalize_status(assignment.status),
                notes=assignment.notes,
                assigned_by_user_id=actor.id,
            )
        )
    await repo.add_audit_event(
        AuditEvent(
            actor_user_id=actor.id,
            entity_type="user_package_assignment",
            entity_id=str(user.id),
            action="packages.manage",
            before_state=None,
            after_state={"package_ids": [str(item.package_id) for item in assignments]},
            ip_address=ip_address,
            browser=user_agent,
            request_id=request_id,
        )
    )
    detail = await get_user_detail(session, user.id)
    return detail.package_assignments


async def assign_services(
    session: AsyncSession,
    user_id: uuid.UUID,
    assignments: list[UserServiceAssignmentRequest],
    *,
    actor: UserResponse,
    ip_address: str | None,
    user_agent: str | None,
    request_id: str | None,
) -> list[UserServiceAssignmentItem]:
    repo = PeopleAccessRepository(session)
    user = await repo.get_user_detail(user_id)
    if user is None:
        raise NotFoundException("User not found")
    _ensure_tenant_provisioning_allowed(user, "assign_services")
    await repo.clear_user_service_assignments(user.id)
    for assignment in assignments:
        service = await repo.get_service(assignment.service_id)
        if service is None:
            raise NotFoundException("Service not found")
        if assignment.organization_id:
            await repo.ensure_organization_product(assignment.organization_id, service.product_id)
        await repo.add_user_service_assignment(
            UserServiceAssignment(
                user_id=user.id,
                service_id=assignment.service_id,
                organization_id=assignment.organization_id,
                product_id=service.product_id,
                status=_normalize_status(assignment.status),
                notes=assignment.notes,
                assigned_by_user_id=actor.id,
            )
        )
    await repo.add_audit_event(
        AuditEvent(
            actor_user_id=actor.id,
            entity_type="user_service_assignment",
            entity_id=str(user.id),
            action="services.manage",
            before_state=None,
            after_state={"service_ids": [str(item.service_id) for item in assignments]},
            ip_address=ip_address,
            browser=user_agent,
            request_id=request_id,
        )
    )
    detail = await get_user_detail(session, user.id)
    return detail.service_assignments


async def revoke_user_session(
    session: AsyncSession,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    *,
    actor: UserResponse,
    ip_address: str | None,
    user_agent: str | None,
    request_id: str | None,
) -> list[LoginSessionItem]:
    repo = PeopleAccessRepository(session)
    token_repo = RefreshTokenRepository(session)
    session_row = await repo.revoke_login_session(session_id, user_id)
    if session_row is None:
        raise NotFoundException("Login session not found")
    if session_row.refresh_token_id:
        await token_repo.revoke(session_row.refresh_token_id)
    await repo.add_audit_event(
        AuditEvent(
            actor_user_id=actor.id,
            entity_type="user_session",
            entity_id=str(user_id),
            action="users.force_logout",
            before_state=None,
            after_state={"session_id": str(session_id)},
            ip_address=ip_address,
            browser=user_agent,
            request_id=request_id,
        )
    )
    detail = await get_user_detail(session, user_id)
    return detail.sessions


async def force_logout_user(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    actor: UserResponse,
    ip_address: str | None,
    user_agent: str | None,
    request_id: str | None,
) -> list[LoginSessionItem]:
    repo = PeopleAccessRepository(session)
    token_repo = RefreshTokenRepository(session)
    sessions = await repo.revoke_all_login_sessions_for_user(user_id)
    for session_row in sessions:
        if session_row.refresh_token_id:
            await token_repo.revoke(session_row.refresh_token_id)
    await repo.add_audit_event(
        AuditEvent(
            actor_user_id=actor.id,
            entity_type="user_session",
            entity_id=str(user_id),
            action="users.force_logout",
            before_state=None,
            after_state={"revoked_sessions": len(sessions)},
            ip_address=ip_address,
            browser=user_agent,
            request_id=request_id,
        )
    )
    detail = await get_user_detail(session, user_id)
    return detail.sessions


async def export_users_csv(session: AsyncSession) -> str:
    rows = await list_users(session, page=1, page_size=5000)
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "name", "email", "phone", "role", "status", "organization", "department", "products"])
    for item in rows.items:
        writer.writerow([
            str(item.id),
            item.name,
            item.email,
            item.phone or "",
            item.role,
            item.status,
            item.organization or "",
            item.department or "",
            ", ".join(item.products),
        ])
    return buffer.getvalue()


async def import_users(
    session: AsyncSession,
    payload: CsvImportRequest,
    *,
    actor: UserResponse,
    ip_address: str | None,
    user_agent: str | None,
    request_id: str | None,
) -> CsvImportResponse:
    created = 0
    skipped = 0
    errors: list[str] = []
    for row in payload.rows:
        try:
            await create_user(
                session,
                ManagedUserCreateRequest(
                    email=row.email,
                    first_name=row.first_name,
                    last_name=row.last_name,
                    phone=row.phone,
                    role=row.role,
                    organization_id=row.organization_id,
                    department_id=row.department_id,
                    employee_id=row.employee_id,
                    primary_product_id=row.primary_product_id,
                    product_ids=[row.primary_product_id] if row.primary_product_id else [],
                    status=row.status,
                ),
                actor=actor,
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
            )
            created += 1
        except ConflictException:
            skipped += 1
        except Exception as exc:
            errors.append(f"{row.email}: {exc}")
    return CsvImportResponse(processed=len(payload.rows), created=created, skipped=skipped, errors=errors)


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
        if _is_platform_owner(user):
            logger.warning(
                "tenant_provisioning_skipped_platform_owner",
                user_id=str(user.id),
                email=user.email,
                action=normalized_action,
            )
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
            device_label=" ".join(part for part in [platform, browser] if part) or None,
            status="ACTIVE",
        )
    )


async def refresh_login_session(
    session: AsyncSession,
    user: User,
    previous_refresh_token_id: uuid.UUID,
    refresh_token_id: uuid.UUID,
    ip_address: str | None,
    user_agent: str | None,
) -> None:
    await revoke_login_session(session, previous_refresh_token_id)
    await register_login_session(session, user, refresh_token_id, ip_address, user_agent)


async def revoke_login_session(session: AsyncSession, refresh_token_id: uuid.UUID) -> None:
    repo = PeopleAccessRepository(session)
    await repo.revoke_login_session_by_refresh_token(refresh_token_id)
