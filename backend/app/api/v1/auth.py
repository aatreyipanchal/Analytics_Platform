from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.config import settings
from app.core.security import (
    ALGORITHM,
    create_access_token,
    create_invitation_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.models.api_key import ApiKey
from app.models.invitation import Invitation
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.schemas.token import Token, TokenPayload
from app.schemas.user import (
    InvitationAccept,
    InvitationCreate,
    InvitationResponse,
    UserCreate,
    UserResponse,
)

router = APIRouter()


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=settings.REFRESH_COOKIE_NAME, path="/")


def _slugify(name: str) -> str:
    return "-".join(part for part in name.lower().strip().replace("_", " ").split() if part)


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_in: UserCreate, response: Response, db: AsyncSession = Depends(deps.get_db)) -> UserResponse:
    existing_user = await db.scalar(select(User).where(User.email == user_in.email))
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    base_slug = _slugify(user_in.organization_name)
    slug = base_slug
    suffix = 1
    while await db.scalar(select(Organization).where(Organization.slug == slug)):
        suffix += 1
        slug = f"{base_slug}-{suffix}"

    organization = Organization(name=user_in.organization_name, slug=slug)
    db.add(organization)
    await db.flush()

    owner = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        role=UserRole.OWNER,
        organization_id=organization.id,
        is_active=True,
    )
    db.add(owner)
    await db.flush()

    from app.core.security import generate_api_key

    secret, key_hash = generate_api_key()
    db.add(
        ApiKey(
            name="Primary ingestion key",
            prefix=secret[:12],
            key_hash=key_hash,
            organization_id=organization.id,
        )
    )
    await db.commit()
    await db.refresh(owner)

    refresh_token = create_refresh_token(str(owner.id), owner.organization_id)
    _set_refresh_cookie(response, refresh_token)
    return owner


@router.post("/login", response_model=Token)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(deps.get_db),
) -> Token:
    user = await db.scalar(select(User).where(User.email == form_data.username))
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")

    access_token = create_access_token(str(user.id), user.organization_id, user.role.value)
    refresh_token = create_refresh_token(str(user.id), user.organization_id)
    _set_refresh_cookie(response, refresh_token)
    return Token(access_token=access_token, token_type="bearer")


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    response: Response,
    refresh_token: str = Depends(deps.get_refresh_token),
    db: AsyncSession = Depends(deps.get_db),
) -> Token:
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

    if token_data.type != "refresh" or token_data.sub is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = await db.get(User, int(token_data.sub))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer available")

    next_refresh_token = create_refresh_token(str(user.id), user.organization_id)
    _set_refresh_cookie(response, next_refresh_token)
    access_token = create_access_token(str(user.id), user.organization_id, user.role.value)
    return Token(access_token=access_token, token_type="bearer")


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> Response:
    _clear_refresh_cookie(response)
    return response


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(deps.get_current_active_user)) -> UserResponse:
    return current_user


@router.post("/invitations", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    invite_in: InvitationCreate,
    current_user: User = Depends(deps.verify_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(deps.get_db),
) -> InvitationResponse:
    if invite_in.role == UserRole.OWNER:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Owner role cannot be invited")

    invitation = Invitation(
        email=invite_in.email,
        token=str(uuid4()),
        role=invite_in.role,
        organization_id=current_user.organization_id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=settings.INVITATION_TOKEN_EXPIRE_HOURS),
    )
    db.add(invitation)
    await db.flush()

    invitation_jwt = create_invitation_token(str(invitation.id), invitation.email, invitation.organization_id)
    invitation.token = invitation_jwt
    await db.commit()
    await db.refresh(invitation)

    return InvitationResponse(
        id=invitation.id,
        email=invitation.email,
        role=invitation.role,
        expires_at=invitation.expires_at,
        accepted_at=invitation.accepted_at,
        invite_link=f"{settings.FRONTEND_URL}/?invite={invitation.token}",
    )


@router.get("/invitations", response_model=list[InvitationResponse])
async def list_invitations(
    current_user: User = Depends(deps.verify_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(deps.get_db),
) -> list[InvitationResponse]:
    invitations = list(
        (
            await db.execute(
                select(Invitation)
                .where(Invitation.organization_id == current_user.organization_id)
                .order_by(Invitation.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    return [
        InvitationResponse(
            id=invitation.id,
            email=invitation.email,
            role=invitation.role,
            expires_at=invitation.expires_at,
            accepted_at=invitation.accepted_at,
            invite_link=f"{settings.FRONTEND_URL}/?invite={invitation.token}",
        )
        for invitation in invitations
    ]


@router.post("/invitations/accept", response_model=UserResponse)
async def accept_invitation(
    invitation_in: InvitationAccept,
    response: Response,
    db: AsyncSession = Depends(deps.get_db),
) -> UserResponse:
    try:
        payload = jwt.decode(invitation_in.token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid invitation token") from exc

    if token_data.type != "invite" or token_data.sub is None or token_data.org is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid invitation token")

    invitation = await db.get(Invitation, int(token_data.sub))
    if not invitation or invitation.token != invitation_in.token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")
    if invitation.accepted_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation already accepted")
    if invitation.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation expired")

    existing_user = await db.scalar(select(User).where(User.email == invitation.email))
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")

    user = User(
        email=invitation.email,
        hashed_password=get_password_hash(invitation_in.password),
        role=invitation.role,
        organization_id=invitation.organization_id,
        is_active=True,
    )
    invitation.accepted_at = datetime.now(timezone.utc)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    refresh_token = create_refresh_token(str(user.id), user.organization_id)
    _set_refresh_cookie(response, refresh_token)
    return user
