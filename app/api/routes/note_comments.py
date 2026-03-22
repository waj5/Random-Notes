from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.deps import get_current_user, get_current_user_optional, get_session
from app.core.response import success_response
from app.models.user import User
from app.schemas.note_comment import NoteCommentCreate, NoteCommentUpdate
from app.services.note_comment_services import (
    create_note_comment,
    delete_note_comment,
    list_note_comments,
    update_note_comment,
)
from app.services.note_services import get_accessible_note

router = APIRouter(prefix="/notes/{note_id}/comments", tags=["note-comments"])


@router.get("/")
def list_note_comments_api(
    note_id: int,
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_current_user_optional),
):
    note = get_accessible_note(session, current_user, note_id)
    comments = list_note_comments(session, note)
    return success_response(comments)


@router.post("/")
def create_note_comment_api(
    note_id: int,
    data: NoteCommentCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    comment = create_note_comment(session, current_user, note_id, data)
    return success_response(comment, "Comment created successfully")


@router.put("/{comment_id}")
def update_note_comment_api(
    note_id: int,
    comment_id: int,
    data: NoteCommentUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    comment = update_note_comment(session, current_user, note_id, comment_id, data)
    return success_response(comment, "Comment updated successfully")


@router.delete("/{comment_id}")
def delete_note_comment_api(
    note_id: int,
    comment_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = delete_note_comment(session, current_user, note_id, comment_id)
    return success_response(result, "Comment deleted successfully")
