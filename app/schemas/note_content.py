from pydantic import BaseModel


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