from pydantic import BaseModel


class BlockMediaRelationCreate(BaseModel):
    media_id: int
    sort_order: int = 0


class BlockMediaRelationPublic(BaseModel):
    id: int
    block_id: int
    media_id: int
    sort_order: int