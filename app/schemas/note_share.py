from datetime import datetime
from typing import Literal

from pydantic import BaseModel


SharePlatform = Literal["xiaohongshu", "weibo", "moments"]


class NoteShareCreate(BaseModel):
    platform: SharePlatform
    share_title: str | None = None
    share_text: str | None = None
    share_url: str | None = None


class NoteSharePublic(BaseModel):
    id: int
    note_id: int
    platform: SharePlatform
    note_title: str
    note_summary: str | None = None
    note_author_name: str | None = None
    cover_image_url: str | None = None
    share_title: str | None = None
    share_text: str | None = None
    share_url: str | None = None
    created_at: datetime
