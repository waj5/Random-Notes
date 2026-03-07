from pydantic import BaseModel


class NoteBlockOrderItem(BaseModel):
    block_id: int
    sort_order: int


class NoteBlockReorder(BaseModel):
    items: list[NoteBlockOrderItem]