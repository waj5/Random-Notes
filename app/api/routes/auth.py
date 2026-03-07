from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from app.api.deps import get_current_session_id, get_current_user, get_session
from app.models.user import User
from app.schemas.auth import (
    MessageResponse,
    RefreshTokenRequest,
    SessionPublic,
    TokenResponse,
    UserDeleteResponse,
    UserLogin,
    UserPublic,
    UserRegister,
)
from app.services.auth_services import (
    delete_current_user,
    list_user_sessions,
    login_user,
    logout_all_user_sessions,
    logout_user,
    refresh_user_token,
    register_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic)
def register_api(
    data: UserRegister,
    session: Session = Depends(get_session),
):
    return register_user(session, data)


@router.post("/login", response_model=TokenResponse)
def login_api(
    request: Request,
    data: UserLogin,
    session: Session = Depends(get_session),
):
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
    return login_user(session, data, user_agent=user_agent, ip_address=ip_address)


@router.post("/refresh", response_model=TokenResponse)
def refresh_api(
    data: RefreshTokenRequest,
    session: Session = Depends(get_session),
):
    return refresh_user_token(session, data.refresh_token)


@router.get("/me", response_model=UserPublic)
def me_api(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.get("/sessions", response_model=list[SessionPublic])
def list_sessions_api(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return list_user_sessions(session, current_user)


@router.post("/logout", response_model=MessageResponse)
def logout_api(
    session: Session = Depends(get_session),
    session_id: int = Depends(get_current_session_id),
):
    logout_user(session, session_id)
    return {"message": "Logged out successfully"}


@router.post("/logout-all", response_model=MessageResponse)
def logout_all_api(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    current_session_id: int = Depends(get_current_session_id),
):
    logout_all_user_sessions(session, current_user, current_session_id)
    return {"message": "Logged out all other sessions successfully"}


@router.delete("/me", response_model=UserDeleteResponse)
def delete_me_api(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    delete_current_user(session, current_user)
    return {"message": "User deleted successfully"}