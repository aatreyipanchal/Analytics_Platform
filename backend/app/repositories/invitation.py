from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.invitation import Invitation
from app.repositories.base import BaseRepository
from app.schemas.user import InvitationCreate
from pydantic import BaseModel


class InvitationUpdate(BaseModel):
    accepted_at: str | None = None


class InvitationRepository(BaseRepository[Invitation, InvitationCreate, InvitationUpdate]):
    async def get_by_token(self, db: AsyncSession, token: str) -> Optional[Invitation]:
        result = await db.execute(select(Invitation).filter(Invitation.token == token))
        return result.scalars().first()

    async def list_for_org(self, db: AsyncSession, organization_id: int) -> list[Invitation]:
        result = await db.execute(
            select(Invitation)
            .filter(Invitation.organization_id == organization_id)
            .order_by(Invitation.created_at.desc())
        )
        return list(result.scalars().all())


invitation_repo = InvitationRepository(Invitation)
