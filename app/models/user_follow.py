from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class UserFollow(SQLModel, table=True):
    __tablename__ = "user_follows"

    id: Optional[int] = Field(default=None, primary_key=True)
    follower_id: int = Field(foreign_key="users.id", index=True)
    followee_id: int = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
