import uuid
from datetime import datetime, timezone

from sqlalchemy import Float, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DietPlan(Base):
    __tablename__ = "diet_plans"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    calorie_target: Mapped[float | None] = mapped_column(Float, nullable=True)
    protein_target: Mapped[float | None] = mapped_column(Float, nullable=True)
    fat_target: Mapped[float | None] = mapped_column(Float, nullable=True)
    carb_target: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    meals: Mapped[list["MealTemplate"]] = relationship(
        "MealTemplate", back_populates="diet_plan", lazy="selectin"
    )
