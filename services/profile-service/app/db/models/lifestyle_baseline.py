import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LifestyleBaseline(Base):
    __tablename__ = "lifestyle_baseline"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(unique=True, index=True, nullable=False)
    activity_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    exercise_frequency: Mapped[int | None] = mapped_column(Integer, nullable=True)
    daily_steps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sleep_duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    sleep_consistency: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-10
    stress_level: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-10
    water_intake: Mapped[float | None] = mapped_column(Float, nullable=True)
    food_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
