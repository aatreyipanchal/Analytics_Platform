from typing import Optional

from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.api_key import ApiKey
from app.repositories.base import BaseRepository
from app.schemas.organization import ApiKeyCreate
from pydantic import BaseModel


class ApiKeyUpdate(BaseModel):
    revoked_at: str | None = None


class ApiKeyRepository(BaseRepository[ApiKey, ApiKeyCreate, ApiKeyUpdate]):
    async def get_active_by_hash(self, db: AsyncSession, key_hash: str) -> Optional[ApiKey]:
        result = await db.execute(
            select(ApiKey).filter(and_(ApiKey.key_hash == key_hash, ApiKey.revoked_at.is_(None)))
        )
        return result.scalars().first()

    async def get_for_organization(self, db: AsyncSession, organization_id: int) -> list[ApiKey]:
        result = await db.execute(
            select(ApiKey)
            .filter(ApiKey.organization_id == organization_id)
            .order_by(ApiKey.created_at.desc())
        )
        return list(result.scalars().all())


api_key_repo = ApiKeyRepository(ApiKey)
