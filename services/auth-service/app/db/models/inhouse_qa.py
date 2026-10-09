import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class InhouseQaProvisioning(Base):
    __tablename__ = "inhouse_qa_provisioning"
    __table_args__ = (
        CheckConstraint("status in ('PENDING','READY','COMPENSATED','FAILED')"),
        CheckConstraint("canonical_role in ('user','consultant','provider','dietician','senior_consultant','practitioner','mentor','admin','super_admin','platform_owner')"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    fixture_key: Mapped[str] = mapped_column(String(96), nullable=False, unique=True)
    auth_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, unique=True)
    fiteatsy_user_id: Mapped[str | None] = mapped_column(String(180), nullable=True, unique=True)
    canonical_role: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    last_error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_by_reference: Mapped[str] = mapped_column(String(180), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
