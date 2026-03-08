from io import BytesIO
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from sqlmodel import Session, select

from app.core.config import (
    ALLOWED_IMAGE_MIME_TYPES,
    IMAGE_UPLOAD_DIR,
    IMAGE_UPLOAD_URL_PREFIX,
    MAX_IMAGE_SIZE,
)
from app.models.block_media_relation import BlockMediaRelation
from app.models.media_asset import MediaAsset
from app.models.note import Note
from app.models.user import User
from app.schemas.media_asset import MediaAssetCreate


def create_media_asset(session: Session, current_user: User, data: MediaAssetCreate):
    media = MediaAsset(
        user_id=current_user.id,
        file_key=data.file_key,
        file_url=data.file_url,
        file_name=data.file_name,
        mime_type=data.mime_type,
        file_size=data.file_size,
        width=data.width,
        height=data.height,
    )
    session.add(media)
    session.commit()
    session.refresh(media)
    return media


def upload_image_and_create_media_asset(
    session: Session,
    current_user: User,
    file: UploadFile,
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File name is required")

    if file.content_type not in ALLOWED_IMAGE_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported image type")

    content = file.file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file is not allowed")

    file_size = len(content)
    if file_size > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="Image size exceeds limit")

    try:
        image = Image.open(BytesIO(content))
        image.verify()
        image = Image.open(BytesIO(content))
        width, height = image.size
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Invalid image file")
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to process image")

    extension = ALLOWED_IMAGE_MIME_TYPES[file.content_type]
    filename = f"{current_user.id}_{uuid4().hex}{extension}"
    file_key = f"images/{current_user.id}/{filename}"

    IMAGE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    save_path = IMAGE_UPLOAD_DIR / filename
    save_path.write_bytes(content)

    file_url = f"{IMAGE_UPLOAD_URL_PREFIX}/{filename}"

    media = MediaAsset(
        user_id=current_user.id,
        file_key=file_key,
        file_url=file_url,
        file_name=file.filename,
        mime_type=file.content_type,
        file_size=file_size,
        width=width,
        height=height,
    )
    session.add(media)
    session.commit()
    session.refresh(media)
    return media


def list_media_assets(session: Session, current_user: User):
    statement = (
        select(MediaAsset)
        .where(MediaAsset.user_id == current_user.id)
        .order_by(MediaAsset.id.desc())
    )
    return session.exec(statement).all()


def get_media_asset(session: Session, current_user: User, media_id: int):
    statement = select(MediaAsset).where(
        MediaAsset.id == media_id,
        MediaAsset.user_id == current_user.id,
    )
    media = session.exec(statement).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media asset not found")
    return media


def delete_media_asset(session: Session, current_user: User, media_id: int):
    media = session.exec(
        select(MediaAsset).where(
            MediaAsset.id == media_id,
            MediaAsset.user_id == current_user.id,
        )
    ).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media asset not found")

    relations = session.exec(
        select(BlockMediaRelation).where(BlockMediaRelation.media_id == media_id)
    ).all()
    for relation in relations:
        session.delete(relation)

    notes = session.exec(
        select(Note).where(
            Note.user_id == current_user.id,
            Note.cover_media_id == media_id,
            Note.deleted_at.is_(None),
        )
    ).all()
    for note in notes:
        note.cover_media_id = None
        session.add(note)

    file_path = IMAGE_UPLOAD_DIR / media.file_url.split("/")[-1]
    if file_path.exists() and file_path.is_file():
        file_path.unlink()

    session.delete(media)
    session.commit()

    return {"message": "Media asset deleted successfully"}