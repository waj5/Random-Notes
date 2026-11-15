from datetime import datetime

from sqlalchemy import Column, Text
from sqlmodel import Field, SQLModel


class Novel(SQLModel, table=True):
    __tablename__ = "novels"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    title: str = Field(max_length=100)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class NovelChapter(SQLModel, table=True):
    __tablename__ = "novel_chapters"

    id: int | None = Field(default=None, primary_key=True)
    novel_id: int = Field(foreign_key="novels.id", index=True)
    title: str = Field(max_length=100)
    body: str = Field(default="", sa_column=Column(Text, nullable=False))
    position: int
    word_count: int = 0
    version: int = 1
    updated_at: datetime = Field(default_factory=datetime.utcnow)
