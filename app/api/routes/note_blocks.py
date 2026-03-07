from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.deps import get_current_user, get_session
from app.models.user import User
from app.schemas.note_block import NoteBlockCreate, NoteBlockPublic, NoteBlockUpdate
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


@router.post("/", response_model=NoteBlockPublic)
def create_note_block_api(
    note_id: int,
    data: NoteBlockCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return create_note_block(session, current_user, note_id, data)


@router.get("/", response_model=list[NoteBlockPublic])
def list_note_blocks_api(
    note_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return list_note_blocks(session, current_user, note_id)


@router.patch("/reorder", response_model=list[NoteBlockPublic])
def reorder_note_blocks_api(
    note_id: int,
    data: NoteBlockReorder,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return reorder_note_blocks(session, current_user, note_id, data.items)


@router.get("/{block_id}", response_model=NoteBlockPublic)
def get_note_block_api(
    note_id: int,
    block_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return get_note_block(session, current_user, note_id, block_id)


@router.put("/{block_id}", response_model=NoteBlockPublic)
def update_note_block_api(
    note_id: int,
    block_id: int,
    data: NoteBlockUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return update_note_block(session, current_user, note_id, block_id, data)


@router.delete("/{block_id}")
def delete_note_block_api(
    note_id: int,
    block_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return delete_note_block(session, current_user, note_id, block_id)