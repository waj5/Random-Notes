from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.deps import get_current_user, get_session
from app.models.user import User
from app.schemas.note import NoteCreate, NotePublic, NoteUpdate
from app.schemas.note_detail import NoteDetailPublic
from app.services.note_services import (
    create_note,
    delete_note,
    get_note,
    get_note_detail,
    list_notes,
    update_note,
)

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("/", response_model=NotePublic)
def create_note_api(
    data: NoteCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return create_note(session, current_user, data)


@router.get("/", response_model=list[NotePublic])
def list_notes_api(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return list_notes(session, current_user)


@router.get("/detail/{note_id}", response_model=NoteDetailPublic)
def get_note_detail_api(
    note_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return get_note_detail(session, current_user, note_id)


@router.get("/{note_id}", response_model=NotePublic)
def get_note_api(
    note_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return get_note(session, current_user, note_id)


@router.put("/{note_id}", response_model=NotePublic)
def update_note_api(
    note_id: int,
    data: NoteUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return update_note(session, current_user, note_id, data)


@router.delete("/{note_id}", response_model=NotePublic)
def delete_note_api(
    note_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return delete_note(session, current_user, note_id)