from datetime import datetime

from pydantic import BaseModel, Field


class NoteCommentCreate(BaseModel):
    content: str
    parent_id: int | None = None


class NoteCommentUpdate(BaseModel):
    content: str


class NoteCommentPublic(BaseModel):
    id: int
    note_id: int
    user_id: int
    parent_id: int | None = None
    username: str
    nickname: str
    avatar_url: str | None = None
    content: str
    created_at: datetime
    replies: list["NoteCommentPublic"] = Field(default_factory=list)
