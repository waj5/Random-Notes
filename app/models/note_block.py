from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class BlockType(str, Enum):
    text = "text"
    image = "image"
    gallery = "gallery"


class TextAlign(str, Enum):
    left = "left"
    center = "center"
    right = "right"


class LayoutStyle(str, Enum):
    normal = "normal"
    image_top = "image_top"
    image_bottom = "image_bottom"
    image_left_text_right = "image_left_text_right"
    text_left_image_right = "text_left_image_right"
    photo_wall = "photo_wall"


class NoteBlock(SQLModel, table=True):
    __tablename__ = "note_blocks"

    id: Optional[int] = Field(default=None, primary_key=True)
    note_id: int = Field(index=True, foreign_key="notes.id")
    block_type: BlockType = Field(nullable=False)
    sort_order: int = Field(index=True, nullable=False)

    text_content: Optional[str] = Field(default=None)
    text_align: TextAlign = Field(default=TextAlign.left)

    layout_style: LayoutStyle = Field(default=LayoutStyle.normal)
    caption: Optional[str] = Field(default=None, max_length=300)

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)