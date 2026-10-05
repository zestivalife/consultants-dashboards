import uuid
from datetime import datetime

from typing import Literal

from pydantic import BaseModel, EmailStr, Field, model_validator


ProfessionalRole = Literal[
    "DIETITIAN_NUTRITIONIST", "HEALTH_COACH", "WELLNESS_COACH", "PSYCHOLOGIST",
    "COUNSELLOR_THERAPIST", "PHYSIOTHERAPIST", "FITNESS_TRAINER",
    "YOGA_MEDITATION_COACH", "DIABETES_EDUCATOR", "WOMENS_HEALTH_PRACTITIONER",
    "LIFESTYLE_MEDICINE_PRACTITIONER", "MENTOR", "DOCTOR_PHYSICIAN",
    "OTHER_HEALTHCARE_PROFESSIONAL",
]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ExternalSignupStartRequest(BaseModel):
    mobile_number: str = Field(min_length=10, max_length=32)


class ExternalSignupResendRequest(BaseModel):
    challenge_id: uuid.UUID


class ExternalSignupVerifyRequest(BaseModel):
    challenge_id: uuid.UUID
    code: str = Field(pattern=r"^[0-9]{6}$")
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr | None = None
    account_type: str = Field(pattern=r"^(INDEPENDENT_CONSULTANT|PRACTICE_OWNER)$")
    professional_title: str | None = Field(default=None, max_length=120)
    speciality: str | None = Field(default=None, max_length=120)
    practice_name: str | None = Field(default=None, max_length=160)


class ExternalConsultantRegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    mobile_number: str = Field(min_length=10, max_length=32)
    email: EmailStr
    account_type: Literal["INDEPENDENT_CONSULTANT", "PRACTICE_OWNER"]
    professional_role: ProfessionalRole
    years_experience: int = Field(ge=0, le=80)
    active_client_range: Literal["0", "1-10", "11-25", "26-50", "51-100", "100+"]
    practice_name: str | None = Field(default=None, max_length=160)
    qualification: str | None = Field(default=None, max_length=180)
    specialisation: str | None = Field(default=None, max_length=180)
    registration_number: str | None = Field(default=None, max_length=120)
    certification: str | None = Field(default=None, max_length=180)
    area_of_expertise: str | None = Field(default=None, max_length=180)
    profession: str | None = Field(default=None, max_length=180)
    mentoring_domain: str | None = Field(default=None, max_length=180)
    recaptcha_token: str = Field(min_length=1, max_length=4096)

    @model_validator(mode="after")
    def validate_professional_fields(self):
        role = self.professional_role
        qualification_roles = {
            "DIETITIAN_NUTRITIONIST", "PSYCHOLOGIST", "COUNSELLOR_THERAPIST",
            "DOCTOR_PHYSICIAN", "PHYSIOTHERAPIST", "DIABETES_EDUCATOR",
            "WOMENS_HEALTH_PRACTITIONER", "LIFESTYLE_MEDICINE_PRACTITIONER",
        }
        certification_roles = {"HEALTH_COACH", "WELLNESS_COACH", "FITNESS_TRAINER", "YOGA_MEDITATION_COACH"}
        if role in qualification_roles and not self.qualification:
            raise ValueError("Qualification is required for the selected professional role.")
        if role in certification_roles and not self.certification:
            raise ValueError("Certification is required for the selected professional role.")
        if role == "MENTOR" and not self.mentoring_domain:
            raise ValueError("Mentoring domain is required.")
        if role == "OTHER_HEALTHCARE_PROFESSIONAL" and (not self.profession or not (self.qualification or self.certification)):
            raise ValueError("Profession and qualification or certification are required.")
        if self.account_type == "PRACTICE_OWNER" and not self.practice_name:
            raise ValueError("Practice or organisation name is required for a Practice Owner.")
        return self


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


class NextAccountAction(BaseModel):
    type: str
    route: str
    reason: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    is_active: bool
    is_verified: bool
    status: str = "ACTIVE"
    credential_status: str = "PERMANENT"
    role: str
    company_name: str | None = None
    company_id: uuid.UUID | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    permissions: list[str] = Field(default_factory=list)
    access_profile: AccessProfile | None = None
    must_change_password: bool = False
    temporary_password_expires_at: datetime | None = None
    next_action: NextAccountAction | None = None
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
