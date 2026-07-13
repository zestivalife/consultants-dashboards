import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.db.models.owner_access import UserRole
from app.db.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.services.password_service import password_service


@dataclass(slots=True)
class CreateUserCommand:
    email: str
    role_name: str
    password: str | None = None
    mobile: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    status: str = "INVITED"
    permissions: list[str] = field(default_factory=list)
    is_active: bool | None = None
    is_verified: bool | None = None
    company_name: str | None = None
    company_id: uuid.UUID | None = None
    location: str | None = None
    employees: int | None = None
    industry: str | None = None
    actor_user_id: uuid.UUID | None = None
    audit_event_type: str = "USER_CREATED"


@dataclass(slots=True)
class CreatedUser:
    user: User
    plain_password: str
    is_temporary_password: bool


class UserService:
    """Shared identity creation service for every role and invitation path."""

    async def create_user(self, session: AsyncSession, command: CreateUserCommand) -> CreatedUser:
        user_repo = UserRepository(session)
        role_repo = RoleRepository(session)
        audit_repo = AuditLogRepository(session)

        email = command.email.lower().strip()
        if await user_repo.get_by_email(email):
            raise ConflictException("A user with this email already exists")

        role = await role_repo.get_by_name(command.role_name)
        if role is None:
            raise NotFoundException(f"Role '{command.role_name}' not found. Run migrations first.")

        plain_password = command.password or password_service.generate_temporary_password()
        is_temporary = command.password is None
        status = command.status.strip().upper()
        is_verified = command.is_verified if command.is_verified is not None else status not in {"INVITED", "PENDING_VERIFICATION"}
        is_active = command.is_active if command.is_active is not None else status not in {"INACTIVE", "SUSPENDED", "DELETED"}
        now = datetime.now(timezone.utc)

        user = User(
            email=email,
            mobile=command.mobile,
            password_hash=password_service.hash_password(plain_password),
            role_id=role.id,
            first_name=command.first_name,
            last_name=command.last_name,
            phone=command.phone,
            company_name=command.company_name,
            company_id=command.company_id,
            location=command.location,
            employees=command.employees,
            industry=command.industry,
            permissions=command.permissions,
            status=status,
            is_active=is_active,
            is_verified=is_verified,
            email_verified=is_verified,
            mobile_verified=False,
            password_changed_at=None if is_temporary else now,
        )
        await user_repo.create(user)

        session.add(
            UserRole(
                user_id=user.id,
                role_id=role.id,
                assigned_by_user_id=command.actor_user_id,
                is_primary=True,
            )
        )
        await session.flush()

        await audit_repo.create(command.audit_event_type, user_id=user.id)
        return CreatedUser(user=user, plain_password=plain_password, is_temporary_password=is_temporary)


user_service = UserService()
