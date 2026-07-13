import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


def _upper(value: str | None) -> str | None:
    return value.upper() if isinstance(value, str) else value


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class MasterDataCategoryBase(BaseModel):
    scope: str = Field(default="GLOBAL", min_length=2, max_length=80)
    key: str = Field(min_length=2, max_length=120)
    name: str = Field(min_length=2, max_length=180)
    description: str | None = None
    status: str = Field(default="ACTIVE", pattern="^(ACTIVE|INACTIVE|DELETED)$")
    is_system: bool = False
    sort_order: int = 0
    metadata_schema: dict[str, Any] = Field(default_factory=dict)

    @field_validator("scope", "status", mode="before")
    @classmethod
    def normalize_uppercase(cls, value):
        return _upper(value)


class MasterDataCategoryCreate(MasterDataCategoryBase):
    pass


class MasterDataCategoryUpdate(BaseModel):
    scope: str | None = Field(default=None, min_length=2, max_length=80)
    key: str | None = Field(default=None, min_length=2, max_length=120)
    name: str | None = Field(default=None, min_length=2, max_length=180)
    description: str | None = None
    status: str | None = Field(default=None, pattern="^(ACTIVE|INACTIVE|DELETED)$")
    is_system: bool | None = None
    sort_order: int | None = None
    metadata_schema: dict[str, Any] | None = None

    @field_validator("scope", "status", mode="before")
    @classmethod
    def normalize_uppercase(cls, value):
        return _upper(value)


class MasterDataCategoryResponse(MasterDataCategoryBase):
    id: uuid.UUID
    item_count: int = 0
    active_item_count: int = 0
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class MasterDataItemBase(BaseModel):
    category_id: uuid.UUID
    product_id: uuid.UUID | None = None
    organization_id: uuid.UUID | None = None
    code: str = Field(min_length=1, max_length=120)
    label: str = Field(min_length=1, max_length=220)
    description: str | None = None
    status: str = Field(default="ACTIVE", pattern="^(ACTIVE|INACTIVE|DELETED)$")
    sort_order: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)
    effective_from: datetime | None = None
    effective_to: datetime | None = None

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value):
        return _upper(value)


class MasterDataItemCreate(MasterDataItemBase):
    pass


class MasterDataItemUpdate(BaseModel):
    category_id: uuid.UUID | None = None
    product_id: uuid.UUID | None = None
    organization_id: uuid.UUID | None = None
    code: str | None = Field(default=None, min_length=1, max_length=120)
    label: str | None = Field(default=None, min_length=1, max_length=220)
    description: str | None = None
    status: str | None = Field(default=None, pattern="^(ACTIVE|INACTIVE|DELETED)$")
    sort_order: int | None = None
    metadata: dict[str, Any] | None = None
    effective_from: datetime | None = None
    effective_to: datetime | None = None

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value):
        return _upper(value)


class MasterDataItemResponse(MasterDataItemBase):
    id: uuid.UUID
    category_key: str
    category_name: str
    product: str | None = None
    organization: str | None = None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class MasterDataCategoryListResponse(BaseModel):
    items: list[MasterDataCategoryResponse]
    pagination: PaginationMeta


class MasterDataItemListResponse(BaseModel):
    items: list[MasterDataItemResponse]
    pagination: PaginationMeta


class MasterDataImportRow(BaseModel):
    category_key: str = Field(min_length=2, max_length=120)
    code: str = Field(min_length=1, max_length=120)
    label: str = Field(min_length=1, max_length=220)
    description: str | None = None
    status: str = Field(default="ACTIVE", pattern="^(ACTIVE|INACTIVE|DELETED)$")
    sort_order: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value):
        return _upper(value)


class MasterDataImportRequest(BaseModel):
    rows: list[MasterDataImportRow] = Field(min_length=1, max_length=1000)


class MasterDataImportResponse(BaseModel):
    created: int
    updated: int
    skipped: int
    errors: list[str] = Field(default_factory=list)
