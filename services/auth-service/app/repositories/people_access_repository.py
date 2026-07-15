import math
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, cast, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.db.models.owner_access import (
    AuditEvent,
    Department,
    InvitationEmailOutbox,
    LoginSession,
    Organization,
    OrganizationMembership,
    OrganizationProduct,
    PackageCatalog,
    Permission,
    Product,
    RolePermission,
    ServiceCatalog,
    UserAttachment,
    UserInvitation,
    UserNote,
    UserPackageAssignment,
    UserProductAccess,
    UserRole,
    UserServiceAssignment,
    UserStatusHistory,
)
from app.db.models.role import Role
from app.db.models.user import User


class PeopleAccessRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_summary_counts(self) -> dict[str, int]:
        total_users = await self._session.scalar(select(func.count(User.id))) or 0
        invited = await self._session.scalar(select(func.count(User.id)).where(User.status == "INVITED")) or 0
        suspended = await self._session.scalar(select(func.count(User.id)).where(User.status == "SUSPENDED")) or 0
        organizations = await self._session.scalar(select(func.count(Organization.id))) or 0
        pending_invitations = await self._session.scalar(
            select(func.count(UserInvitation.id)).where(UserInvitation.status == "INVITED")
        ) or 0
        return {
            "users": total_users,
            "organizations": organizations,
            "invited": invited,
            "suspended": suspended,
            "pending_invitations": pending_invitations,
        }

    async def role_distribution(self) -> list[tuple[str, int]]:
        stmt = (
            select(Role.name, func.count(User.id))
            .join(User, User.role_id == Role.id)
            .group_by(Role.name)
            .order_by(func.count(User.id).desc(), Role.name.asc())
        )
        result = await self._session.execute(stmt)
        return [(name, count) for name, count in result.all()]

    async def organization_distribution(self) -> list[tuple[str, int]]:
        stmt = (
            select(Organization.name, func.count(OrganizationMembership.id))
            .outerjoin(OrganizationMembership, OrganizationMembership.organization_id == Organization.id)
            .group_by(Organization.id)
            .order_by(func.count(OrganizationMembership.id).desc(), Organization.name.asc())
        )
        result = await self._session.execute(stmt)
        return [(name, count) for name, count in result.all()]

    async def pending_invitations(self, limit: int = 5) -> list[UserInvitation]:
        stmt = (
            select(UserInvitation)
            .options(
                joinedload(UserInvitation.role),
                joinedload(UserInvitation.product),
                joinedload(UserInvitation.organization),
            )
            .where(UserInvitation.status == "INVITED")
            .order_by(UserInvitation.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def recent_audit_events(self, limit: int = 10) -> list[AuditEvent]:
        stmt = (
            select(AuditEvent)
            .options(joinedload(AuditEvent.product))
            .order_by(AuditEvent.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_users(
        self,
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
    ) -> tuple[list[User], int]:
        membership_subq = (
            select(
                OrganizationMembership.user_id.label("user_id"),
                OrganizationMembership.employee_id.label("employee_id"),
                OrganizationMembership.package_name.label("package_name"),
                OrganizationMembership.organization_id.label("organization_id"),
                OrganizationMembership.department_id.label("department_id"),
            )
            .subquery()
        )

        stmt = (
            select(User)
            .options(
                joinedload(User.role),
                selectinload(User.organization_memberships).joinedload(OrganizationMembership.organization),
                selectinload(User.organization_memberships).joinedload(OrganizationMembership.department),
                selectinload(User.organization_memberships).joinedload(OrganizationMembership.primary_product),
                selectinload(User.user_roles).joinedload(UserRole.role),
                selectinload(User.product_access).joinedload(UserProductAccess.product),
                selectinload(User.notes),
                selectinload(User.attachments),
                selectinload(User.login_sessions),
                selectinload(User.status_history),
            )
            .outerjoin(membership_subq, membership_subq.c.user_id == User.id)
        )

        if search:
            search_term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    User.email.ilike(search_term),
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term),
                    cast(membership_subq.c.employee_id, String).ilike(search_term),
                )
            )

        if role:
            stmt = stmt.join(Role, Role.id == User.role_id).where(Role.name == role)

        if organization_id:
            stmt = stmt.where(membership_subq.c.organization_id == organization_id)

        if department_id:
            stmt = stmt.where(membership_subq.c.department_id == department_id)

        if product_id:
            stmt = stmt.where(
                User.id.in_(
                    select(UserProductAccess.user_id).where(UserProductAccess.product_id == product_id)
                )
            )

        if status:
            stmt = stmt.where(User.status == status)

        if verification == "verified":
            stmt = stmt.where(User.is_verified.is_(True))
        elif verification == "pending":
            stmt = stmt.where(User.is_verified.is_(False))

        sort_column = {
            "name": func.coalesce(User.first_name, User.email),
            "email": User.email,
            "status": User.status,
            "last_login_at": User.last_login_at,
            "created_at": User.created_at,
        }.get(sort_by, User.created_at)
        sort_expr = sort_column.asc() if sort_order == "asc" else sort_column.desc()
        stmt = stmt.order_by(sort_expr, User.email.asc())

        count_stmt = select(func.count(func.distinct(User.id))).select_from(stmt.subquery())
        total = await self._session.scalar(count_stmt) or 0

        result = await self._session.execute(stmt.offset((page - 1) * page_size).limit(page_size))
        users = list(result.scalars().unique().all())
        return users, total

    async def list_roles_with_counts(self) -> list[tuple[Role, int]]:
        stmt = (
            select(Role, func.count(User.id))
            .outerjoin(User, User.role_id == Role.id)
            .group_by(Role.id)
            .order_by(Role.name.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.all())

    async def list_permissions(self) -> list[Permission]:
        result = await self._session.execute(select(Permission).order_by(Permission.module.asc(), Permission.key.asc()))
        return list(result.scalars().all())

    async def get_role_permissions(self, role_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[str]]:
        if not role_ids:
            return {}
        stmt = (
            select(RolePermission.role_id, Permission.key)
            .join(Permission, Permission.id == RolePermission.permission_id)
            .where(RolePermission.role_id.in_(role_ids))
        )
        result = await self._session.execute(stmt)
        role_permissions: dict[uuid.UUID, list[str]] = {role_id: [] for role_id in role_ids}
        for role_id, key in result.all():
            role_permissions.setdefault(role_id, []).append(key)
        return role_permissions

    async def list_organizations(self) -> list[Organization]:
        result = await self._session.execute(select(Organization).order_by(Organization.name.asc()))
        return list(result.scalars().all())

    async def list_departments(self) -> list[Department]:
        result = await self._session.execute(select(Department).order_by(Department.name.asc()))
        return list(result.scalars().all())

    async def list_products(self) -> list[Product]:
        result = await self._session.execute(select(Product).order_by(Product.name.asc()))
        return list(result.scalars().all())

    async def list_packages(self) -> list[PackageCatalog]:
        stmt = select(PackageCatalog).options(joinedload(PackageCatalog.product)).order_by(PackageCatalog.name.asc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_services(self) -> list[ServiceCatalog]:
        stmt = select(ServiceCatalog).options(joinedload(ServiceCatalog.product)).order_by(ServiceCatalog.name.asc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_assignable_users(self, role_names: list[str]) -> list[User]:
        stmt = (
            select(User)
            .join(Role, Role.id == User.role_id)
            .options(
                joinedload(User.role),
                selectinload(User.organization_memberships).joinedload(OrganizationMembership.organization),
                selectinload(User.product_access).joinedload(UserProductAccess.product),
            )
            .where(Role.name.in_(role_names), User.status != "DELETED")
            .order_by(User.first_name.asc().nulls_last(), User.email.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().unique().all())

    async def get_user_detail(self, user_id: uuid.UUID) -> User | None:
        stmt = (
            select(User)
            .options(
                joinedload(User.role),
                selectinload(User.user_roles).joinedload(UserRole.role),
                selectinload(User.organization_memberships).joinedload(OrganizationMembership.organization),
                selectinload(User.organization_memberships).joinedload(OrganizationMembership.department),
                selectinload(User.organization_memberships).joinedload(OrganizationMembership.primary_product),
                selectinload(User.organization_memberships).joinedload(OrganizationMembership.assigned_practitioner),
                selectinload(User.organization_memberships).joinedload(OrganizationMembership.assigned_mentor),
                selectinload(User.organization_memberships).joinedload(OrganizationMembership.assigned_consultant),
                selectinload(User.product_access).joinedload(UserProductAccess.product),
                selectinload(User.product_access).joinedload(UserProductAccess.organization),
                selectinload(User.product_access).joinedload(UserProductAccess.role),
                selectinload(User.package_assignments).joinedload(UserPackageAssignment.package).joinedload(PackageCatalog.product),
                selectinload(User.package_assignments).joinedload(UserPackageAssignment.organization),
                selectinload(User.service_assignments).joinedload(UserServiceAssignment.service).joinedload(ServiceCatalog.product),
                selectinload(User.service_assignments).joinedload(UserServiceAssignment.organization),
                selectinload(User.login_sessions),
                selectinload(User.notes).joinedload(UserNote.author),
                selectinload(User.attachments).joinedload(UserAttachment.uploaded_by),
                selectinload(User.status_history).joinedload(UserStatusHistory.changed_by),
            )
            .where(User.id == user_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(User).options(joinedload(User.role)).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_role_by_name(self, role_name: str) -> Role | None:
        result = await self._session.execute(select(Role).where(Role.name == role_name))
        return result.scalar_one_or_none()

    async def get_role_by_id(self, role_id: uuid.UUID) -> Role | None:
        result = await self._session.execute(select(Role).where(Role.id == role_id))
        return result.scalar_one_or_none()

    async def get_permission_by_keys(self, keys: list[str]) -> list[Permission]:
        if not keys:
            return []
        result = await self._session.execute(select(Permission).where(Permission.key.in_(keys)))
        return list(result.scalars().all())

    async def get_organization(self, organization_id: uuid.UUID) -> Organization | None:
        result = await self._session.execute(select(Organization).where(Organization.id == organization_id))
        return result.scalar_one_or_none()

    async def get_department(self, department_id: uuid.UUID) -> Department | None:
        result = await self._session.execute(select(Department).where(Department.id == department_id))
        return result.scalar_one_or_none()

    async def get_product(self, product_id: uuid.UUID) -> Product | None:
        result = await self._session.execute(select(Product).where(Product.id == product_id))
        return result.scalar_one_or_none()

    async def get_package(self, package_id: uuid.UUID) -> PackageCatalog | None:
        stmt = select(PackageCatalog).options(joinedload(PackageCatalog.product)).where(PackageCatalog.id == package_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_service(self, service_id: uuid.UUID) -> ServiceCatalog | None:
        stmt = select(ServiceCatalog).options(joinedload(ServiceCatalog.product)).where(ServiceCatalog.id == service_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, user: User) -> User:
        self._session.add(user)
        await self._session.flush()
        return user

    async def create_role(self, role: Role) -> Role:
        self._session.add(role)
        await self._session.flush()
        return role

    async def create_organization(self, organization: Organization) -> Organization:
        self._session.add(organization)
        await self._session.flush()
        return organization

    async def create_membership(self, membership: OrganizationMembership) -> OrganizationMembership:
        self._session.add(membership)
        await self._session.flush()
        return membership

    async def get_membership(self, user_id: uuid.UUID, organization_id: uuid.UUID | None = None) -> OrganizationMembership | None:
        stmt = select(OrganizationMembership).where(OrganizationMembership.user_id == user_id)
        if organization_id:
            stmt = stmt.where(OrganizationMembership.organization_id == organization_id)
        stmt = stmt.order_by(OrganizationMembership.created_at.asc())
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def upsert_primary_membership(self, user_id: uuid.UUID, membership_data: dict) -> OrganizationMembership:
        membership = await self.get_membership(user_id, membership_data.get("organization_id"))
        if membership is None:
            membership = OrganizationMembership(user_id=user_id, **membership_data)
            self._session.add(membership)
        else:
            for field, value in membership_data.items():
                setattr(membership, field, value)
        await self._session.flush()
        return membership

    async def ensure_organization_product(self, organization_id: uuid.UUID, product_id: uuid.UUID) -> OrganizationProduct:
        result = await self._session.execute(
            select(OrganizationProduct).where(
                OrganizationProduct.organization_id == organization_id,
                OrganizationProduct.product_id == product_id,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = OrganizationProduct(organization_id=organization_id, product_id=product_id, status="ACTIVE")
            self._session.add(row)
            await self._session.flush()
        return row

    async def ensure_user_role(
        self,
        user_id: uuid.UUID,
        role_id: uuid.UUID,
        assigned_by_user_id: uuid.UUID | None,
        is_primary: bool = True,
    ) -> UserRole:
        result = await self._session.execute(select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id))
        user_role = result.scalar_one_or_none()
        if user_role is None:
            user_role = UserRole(
                user_id=user_id,
                role_id=role_id,
                assigned_by_user_id=assigned_by_user_id,
                is_primary=is_primary,
            )
            self._session.add(user_role)
        else:
            user_role.is_primary = is_primary
        await self._session.flush()
        return user_role

    async def clear_primary_roles(self, user_id: uuid.UUID) -> None:
        result = await self._session.execute(select(UserRole).where(UserRole.user_id == user_id))
        for user_role in result.scalars().all():
            user_role.is_primary = False

    async def replace_role_permissions(self, role_id: uuid.UUID, permission_ids: list[uuid.UUID]) -> None:
        await self._session.execute(delete(RolePermission).where(RolePermission.role_id == role_id))
        for permission_id in permission_ids:
            self._session.add(RolePermission(role_id=role_id, permission_id=permission_id))

    async def create_invitation(self, invitation: UserInvitation) -> UserInvitation:
        self._session.add(invitation)
        await self._session.flush()
        return invitation

    async def find_open_invitation(
        self,
        *,
        email: str,
        role_id: uuid.UUID,
        product_id: uuid.UUID | None,
        organization_id: uuid.UUID | None,
        now: datetime,
    ) -> UserInvitation | None:
        stmt = select(UserInvitation).where(
            UserInvitation.email == email,
            UserInvitation.invited_role_id == role_id,
            UserInvitation.status == "INVITED",
            or_(UserInvitation.expires_at.is_(None), UserInvitation.expires_at > now),
        )
        if product_id is None:
            stmt = stmt.where(UserInvitation.product_id.is_(None))
        else:
            stmt = stmt.where(UserInvitation.product_id == product_id)
        if organization_id is None:
            stmt = stmt.where(UserInvitation.organization_id.is_(None))
        else:
            stmt = stmt.where(UserInvitation.organization_id == organization_id)

        result = await self._session.execute(stmt.limit(1))
        return result.scalar_one_or_none()

    async def create_invitation_email_outbox(self, event: InvitationEmailOutbox) -> InvitationEmailOutbox:
        self._session.add(event)
        await self._session.flush()
        return event

    async def list_invitations(
        self,
        *,
        search: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[UserInvitation], int]:
        stmt = (
            select(UserInvitation)
            .options(
                joinedload(UserInvitation.role),
                joinedload(UserInvitation.product),
                joinedload(UserInvitation.organization),
            )
            .order_by(UserInvitation.created_at.desc())
        )
        if search:
            stmt = stmt.where(UserInvitation.email.ilike(f"%{search.strip()}%"))
        if status:
            stmt = stmt.where(UserInvitation.status == status)
        count_stmt = select(func.count(UserInvitation.id)).select_from(stmt.subquery())
        total = await self._session.scalar(count_stmt) or 0
        result = await self._session.execute(stmt.offset((page - 1) * page_size).limit(page_size))
        return list(result.scalars().all()), total

    async def get_invitation(self, invitation_id: uuid.UUID) -> UserInvitation | None:
        stmt = (
            select(UserInvitation)
            .options(
                joinedload(UserInvitation.role),
                joinedload(UserInvitation.product),
                joinedload(UserInvitation.organization),
            )
            .where(UserInvitation.id == invitation_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_status_history(self, history: UserStatusHistory) -> UserStatusHistory:
        self._session.add(history)
        await self._session.flush()
        return history

    async def add_note(self, note: UserNote) -> UserNote:
        self._session.add(note)
        await self._session.flush()
        return note

    async def add_attachment(self, attachment: UserAttachment) -> UserAttachment:
        self._session.add(attachment)
        await self._session.flush()
        return attachment

    async def add_audit_event(self, event: AuditEvent) -> AuditEvent:
        self._session.add(event)
        await self._session.flush()
        return event

    async def list_user_audit_events(self, user_id: uuid.UUID, limit: int = 100) -> list[AuditEvent]:
        stmt = (
            select(AuditEvent)
            .options(joinedload(AuditEvent.product))
            .where(or_(AuditEvent.entity_id == str(user_id), AuditEvent.actor_user_id == user_id))
            .order_by(AuditEvent.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def clear_user_product_access(self, user_id: uuid.UUID) -> None:
        await self._session.execute(delete(UserProductAccess).where(UserProductAccess.user_id == user_id))

    async def add_user_product_access(self, product_access: UserProductAccess) -> UserProductAccess:
        self._session.add(product_access)
        await self._session.flush()
        return product_access

    async def clear_user_package_assignments(self, user_id: uuid.UUID) -> None:
        await self._session.execute(delete(UserPackageAssignment).where(UserPackageAssignment.user_id == user_id))

    async def add_user_package_assignment(self, assignment: UserPackageAssignment) -> UserPackageAssignment:
        self._session.add(assignment)
        await self._session.flush()
        return assignment

    async def clear_user_service_assignments(self, user_id: uuid.UUID) -> None:
        await self._session.execute(delete(UserServiceAssignment).where(UserServiceAssignment.user_id == user_id))

    async def add_user_service_assignment(self, assignment: UserServiceAssignment) -> UserServiceAssignment:
        self._session.add(assignment)
        await self._session.flush()
        return assignment

    async def add_login_session(self, login_session: LoginSession) -> LoginSession:
        self._session.add(login_session)
        await self._session.flush()
        return login_session

    async def revoke_login_session_by_refresh_token(self, refresh_token_id: uuid.UUID) -> None:
        result = await self._session.execute(
            select(LoginSession).where(LoginSession.refresh_token_id == refresh_token_id, LoginSession.revoked_at.is_(None))
        )
        session_row = result.scalar_one_or_none()
        if session_row:
            session_row.revoked_at = datetime.now(timezone.utc)
            session_row.status = "REVOKED"
            session_row.last_seen_at = datetime.now(timezone.utc)

    async def get_login_session(self, session_id: uuid.UUID, user_id: uuid.UUID) -> LoginSession | None:
        result = await self._session.execute(
            select(LoginSession).where(LoginSession.id == session_id, LoginSession.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def revoke_login_session(self, session_id: uuid.UUID, user_id: uuid.UUID) -> LoginSession | None:
        session_row = await self.get_login_session(session_id, user_id)
        if session_row and session_row.revoked_at is None:
            revoked_at = datetime.now(timezone.utc)
            session_row.revoked_at = revoked_at
            session_row.status = "REVOKED"
            session_row.last_seen_at = revoked_at
        return session_row

    async def revoke_all_login_sessions_for_user(self, user_id: uuid.UUID) -> list[LoginSession]:
        result = await self._session.execute(
            select(LoginSession).where(LoginSession.user_id == user_id, LoginSession.revoked_at.is_(None))
        )
        sessions = list(result.scalars().all())
        revoked_at = datetime.now(timezone.utc)
        for session_row in sessions:
            session_row.revoked_at = revoked_at
            session_row.status = "REVOKED"
            session_row.last_seen_at = revoked_at
        return sessions

    @staticmethod
    def build_pagination(page: int, page_size: int, total: int) -> dict[str, int]:
        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": max(1, math.ceil(total / page_size)) if page_size else 1,
        }
