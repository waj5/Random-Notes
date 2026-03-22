from datetime import datetime

from pydantic import BaseModel


class NoteCommentCreate(BaseModel):
    content: str


class NoteCommentUpdate(BaseModel):
    content: str


class NoteCommentPublic(BaseModel):
    id: int
    note_id: int
    user_id: int
    username: str
    nickname: str
    avatar_url: str | None = None
    content: str
    created_at: datetime
