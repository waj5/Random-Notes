from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException
from sqlmodel import Session, select

from app.core.security import (
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    verify_password,
    decode_token,
)
from app.models.user import User, UserStatus
from app.models.user_session import UserSession
from app.schemas.auth import TokenResponse, UserLogin, UserRegister


def register_user(session: Session, data: UserRegister):
    existing_user = session.exec(
        select(User).where(User.username == data.username)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    if data.email:
        existing_email = session.exec(
            select(User).where(User.email == data.email)
        ).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already exists")

    user = User(
        username=data.username,
        nickname=data.nickname,
        email=data.email,
        password_hash=hash_password(data.password),
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
    user = session.exec(
        select(User).where(User.username == data.username)
    ).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if user.deleted_at is not None or user.status != UserStatus.active:
        raise HTTPException(status_code=403, detail="User is not available")

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