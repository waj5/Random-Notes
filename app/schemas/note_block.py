from datetime import datetime
from pydantic import BaseModel


class NoteBlockCreate(BaseModel):
    block_type: str
    sort_order: int
    text_content: str | None = None
    text_align: str = "left"
    layout_style: str = "normal"
    caption: str | None = None


class NoteBlockUpdate(BaseModel):
    sort_order: int | None = None
    text_content: str | None = None
    text_align: str | None = None
    layout_style: str | None = None
    caption: str | None = None


class NoteBlockPublic(BaseModel):
    id: int
    note_id: int
    block_type: str
    sort_order: int
    text_content: str | None = None
    text_align: str
    layout_style: str
    caption: str | None = None
    created_at: datetime
    updated_at: datetime

class NoteBlockContentItem(BaseModel):
    id: int | None = None
    block_type: str
    sort_order: int
    text_content: str | None = None
    text_align: str = "left"
    layout_style: str = "normal"
    caption: str | None = None
    media_ids: list[int] = []


class NoteContentUpdate(BaseModel):
    title: str | None = None
    summary: str | None = None
    mood: str | None = None
    scene: str | None = None
    book_theme: str | None = None
    is_private: bool | None = None
    status: str | None = None
    blocks: list[NoteBlockContentItem]