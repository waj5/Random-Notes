from fastapi import APIRouter, Depends, File, Request, UploadFile
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
    serve_signed_media,
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


@router.get("/{media_id}/view")
def view_media_asset_api(
    media_id: int,
    exp: int,
    nonce: str,
    wm: str,
    sig: str,
    request: Request,
    session: Session = Depends(get_session),
):
    forwarded_for = request.headers.get("x-forwarded-for", "")
    client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else (request.client.host if request.client else "unknown")
    return serve_signed_media(session, media_id, exp, nonce, wm, sig, client_ip)


@router.get("/{media_id}/download")
def download_media_asset_api(
    media_id: int,
    exp: int,
    nonce: str,
    wm: str,
    sig: str,
    request: Request,
    session: Session = Depends(get_session),
):
    forwarded_for = request.headers.get("x-forwarded-for", "")
    client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else (request.client.host if request.client else "unknown")
    return serve_signed_media(
        session,
        media_id,
        exp,
        nonce,
        wm,
        sig,
        client_ip,
        apply_watermark=True,
        as_attachment=True,
    )


@router.delete("/{media_id}")
def delete_media_asset_api(
    media_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = delete_media_asset(session, current_user, media_id)
    return success_response(result, "Media asset deleted successfully")