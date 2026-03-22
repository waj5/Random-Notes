from fastapi import HTTPException
from sqlmodel import Session, select

from app.models.user import User, UserStatus
from app.models.user_follow import UserFollow


def list_following_ids(session: Session, current_user: User):
    relations = session.exec(
        select(UserFollow).where(UserFollow.follower_id == current_user.id)
    ).all()
    return [relation.followee_id for relation in relations]


def follow_user(session: Session, current_user: User, target_user_id: int):
    if current_user.id == target_user_id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    target_user = session.get(User, target_user_id)
    if not target_user or target_user.deleted_at is not None or target_user.status != UserStatus.active:
        raise HTTPException(status_code=404, detail="User not found")

    existing = session.exec(
        select(UserFollow).where(
            UserFollow.follower_id == current_user.id,
            UserFollow.followee_id == target_user_id,
        )
    ).first()
    if existing:
        return existing

    relation = UserFollow(
        follower_id=current_user.id,
        followee_id=target_user_id,
    )
    session.add(relation)
    session.commit()
    session.refresh(relation)
    return relation


def unfollow_user(session: Session, current_user: User, target_user_id: int):
    relation = session.exec(
        select(UserFollow).where(
            UserFollow.follower_id == current_user.id,
            UserFollow.followee_id == target_user_id,
        )
    ).first()
    if not relation:
        return {"message": "Not following"}

    session.delete(relation)
    session.commit()
    return {"message": "Unfollowed"}
