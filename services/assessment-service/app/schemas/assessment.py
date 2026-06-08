import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AnswerItem(BaseModel):
    question_id: int
    response_value: int


class SubmissionRequest(BaseModel):
    answers: list[AnswerItem] = Field(min_length=1)


class AnswerResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    question_id: int
    response_value: int
    submitted_at: datetime
    model_config = {"from_attributes": True}


class SubmissionResponse(BaseModel):
    assessment_type: str
    count: int
    answers: list[AnswerResponse]


class HistoryEntry(BaseModel):
    assessment_type: str
    submitted_at: datetime
    count: int


class HistoryResponse(BaseModel):
    submissions: list[HistoryEntry]
