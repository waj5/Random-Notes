from datetime import datetime
from pydantic import BaseModel


class MediaAssetCreate(BaseModel):
    file_key: str
    file_url: str
    file_name: str | None = None
    mime_type: str
    file_size: int
    width: int | None = None
    height: int | None = None


class MediaAssetPublic(BaseModel):
    id: int
    user_id: int
    file_key: str
    file_url: str
    file_name: str | None = None
    mime_type: str
    file_size: int
    width: int | None = None
    height: int | None = None
    created_at: datetime