from fastapi import HTTPException
from sqlmodel import Session, func, select

from app.models.block_media_relation import BlockMediaRelation
from app.models.note import Note
from app.models.note_block import NoteBlock
from app.models.note_share import NoteShare
from app.models.user import User
from app.schemas.note_share import NoteShareCreate
from app.services.note_services import get_accessible_note


def _get_cover_media_id(session: Session, note: Note) -> int | None:
    if note.cover_media_id:
        return note.cover_media_id

    first_relation = session.exec(
        select(BlockMediaRelation)
        .join(NoteBlock, BlockMediaRelation.block_id == NoteBlock.id)
        .where(NoteBlock.note_id == note.id)
        .order_by(NoteBlock.sort_order, BlockMediaRelation.sort_order)
    ).first()
    if not first_relation:
        return None

    return first_relation.media_id


def create_note_share(
    session: Session,
    current_user: User,
    note_id: int,
    data: NoteShareCreate,
):
    note = get_accessible_note(session, current_user, note_id)
    if note.status != "published" or note.is_private:
        raise HTTPException(status_code=400, detail="Only public published notes can be shared")

    author = session.get(User, note.user_id)
    share = NoteShare(
        user_id=current_user.id,
        note_id=note.id,
        platform=data.platform,
        note_title=note.title or "无题",
        note_summary=note.summary,
        note_author_name=(author.nickname or author.username) if author else None,
        cover_media_id=_get_cover_media_id(session, note),
        share_title=data.share_title,
        share_text=data.share_text,
        share_url=data.share_url,
    )
    session.add(share)
    session.commit()
    session.refresh(share)
    return share


def list_my_note_shares(
    session: Session,
    current_user: User,
    offset: int = 0,
    limit: int = 20,
):
    statement = (
        select(NoteShare)
        .where(NoteShare.user_id == current_user.id)
        .order_by(NoteShare.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    items = session.exec(statement).all()
    total = session.exec(
        select(func.count()).select_from(NoteShare).where(NoteShare.user_id == current_user.id)
    ).one()
    serialized_items = []
    for item in items:
        serialized_items.append({
            "id": item.id,
            "note_id": item.note_id,
            "platform": item.platform,
            "note_title": item.note_title,
            "note_summary": item.note_summary,
            "note_author_name": item.note_author_name,
            "cover_image_url": None,
            "share_title": item.share_title,
            "share_text": item.share_text,
            "share_url": item.share_url,
            "created_at": item.created_at,
        })
    return {
        "items": serialized_items,
        "total": total,
        "offset": offset,
        "limit": limit,
    }
