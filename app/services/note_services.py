from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models.block_media_relation import BlockMediaRelation
from app.models.media_asset import MediaAsset
from app.models.note import Note
from app.models.note_block import NoteBlock
from app.models.user import User
from app.schemas.note import NoteCreate, NoteUpdate


def create_note(session: Session, current_user: User, data: NoteCreate):
    note = Note(
        user_id=current_user.id,
        title=data.title,
        summary=data.summary,
        mood=data.mood,
        scene=data.scene,
        book_theme=data.book_theme or "default",
        is_private=data.is_private,
    )
    session.add(note)
    session.commit()
    session.refresh(note)
    return note


def list_notes(session: Session, current_user: User):
    statement = select(Note).where(
        Note.user_id == current_user.id,
        Note.deleted_at.is_(None),
    )
    return session.exec(statement).all()


def get_note(session: Session, current_user: User, note_id: int):
    statement = select(Note).where(
        Note.id == note_id,
        Note.user_id == current_user.id,
        Note.deleted_at.is_(None),
    )
    note = session.exec(statement).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


def update_note(session: Session, current_user: User, note_id: int, data: NoteUpdate):
    note = get_note(session, current_user, note_id)

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(note, key, value)

    note.updated_at = datetime.utcnow()
    session.add(note)
    session.commit()
    session.refresh(note)
    return note


def delete_note(session: Session, current_user: User, note_id: int):
    note = get_note(session, current_user, note_id)

    note.deleted_at = datetime.utcnow()
    note.updated_at = datetime.utcnow()
    session.add(note)
    session.commit()
    session.refresh(note)
    return note


def get_note_detail(session: Session, current_user: User, note_id: int):
    note = get_note(session, current_user, note_id)

    blocks = session.exec(
        select(NoteBlock)
        .where(NoteBlock.note_id == note_id)
        .order_by(NoteBlock.sort_order)
    ).all()

    block_ids = [block.id for block in blocks]

    relations = []
    media_assets = []

    if block_ids:
        relations = session.exec(
            select(BlockMediaRelation)
            .where(BlockMediaRelation.block_id.in_(block_ids))
            .order_by(BlockMediaRelation.sort_order)
        ).all()

        media_ids = [relation.media_id for relation in relations]
        if media_ids:
            media_assets = session.exec(
                select(MediaAsset).where(MediaAsset.id.in_(media_ids))
            ).all()

    media_map = {media.id: media for media in media_assets}

    relation_map: dict[int, list[MediaAsset]] = {}
    for relation in relations:
        media = media_map.get(relation.media_id)
        if not media:
            continue
        relation_map.setdefault(relation.block_id, []).append(media)

    block_details = []
    for block in blocks:
        block_details.append(
            {
                "id": block.id,
                "note_id": block.note_id,
                "block_type": block.block_type,
                "sort_order": block.sort_order,
                "text_content": block.text_content,
                "text_align": block.text_align,
                "layout_style": block.layout_style,
                "caption": block.caption,
                "created_at": block.created_at,
                "updated_at": block.updated_at,
                "media_assets": relation_map.get(block.id, []),
            }
        )

    return {
        "id": note.id,
        "user_id": note.user_id,
        "title": note.title,
        "summary": note.summary,
        "mood": note.mood,
        "scene": note.scene,
        "book_theme": note.book_theme,
        "is_private": note.is_private,
        "status": note.status,
        "created_at": note.created_at,
        "updated_at": note.updated_at,
        "blocks": block_details,
    }