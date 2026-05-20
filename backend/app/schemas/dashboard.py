from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.dashboard import WidgetType


class WidgetBase(BaseModel):
    type: WidgetType
    title: str
    position: int = 0
    configuration: dict[str, Any]


class WidgetCreate(WidgetBase):
    pass


class WidgetInDB(WidgetBase):
    id: int
    dashboard_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DashboardBase(BaseModel):
    name: str
    description: str | None = None
    is_public: bool = False
    refresh_interval_seconds: int = Field(default=60, ge=30, le=300)


class DashboardCreate(DashboardBase):
    pass


class DashboardUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_public: bool | None = None
    refresh_interval_seconds: int | None = Field(default=None, ge=30, le=300)


class DashboardInDB(DashboardBase):
    id: int
    organization_id: int
    created_at: datetime
    widgets: list[WidgetInDB] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class WidgetQueryResult(BaseModel):
    widget_id: int
    widget_type: WidgetType
    title: str
    data: list[dict[str, Any]]


class DashboardTemplateWidget(BaseModel):
    title: str
    type: WidgetType
    configuration: dict[str, Any]


class DashboardTemplate(BaseModel):
    slug: str
    name: str
    description: str
    widgets: list[DashboardTemplateWidget]
