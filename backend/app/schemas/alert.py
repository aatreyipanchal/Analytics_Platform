from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.alert import AlertStatus


class AlertCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    event_name: str = Field(min_length=1, max_length=120)
    threshold: float = Field(gt=0)
    window_minutes: int = Field(default=10, ge=1, le=1440)
    webhook_url: str | None = None
    notify_email: str | None = None


class AlertUpdate(BaseModel):
    name: str | None = None
    threshold: float | None = Field(default=None, gt=0)
    window_minutes: int | None = Field(default=None, ge=1, le=1440)
    webhook_url: str | None = None
    notify_email: str | None = None
    status: AlertStatus | None = None


class AlertMute(BaseModel):
    minutes: int = Field(default=60, ge=5, le=10080)


class AlertInDB(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    name: str
    event_name: str
    threshold: float
    window_minutes: int
    status: AlertStatus
    muted_until: datetime | None
    webhook_url: str | None
    notify_email: str | None
    created_at: datetime


class AlertHistoryInDB(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    alert_id: int
    triggered_value: float
    message: str
    created_at: datetime


class NotificationInDB(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    user_id: int | None
    title: str
    message: str
    read: bool
    alert_id: int | None
    created_at: datetime
