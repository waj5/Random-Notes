from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class MediaAsset(SQLModel, table=True):
    __tablename__ = "media_assets"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="users.id")
    file_key: str = Field(unique=True, max_length=255)
    file_url: str = Field(max_length=500)
    file_name: Optional[str] = Field(default=None, max_length=255)
    mime_type: str = Field(max_length=100)
    file_size: int = Field(nullable=False)
    width: Optional[int] = Field(default=None)
    height: Optional[int] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)