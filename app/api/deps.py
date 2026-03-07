from datetime import datetime

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from app.core.security import decode_token
from app.db.database import engine
from app.models.user import User, UserStatus
from app.models.user_session import UserSession

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_session():
    with Session(engine) as session:
        yield session


def get_current_session(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
    )

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