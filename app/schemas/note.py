from datetime import datetime

from pydantic import BaseModel


class NoteCreate(BaseModel):
    title: str | None = None
    summary: str | None = None
    mood: str | None = None
    scene: str | None = None
    book_theme: str | None = "default"
    is_private: bool = True


class NoteUpdate(BaseModel):
    title: str | None = None
    summary: str | None = None
    mood: str | None = None
    scene: str | None = None
    book_theme: str | None = None
    is_private: bool | None = None
    status: str | None = None


class NotePublic(BaseModel):
    id: int
    user_id: int
    title: str | None = None
    summary: str | None = None
    mood: str | None = None
    scene: str | None = None
    book_theme: str | None = None
    is_private: bool
    status: str
    created_at: datetime
    updated_at: datetime