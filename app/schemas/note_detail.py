from datetime import datetime
from pydantic import BaseModel

from app.schemas.media_asset import MediaAssetPublic


class NoteBlockDetailPublic(BaseModel):
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
    media_assets: list[MediaAssetPublic]


class NoteDetailPublic(BaseModel):
    id: int
    user_id: int
    title: str | None = None
    summary: str | None = None
    mood: str | None = None
    weather_wmo_code: int | None = None
    scene: str | None = None
    book_theme: str | None = None
    is_private: bool
    status: str
    created_at: datetime
    updated_at: datetime
    blocks: list[NoteBlockDetailPublic]