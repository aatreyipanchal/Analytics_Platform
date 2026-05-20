from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.repositories.base import BaseRepository
from app.models.dashboard import Dashboard
from app.schemas.dashboard import DashboardCreate
from pydantic import BaseModel

class DashboardUpdate(BaseModel):
    name: Optional[str] = None

class DashboardRepository(BaseRepository[Dashboard, DashboardCreate, DashboardUpdate]):
    async def get_with_widgets(self, db: AsyncSession, id: int) -> Optional[Dashboard]:
        result = await db.execute(
            select(Dashboard)
            .options(selectinload(Dashboard.widgets))
            .filter(Dashboard.id == id)
        )
        return result.scalars().first()

    async def get_by_organization(self, db: AsyncSession, organization_id: int) -> List[Dashboard]:
        result = await db.execute(
            select(Dashboard)
            .options(selectinload(Dashboard.widgets))
            .filter(Dashboard.organization_id == organization_id)
        )
        return list(result.scalars().all())

dashboard_repo = DashboardRepository(Dashboard)
