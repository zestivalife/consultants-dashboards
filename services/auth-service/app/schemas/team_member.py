from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class TeamMemberStats(BaseModel):
    completedSessions: int = 0
    totalSessions: int = 0
    wellnessScore: Optional[float] = None
    activeGoals: int = 0
    upcomingSessions: int = 0
    completionRate: int = 0
    energyBalance: Optional[float] = None
    bodySupport: Optional[float] = None
    nourishmentScore: Optional[float] = None
    recoveryScore: Optional[float] = None
    stressLevel: Optional[float] = None
    activeCalories: Optional[float] = None
    heartRate: Optional[float] = None
    stepsToday: Optional[float] = None
    sleepHours: Optional[float] = None
    waterLiters: Optional[float] = None
    sunlightToday: Optional[float] = None
    physicalEase: Optional[float] = None
    performanceScore: Optional[float] = None


class MemberTeamInfo(BaseModel):
    team: Optional[dict] = None
    isLead: bool = False
    joinedAt: Optional[datetime] = None
    membershipId: Optional[UUID] = None


class JoinTeamRequest(BaseModel):
    teamCode: str = Field(..., min_length=1)


class MetricCreate(BaseModel):
    type: str
    value: float
    unit: Optional[str] = None
    notes: Optional[str] = None


class MetricResponse(BaseModel):
    id: UUID
    type: str
    value: float
    unit: Optional[str] = None
    notes: Optional[str] = None
    recordedAt: datetime

    model_config = {"from_attributes": True}
