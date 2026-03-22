from datetime import datetime, timedelta
import re
from uuid import uuid4

from fastapi import HTTPException
from sqlmodel import Session, select

from app.core.config import APP_ENV, SMS_CODE_EXPIRE_MINUTES
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
from app.models.user import User, UserStatus
from app.models.user_session import UserSession
from app.schemas.auth import TokenResponse, UserLogin, UserRegister

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
    if data.sms_code and (data.phone or data.account):
        phone = verify_sms_code(session, data.phone or data.account or "", "login", data.sms_code)
        user = session.exec(select(User).where(User.phone == phone)).first()
        user = _get_active_user(session, user)
        return _create_user_session(session, user, user_agent, ip_address)

    if data.password and data.account:
        account = data.account.strip()
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