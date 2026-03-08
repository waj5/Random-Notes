from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.deps import get_current_user, get_session
from app.core.response import success_response
from app.models.user import User
from app.schemas.note import NoteCreate, NoteUpdate
from app.services.note_services import (
    create_note,
    delete_note,
    get_note,
    get_note_detail,
    list_notes,
    update_note,
)

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("/")
def create_note_api(
    data: NoteCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    note = create_note(session, current_user, data)
    return success_response(note, "Note created successfully")


@router.get("/")
def list_notes_api(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    notes = list_notes(session, current_user)
    return success_response(notes)


@router.get("/detail/{note_id}")
def get_note_detail_api(
    note_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    note = get_note_detail(session, current_user, note_id)
    return success_response(note)


@router.get("/{note_id}")
def get_note_api(
    note_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    note = get_note(session, current_user, note_id)
    return success_response(note)


@router.put("/{note_id}")
def update_note_api(
    note_id: int,
    data: NoteUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    note = update_note(session, current_user, note_id, data)
    return success_response(note, "Note updated successfully")


@router.delete("/{note_id}")
def delete_note_api(
    note_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    note = delete_note(session, current_user, note_id)
    return success_response(note, "Note deleted successfully")