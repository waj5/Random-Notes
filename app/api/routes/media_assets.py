from fastapi import APIRouter, Depends, File, UploadFile
from sqlmodel import Session

from app.api.deps import get_current_user, get_session
from app.core.response import success_response
from app.models.user import User
from app.schemas.media_asset import MediaAssetCreate
from app.services.media_asset_services import (
    create_media_asset,
    delete_media_asset,
    get_media_asset,
    list_media_assets,
    upload_image_and_create_media_asset,
)

router = APIRouter(prefix="/media-assets", tags=["media-assets"])


@router.post("/")
def create_media_asset_api(
    data: MediaAssetCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    media = create_media_asset(session, current_user, data)
    return success_response(media, "Media asset created successfully")


@router.post("/upload/image")
def upload_image_api(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    media = upload_image_and_create_media_asset(session, current_user, file)
    return success_response(media, "Image uploaded successfully")


@router.get("/")
def list_media_assets_api(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    media_assets = list_media_assets(session, current_user)
    return success_response(media_assets)


@router.get("/{media_id}")
def get_media_asset_api(
    media_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    media = get_media_asset(session, current_user, media_id)
    return success_response(media)


@router.delete("/{media_id}")
def delete_media_asset_api(
    media_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = delete_media_asset(session, current_user, media_id)
    return success_response(result, "Media asset deleted successfully")