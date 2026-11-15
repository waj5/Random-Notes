from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy import update
from sqlmodel import Session, select

from app.api.deps import get_current_user, get_session
from app.core.response import success_response
from app.models.novel import Novel, NovelChapter
from app.models.user import User


def no_cache(response: Response):
    response.headers["Cache-Control"] = "no-store"


router = APIRouter(prefix="/novels", tags=["novels"], dependencies=[Depends(no_cache)])
Database = Annotated[Session, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]
Title = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100, pattern=r"^[^\x00]*$"),
]


class NewNovel(BaseModel):
    title: Title


class ChapterDraft(BaseModel):
    title: Title
    body: str = Field(max_length=1_000_000, pattern=r"^[^\x00]*$")
    version: int = Field(ge=1)


class ChapterOrder(BaseModel):
    chapter_ids: list[int]


def owned_novel(session: Session, user: User, novel_id: int) -> Novel:
    novel = session.exec(
        select(Novel).where(Novel.id == novel_id, Novel.user_id == user.id)
    ).one_or_none()
    if novel is None:
        raise HTTPException(404, "Novel not found")
    return novel


def lock_novel(session: Session, user: User, novel_id: int):
    # Serialize mutations within a novel on PostgreSQL and SQLite before reading its chapters.
    result = session.execute(
        update(Novel)
        .where(Novel.id == novel_id, Novel.user_id == user.id)
        .values(updated_at=Novel.updated_at)
    )
    if not result.rowcount:
        raise HTTPException(404, "Novel not found")


def get_chapter(session: Session, novel_id: int, chapter_id: int) -> NovelChapter:
    chapter = session.exec(
        select(NovelChapter).where(
            NovelChapter.novel_id == novel_id, NovelChapter.id == chapter_id
        )
    ).one_or_none()
    if chapter is None:
        raise HTTPException(404, "Chapter not found")
    return chapter


def chapter_dto(chapter: NovelChapter) -> dict:
    data = chapter.model_dump()
    data["updated_at"] = chapter.updated_at.replace(tzinfo=timezone.utc)
    return data


def chapter_directory(session: Session, novel_ids: list[int]):
    return session.exec(
        select(
            NovelChapter.novel_id, NovelChapter.id, NovelChapter.title,
            NovelChapter.position, NovelChapter.word_count, NovelChapter.updated_at,
        ).where(NovelChapter.novel_id.in_(novel_ids))
        .order_by(NovelChapter.position, NovelChapter.id)
    ).all()


def novel_summary(novel: Novel, chapters: list) -> dict:
    latest = max(chapters, key=lambda row: (row.updated_at, row.id), default=None)
    return {
        "id": novel.id,
        "title": novel.title,
        "updated_at": novel.updated_at.replace(tzinfo=timezone.utc),
        "last_chapter_id": latest.id if latest else None,
        "chapter_count": len(chapters),
        "word_count": sum(row.word_count for row in chapters),
    }


@router.get("")
def list_novels(session: Database, user: CurrentUser):
    novels = session.exec(
        select(Novel).where(Novel.user_id == user.id).order_by(Novel.updated_at.desc(), Novel.id.desc())
    ).all()
    directories = {novel.id: [] for novel in novels}
    if directories:
        for row in chapter_directory(session, list(directories)):
            directories[row.novel_id].append(row)
    return success_response([novel_summary(novel, directories[novel.id]) for novel in novels])


@router.post("")
def create_novel(data: NewNovel, session: Database, user: CurrentUser):
    novel = Novel(user_id=user.id, title=data.title)
    session.add(novel)
    session.flush()
    session.add(NovelChapter(novel_id=novel.id, title="第一章", position=0))
    session.flush()
    result = novel_summary(novel, chapter_directory(session, [novel.id]))
    session.commit()
    return success_response(result)


@router.get("/{novel_id}")
def read_novel(novel_id: int, session: Database, user: CurrentUser):
    novel = owned_novel(session, user, novel_id)
    chapters = chapter_directory(session, [novel_id])
    return success_response({
        **novel_summary(novel, chapters),
        "chapters": [
            {key: getattr(row, key) for key in ("id", "title", "position", "word_count")}
            for row in chapters
        ],
    })


@router.post("/{novel_id}/chapters")
def create_chapter(novel_id: int, session: Database, user: CurrentUser):
    lock_novel(session, user, novel_id)
    novel = owned_novel(session, user, novel_id)
    count = len(chapter_directory(session, [novel_id]))
    chapter = NovelChapter(novel_id=novel_id, title=f"第 {count + 1} 章", position=count)
    novel.updated_at = chapter.updated_at
    session.add(chapter)
    session.flush()
    result = chapter_dto(chapter)
    session.commit()
    return success_response(result)


@router.put("/{novel_id}/chapter-order")
def reorder_chapters(novel_id: int, data: ChapterOrder, session: Database, user: CurrentUser):
    lock_novel(session, user, novel_id)
    chapters = chapter_directory(session, [novel_id])
    if sorted(data.chapter_ids) != sorted(row.id for row in chapters):
        raise HTTPException(409, "Chapter directory changed")
    for position, chapter_id in enumerate(data.chapter_ids):
        session.execute(
            update(NovelChapter).where(NovelChapter.id == chapter_id).values(position=position)
        )
    session.commit()
    return success_response()


@router.get("/{novel_id}/chapters/{chapter_id}")
def read_chapter(novel_id: int, chapter_id: int, session: Database, user: CurrentUser):
    owned_novel(session, user, novel_id)
    return success_response(chapter_dto(get_chapter(session, novel_id, chapter_id)))


@router.put("/{novel_id}/chapters/{chapter_id}")
def save_chapter(novel_id: int, chapter_id: int, data: ChapterDraft, session: Database, user: CurrentUser):
    lock_novel(session, user, novel_id)
    chapter = get_chapter(session, novel_id, chapter_id)
    # A retried request may already have committed before the connection dropped.
    if chapter.title == data.title and chapter.body == data.body:
        result = chapter_dto(chapter)
        session.rollback()
        return success_response(result)
    if chapter.version != data.version:
        server = chapter_dto(chapter)
        session.rollback()
        return JSONResponse(
            status_code=409,
            content=success_response({"server": server}, "Chapter has changed", code=409),
            headers={"Cache-Control": "no-store"},
        )
    chapter.title = data.title
    chapter.body = data.body
    chapter.word_count = sum(not char.isspace() for char in chapter.body)
    chapter.version += 1
    chapter.updated_at = datetime.utcnow()
    owned_novel(session, user, novel_id).updated_at = chapter.updated_at
    result = chapter_dto(chapter)
    session.commit()
    return success_response(result)


@router.get("/{novel_id}/manuscript")
def read_manuscript(novel_id: int, session: Database, user: CurrentUser):
    owned_novel(session, user, novel_id)
    chapters = session.exec(
        select(NovelChapter).where(NovelChapter.novel_id == novel_id)
        .order_by(NovelChapter.position, NovelChapter.id)
    ).all()
    return success_response([chapter_dto(chapter) for chapter in chapters])
