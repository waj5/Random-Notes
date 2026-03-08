from pydantic import BaseModel


class NoteCoverUpdate(BaseModel):
    cover_media_id: int | None = None