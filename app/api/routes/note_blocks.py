from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.deps import get_current_user, get_session
from app.models.user import User
from app.core.response import success_response
from app.schemas.note_block import NoteBlockCreate, NoteBlockUpdate
from app.schemas.note_block_order import NoteBlockReorder
from app.services.note_block_services import (
    create_note_block,
    list_note_blocks,
    get_note_block,
    update_note_block,
    delete_note_block,
    reorder_note_blocks,
)

router = APIRouter(prefix="/notes/{note_id}/blocks", tags=["note-blocks"])


@router.post("/")
def create_note_block_api(
    note_id: int,
    data: NoteBlockCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    note_block = create_note_block(session, current_user, note_id, data)
    return success_response(note_block, "Note block created successfully")


@router.get("/", )
def list_note_blocks_api(
    note_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    note_blocks = list_note_blocks(session, current_user, note_id)
    return success_response(note_blocks)


@router.patch("/reorder")
def reorder_note_blocks_api(
    note_id: int,
    data: NoteBlockReorder,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    note_blocks = reorder_note_blocks(session, current_user, note_id, data.items)
    return success_response(note_blocks, "Note blocks reordered successfully")


@router.get("/{block_id}")
def get_note_block_api(
    note_id: int,
    block_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    note_block = get_note_block(session, current_user, note_id, block_id)
    return success_response(note_block)


@router.put("/{block_id}")
def update_note_block_api(
    note_id: int,
    block_id: int,
    data: NoteBlockUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    note_block = update_note_block(session, current_user, note_id, block_id, data)
    return success_response(note_block, "Note block updated successfully")


@router.delete("/{block_id}")
def delete_note_block_api(
    note_id: int,
    block_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    note_block = delete_note_block(session, current_user, note_id, block_id)
    return success_response(note_block, "Note block deleted successfully")