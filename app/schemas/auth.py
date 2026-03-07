from datetime import datetime

from pydantic import BaseModel


class UserRegister(BaseModel):
    username: str
    nickname: str
    email: str | None = None
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserPublic(BaseModel):
    id: int
    username: str
    nickname: str
    email: str | None = None
    avatar_url: str | None = None


class MessageResponse(BaseModel):
    message: str


class UserDeleteResponse(BaseModel):
    message: str


class SessionPublic(BaseModel):
    id: int
    user_id: int
    device_name: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    expires_at: datetime
    revoked_at: datetime | None = None
    created_at: datetime