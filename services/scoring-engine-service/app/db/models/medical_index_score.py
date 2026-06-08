import uuid
from datetime import datetime, timezone

from sqlalchemy import Float, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MedicalIndexScore(Base):
    __tablename__ = "medical_index_scores"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(index=True, nullable=False)
    vitamin_d: Mapped[float | None] = mapped_column(Float, nullable=True)
    hba1c: Mapped[float | None] = mapped_column(Float, nullable=True)
    thyroid: Mapped[float | None] = mapped_column(Float, nullable=True)
    b12: Mapped[float | None] = mapped_column(Float, nullable=True)
    lipid_profile: Mapped[float | None] = mapped_column(Float, nullable=True)
    ferritin: Mapped[float | None] = mapped_column(Float, nullable=True)
    hemoglobin: Mapped[float | None] = mapped_column(Float, nullable=True)
    crp: Mapped[float | None] = mapped_column(Float, nullable=True)
    medical_index: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_version: Mapped[str] = mapped_column(String(20), nullable=False, default="v1")
    algorithm_version: Mapped[str] = mapped_column(String(20), nullable=False, default="2026-03")
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
