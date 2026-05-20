from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str | None = None


class TokenPayload(BaseModel):
    sub: str | None = None
    type: str | None = None
    org: int | None = None
    role: str | None = None
