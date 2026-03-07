from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.deps import get_session
from app.schemas.note import NoteCreate, NotePublic, NoteUpdate
from app.services.note_services import (
    create_note,
    list_notes,
    get_note,
    update_note,
    delete_note,
)

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("/", response_model=NotePublic)
def create_note_api(
    data: NoteCreate,
    session: Session = Depends(get_session),
):
    return create_note(session, data)


@router.get("/", response_model=list[NotePublic])
def list_notes_api(
    session: Session = Depends(get_session),
):
    return list_notes(session)


@router.get("/{note_id}", response_model=NotePublic)
def get_note_api(
    note_id: int,
    session: Session = Depends(get_session),
):
    return get_note(session, note_id)


@router.put("/{note_id}", response_model=NotePublic)
def update_note_api(
    note_id: int,
    data: NoteUpdate,
    session: Session = Depends(get_session),
):
    return update_note(session, note_id, data)


@router.delete("/{note_id}", response_model=NotePublic)
def delete_note_api(
    note_id: int,
    session: Session = Depends(get_session),
):
    return delete_note(session, note_id)