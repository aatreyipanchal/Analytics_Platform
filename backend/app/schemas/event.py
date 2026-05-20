from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class EventBase(BaseModel):
    event_name: str
    timestamp: datetime
    user_id: str
    properties: dict[str, Any] = Field(default_factory=dict)

    @field_validator("event_name")
    @classmethod
    def validate_event_name(cls, value: str) -> str:
        clean = value.strip()
        if not clean:
            raise ValueError("event_name cannot be empty")
        return clean

class EventCreate(EventBase):
    pass


class EventBatchCreate(BaseModel):
    events: list[EventCreate]


class EventIngestionResponse(BaseModel):
    status: str
    accepted: int


class EventInDB(EventBase):
    id: int
    source: str
    organization_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
