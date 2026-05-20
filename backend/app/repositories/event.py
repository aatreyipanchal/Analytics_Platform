from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from datetime import datetime
from app.repositories.base import BaseRepository
from app.models.event import Event
from app.schemas.event import EventCreate

class RepositoryEvent(BaseRepository[Event, EventCreate, EventCreate]):
    async def get_by_organization(
        self, db: AsyncSession, *, organization_id: int, skip: int = 0, limit: int = 100
    ) -> List[Event]:
        result = await db.execute(
            select(self.model)
            .filter(self.model.organization_id == organization_id)
            .order_by(self.model.timestamp.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_time_range(
        self, 
        db: AsyncSession, 
        *, 
        organization_id: int, 
        start_time: datetime, 
        end_time: datetime,
        event_name: Optional[str] = None
    ) -> List[Event]:
        query = select(self.model).filter(
            and_(
                self.model.organization_id == organization_id,
                self.model.timestamp >= start_time,
                self.model.timestamp <= end_time
            )
        )
        if event_name:
            query = query.filter(self.model.event_name == event_name)
            
        query = query.order_by(self.model.timestamp.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

event_repo = RepositoryEvent(Event)
