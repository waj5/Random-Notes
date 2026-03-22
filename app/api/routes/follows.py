from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.deps import get_current_user, get_session
from app.core.response import success_response
from app.models.user import User
from app.services.follow_services import follow_user, list_following_ids, unfollow_user

router = APIRouter(prefix="/follows", tags=["follows"])


@router.get("/")
def list_following_api(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    following_ids = list_following_ids(session, current_user)
    return success_response({"following_ids": following_ids})


@router.post("/{target_user_id}")
def follow_user_api(
    target_user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    relation = follow_user(session, current_user, target_user_id)
    return success_response(relation, "Followed successfully")


@router.delete("/{target_user_id}")
def unfollow_user_api(
    target_user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = unfollow_user(session, current_user, target_user_id)
    return success_response(result, "Unfollowed successfully")
