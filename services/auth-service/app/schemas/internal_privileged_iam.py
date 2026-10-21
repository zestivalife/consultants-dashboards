import uuid
from pydantic import BaseModel, EmailStr, Field

class PrivilegedInvitationCreate(BaseModel):
    email: EmailStr
    phone: str = Field(pattern=r"^\+[1-9][0-9]{7,14}$")
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)

class PrivilegedInvitationAccept(BaseModel):
    token: str = Field(min_length=40, max_length=256)
    password: str = Field(min_length=12, max_length=256)

class PrivilegedOutOfBandApproval(BaseModel):
    confirmed_email: EmailStr
    confirmed_phone: str = Field(pattern=r"^\+[1-9][0-9]{7,14}$")
    reason: str = Field(min_length=12, max_length=500)

class PrivilegedMfaConfirm(BaseModel):
    activation_token: str = Field(min_length=40, max_length=256)
    code: str = Field(pattern=r"^[0-9]{6}$")

class PrivilegedInvitationId(BaseModel):
    invitation_id: uuid.UUID
