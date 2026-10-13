from enum import StrEnum
from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field


class ConsultationStatus(StrEnum):
    SCHEDULED="SCHEDULED"; IN_PROGRESS="IN_PROGRESS"; COMPLETED="COMPLETED"; CANCELLED="CANCELLED"; NO_SHOW="NO_SHOW"


class WorkStatus(StrEnum):
    TODO="TODO"; IN_PROGRESS="IN_PROGRESS"; COMPLETED="COMPLETED"; OVERDUE="OVERDUE"; CANCELLED="CANCELLED"


class ResourceCreate(BaseModel):
    client_id: str
    type: str
    title: str = Field(min_length=1, max_length=240)
    status: str
    due_at: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class ResourceUpdate(BaseModel):
    version: int = Field(ge=1)
    status: str | None = None
    title: str | None = Field(default=None, min_length=1, max_length=240)
    due_at: str | None = None
    payload: dict[str, Any] | None = None


class Page(BaseModel):
    items: list[dict[str, Any]]
    next_cursor: UUID | None = None
