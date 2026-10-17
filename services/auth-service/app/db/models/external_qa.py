import uuid
from datetime import datetime, timezone
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class ExternalQaPracticeProvisioning(Base):
    __tablename__ = "external_qa_practice_provisioning"
    __table_args__ = (
        CheckConstraint("status in ('PENDING','WORKSPACE_READY','READY','FAILED','DEACTIVATED')"),
        CheckConstraint("profession_code in ('DIABETES_EDUCATOR','PSYCHOLOGIST','WELLNESS_CONSULTANT','HEALTH_COACH','BEHAVIOURAL_THERAPIST','OCCUPATIONAL_THERAPIST','PHYSIOTHERAPIST','MENTAL_WELLNESS_THERAPIST')"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    fixture_key: Mapped[str] = mapped_column(String(96), nullable=False, unique=True)
    auth_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, unique=True)
    fiteatsy_user_id: Mapped[str | None] = mapped_column(String(180), unique=True)
    tenant_id: Mapped[str | None] = mapped_column(String(80), unique=True)
    profession_code: Mapped[str] = mapped_column(String(80), nullable=False)
    tenant_name: Mapped[str] = mapped_column(String(160), nullable=False)
    input_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    client_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    client_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    provisioning_source: Mapped[str] = mapped_column(String(80), nullable=False, default="PLATFORM_OWNER_GOVERNED_EXTERNAL_QA")
    created_by_reference: Mapped[str] = mapped_column(String(180), nullable=False)
    last_error_code: Mapped[str | None] = mapped_column(String(80))
    deactivation_reason: Mapped[str | None] = mapped_column(Text)
    deactivated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
