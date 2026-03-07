from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class NoteStatus(str, Enum):
    draft = "draft"
    published = "published"
    deleted = "deleted"


class Note(SQLModel, table=True):
    __tablename__ = "notes"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    title: Optional[str] = Field(default=None, max_length=100)
    summary: Optional[str] = Field(default=None, max_length=300)
    cover_media_id: Optional[int] = Field(default=None, foreign_key="media_assets.id")
    status: NoteStatus = Field(default=NoteStatus.draft)
    mood: Optional[str] = Field(default=None, max_length=30)
    scene: Optional[str] = Field(default=None, max_length=100)
    book_theme: Optional[str] = Field(default="default", max_length=30)
    is_private: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    deleted_at: Optional[datetime] = Field(default=None)