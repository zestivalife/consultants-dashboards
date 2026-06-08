import uuid
from datetime import datetime, timezone

from sqlalchemy import Float, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class HealthScore(Base):
    __tablename__ = "health_scores"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(index=True, nullable=False)
    bmi_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    whr_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    muscle_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    stress_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    lifestyle_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_health_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_version: Mapped[str] = mapped_column(String(20), nullable=False, default="v1")
    algorithm_version: Mapped[str] = mapped_column(String(20), nullable=False, default="2026-03")
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
