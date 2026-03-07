from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models.note import Note
from app.schemas.note import NoteCreate, NoteUpdate


def create_note(session: Session, data: NoteCreate):
    note = Note(
        user_id=1,
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


def list_notes(session: Session):
    statement = select(Note).where(Note.deleted_at.is_(None))
    return session.exec(statement).all()


def get_note(session: Session, note_id: int):
    note = session.get(Note, note_id)
    if not note or note.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


def update_note(session: Session, note_id: int, data: NoteUpdate):
    note = session.get(Note, note_id)
    if not note or note.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Note not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(note, key, value)

    note.updated_at = datetime.utcnow()
    session.add(note)
    session.commit()
    session.refresh(note)
    return note


def delete_note(session: Session, note_id: int):
    note = session.get(Note, note_id)
    if not note or note.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Note not found")

    note.deleted_at = datetime.utcnow()
    note.updated_at = datetime.utcnow()
    session.add(note)
    session.commit()
    session.refresh(note)
    return note