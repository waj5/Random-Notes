from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class NoteComment(SQLModel, table=True):
    __tablename__ = "note_comments"

    id: Optional[int] = Field(default=None, primary_key=True)
    note_id: int = Field(foreign_key="notes.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    content: str = Field(max_length=1000)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    deleted_at: Optional[datetime] = Field(default=None)
