from fastapi import HTTPException
from sqlmodel import Session, select

from app.models.media_asset import MediaAsset
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