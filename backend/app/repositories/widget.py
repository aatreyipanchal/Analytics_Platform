from app.repositories.base import BaseRepository
from app.models.dashboard import Widget
from app.schemas.dashboard import WidgetCreate
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.models.dashboard import WidgetType

class WidgetUpdate(BaseModel):
    type: Optional[WidgetType] = None
    configuration: Optional[Dict[str, Any]] = None

class WidgetRepository(BaseRepository[Widget, WidgetCreate, WidgetUpdate]):
    pass

widget_repo = WidgetRepository(Widget)
