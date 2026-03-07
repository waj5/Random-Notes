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