import uuid

from sqlalchemy import Float, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MealTemplate(Base):
    __tablename__ = "meal_templates"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    diet_plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("diet_plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    meal_type: Mapped[str] = mapped_column(String(20), nullable=False)
    meal_name: Mapped[str] = mapped_column(String(200), nullable=False)
    calories: Mapped[float | None] = mapped_column(Float, nullable=True)
    protein: Mapped[float | None] = mapped_column(Float, nullable=True)
    carbs: Mapped[float | None] = mapped_column(Float, nullable=True)
    fats: Mapped[float | None] = mapped_column(Float, nullable=True)

    diet_plan: Mapped["DietPlan"] = relationship("DietPlan", back_populates="meals")
