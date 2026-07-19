import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field


class PeopleAccessSummaryMetric(BaseModel):
    label: str
    value: int


class PeopleAccessDistributionItem(BaseModel):
    label: str
    value: int


class ProductOption(BaseModel):
    id: uuid.UUID
    key: str
    name: str
    status: str


class PackageCatalogItem(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    product: str
    code: str
    name: str
    category: str | None = None
    status: str
    description: str | None = None


class ServiceCatalogItem(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    product: str
    code: str
    name: str
    category: str | None = None
    provider_type: str | None = None
    status: str
    description: str | None = None


class PeopleAccessAuditItem(BaseModel):
    id: uuid.UUID
    actor: str
    action: str
    entity_type: str
    entity_id: str
    product: str | None = None
    created_at: datetime
    request_id: str | None = None


class PeopleAccessSummaryResponse(BaseModel):
    metrics: list[PeopleAccessSummaryMetric]
    role_distribution: list[PeopleAccessDistributionItem]
    organization_distribution: list[PeopleAccessDistributionItem]
    recent_activity: list[PeopleAccessAuditItem]


class PeopleAccessUserRow(BaseModel):
    id: uuid.UUID
    avatar: str | None = None
    name: str
    email: str
    phone: str | None = None
    employee_id: str | None = None
    organization: str | None = None
    department: str | None = None
    role: str
    status: str
    verification: str
    package: str | None = None
    practitioner: str | None = None
    mentor: str | None = None
    consultant: str | None = None
    products: list[str] = Field(default_factory=list)
    created_at: datetime
    last_login_at: datetime | None = None
    tags: list[str] = Field(default_factory=list)


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class PeopleAccessUsersResponse(BaseModel):
    items: list[PeopleAccessUserRow]
    pagination: PaginationMeta


class UserRoleAssignment(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    is_primary: bool = False


class MembershipSummary(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    organization: str
    department_id: uuid.UUID | None = None
    department: str | None = None
    primary_product_id: uuid.UUID | None = None
    primary_product: str | None = None
    employee_id: str | None = None
    package: str | None = None
    practitioner_id: uuid.UUID | None = None
    practitioner: str | None = None
    mentor_id: uuid.UUID | None = None
    mentor: str | None = None
    consultant_id: uuid.UUID | None = None
    consultant: str | None = None
    status: str
    verification: str
    tags: list[str] = Field(default_factory=list)
    joined_at: datetime


class UserProductAccessItem(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    product: str
    organization_id: uuid.UUID | None = None
    organization: str | None = None
    role_id: uuid.UUID | None = None
    role: str | None = None
    status: str
    is_primary: bool = False
    permissions: list[str] = Field(default_factory=list)
    created_at: datetime


class UserPackageAssignmentItem(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    product: str
    package_id: uuid.UUID
    package: str
    organization_id: uuid.UUID | None = None
    organization: str | None = None
    status: str
    notes: str | None = None
    started_at: datetime
    ended_at: datetime | None = None


class UserServiceAssignmentItem(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    product: str
    service_id: uuid.UUID
    service: str
    organization_id: uuid.UUID | None = None
    organization: str | None = None
    status: str
    notes: str | None = None
    started_at: datetime
    ended_at: datetime | None = None


class LoginSessionItem(BaseModel):
    id: uuid.UUID
    browser: str | None = None
    platform: str | None = None
    device_label: str | None = None
    ip_address: str | None = None
    status: str
    created_at: datetime
    last_seen_at: datetime
    revoked_at: datetime | None = None


class UserNoteItem(BaseModel):
    id: uuid.UUID
    body: str
    author: str
    created_at: datetime
    updated_at: datetime


class UserAttachmentItem(BaseModel):
    id: uuid.UUID
    file_name: str
    file_url: str
    content_type: str | None = None
    attachment_type: str | None = None
    note: str | None = None
    created_at: datetime


class UserStatusHistoryItem(BaseModel):
    id: uuid.UUID
    previous_status: str | None = None
    new_status: str
    reason: str | None = None
    changed_by: str
    created_at: datetime


class UserProfileDetail(BaseModel):
    id: uuid.UUID
    avatar: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    name: str
    email: str
    phone: str | None = None
    role: str
    roles: list[UserRoleAssignment]
    permissions: list[str] = Field(default_factory=list)
    professional_title: str | None = None
    status: str
    verification: str
    must_change_password: bool = False
    last_login_at: datetime | None = None
    created_at: datetime
    memberships: list[MembershipSummary] = Field(default_factory=list)
    product_access: list[UserProductAccessItem] = Field(default_factory=list)
    package_assignments: list[UserPackageAssignmentItem] = Field(default_factory=list)
    service_assignments: list[UserServiceAssignmentItem] = Field(default_factory=list)
    sessions: list[LoginSessionItem] = Field(default_factory=list)
    notes: list[UserNoteItem] = Field(default_factory=list)
    attachments: list[UserAttachmentItem] = Field(default_factory=list)
    status_history: list[UserStatusHistoryItem] = Field(default_factory=list)
    audit_events: list[PeopleAccessAuditItem] = Field(default_factory=list)


class TemporaryCredentialResponse(BaseModel):
    username: str
    temporary_password: str
    must_change_password: bool = True
    message: str = "Copy this temporary password now. It will not be shown again."


class ManagedUserCreateResponse(UserProfileDetail):
    temporary_credentials: TemporaryCredentialResponse


class AdminPasswordResetResponse(BaseModel):
    user_id: uuid.UUID
    username: str
    temporary_password: str
    must_change_password: bool = True
    message: str = "Copy this temporary password now. It will not be shown again."


class PermissionCatalogItem(BaseModel):
    id: uuid.UUID
    key: str
    module: str
    label: str
    description: str | None = None


class RolePermissionMatrixRow(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    users: int
    cloneable: bool
    permissions: list[str]


class DepartmentOption(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str


class OrganizationOption(BaseModel):
    id: uuid.UUID
    name: str
    status: str


class PeopleAccessMetadataResponse(BaseModel):
    roles: list[RolePermissionMatrixRow]
    permissions: list[PermissionCatalogItem]
    organizations: list[OrganizationOption]
    departments: list[DepartmentOption]
    products: list[ProductOption]
    packages: list[PackageCatalogItem]
    services: list[ServiceCatalogItem]
    practitioners: list[PeopleAccessUserRow]
    mentors: list[PeopleAccessUserRow]
    consultants: list[PeopleAccessUserRow]


class ManagedUserCreateRequest(BaseModel):
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    role: str
    organization_id: uuid.UUID | None = None
    department_id: uuid.UUID | None = None
    employee_id: str | None = None
    package_name: str | None = None
    assigned_practitioner_id: uuid.UUID | None = None
    assigned_mentor_id: uuid.UUID | None = None
    assigned_consultant_id: uuid.UUID | None = None
    primary_product_id: uuid.UUID | None = None
    product_ids: list[uuid.UUID] = Field(default_factory=list)
    package_ids: list[uuid.UUID] = Field(default_factory=list)
    service_ids: list[uuid.UUID] = Field(default_factory=list)
    status: str = "PENDING_CREDENTIALS"
    permissions: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    note: str | None = None


class ManagedUserUpdateRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    role: str | None = None
    organization_id: uuid.UUID | None = None
    department_id: uuid.UUID | None = None
    employee_id: str | None = None
    package_name: str | None = None
    assigned_practitioner_id: uuid.UUID | None = None
    assigned_mentor_id: uuid.UUID | None = None
    assigned_consultant_id: uuid.UUID | None = None
    primary_product_id: uuid.UUID | None = None
    product_ids: list[uuid.UUID] | None = None
    package_ids: list[uuid.UUID] | None = None
    service_ids: list[uuid.UUID] | None = None
    status: str | None = None
    permissions: list[str] | None = None
    tags: list[str] | None = None
    note: str | None = None


class UserNoteCreateRequest(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


class UserAttachmentCreateRequest(BaseModel):
    file_name: str = Field(min_length=1, max_length=255)
    file_url: str = Field(min_length=1, max_length=2000)
    content_type: str | None = None
    attachment_type: str | None = None
    note: str | None = None


class BulkActionRequest(BaseModel):
    action: str
    user_ids: list[uuid.UUID] = Field(default_factory=list)
    organization_id: uuid.UUID | None = None
    department_id: uuid.UUID | None = None
    product_id: uuid.UUID | None = None
    role: str | None = None
    package_name: str | None = None
    package_id: uuid.UUID | None = None
    service_id: uuid.UUID | None = None
    status: str | None = None


class BulkActionResponse(BaseModel):
    action: str
    processed: int
    affected_ids: list[uuid.UUID]


class RolePermissionUpdateRequest(BaseModel):
    permission_keys: list[str] = Field(default_factory=list)


class CustomRoleCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    description: str | None = None
    permission_keys: list[str] = Field(default_factory=list)


class RoleCloneRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    description: str | None = None


class UserProductAssignmentRequest(BaseModel):
    product_id: uuid.UUID
    organization_id: uuid.UUID | None = None
    role_id: uuid.UUID | None = None
    status: str = "ACTIVE"
    is_primary: bool = False
    permissions: list[str] = Field(default_factory=list)


class UserPackageAssignmentRequest(BaseModel):
    package_id: uuid.UUID
    organization_id: uuid.UUID | None = None
    status: str = "ACTIVE"
    notes: str | None = None


class UserServiceAssignmentRequest(BaseModel):
    service_id: uuid.UUID
    organization_id: uuid.UUID | None = None
    status: str = "ACTIVE"
    notes: str | None = None


class CsvImportRow(BaseModel):
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    role: str
    organization_id: uuid.UUID | None = None
    department_id: uuid.UUID | None = None
    employee_id: str | None = None
    primary_product_id: uuid.UUID | None = None
    status: str = "PENDING_CREDENTIALS"


class CsvImportRequest(BaseModel):
    rows: list[CsvImportRow] = Field(default_factory=list)


class CsvImportResponse(BaseModel):
    processed: int
    created: int
    skipped: int
    errors: list[str] = Field(default_factory=list)


class OrganizationCreateRequest(BaseModel):
    name: str
    industry: str | None = None
    company_size: str | None = None
    gst_number: str | None = None
    address: str | None = None
    timezone_name: str | None = None
    country: str | None = None
    subscription_name: str | None = None
    renewal_date: date | None = None
    primary_contact_name: str | None = None
    primary_contact_email: EmailStr | None = None
    status: str = "ACTIVE"


class OrganizationResponse(BaseModel):
    id: uuid.UUID
    name: str
    industry: str | None = None
    company_size: str | None = None
    gst_number: str | None = None
    address: str | None = None
    timezone_name: str | None = None
    country: str | None = None
    subscription_name: str | None = None
    renewal_date: date | None = None
    primary_contact_name: str | None = None
    primary_contact_email: str | None = None
    status: str
    created_at: datetime
