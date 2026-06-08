from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class TeamLeadStats(BaseModel):
    totalMembers: int = 0
    activeMembers: int = 0
    completedSessions: int = 0
    avgWellnessScore: int = 0
    pendingRequests: int = 0
    teamMood: float = 7.8
    participationRate: int = 78


class TeamLeadTeamInfo(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    joinCode: str
    memberCount: int = 0
    createdAt: datetime


class TeamMemberInfo(BaseModel):
    id: UUID
    email: str
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    phone: Optional[str] = None
    wellnessScore: int = 85
    status: str = "Active"
    joinedAt: Optional[datetime] = None


class UpcomingSession(BaseModel):
    id: UUID
    title: str
    type: str
    date: datetime
    duration: int
    participants: int = 0
    status: str
