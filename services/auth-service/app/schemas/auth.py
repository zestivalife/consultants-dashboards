import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=1, max_length=256)
    confirm_password: str = Field(min_length=1, max_length=256)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AccessOrganization(BaseModel):
    id: uuid.UUID
    name: str
    department_id: uuid.UUID | None = None
    department: str | None = None
    status: str


class AccessProduct(BaseModel):
    id: uuid.UUID
    name: str
    role: str | None = None
    status: str
    is_primary: bool = False


class AccessWorkspace(BaseModel):
    id: str
    label: str
    landing_page: str
    required_permissions: list[str] = Field(default_factory=list)


class AccessProfile(BaseModel):
    persona: str
    role: str
    permissions: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    active_organization: AccessOrganization | None = None
    active_product: AccessProduct | None = None
    workspace: AccessWorkspace


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    is_active: bool
    is_verified: bool
    role: str
    company_name: str | None = None
    company_id: uuid.UUID | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    permissions: list[str] = Field(default_factory=list)
    access_profile: AccessProfile | None = None
    must_change_password: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    tokens: TokenResponse
    user: UserResponse


class RoleResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None

    model_config = {"from_attributes": True}
