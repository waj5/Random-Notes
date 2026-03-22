from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models.note import Note
from app.models.note_comment import NoteComment
from app.models.user import User
from app.schemas.note_comment import NoteCommentCreate, NoteCommentUpdate
from app.services.note_services import get_accessible_note


def list_note_comments(session: Session, note: Note):
    comments = session.exec(
        select(NoteComment)
        .where(
            NoteComment.note_id == note.id,
            NoteComment.deleted_at.is_(None),
        )
        .order_by(NoteComment.created_at.asc())
    ).all()

    user_ids = list({comment.user_id for comment in comments})
    users = session.exec(
        select(User).where(User.id.in_(user_ids))
    ).all() if user_ids else []
    user_map = {user.id: user for user in users}

    return [
        {
            "id": comment.id,
            "note_id": comment.note_id,
            "user_id": comment.user_id,
            "username": user_map[comment.user_id].username if comment.user_id in user_map else "",
            "nickname": user_map[comment.user_id].nickname if comment.user_id in user_map else "",
            "avatar_url": user_map[comment.user_id].avatar_url if comment.user_id in user_map else None,
            "content": comment.content,
            "created_at": comment.created_at,
        }
        for comment in comments
    ]


def create_note_comment(
    session: Session,
    current_user: User,
    note_id: int,
    data: NoteCommentCreate,
):
    note = get_accessible_note(session, current_user, note_id)
    if note.status != "published" or note.is_private:
        raise HTTPException(status_code=403, detail="Cannot comment on this note")

    content = data.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Comment content cannot be empty")

    comment = NoteComment(
        note_id=note_id,
        user_id=current_user.id,
        content=content,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(comment)
    session.commit()
    session.refresh(comment)

    return {
        "id": comment.id,
        "note_id": comment.note_id,
        "user_id": current_user.id,
        "username": current_user.username,
        "nickname": current_user.nickname,
        "avatar_url": current_user.avatar_url,
        "content": comment.content,
        "created_at": comment.created_at,
    }


def _serialize_comment(comment: NoteComment, user: User | None):
    return {
        "id": comment.id,
        "note_id": comment.note_id,
        "user_id": comment.user_id,
        "username": user.username if user else "",
        "nickname": user.nickname if user else "",
        "avatar_url": user.avatar_url if user else None,
        "content": comment.content,
        "created_at": comment.created_at,
    }


def update_note_comment(
    session: Session,
    current_user: User,
    note_id: int,
    comment_id: int,
    data: NoteCommentUpdate,
):
    note = get_accessible_note(session, current_user, note_id)
    comment = session.get(NoteComment, comment_id)
    if not comment or comment.note_id != note.id or comment.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own comments")

    content = data.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Comment content cannot be empty")

    comment.content = content
    comment.updated_at = datetime.utcnow()
    session.add(comment)
    session.commit()
    session.refresh(comment)

    return _serialize_comment(comment, current_user)


def delete_note_comment(
    session: Session,
    current_user: User,
    note_id: int,
    comment_id: int,
):
    note = get_accessible_note(session, current_user, note_id)
    comment = session.get(NoteComment, comment_id)
    if not comment or comment.note_id != note.id or comment.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.user_id != current_user.id and note.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No permission to delete this comment")

    comment.deleted_at = datetime.utcnow()
    comment.updated_at = datetime.utcnow()
    session.add(comment)
    session.commit()
    return {"message": "Comment deleted"}
