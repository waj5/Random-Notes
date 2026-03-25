from datetime import datetime
import math

from fastapi import HTTPException
from sqlmodel import Session, func, or_, select

from app.models.block_media_relation import BlockMediaRelation
from app.models.media_asset import MediaAsset
from app.models.note import Note
from app.models.note_comment import NoteComment
from app.models.note_block import NoteBlock
from app.models.user import User
from app.models.user_follow import UserFollow
from app.schemas.note import NoteCreate, NoteUpdate
from app.services.media_asset_services import serialize_media_asset


def create_note(session: Session, current_user: User, data: NoteCreate):
    note = Note(
        user_id=current_user.id,
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


def _build_note_list_response(
    session: Session,
    filters: list,
    offset: int,
    limit: int,
    current_user: User | None = None,
    score_fn=None,
):
    total = session.exec(
        select(func.count()).select_from(Note).where(*filters)
    ).one()

    items = session.exec(
        select(Note)
        .where(*filters)
        .order_by(Note.created_at.desc())
    ).all()

    note_ids = [note.id for note in items]
    blocks = session.exec(
        select(NoteBlock)
        .where(NoteBlock.note_id.in_(note_ids))
        .order_by(NoteBlock.sort_order)
    ).all() if note_ids else []

    block_map = {}
    for block in blocks:
        block_map.setdefault(block.note_id, []).append(block)

    block_ids = [block.id for block in blocks]
    relations = session.exec(
        select(BlockMediaRelation)
        .where(BlockMediaRelation.block_id.in_(block_ids))
        .order_by(BlockMediaRelation.sort_order)
    ).all() if block_ids else []

    media_ids = [relation.media_id for relation in relations]
    media_assets = session.exec(
        select(MediaAsset).where(MediaAsset.id.in_(media_ids))
    ).all() if media_ids else []
    media_lookup = {media.id: media for media in media_assets}

    relation_map = {}
    for relation in relations:
        media = media_lookup.get(relation.media_id)
        if media:
            relation_map.setdefault(relation.block_id, []).append(media)

    author_ids = list({note.user_id for note in items})
    authors = session.exec(
        select(User).where(User.id.in_(author_ids))
    ).all() if author_ids else []
    author_map = {author.id: author for author in authors}

    comments = session.exec(
        select(NoteComment)
        .where(
            NoteComment.note_id.in_(note_ids),
            NoteComment.deleted_at.is_(None),
        )
        .order_by(NoteComment.created_at.desc())
    ).all() if note_ids else []

    comment_user_ids = list({comment.user_id for comment in comments})
    comment_users = session.exec(
        select(User).where(User.id.in_(comment_user_ids))
    ).all() if comment_user_ids else []
    comment_user_map = {user.id: user for user in comment_users}

    comment_count_map: dict[int, int] = {}
    hot_comment_map: dict[int, dict] = {}
    for comment in comments:
        comment_count_map[comment.note_id] = comment_count_map.get(comment.note_id, 0) + 1

        age_hours = max((datetime.utcnow() - comment.created_at).total_seconds() / 3600, 0)
        freshness = 1 / (1 + age_hours / 24)
        score = len(comment.content.strip()) * 0.02 + freshness
        current_hot_comment = hot_comment_map.get(comment.note_id)
        if not current_hot_comment or score > current_hot_comment["_score"]:
            comment_user = comment_user_map.get(comment.user_id)
            hot_comment_map[comment.note_id] = {
                "_score": score,
                "id": comment.id,
                "user_id": comment.user_id,
                "nickname": comment_user.nickname if comment_user else "",
                "username": comment_user.username if comment_user else "",
                "content": comment.content,
                "created_at": comment.created_at,
            }

    result_items = []
    for note in items:
        note_blocks = block_map.get(note.id, [])
        author = author_map.get(note.user_id)
        note_dict = {
            "id": note.id,
            "user_id": note.user_id,
            "author_username": author.username if author else None,
            "author_nickname": author.nickname if author else None,
            "author_avatar_url": author.avatar_url if author else None,
            "title": note.title,
            "summary": note.summary,
            "created_at": note.created_at,
            "book_theme": note.book_theme,
            "status": note.status,
            "is_private": note.is_private,
            "comment_count": comment_count_map.get(note.id, 0),
            "hot_comment": None,
            "blocks": []
        }

        if note.id in hot_comment_map:
            hot_comment = hot_comment_map[note.id].copy()
            hot_comment.pop("_score", None)
            note_dict["hot_comment"] = hot_comment

        for block in note_blocks:
            note_dict["blocks"].append({
                "id": block.id,
                "text_content": block.text_content,
                "media_assets": [
                    serialize_media_asset(media, current_user)
                    for media in relation_map.get(block.id, [])
                ]
            })
        result_items.append(note_dict)

    if score_fn is not None:
        result_items = sorted(result_items, key=score_fn, reverse=True)

    paged_items = result_items[offset:offset + limit]

    return {
        "items": paged_items,
        "total": total,
        "offset": offset,
        "limit": limit,
    }


def _get_note_content_features(note_dict: dict):
    image_count = 0
    text_length = 0
    gallery_block_count = 0

    for block in note_dict.get("blocks", []):
        image_count += len(block.get("media_assets", []))
        text_length += len((block.get("text_content") or "").strip())

    return {
        "image_count": image_count,
        "text_length": text_length,
        "gallery_block_count": gallery_block_count,
    }


def _get_user_profile(session: Session, current_user: User):
    notes = session.exec(
        select(Note).where(
            Note.user_id == current_user.id,
            Note.deleted_at.is_(None),
        )
    ).all()

    if not notes:
        return {
            "image_pref": 0.35,
            "text_pref": 0.45,
        }

    note_ids = [note.id for note in notes]
    blocks = session.exec(
        select(NoteBlock).where(NoteBlock.note_id.in_(note_ids))
    ).all() if note_ids else []

    block_ids = [block.id for block in blocks]
    relations = session.exec(
        select(BlockMediaRelation).where(BlockMediaRelation.block_id.in_(block_ids))
    ).all() if block_ids else []

    image_count_by_block: dict[int, int] = {}
    for relation in relations:
        image_count_by_block[relation.block_id] = image_count_by_block.get(relation.block_id, 0) + 1

    image_total = 0
    text_total = 0
    for block in blocks:
        image_total += image_count_by_block.get(block.id, 0)
        text_total += len((block.text_content or "").strip())

    note_count = max(len(notes), 1)
    image_pref = min((image_total / note_count) / 6, 1)
    text_pref = min((text_total / note_count) / 200, 1)

    return {
        "image_pref": image_pref,
        "text_pref": text_pref,
    }


def _get_author_follower_count_map(session: Session, author_ids: list[int]):
    relations = session.exec(
        select(UserFollow).where(UserFollow.followee_id.in_(author_ids))
    ).all() if author_ids else []

    follower_counts: dict[int, int] = {}
    for relation in relations:
        follower_counts[relation.followee_id] = follower_counts.get(relation.followee_id, 0) + 1

    return follower_counts


def list_notes(
    session: Session,
    current_user: User,
    offset: int = 0,
    limit: int = 10,
    status: str | None = None,
    keyword: str | None = None,
    mood: str | None = None,
    scene: str | None = None,
):
    filters = [
        Note.user_id == current_user.id,
        Note.deleted_at.is_(None),
    ]

    if status:
        filters.append(Note.status == status)

    if mood:
        filters.append(Note.mood == mood)

    if scene:
        filters.append(Note.scene == scene)

    if keyword:
        keyword_value = f"%{keyword}%"

        matching_note_ids_subquery = (
            select(NoteBlock.note_id)
            .where(NoteBlock.text_content.ilike(keyword_value))
        )

        filters.append(
            or_(
                Note.title.ilike(keyword_value),
                Note.summary.ilike(keyword_value),
                Note.id.in_(matching_note_ids_subquery),
            )
        )

    return _build_note_list_response(session, filters, offset, limit, current_user)


def list_public_notes(
    session: Session,
    current_user: User | None,
    offset: int = 0,
    limit: int = 10,
    keyword: str | None = None,
    mood: str | None = None,
    scene: str | None = None,
):
    filters = [
        Note.deleted_at.is_(None),
        Note.status == "published",
        Note.is_private.is_(False),
    ]

    if mood:
        filters.append(Note.mood == mood)

    if scene:
        filters.append(Note.scene == scene)

    if keyword:
        keyword_value = f"%{keyword}%"

        matching_note_ids_subquery = (
            select(NoteBlock.note_id)
            .where(NoteBlock.text_content.ilike(keyword_value))
        )

        filters.append(
            or_(
                Note.title.ilike(keyword_value),
                Note.summary.ilike(keyword_value),
                Note.id.in_(matching_note_ids_subquery),
            )
        )

    author_ids = session.exec(
        select(Note.user_id).where(*filters)
    ).all()
    follower_count_map = _get_author_follower_count_map(session, list(set(author_ids)))

    if not current_user:
        def guest_score(note_dict: dict):
            features = _get_note_content_features(note_dict)
            image_density = min(features["image_count"] / 9, 1)
            text_density = min(features["text_length"] / 220, 1)
            age_hours = max((datetime.utcnow() - note_dict["created_at"]).total_seconds() / 3600, 0)
            freshness = 1 / (1 + age_hours / 24)
            follower_score = min(follower_count_map.get(note_dict["user_id"], 0) / 20, 1) * 0.18
            return freshness * 0.52 + image_density * 0.18 + text_density * 0.12 + follower_score

        return _build_note_list_response(session, filters, offset, limit, current_user, guest_score)

    following_ids = set(session.exec(
        select(UserFollow.followee_id).where(UserFollow.follower_id == current_user.id)
    ).all())
    profile = _get_user_profile(session, current_user)

    def personalized_score(note_dict: dict):
        features = _get_note_content_features(note_dict)
        image_density = min(features["image_count"] / 6, 1)
        text_density = min(features["text_length"] / 180, 1)
        age_hours = max((datetime.utcnow() - note_dict["created_at"]).total_seconds() / 3600, 0)
        freshness = 1 / (1 + age_hours / 18)
        follow_boost = 0.38 if note_dict["user_id"] in following_ids else 0
        preference_score = (
            (1 - abs(image_density - profile["image_pref"])) * 0.22
            + (1 - abs(text_density - profile["text_pref"])) * 0.16
        )
        content_score = image_density * 0.14 + text_density * 0.1
        follower_score = min(follower_count_map.get(note_dict["user_id"], 0) / 20, 1) * 0.08
        return freshness * 0.32 + follow_boost + preference_score + content_score + follower_score

    return _build_note_list_response(session, filters, offset, limit, current_user, personalized_score)


def list_following_notes(
    session: Session,
    current_user: User,
    offset: int = 0,
    limit: int = 10,
):
    following_ids = session.exec(
        select(UserFollow.followee_id).where(UserFollow.follower_id == current_user.id)
    ).all()

    if not following_ids:
        return {
            "items": [],
            "total": 0,
            "offset": offset,
            "limit": limit,
        }

    filters = [
        Note.deleted_at.is_(None),
        Note.status == "published",
        Note.is_private.is_(False),
        Note.user_id.in_(following_ids),
    ]

    return _build_note_list_response(session, filters, offset, limit, current_user)


def list_hot_notes(
    session: Session,
    current_user: User | None,
    offset: int = 0,
    limit: int = 10,
):
    filters = [
        Note.deleted_at.is_(None),
        Note.status == "published",
        Note.is_private.is_(False),
    ]

    author_ids = session.exec(
        select(Note.user_id).where(*filters)
    ).all()
    follower_count_map = _get_author_follower_count_map(session, list(set(author_ids)))

    def hot_score(note_dict: dict):
        features = _get_note_content_features(note_dict)
        image_density = min(features["image_count"] / 9, 1)
        text_density = min(features["text_length"] / 220, 1)
        age_hours = max((datetime.utcnow() - note_dict["created_at"]).total_seconds() / 3600, 0)
        freshness = 1 / (1 + age_hours / 30)
        follower_score = min(math.log1p(follower_count_map.get(note_dict["user_id"], 0)) / math.log(10), 1)
        return freshness * 0.42 + follower_score * 0.28 + image_density * 0.2 + text_density * 0.1

    return _build_note_list_response(session, filters, offset, limit, current_user, hot_score)


def list_user_public_notes(
    session: Session,
    current_user: User | None,
    user_id: int,
    offset: int = 0,
    limit: int = 10,
):
    author = session.get(User, user_id)
    if not author or author.deleted_at is not None or author.status != "active":
        raise HTTPException(status_code=404, detail="User not found")

    filters = [
        Note.deleted_at.is_(None),
        Note.status == "published",
        Note.is_private.is_(False),
        Note.user_id == user_id,
    ]
    return _build_note_list_response(session, filters, offset, limit, current_user)


def get_note(session: Session, current_user: User, note_id: int):
    statement = select(Note).where(
        Note.id == note_id,
        Note.user_id == current_user.id,
        Note.deleted_at.is_(None),
    )
    note = session.exec(statement).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


def get_accessible_note(session: Session, current_user: User | None, note_id: int):
    note = session.exec(
        select(Note).where(
            Note.id == note_id,
            Note.deleted_at.is_(None),
        )
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    if current_user and note.user_id == current_user.id:
        return note

    if note.status == "published" and note.is_private is False:
        return note

    raise HTTPException(status_code=404, detail="Note not found")


def update_note(session: Session, current_user: User, note_id: int, data: NoteUpdate):
    note = get_note(session, current_user, note_id)

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(note, key, value)

    note.updated_at = datetime.utcnow()
    session.add(note)
    session.commit()
    session.refresh(note)
    return note


def delete_note(session: Session, current_user: User, note_id: int):
    note = get_note(session, current_user, note_id)

    note.deleted_at = datetime.utcnow()
    note.updated_at = datetime.utcnow()
    session.add(note)
    session.commit()
    session.refresh(note)
    return note


def publish_note(session: Session, current_user: User, note_id: int):
    note = get_note(session, current_user, note_id)

    blocks = session.exec(
        select(NoteBlock).where(NoteBlock.note_id == note_id)
    ).all()
    if not blocks:
        raise HTTPException(status_code=400, detail="Cannot publish an empty note")

    note.status = "published"
    note.is_private = False
    note.updated_at = datetime.utcnow()
    session.add(note)
    session.commit()
    session.refresh(note)
    return note


def unpublish_note(session: Session, current_user: User, note_id: int):
    note = get_note(session, current_user, note_id)

    note.status = "draft"
    note.is_private = True
    note.updated_at = datetime.utcnow()
    session.add(note)
    session.commit()
    session.refresh(note)
    return note


def get_note_detail(session: Session, current_user: User | None, note_id: int):
    note = get_accessible_note(session, current_user, note_id)
    author = session.get(User, note.user_id)

    blocks = session.exec(
        select(NoteBlock)
        .where(NoteBlock.note_id == note_id)
        .order_by(NoteBlock.sort_order)
    ).all()

    block_ids = [block.id for block in blocks]

    relations = []
    media_assets = []

    if block_ids:
        relations = session.exec(
            select(BlockMediaRelation)
            .where(BlockMediaRelation.block_id.in_(block_ids))
            .order_by(BlockMediaRelation.sort_order)
        ).all()

        media_ids = [relation.media_id for relation in relations]
        if media_ids:
            media_assets = session.exec(
                select(MediaAsset).where(MediaAsset.id.in_(media_ids))
            ).all()

    media_map = {media.id: media for media in media_assets}

    relation_map: dict[int, list[MediaAsset]] = {}
    for relation in relations:
        media = media_map.get(relation.media_id)
        if not media:
            continue
        relation_map.setdefault(relation.block_id, []).append(media)

    block_details = []
    for block in blocks:
        block_details.append(
            {
                "id": block.id,
                "note_id": block.note_id,
                "block_type": block.block_type,
                "sort_order": block.sort_order,
                "text_content": block.text_content,
                "text_align": block.text_align,
                "layout_style": block.layout_style,
                "caption": block.caption,
                "created_at": block.created_at,
                "updated_at": block.updated_at,
                "media_assets": [
                    serialize_media_asset(media, current_user)
                    for media in relation_map.get(block.id, [])
                ],
            }
        )

    return {
        "id": note.id,
        "user_id": note.user_id,
        "author_username": author.username if author else None,
        "author_nickname": author.nickname if author else None,
        "author_avatar_url": author.avatar_url if author else None,
        "title": note.title,
        "summary": note.summary,
        "mood": note.mood,
        "scene": note.scene,
        "book_theme": note.book_theme,
        "is_private": note.is_private,
        "status": note.status,
        "cover_media_id": note.cover_media_id,
        "created_at": note.created_at,
        "updated_at": note.updated_at,
        "blocks": block_details,
    }

def update_note_cover(
    session: Session,
    current_user: User,
    note_id: int,
    cover_media_id: int | None,
):
    note = get_note(session, current_user, note_id)

    if cover_media_id is None:
        note.cover_media_id = None
        note.updated_at = datetime.utcnow()
        session.add(note)
        session.commit()
        session.refresh(note)
        return note

    media = session.exec(
        select(MediaAsset).where(
            MediaAsset.id == cover_media_id,
            MediaAsset.user_id == current_user.id,
        )
    ).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media asset not found")

    relation = session.exec(
        select(BlockMediaRelation)
        .join(NoteBlock, BlockMediaRelation.block_id == NoteBlock.id)
        .where(
            NoteBlock.note_id == note_id,
            BlockMediaRelation.media_id == cover_media_id,
        )
    ).first()
    if not relation:
        raise HTTPException(
            status_code=400,
            detail="Cover media must belong to the note",
        )

    note.cover_media_id = cover_media_id
    note.updated_at = datetime.utcnow()
    session.add(note)
    session.commit()
    session.refresh(note)
    return note