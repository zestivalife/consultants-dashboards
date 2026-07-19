from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class AuthorityOption(BaseModel):
    id: str
    label: str
    description: str
    audience: str

class TeamCreate(BaseModel):
    name: str
    description: Optional[str] = None
    leadId: Optional[UUID] = None
    settings: Optional[dict] = {}

class TeamResponse(TeamCreate):
    id: UUID
    company_id: UUID
    created_at: datetime
    active_members: int = 0
    total_members: int = 0
    engagement: int = 0

    class Config:
        from_attributes = True

class EmployeeCreate(BaseModel):
    email: EmailStr
    firstName: str
    lastName: str
    phone: Optional[str] = None
    role: str

class EmployeeResponse(BaseModel):
    id: UUID
    email: str
    firstName: str
    lastName: str
    role: str
    status: str = "Active"
    engagement: int = 0

    class Config:
        from_attributes = True

class ConsultantCreate(BaseModel):
    email: EmailStr
    firstName: str
    lastName: str
    phone: Optional[str] = None
    role: str = "consultant"
    specialization: Optional[str] = None

class ConsultantResponse(BaseModel):
    id: UUID
    email: str
    firstName: str
    lastName: str
    phone: Optional[str] = None
    role: str
    specialization: Optional[str] = None
    status: str = "Active"
    createdAt: datetime
    authorities: List[str] = Field(default_factory=list)


class ManagedPersonCreate(BaseModel):
    email: EmailStr
    firstName: str
    lastName: str
    phone: Optional[str] = None
    role: str
    specialization: Optional[str] = None
    authorities: List[str] = Field(default_factory=list)


class ManagedPersonUpdate(BaseModel):
    authorities: List[str] = Field(default_factory=list)


class ManagedPersonResponse(BaseModel):
    id: UUID
    email: str
    firstName: str
    lastName: str
    phone: Optional[str] = None
    role: str
    specialization: Optional[str] = None
    authorities: List[str] = Field(default_factory=list)
    status: str = "Active"
    createdAt: datetime

class SessionRequestCreate(BaseModel):
    title: str
    description: Optional[str] = None
    type: str # mindfulness, physical, etc.
    mode: str
    duration: int
    scheduled_at: datetime = Field(..., alias="scheduledAt")
    target_audience: str = Field(..., alias="targetAudience")
    timezone: str
    request_notes: Optional[str] = Field(None, alias="requestNotes")
    team_id: Optional[UUID] = Field(None, alias="teamId")
    
    model_config = ConfigDict(populate_by_name=True)

class SessionRequestResponse(SessionRequestCreate):
    id: UUID
    status: str
    created_at: datetime
    
    specialist_name: Optional[str] = Field(None, alias="specialistName")
    specialist_role: Optional[str] = Field(None, alias="specialistRole")
    specialist_avatar: Optional[str] = Field(None, alias="specialistAvatar")
    thumbnail_url: Optional[str] = Field(None, alias="thumbnailUrl")
    meeting_link: Optional[str] = Field(None, alias="meetingLink")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class DashboardStats(BaseModel):
    avgWellnessScore: int
    totalEmployees: int
    activeEmployees: int
    totalTeams: int
    completedThisMonth: int

class AnalyticsData(BaseModel):
    months: List[str]
    engagementScores: List[int]
