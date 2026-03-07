from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.deps import get_current_user, get_session
from app.models.user import User
from app.schemas.media_asset import MediaAssetCreate, MediaAssetPublic
from app.services.media_asset_services import (
    create_media_asset,
    get_media_asset,
    list_media_assets,
)

router = APIRouter(prefix="/media-assets", tags=["media-assets"])


@router.post("/", response_model=MediaAssetPublic)
def create_media_asset_api(
    data: MediaAssetCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return create_media_asset(session, current_user, data)


@router.get("/", response_model=list[MediaAssetPublic])
def list_media_assets_api(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return list_media_assets(session, current_user)


@router.get("/{media_id}", response_model=MediaAssetPublic)
def get_media_asset_api(
    media_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return get_media_asset(session, current_user, media_id)