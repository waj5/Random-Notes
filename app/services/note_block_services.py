from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models.note import Note
from app.models.note_block import NoteBlock
from app.models.user import User
from app.schemas.note_block import NoteBlockCreate, NoteBlockUpdate
from app.schemas.note_block_order import NoteBlockOrderItem


def get_user_note(session: Session, current_user: User, note_id: int):
    statement = select(Note).where(
        Note.id == note_id,
        Note.user_id == current_user.id,
        Note.deleted_at.is_(None),
    )
    note = session.exec(statement).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


def create_note_block(session: Session, current_user: User, note_id: int, data: NoteBlockCreate):
    get_user_note(session, current_user, note_id)

    block = NoteBlock(
        note_id=note_id,
        block_type=data.block_type,
        sort_order=data.sort_order,
        text_content=data.text_content,
        text_align=data.text_align,
        layout_style=data.layout_style,
        caption=data.caption,
    )
    session.add(block)
    session.commit()
    session.refresh(block)
    return block


def list_note_blocks(session: Session, current_user: User, note_id: int):
    get_user_note(session, current_user, note_id)

    statement = (
        select(NoteBlock)
        .where(NoteBlock.note_id == note_id)
        .order_by(NoteBlock.sort_order)
    )
    return session.exec(statement).all()


def get_note_block(session: Session, current_user: User, note_id: int, block_id: int):
    get_user_note(session, current_user, note_id)

    block = session.get(NoteBlock, block_id)
    if not block or block.note_id != note_id:
        raise HTTPException(status_code=404, detail="Note block not found")
    return block


def update_note_block(
    session: Session,
    current_user: User,
    note_id: int,
    block_id: int,
    data: NoteBlockUpdate,
):
    get_user_note(session, current_user, note_id)

    block = session.get(NoteBlock, block_id)
    if not block or block.note_id != note_id:
        raise HTTPException(status_code=404, detail="Note block not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(block, key, value)

    block.updated_at = datetime.utcnow()
    session.add(block)
    session.commit()
    session.refresh(block)
    return block


def delete_note_block(session: Session, current_user: User, note_id: int, block_id: int):
    get_user_note(session, current_user, note_id)

    block = session.get(NoteBlock, block_id)
    if not block or block.note_id != note_id:
        raise HTTPException(status_code=404, detail="Note block not found")

    session.delete(block)
    session.commit()
    return {"message": "Note block deleted"}


def reorder_note_blocks(
    session: Session,
    current_user: User,
    note_id: int,
    items: list[NoteBlockOrderItem],
):
    get_user_note(session, current_user, note_id)

    block_ids = [item.block_id for item in items]

    statement = select(NoteBlock).where(
        NoteBlock.note_id == note_id,
        NoteBlock.id.in_(block_ids),
    )
    blocks = session.exec(statement).all()

    if len(blocks) != len(items):
        raise HTTPException(status_code=404, detail="Some note blocks were not found")

    block_map = {block.id: block for block in blocks}

    for item in items:
        block = block_map[item.block_id]
        block.sort_order = item.sort_order
        block.updated_at = datetime.utcnow()
        session.add(block)

    session.commit()

    statement = (
        select(NoteBlock)
        .where(NoteBlock.note_id == note_id)
        .order_by(NoteBlock.sort_order)
    )
    return session.exec(statement).all()