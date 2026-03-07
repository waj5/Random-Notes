from typing import Optional

from sqlmodel import Field, SQLModel


class BlockMediaRelation(SQLModel, table=True):
    __tablename__ = "block_media_relations"

    id: Optional[int] = Field(default=None, primary_key=True)
    block_id: int = Field(index=True, foreign_key="note_blocks.id")
    media_id: int = Field(index=True, foreign_key="media_assets.id")
    sort_order: int = Field(default=0, nullable=False)