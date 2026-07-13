import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class PractitionerProfile(Base):
    __tablename__ = "practitioner_profiles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    specialization: Mapped[str | None] = mapped_column(String(160), nullable=True)
    qualifications: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    certificates: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    profile_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="DRAFT", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    user: Mapped["User"] = relationship()  # noqa: F821


class MentorProfile(Base):
    __tablename__ = "mentor_profiles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    specialization: Mapped[str | None] = mapped_column(String(160), nullable=True)
    qualifications: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    certificates: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    program_focus: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    availability: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    profile_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="DRAFT", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    user: Mapped["User"] = relationship()  # noqa: F821


class ConsultantProfile(Base):
    __tablename__ = "consultant_profiles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    specialization: Mapped[str | None] = mapped_column(String(160), nullable=True)
    seniority: Mapped[str | None] = mapped_column(String(80), nullable=True)
    availability: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    profile_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="DRAFT", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    user: Mapped["User"] = relationship()  # noqa: F821


class OrganizationAdminProfile(Base):
    __tablename__ = "organization_admin_profiles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    specialization: Mapped[str | None] = mapped_column(String(160), nullable=True)
    qualifications: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    certificates: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    organization_scope: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    profile_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="DRAFT", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    user: Mapped["User"] = relationship()  # noqa: F821


class CorporateAdminProfile(Base):
    __tablename__ = "corporate_admin_profiles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    specialization: Mapped[str | None] = mapped_column(String(160), nullable=True)
    qualifications: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    certificates: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    company_scope: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    profile_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="DRAFT", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    user: Mapped["User"] = relationship()  # noqa: F821


class OnboardingTemplate(Base):
    __tablename__ = "onboarding_templates"
    __table_args__ = (UniqueConstraint("role_id", "product_id", "version", name="uq_onboarding_template_scope"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=True, index=True)
    version: Mapped[str] = mapped_column(String(40), default="1", nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    fields: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    documents: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    agreements: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    approval_steps: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    profile_sections: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="ACTIVE", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    role: Mapped["Role"] = relationship()  # noqa: F821
    product: Mapped["Product | None"] = relationship()  # noqa: F821


class OnboardingInstance(Base):
    __tablename__ = "onboarding_instances"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    template_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("onboarding_templates.id", ondelete="SET NULL"), nullable=True)
    invitation_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("user_invitations.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="INVITED", nullable=False, index=True)
    current_step_key: Mapped[str | None] = mapped_column(String(120), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    user: Mapped["User"] = relationship()  # noqa: F821
    template: Mapped["OnboardingTemplate | None"] = relationship()


class OnboardingStep(Base):
    __tablename__ = "onboarding_steps"
    __table_args__ = (UniqueConstraint("instance_id", "step_key", name="uq_onboarding_instance_step"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    instance_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("onboarding_instances.id", ondelete="CASCADE"), nullable=False, index=True)
    step_key: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="PENDING", nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    instance: Mapped["OnboardingInstance"] = relationship()


class OnboardingDocument(Base):
    __tablename__ = "onboarding_documents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    instance_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("onboarding_instances.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    document_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="UPLOADED", nullable=False, index=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    instance: Mapped["OnboardingInstance"] = relationship()
    uploaded_by: Mapped["User | None"] = relationship()  # noqa: F821


class ApprovalWorkflow(Base):
    __tablename__ = "approval_workflows"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    entity_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    assigned_to_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="PENDING", nullable=False, index=True)
    decision: Mapped[str | None] = mapped_column(String(40), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    assigned_to: Mapped["User | None"] = relationship()  # noqa: F821
