import uuid
from datetime import datetime, timezone

from sqlalchemy import Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BodyMeasurement(Base):
    __tablename__ = "body_measurements"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(unique=True, index=True, nullable=False)
    arm_circumference: Mapped[float | None] = mapped_column(Float, nullable=True)
    thigh_circumference: Mapped[float | None] = mapped_column(Float, nullable=True)
    calf_circumference: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
