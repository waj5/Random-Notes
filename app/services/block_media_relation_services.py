from fastapi import HTTPException
from sqlmodel import Session, select

from app.models.block_media_relation import BlockMediaRelation
from app.models.media_asset import MediaAsset
from app.models.note import Note
from app.models.note_block import NoteBlock, BlockType
from app.models.user import User
from app.schemas.block_media_relation import BlockMediaRelationCreate


def get_user_note_block(session: Session, current_user: User, note_id: int, block_id: int):
    note = session.exec(
        select(Note).where(
            Note.id == note_id,
            Note.user_id == current_user.id,
            Note.deleted_at.is_(None),
        )
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    block = session.get(NoteBlock, block_id)
    if not block or block.note_id != note_id:
        raise HTTPException(status_code=404, detail="Note block not found")

    return block


def get_user_media_asset(session: Session, current_user: User, media_id: int):
    media = session.exec(
        select(MediaAsset).where(
            MediaAsset.id == media_id,
            MediaAsset.user_id == current_user.id,
        )
    ).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media asset not found")
    return media


def create_block_media_relation(
    session: Session,
    current_user: User,
    note_id: int,
    block_id: int,
    data: BlockMediaRelationCreate,
):
    block = get_user_note_block(session, current_user, note_id, block_id)
    get_user_media_asset(session, current_user, data.media_id)

    if block.block_type == BlockType.text:
        raise HTTPException(
            status_code=400,
            detail="Text block does not support media",
        )

    existing_relations = session.exec(
        select(BlockMediaRelation).where(BlockMediaRelation.block_id == block_id)
    ).all()

    if block.block_type == BlockType.image and existing_relations:
        raise HTTPException(
            status_code=400,
            detail="Image block can only have one media asset",
        )

    relation = BlockMediaRelation(
        block_id=block_id,
        media_id=data.media_id,
        sort_order=data.sort_order,
    )
    session.add(relation)
    session.commit()
    session.refresh(relation)
    return relation


def list_block_media_relations(
    session: Session,
    current_user: User,
    note_id: int,
    block_id: int,
):
    get_user_note_block(session, current_user, note_id, block_id)

    statement = (
        select(BlockMediaRelation)
        .where(BlockMediaRelation.block_id == block_id)
        .order_by(BlockMediaRelation.sort_order)
    )
    return session.exec(statement).all()


def delete_block_media_relation(
    session: Session,
    current_user: User,
    note_id: int,
    block_id: int,
    relation_id: int,
):
    get_user_note_block(session, current_user, note_id, block_id)

    relation = session.get(BlockMediaRelation, relation_id)
    if not relation or relation.block_id != block_id:
        raise HTTPException(status_code=404, detail="Block media relation not found")

    session.delete(relation)
    session.commit()
    return {"message": "Block media relation deleted"}