from typing import Optional

from sqlalchemy.future import select

from app.models.organization import Organization
from app.repositories.base import BaseRepository
from app.schemas.organization import OrganizationCreate
from pydantic import BaseModel


class OrganizationUpdate(BaseModel):
    pass


class OrganizationRepository(BaseRepository[Organization, OrganizationCreate, OrganizationUpdate]):
    async def get_by_slug(self, db: AsyncSession, slug: str) -> Optional[Organization]:
        result = await db.execute(select(Organization).filter(Organization.slug == slug))
        return result.scalars().first()


organization_repo = OrganizationRepository(Organization)
