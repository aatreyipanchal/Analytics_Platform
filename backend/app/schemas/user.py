from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.VIEWER


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=256)
    organization_name: str


class InvitationAccept(BaseModel):
    token: str
    password: str = Field(min_length=8, max_length=256)


class InvitationCreate(BaseModel):
    email: EmailStr
    role: UserRole


class InvitationResponse(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
    invite_link: str
    expires_at: datetime
    accepted_at: datetime | None

    model_config = {"from_attributes": True}

class UserInDB(UserBase):
    id: int
    organization_id: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserResponse(UserInDB):
    pass
