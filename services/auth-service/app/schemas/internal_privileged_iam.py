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

class PrivilegedInvitationId(BaseModel):
    invitation_id: uuid.UUID
