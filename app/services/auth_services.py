from datetime import datetime, timedelta
import re
from uuid import uuid4

from fastapi import HTTPException
from sqlmodel import Session, select

from app.core.config import APP_ENV, REQUIRE_SMS_VERIFICATION, SMS_CODE_EXPIRE_MINUTES
from app.core.security import (
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    verify_password,
    decode_token,
)
from app.models.sms_verification_code import SmsVerificationCode
from app.models.note import Note
from app.models.note_block import NoteBlock
from app.models.block_media_relation import BlockMediaRelation
from app.models.user import User, UserStatus
from app.models.user_session import UserSession
from app.models.user_follow import UserFollow
from app.schemas.auth import TokenResponse, UserLogin, UserProfileUpdate, UserRegister

PHONE_PATTERN = re.compile(r"^(?:\+?86)?1\d{10}$")


def normalize_phone(phone: str):
    raw = (phone or "").strip().replace(" ", "")
    if not PHONE_PATTERN.match(raw):
        raise HTTPException(status_code=400, detail="Invalid phone number")
    return raw[-11:]


def _generate_username_from_phone(session: Session, phone: str):
    while True:
        username = f"user_{phone[-4:]}_{uuid4().hex[:6]}"
        existing = session.exec(select(User).where(User.username == username)).first()
        if not existing:
            return username


def _create_user_session(
    session: Session,
    user: User,
    user_agent: str | None = None,
    ip_address: str | None = None,
):
    expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    user_session = UserSession(
        user_id=user.id,
        refresh_token_hash=uuid4().hex,
        user_agent=user_agent,
        ip_address=ip_address,
        expires_at=expires_at,
    )
    session.add(user_session)
    session.commit()
    session.refresh(user_session)

    access_token = create_access_token(user.id, user_session.id)
    refresh_token = create_refresh_token(user.id, user_session.id)

    user_session.refresh_token_hash = hash_token(refresh_token)
    session.add(user_session)
    session.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


def _get_active_user(session: Session, user: User | None):
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.deleted_at is not None or user.status != UserStatus.active:
        raise HTTPException(status_code=403, detail="User is not available")
    return user


def create_sms_code(session: Session, phone: str, purpose: str):
    normalized_phone = normalize_phone(phone)
    existing_user = session.exec(select(User).where(User.phone == normalized_phone)).first()
    if purpose == "register" and existing_user:
        raise HTTPException(status_code=400, detail="Phone number already registered")
    if purpose == "login" and not existing_user:
        raise HTTPException(status_code=404, detail="Phone number not registered")

    session_codes = session.exec(
        select(SmsVerificationCode).where(
            SmsVerificationCode.phone == normalized_phone,
            SmsVerificationCode.purpose == purpose,
            SmsVerificationCode.used_at.is_(None),
        )
    ).all()
    now = datetime.utcnow()
    for item in session_codes:
        item.used_at = now
        session.add(item)

    code = f"{uuid4().int % 1000000:06d}"
    sms_code = SmsVerificationCode(
        phone=normalized_phone,
        purpose=purpose,
        code_hash=hash_token(code),
        expires_at=now + timedelta(minutes=SMS_CODE_EXPIRE_MINUTES),
    )
    session.add(sms_code)
    session.commit()

    print(f"[SMS MOCK] purpose={purpose} phone={normalized_phone} code={code}")

    return {
        "phone": normalized_phone,
        "expires_in_minutes": SMS_CODE_EXPIRE_MINUTES,
        "preview_code": code if APP_ENV != "production" else None,
    }


def verify_sms_code(session: Session, phone: str, purpose: str, code: str):
    normalized_phone = normalize_phone(phone)
    sms_code = session.exec(
        select(SmsVerificationCode)
        .where(
            SmsVerificationCode.phone == normalized_phone,
            SmsVerificationCode.purpose == purpose,
            SmsVerificationCode.used_at.is_(None),
        )
        .order_by(SmsVerificationCode.created_at.desc())
    ).first()
    if not sms_code:
        raise HTTPException(status_code=400, detail="Verification code not found")
    if sms_code.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Verification code expired")
    if sms_code.code_hash != hash_token((code or "").strip()):
        raise HTTPException(status_code=400, detail="Invalid verification code")

    sms_code.used_at = datetime.utcnow()
    session.add(sms_code)
    session.commit()
    return normalized_phone


def register_user(session: Session, data: UserRegister):
    if data.phone:
        phone = normalize_phone(data.phone)
        if not REQUIRE_SMS_VERIFICATION and not (data.password or "").strip():
            raise HTTPException(status_code=400, detail="Password is required")
        if REQUIRE_SMS_VERIFICATION:
            phone = verify_sms_code(session, data.phone, "register", data.sms_code or "")
        existing_phone_user = session.exec(
            select(User).where(User.phone == phone)
        ).first()
        if existing_phone_user:
            raise HTTPException(status_code=400, detail="Phone number already registered")

        username = data.username.strip() if data.username else _generate_username_from_phone(session, phone)
        existing_user = session.exec(
            select(User).where(User.username == username)
        ).first()
        if existing_user:
            username = _generate_username_from_phone(session, phone)
    else:
        if not data.username or not data.password:
            raise HTTPException(status_code=400, detail="Username and password are required")
        username = data.username.strip()
        existing_user = session.exec(
            select(User).where(User.username == username)
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
        phone = None

    if data.email:
        existing_email = session.exec(
            select(User).where(User.email == data.email)
        ).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already exists")

    user = User(
        username=username,
        phone=phone,
        nickname=data.nickname,
        email=data.email,
        password_hash=hash_password(data.password or uuid4().hex),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def login_user(
    session: Session,
    data: UserLogin,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> TokenResponse:
    if REQUIRE_SMS_VERIFICATION and data.sms_code and (data.phone or data.account):
        phone = verify_sms_code(session, data.phone or data.account or "", "login", data.sms_code)
        user = session.exec(select(User).where(User.phone == phone)).first()
        user = _get_active_user(session, user)
        return _create_user_session(session, user, user_agent, ip_address)

    login_account = (data.account or data.phone or "").strip()
    if data.password and login_account:
        account = login_account
        user = session.exec(
            select(User).where(
                (User.username == account) | (User.phone == account)
            )
        ).first()
        if not user or not verify_password(data.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid username, phone or password")
        user = _get_active_user(session, user)
        return _create_user_session(session, user, user_agent, ip_address)

    raise HTTPException(status_code=400, detail="Invalid login payload")


def refresh_user_token(session: Session, refresh_token: str) -> TokenResponse:
    try:
        payload = decode_token(refresh_token)
        user_id = int(payload.get("sub"))
        session_id = int(payload.get("sid"))
        token_type = payload.get("type")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if token_type != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_session = session.get(UserSession, session_id)
    if not user_session:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if user_session.user_id != user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if user_session.revoked_at is not None:
        raise HTTPException(status_code=401, detail="Session has been revoked")

    if user_session.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Refresh token expired")

    if user_session.refresh_token_hash != hash_token(refresh_token):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = session.get(User, user_id)
    if not user or user.deleted_at is not None or user.status != UserStatus.active:
        raise HTTPException(status_code=401, detail="User is not available")

    new_access_token = create_access_token(user.id, user_session.id)
    new_refresh_token = create_refresh_token(user.id, user_session.id)

    user_session.refresh_token_hash = hash_token(new_refresh_token)
    user_session.expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    session.add(user_session)
    session.commit()

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
    )


def update_current_user(session: Session, current_user: User, data: UserProfileUpdate):
    if data.nickname is not None:
        nickname = data.nickname.strip()
        if not nickname:
            raise HTTPException(status_code=400, detail="Nickname cannot be empty")
        current_user.nickname = nickname

    if data.phone is not None:
        phone = normalize_phone(data.phone) if data.phone else None
        if phone and phone != current_user.phone:
            existing_phone_user = session.exec(
                select(User).where(User.phone == phone, User.id != current_user.id)
            ).first()
            if existing_phone_user:
                raise HTTPException(status_code=400, detail="Phone number already registered")
        current_user.phone = phone

    if data.email is not None:
        email = data.email.strip() or None
        if email and email != current_user.email:
            existing_email_user = session.exec(
                select(User).where(User.email == email, User.id != current_user.id)
            ).first()
            if existing_email_user:
                raise HTTPException(status_code=400, detail="Email already exists")
        current_user.email = email

    if data.avatar_url is not None:
        current_user.avatar_url = data.avatar_url.strip() or None

    if data.profile_background_url is not None:
        current_user.profile_background_url = data.profile_background_url.strip() or None

    if data.new_password:
        if not data.current_password:
            raise HTTPException(status_code=400, detail="Current password is required")
        if not verify_password(data.current_password, current_user.password_hash):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        current_user.password_hash = hash_password(data.new_password)

    current_user.updated_at = datetime.utcnow()
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user


def get_user_public_profile(session: Session, user_id: int, current_user: User | None = None):
    user = session.get(User, user_id)
    if not user or user.deleted_at is not None or user.status != UserStatus.active:
        raise HTTPException(status_code=404, detail="User not found")

    published_notes = session.exec(
        select(Note).where(
            Note.user_id == user_id,
            Note.deleted_at.is_(None),
            Note.status == "published",
            Note.is_private.is_(False),
        )
    ).all()
    note_ids = [note.id for note in published_notes]
    blocks = session.exec(
        select(NoteBlock).where(NoteBlock.note_id.in_(note_ids))
    ).all() if note_ids else []
    block_ids = [block.id for block in blocks]
    image_count = len(session.exec(
        select(BlockMediaRelation).where(BlockMediaRelation.block_id.in_(block_ids))
    ).all()) if block_ids else 0
    follower_count = len(session.exec(
        select(UserFollow).where(UserFollow.followee_id == user_id)
    ).all())
    is_following = False
    if current_user and current_user.id != user_id:
        is_following = session.exec(
            select(UserFollow).where(
                UserFollow.follower_id == current_user.id,
                UserFollow.followee_id == user_id,
            )
        ).first() is not None

    return {
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "avatar_url": user.avatar_url,
        "profile_background_url": user.profile_background_url,
        "published_count": len(published_notes),
        "image_count": image_count,
        "follower_count": follower_count,
        "is_following": is_following,
    }


def list_user_sessions(session: Session, current_user: User):
    statement = (
        select(UserSession)
        .where(UserSession.user_id == current_user.id)
        .order_by(UserSession.created_at.desc())
    )
    return session.exec(statement).all()


def logout_user(session: Session, session_id: int):
    user_session = session.get(UserSession, session_id)
    if not user_session or user_session.revoked_at is not None:
        raise HTTPException(status_code=404, detail="Session not found")

    user_session.revoked_at = datetime.utcnow()
    session.add(user_session)
    session.commit()


def logout_all_user_sessions(session: Session, current_user: User, current_session_id: int):
    sessions = session.exec(
        select(UserSession).where(
            UserSession.user_id == current_user.id,
            UserSession.revoked_at.is_(None),
        )
    ).all()

    for user_session in sessions:
        if user_session.id == current_session_id:
            continue
        user_session.revoked_at = datetime.utcnow()
        session.add(user_session)

    session.commit()


def delete_current_user(session: Session, current_user: User):
    current_user.status = UserStatus.deleted
    current_user.deleted_at = datetime.utcnow()
    current_user.updated_at = datetime.utcnow()
    session.add(current_user)

    sessions = session.exec(
        select(UserSession).where(
            UserSession.user_id == current_user.id,
            UserSession.revoked_at.is_(None),
        )
    ).all()

    for user_session in sessions:
        user_session.revoked_at = datetime.utcnow()
        session.add(user_session)

    session.commit()