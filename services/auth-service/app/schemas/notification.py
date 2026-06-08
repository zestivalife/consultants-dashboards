from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: UUID
    title: str
    message: str
    type: str
    priority: str
    read: bool
    timestamp: datetime

    model_config = {"from_attributes": True}


class NotificationCreate(BaseModel):
    user_id: UUID
    title: str
    message: str
    type: str = "system"
    priority: str = "low"
