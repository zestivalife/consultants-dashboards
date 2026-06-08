import uuid
import secrets
import string
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Text, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


def _gen_join_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(8))


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    join_code: Mapped[str] = mapped_column(String(10), nullable=False, unique=True, index=True, default=_gen_join_code)

    # The corporate admin who created this team
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    # The team lead
    lead_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships (if you need them)
    # company: Mapped["User"] = relationship("User", foreign_keys=[company_id])
    # lead: Mapped["User"] = relationship("User", foreign_keys=[lead_id])

class SessionRequest(Base):
    __tablename__ = "session_requests"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # MINDFULNESS, PHYSICAL, etc.
    mode: Mapped[str] = mapped_column(String(50), nullable=False) # ONLINE / OFFLINE etc.
    duration: Mapped[int] = mapped_column(nullable=False) # minutes
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    target_audience: Mapped[str] = mapped_column(String(50), default="ALL_EMPLOYEES")
    timezone: Mapped[str] = mapped_column(String(50), nullable=False)
    request_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Optional team reference
    team_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    
    # Keep status, company_id and created_at
    status: Mapped[str] = mapped_column(String(50), default="SCHEDULED")
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # UI fields for approved sessions
    specialist_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    specialist_role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    specialist_avatar: Mapped[str | None] = mapped_column(Text, nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    meeting_link: Mapped[str | None] = mapped_column(Text, nullable=True)


class TeamMembership(Base):
    """Tracks which users belong to which teams."""
    __tablename__ = "team_memberships"
    __table_args__ = (UniqueConstraint("team_id", "user_id", name="uq_team_membership"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    is_lead: Mapped[bool] = mapped_column(Boolean, default=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

