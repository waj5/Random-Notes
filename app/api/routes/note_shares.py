from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.api.deps import get_current_user, get_session
from app.core.response import success_response
from app.models.user import User
from app.schemas.note_share import NoteShareCreate
from app.services.note_share_services import create_note_share, list_my_note_shares

router = APIRouter(prefix="/notes/shares", tags=["note shares"])


@router.get("/me")
def list_my_note_shares_api(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = list_my_note_shares(session, current_user, offset, limit)
    return success_response(result)


@router.post("/{note_id}")
def create_note_share_api(
    note_id: int,
    data: NoteShareCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = create_note_share(session, current_user, note_id, data)
    return success_response(result, "Share record created successfully")
