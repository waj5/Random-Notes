from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models.block_media_relation import BlockMediaRelation
from app.models.media_asset import MediaAsset
from app.models.note import Note
from app.models.note_block import NoteBlock
from app.models.user import User
from app.schemas.note_content import NoteContentUpdate
from app.services.note_services import get_note_detail


def save_note_content(
    session: Session,
    current_user: User,
    note_id: int,
    data: NoteContentUpdate,
):
    note = session.exec(
        select(Note).where(
            Note.id == note_id,
            Note.user_id == current_user.id,
            Note.deleted_at.is_(None),
        )
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    update_data = data.model_dump(exclude={"blocks"}, exclude_unset=True)
    for key, value in update_data.items():
        setattr(note, key, value)

    existing_blocks = session.exec(
        select(NoteBlock).where(NoteBlock.note_id == note_id)
    ).all()
    existing_block_map = {block.id: block for block in existing_blocks}

    incoming_block_ids = {item.id for item in data.blocks if item.id is not None}
    existing_block_ids = set(existing_block_map.keys())

    blocks_to_delete = existing_block_ids - incoming_block_ids
    if blocks_to_delete:
        relations_to_delete = session.exec(
            select(BlockMediaRelation).where(BlockMediaRelation.block_id.in_(blocks_to_delete))
        ).all()
        for relation in relations_to_delete:
            session.delete(relation)

        for block_id in blocks_to_delete:
            session.delete(existing_block_map[block_id])

    first_cover_media_id = None

    for item in data.blocks:
        if item.id is not None:
            block = existing_block_map.get(item.id)
            if not block or block.note_id != note_id:
                raise HTTPException(status_code=404, detail=f"Note block {item.id} not found")

            block.block_type = item.block_type
            block.sort_order = item.sort_order
            block.text_content = item.text_content
            block.text_align = item.text_align
            block.layout_style = item.layout_style
            block.caption = item.caption
            block.updated_at = datetime.utcnow()
            session.add(block)
        else:
            block = NoteBlock(
                note_id=note_id,
                block_type=item.block_type,
                sort_order=item.sort_order,
                text_content=item.text_content,
                text_align=item.text_align,
                layout_style=item.layout_style,
                caption=item.caption,
            )
            session.add(block)
            session.flush()

        old_relations = session.exec(
            select(BlockMediaRelation).where(BlockMediaRelation.block_id == block.id)
        ).all()
        for relation in old_relations:
            session.delete(relation)

        if item.media_ids:
            media_assets = session.exec(
                select(MediaAsset).where(
                    MediaAsset.id.in_(item.media_ids),
                    MediaAsset.user_id == current_user.id,
                )
            ).all()

            media_map = {media.id: media for media in media_assets}
            if len(media_map) != len(item.media_ids):
                raise HTTPException(status_code=404, detail="Some media assets were not found")

            for index, media_id in enumerate(item.media_ids):
                relation = BlockMediaRelation(
                    block_id=block.id,
                    media_id=media_id,
                    sort_order=index,
                )
                session.add(relation)

            if first_cover_media_id is None and item.media_ids:
                first_cover_media_id = item.media_ids[0]

    note.cover_media_id = first_cover_media_id
    note.updated_at = datetime.utcnow()
    session.add(note)

    session.commit()
    return get_note_detail(session, current_user, note_id)