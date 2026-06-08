import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class NutritionBaseline(Base):
    __tablename__ = "nutrition_baseline"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(unique=True, index=True, nullable=False)
    meal_frequency: Mapped[int | None] = mapped_column(Integer, nullable=True)
    protein_intake: Mapped[str | None] = mapped_column(String(50), nullable=True)  # low/moderate/high
    water_intake: Mapped[float | None] = mapped_column(Float, nullable=True)  # litres/day
    food_source: Mapped[str | None] = mapped_column(String(50), nullable=True)  # home_cooked/outside/mixed
    target_protein: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_fat: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_carbs: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_calories: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
