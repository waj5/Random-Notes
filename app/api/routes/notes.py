from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from app.schemas.note_cover import NoteCoverUpdate

from app.api.deps import get_current_user, get_current_user_optional, get_session
from app.core.response import success_response
from app.models.user import User
from app.schemas.note import NoteCreate, NoteUpdate
from app.schemas.note_content import NoteContentUpdate
from app.services.note_content_services import save_note_content
from app.services.note_services import (
    create_note,
    delete_note,
    get_note,
    get_note_detail,
    list_following_notes,
    list_hot_notes,
    list_notes,
    list_public_notes,
    list_user_public_notes,
    publish_note,
    unpublish_note,
    update_note,
    update_note_cover,
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
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: str | None = Query(None),
    keyword: str | None = Query(None),
    mood: str | None = Query(None),
    scene: str | None = Query(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    notes = list_notes(
        session=session,
        current_user=current_user,
        offset=offset,
        limit=limit,
        status=status,
        keyword=keyword,
        mood=mood,
        scene=scene,
    )
    return success_response(notes)


@router.get("/public")
def list_public_notes_api(
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    keyword: str | None = Query(None),
    mood: str | None = Query(None),
    scene: str | None = Query(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    notes = list_public_notes(
        session=session,
        current_user=current_user,
        offset=offset,
        limit=limit,
        keyword=keyword,
        mood=mood,
        scene=scene,
    )
    return success_response(notes)


@router.get("/hot")
def list_hot_notes_api(
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    notes = list_hot_notes(
        session=session,
        current_user=current_user,
        offset=offset,
        limit=limit,
    )
    return success_response(notes)


@router.get("/following")
def list_following_notes_api(
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    notes = list_following_notes(
        session=session,
        current_user=current_user,
        offset=offset,
        limit=limit,
    )
    return success_response(notes)


@router.get("/public/user/{user_id}")
def list_user_public_notes_api(
    user_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_current_user_optional),
):
    notes = list_user_public_notes(
        session=session,
        current_user=current_user,
        user_id=user_id,
        offset=offset,
        limit=limit,
    )
    return success_response(notes)


@router.put("/content/{note_id}")
def save_note_content_api(
    note_id: int,
    data: NoteContentUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = save_note_content(session, current_user, note_id, data)
    return success_response(result, "Note content saved successfully")


@router.get("/detail/{note_id}")
def get_note_detail_api(
    note_id: int,
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_current_user_optional),
):
    note = get_note_detail(session, current_user, note_id)
    return success_response(note)


@router.post("/{note_id}/publish")
def publish_note_api(
    note_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    note = publish_note(session, current_user, note_id)
    return success_response(note, "Note published successfully")


@router.post("/{note_id}/unpublish")
def unpublish_note_api(
    note_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    note = unpublish_note(session, current_user, note_id)
    return success_response(note, "Note moved to draft successfully")


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

@router.put("/{note_id}/cover")
def update_note_cover_api(
    note_id: int,
    data: NoteCoverUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    note = update_note_cover(session, current_user, note_id, data.cover_media_id)
    return success_response(note, "Note cover updated successfully")