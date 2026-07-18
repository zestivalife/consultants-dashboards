import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    companyName: str | None = None
    location: str | None = None
    employees: int | None = None
    industry: str | None = None
    role: str | None = None


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)


class ResendOtpRequest(BaseModel):
    email: EmailStr


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
