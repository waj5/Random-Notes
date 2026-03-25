from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class NoteShare(SQLModel, table=True):
    __tablename__ = "note_shares"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    note_id: int = Field(foreign_key="notes.id", index=True)
    platform: str = Field(max_length=30, index=True)
    note_title: str = Field(max_length=200)
    note_summary: Optional[str] = Field(default=None, max_length=500)
    note_author_name: Optional[str] = Field(default=None, max_length=100)
    cover_media_id: Optional[int] = Field(default=None)
    share_title: Optional[str] = Field(default=None, max_length=200)
    share_text: Optional[str] = Field(default=None, max_length=2000)
    share_url: Optional[str] = Field(default=None, max_length=1000)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
