import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    employees: Mapped[int | None] = mapped_column(Integer, nullable=True)
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("roles.id"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    lock_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="ACTIVE", nullable=False, index=True)
    permissions: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    role: Mapped["Role"] = relationship(back_populates="users")  # noqa: F821
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(  # noqa: F821
        back_populates="user"
    )
    consents: Mapped[list["Consent"]] = relationship(back_populates="user")  # noqa: F821
    user_roles: Mapped[list["UserRole"]] = relationship(  # noqa: F821
        foreign_keys="UserRole.user_id", back_populates="user"
    )
    organization_memberships: Mapped[list["OrganizationMembership"]] = relationship(  # noqa: F821
        foreign_keys="OrganizationMembership.user_id", back_populates="user"
    )
    product_access: Mapped[list["UserProductAccess"]] = relationship(  # noqa: F821
        foreign_keys="UserProductAccess.user_id", back_populates="user"
    )
    package_assignments: Mapped[list["UserPackageAssignment"]] = relationship(  # noqa: F821
        foreign_keys="UserPackageAssignment.user_id", back_populates="user"
    )
    service_assignments: Mapped[list["UserServiceAssignment"]] = relationship(  # noqa: F821
        foreign_keys="UserServiceAssignment.user_id", back_populates="user"
    )
    login_sessions: Mapped[list["LoginSession"]] = relationship(  # noqa: F821
        back_populates="user"
    )
    notes: Mapped[list["UserNote"]] = relationship(  # noqa: F821
        foreign_keys="UserNote.user_id", back_populates="user"
    )
    attachments: Mapped[list["UserAttachment"]] = relationship(  # noqa: F821
        foreign_keys="UserAttachment.user_id", back_populates="user"
    )
    status_history: Mapped[list["UserStatusHistory"]] = relationship(  # noqa: F821
        foreign_keys="UserStatusHistory.user_id", back_populates="user"
    )
