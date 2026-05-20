from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.security import generate_api_key
from app.models.api_key import ApiKey
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.schemas.organization import ApiKeyCreate, ApiKeyResponse, ApiKeyWithSecret, OrganizationInDB

router = APIRouter()


@router.get("/me", response_model=OrganizationInDB)
async def get_my_organization(
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db),
) -> OrganizationInDB:
    organization = await db.get(Organization, current_user.organization_id)
    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return organization


@router.get("/api-keys", response_model=list[ApiKeyResponse])
async def list_api_keys(
    current_user: User = Depends(deps.verify_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(deps.get_db),
) -> list[ApiKeyResponse]:
    api_keys = list(
        (
            await db.execute(
                select(ApiKey)
                .where(ApiKey.organization_id == current_user.organization_id)
                .order_by(ApiKey.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    return api_keys


@router.post("/api-keys", response_model=ApiKeyWithSecret, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    api_key_in: ApiKeyCreate,
    current_user: User = Depends(deps.verify_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(deps.get_db),
) -> ApiKeyWithSecret:
    secret, key_hash = generate_api_key()
    api_key = ApiKey(
        name=api_key_in.name,
        prefix=secret[:12],
        key_hash=key_hash,
        organization_id=current_user.organization_id,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return ApiKeyWithSecret(
        id=api_key.id,
        name=api_key.name,
        prefix=api_key.prefix,
        revoked_at=api_key.revoked_at,
        last_used_at=api_key.last_used_at,
        created_at=api_key.created_at,
        secret=secret,
    )


@router.post("/api-keys/{api_key_id}/rotate", response_model=ApiKeyWithSecret)
async def rotate_api_key(
    api_key_id: int,
    current_user: User = Depends(deps.verify_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(deps.get_db),
) -> ApiKeyWithSecret:
    api_key = await db.get(ApiKey, api_key_id)
    if not api_key or api_key.organization_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    secret, key_hash = generate_api_key()
    api_key.key_hash = key_hash
    api_key.prefix = secret[:12]
    api_key.revoked_at = None
    api_key.last_used_at = None
    await db.commit()
    await db.refresh(api_key)
    return ApiKeyWithSecret(
        id=api_key.id,
        name=api_key.name,
        prefix=api_key.prefix,
        revoked_at=api_key.revoked_at,
        last_used_at=api_key.last_used_at,
        created_at=api_key.created_at,
        secret=secret,
    )


@router.delete("/api-keys/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    api_key_id: int,
    current_user: User = Depends(deps.verify_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(deps.get_db),
) -> None:
    api_key = await db.get(ApiKey, api_key_id)
    if not api_key or api_key.organization_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    api_key.revoked_at = datetime.now(timezone.utc)
    await db.commit()
