import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class ToolUsage(Base):
    """Tracks each time a user completes a wellness tool session."""
    __tablename__ = "tool_usages"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    # Tool identifier: breathing | lungs | eye-rest | meditation | pomodoro
    tool_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Optional sub-type (e.g. breathing technique used)
    sub_type: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Duration of the completed session in seconds
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Consecutive day streak at time of completion
    streak_days: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
