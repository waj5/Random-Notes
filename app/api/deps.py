from datetime import datetime

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from app.core.config import ACCESS_COOKIE_NAME
from app.core.security import decode_token
from app.db.database import engine
from app.models.user import User, UserStatus
from app.models.user_session import UserSession

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_session():
    with Session(engine) as session:
        yield session


def get_bearer_or_cookie_token(
    request: Request,
    token: str | None = Depends(oauth2_scheme_optional),
):
    if token:
        return token
    return request.cookies.get(ACCESS_COOKIE_NAME)


def get_current_session(
    token: str | None = Depends(get_bearer_or_cookie_token),
    session: Session = Depends(get_session),
):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
    )

    if not token:
        raise credentials_exception

    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        session_id = payload.get("sid")
        token_type = payload.get("type")
        if user_id is None or session_id is None or token_type != "access":
            raise credentials_exception
        user_id = int(user_id)
        session_id = int(session_id)
    except Exception:
        raise credentials_exception

    user_session = session.get(UserSession, session_id)
    if not user_session:
        raise credentials_exception

    if user_session.user_id != user_id:
        raise credentials_exception

    if user_session.revoked_at is not None:
        raise credentials_exception

    if user_session.expires_at < datetime.utcnow():
        raise credentials_exception

    return user_session


def get_current_session_id(
    current_session: UserSession = Depends(get_current_session),
):
    return current_session.id


def get_current_user(
    current_session: UserSession = Depends(get_current_session),
    session: Session = Depends(get_session),
):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
    )

    user = session.get(User, current_session.user_id)
    if not user or user.deleted_at is not None or user.status != UserStatus.active:
        raise credentials_exception

    return user


def get_current_user_optional(
    token: str | None = Depends(get_bearer_or_cookie_token),
    session: Session = Depends(get_session),
):
    if not token:
        return None

    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        session_id = payload.get("sid")
        token_type = payload.get("type")
        if user_id is None or session_id is None or token_type != "access":
            return None
        user_id = int(user_id)
        session_id = int(session_id)
    except Exception:
        return None

    user_session = session.get(UserSession, session_id)
    if not user_session:
        return None
    if user_session.user_id != user_id:
        return None
    if user_session.revoked_at is not None:
        return None
    if user_session.expires_at < datetime.utcnow():
        return None

    user = session.get(User, user_id)
    if not user or user.deleted_at is not None or user.status != UserStatus.active:
        return None

    return user