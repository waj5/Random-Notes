from datetime import datetime, timedelta
import hashlib
import hmac
from io import BytesIO
from urllib.parse import urlencode
from urllib.request import urlopen
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
from sqlmodel import Session, select

from app.core.config import (
    ALLOWED_IMAGE_MIME_TYPES,
    IMAGE_UPLOAD_DIR,
    MEDIA_RATE_LIMIT_MAX_REQUESTS,
    MEDIA_RATE_LIMIT_WINDOW_SECONDS,
    MEDIA_SIGNATURE_SECRET,
    MEDIA_URL_EXPIRE_SECONDS,
    MAX_IMAGE_SIZE,
    PUBLIC_BASE_URL,
    QINIU_ACCESS_KEY,
    QINIU_BUCKET_NAME,
    QINIU_DOMAIN,
    QINIU_SECRET_KEY,
    STORAGE_TYPE,
    WATERMARK_TEXT_PREFIX,
)
from app.core.rate_limit import rate_limiter
from app.models.block_media_relation import BlockMediaRelation
from app.models.media_asset import MediaAsset
from app.models.note import Note
from app.models.user import User
from app.schemas.media_asset import MediaAssetCreate
from qiniu import Auth, put_data


def upload_to_qiniu(filename: str, content: bytes):
    q = Auth(QINIU_ACCESS_KEY, QINIU_SECRET_KEY)
    token = q.upload_token(QINIU_BUCKET_NAME, filename, 3600)
    ret, info = put_data(token, filename, content)
    if info.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to upload to Qiniu")
    
    domain = QINIU_DOMAIN.rstrip("/")
    if not domain.startswith("http"):
        domain = f"http://{domain}"
        
    return f"{domain}/{filename}"


def _build_media_signature(media_id: int, expires_at: int, nonce: str, watermark_text: str):
    payload = f"{media_id}:{expires_at}:{nonce}:{watermark_text}"
    return hmac.new(
        MEDIA_SIGNATURE_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _watermark_identity(current_user: User | None):
    if current_user:
        return f"user-{current_user.id}"
    return "guest"


def build_signed_media_url(media: MediaAsset, current_user: User | None = None):
    expires_at = int((datetime.utcnow() + timedelta(seconds=MEDIA_URL_EXPIRE_SECONDS)).timestamp())
    nonce = uuid4().hex
    watermark_text = f"{WATERMARK_TEXT_PREFIX} {_watermark_identity(current_user)} {expires_at}"
    signature = _build_media_signature(media.id, expires_at, nonce, watermark_text)
    base_path = f"/api/media-assets/{media.id}/view"
    query = urlencode({
        "exp": expires_at,
        "nonce": nonce,
        "wm": watermark_text,
        "sig": signature,
    })
    if PUBLIC_BASE_URL:
        return f"{PUBLIC_BASE_URL}{base_path}?{query}"
    return f"{base_path}?{query}"


def serialize_media_asset(media: MediaAsset, current_user: User | None = None):
    return {
        "id": media.id,
        "user_id": media.user_id,
        "file_key": media.file_key,
        "file_url": build_signed_media_url(media, current_user),
        "file_name": media.file_name,
        "mime_type": media.mime_type,
        "file_size": media.file_size,
        "width": media.width,
        "height": media.height,
        "created_at": media.created_at,
    }


def _load_media_content(media: MediaAsset):
    if STORAGE_TYPE == "qiniu":
        try:
            with urlopen(media.file_url, timeout=10) as response:
                return response.read()
        except Exception as exc:
            raise HTTPException(status_code=502, detail="Failed to fetch remote media") from exc

    file_path = IMAGE_UPLOAD_DIR.parent / media.file_key
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Media file not found")
    return file_path.read_bytes()


def _apply_watermark(content: bytes, mime_type: str, watermark_text: str):
    try:
        image = Image.open(BytesIO(content)).convert("RGBA")
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Failed to read image") from exc

    overlay = Image.new("RGBA", image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    font = ImageFont.load_default()
    text = watermark_text[:96]
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = max(text_bbox[2] - text_bbox[0], 140)
    text_height = max(text_bbox[3] - text_bbox[1], 18)
    step_x = max(text_width + 80, 220)
    step_y = max(text_height + 70, 140)

    for y in range(-40, image.size[1] + step_y, step_y):
        for x in range(-80, image.size[0] + step_x, step_x):
            draw.text((x, y), text, fill=(255, 255, 255, 70), font=font)

    watermarked = Image.alpha_composite(image, overlay)
    output = BytesIO()
    if mime_type == "image/png":
        watermarked.save(output, format="PNG")
    elif mime_type == "image/webp":
        watermarked.save(output, format="WEBP", quality=92)
    else:
        watermarked.convert("RGB").save(output, format="JPEG", quality=92)
    output.seek(0)
    return output


def _get_download_watermark_text(session: Session, media: MediaAsset):
    author = session.get(User, media.user_id)
    if author:
        return author.nickname or author.username or WATERMARK_TEXT_PREFIX
    return WATERMARK_TEXT_PREFIX


def serve_signed_media(
    session: Session,
    media_id: int,
    expires_at: int,
    nonce: str,
    watermark_text: str,
    signature: str,
    client_identity: str,
    apply_watermark: bool = False,
    as_attachment: bool = False,
):
    if expires_at < int(datetime.utcnow().timestamp()):
        raise HTTPException(status_code=403, detail="Media URL expired")

    expected_signature = _build_media_signature(media_id, expires_at, nonce, watermark_text)
    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(status_code=403, detail="Invalid media signature")

    rate_limiter.hit(
        f"media:{client_identity}",
        MEDIA_RATE_LIMIT_MAX_REQUESTS,
        MEDIA_RATE_LIMIT_WINDOW_SECONDS,
        "Too many media requests, please try again later",
    )

    media = session.get(MediaAsset, media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media asset not found")

    content = _load_media_content(media)
    if apply_watermark:
        output = _apply_watermark(content, media.mime_type, _get_download_watermark_text(session, media))
    else:
        output = BytesIO(content)
    output.seek(0)
    download_name = media.file_name or "image"
    headers = {
        "Cache-Control": "private, no-store, max-age=0",
        "Content-Disposition": f'{"attachment" if as_attachment else "inline"}; filename="{download_name}"',
        "X-Robots-Tag": "noindex, noimageindex",
    }
    return StreamingResponse(output, media_type=media.mime_type, headers=headers)


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
    return serialize_media_asset(media, current_user)


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
    
    if STORAGE_TYPE == "qiniu":
        if not all([QINIU_ACCESS_KEY, QINIU_SECRET_KEY, QINIU_BUCKET_NAME, QINIU_DOMAIN]):
             raise HTTPException(status_code=500, detail="Qiniu configuration missing")
        file_url = upload_to_qiniu(filename, content)
        file_key = filename
    else:
        file_key = f"images/{current_user.id}/{filename}"
        IMAGE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        save_path = IMAGE_UPLOAD_DIR.parent / file_key
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_bytes(content)
        file_url = file_key

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
    return serialize_media_asset(media, current_user)


def list_media_assets(session: Session, current_user: User):
    statement = (
        select(MediaAsset)
        .where(MediaAsset.user_id == current_user.id)
        .order_by(MediaAsset.id.desc())
    )
    media_assets = session.exec(statement).all()
    return [serialize_media_asset(media, current_user) for media in media_assets]


def get_media_asset(session: Session, current_user: User, media_id: int):
    statement = select(MediaAsset).where(
        MediaAsset.id == media_id,
        MediaAsset.user_id == current_user.id,
    )
    media = session.exec(statement).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media asset not found")
    return serialize_media_asset(media, current_user)


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

    file_path = IMAGE_UPLOAD_DIR.parent / media.file_key
    if STORAGE_TYPE != "qiniu" and file_path.exists() and file_path.is_file():
        file_path.unlink()

    session.delete(media)
    session.commit()

    return {"message": "Media asset deleted successfully"}