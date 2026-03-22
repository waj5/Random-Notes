from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlmodel import Session

from app.api.deps import get_current_session_id, get_current_user, get_session
from app.core.config import (
    ACCESS_COOKIE_NAME,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    COOKIE_SAMESITE,
    COOKIE_SECURE,
    LOGIN_BLOCK_SECONDS,
    LOGIN_RATE_LIMIT_MAX_ATTEMPTS,
    LOGIN_RATE_LIMIT_WINDOW_SECONDS,
    LOGIN_USER_RATE_LIMIT_MAX_ATTEMPTS,
    REFRESH_COOKIE_NAME,
    REFRESH_TOKEN_EXPIRE_DAYS,
    SMS_SEND_COOLDOWN_SECONDS,
    SMS_SEND_IP_LIMIT,
    SMS_SEND_PHONE_LIMIT,
    SMS_SEND_WINDOW_SECONDS,
)
from app.core.rate_limit import rate_limiter
from app.models.user import User
from app.core.response import success_response
from app.schemas.auth import (
    MessageResponse,
    RefreshTokenRequest,
    SessionPublic,
    SmsCodeSendRequest,
    TokenResponse,
    UserDeleteResponse,
    UserLogin,
    UserRegister,
)
from app.services.auth_services import (
    delete_current_user,
    create_sms_code,
    list_user_sessions,
    login_user,
    normalize_phone,
    logout_all_user_sessions,
    logout_user,
    refresh_user_token,
    register_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])
LOGIN_MODE_COOKIE_NAME = "remember_login"


def _set_auth_cookies(response: Response, token_payload: TokenResponse, persistent_login: bool):
    response.set_cookie(
        key=ACCESS_COOKIE_NAME,
        value=token_payload.access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60 if persistent_login else None,
        path="/",
    )
    if token_payload.refresh_token:
        refresh_cookie_kwargs = {
            "key": REFRESH_COOKIE_NAME,
            "value": token_payload.refresh_token,
            "httponly": True,
            "secure": COOKIE_SECURE,
            "samesite": COOKIE_SAMESITE,
            "path": "/api/auth",
        }
        if persistent_login:
            refresh_cookie_kwargs["max_age"] = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        response.set_cookie(**refresh_cookie_kwargs)
    response.set_cookie(
        key=LOGIN_MODE_COOKIE_NAME,
        value="1" if persistent_login else "0",
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60 if persistent_login else None,
        path="/api/auth",
    )


def _clear_auth_cookies(response: Response):
    response.delete_cookie(key=ACCESS_COOKIE_NAME, path="/")
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path="/api/auth")
    response.delete_cookie(key=LOGIN_MODE_COOKIE_NAME, path="/api/auth")


def _client_ip(request: Request):
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/register")
def register_api(
    data: UserRegister,
    session: Session = Depends(get_session),
):
    user = register_user(session, data)
    return success_response(user, "User registered successfully")


@router.post("/sms-code")
def send_sms_code_api(
    request: Request,
    data: SmsCodeSendRequest,
    session: Session = Depends(get_session),
):
    ip_address = _client_ip(request)
    phone = normalize_phone(data.phone)
    rate_limiter.hit(
        f"sms:ip:{ip_address}",
        SMS_SEND_IP_LIMIT,
        SMS_SEND_WINDOW_SECONDS,
        "SMS requests are too frequent, please try again later",
    )
    rate_limiter.hit(
        f"sms:phone:{phone}",
        SMS_SEND_PHONE_LIMIT,
        SMS_SEND_WINDOW_SECONDS,
        "This phone has requested too many codes, please try again later",
    )
    rate_limiter.ensure_allowed(
        f"sms:cooldown:{phone}",
        1,
        SMS_SEND_COOLDOWN_SECONDS,
        "Please wait before requesting another verification code",
    )
    rate_limiter.hit(
        f"sms:cooldown:{phone}",
        1,
        SMS_SEND_COOLDOWN_SECONDS,
        "Please wait before requesting another verification code",
    )
    result = create_sms_code(session, phone, data.purpose)
    return success_response(result, "Verification code sent")


@router.post("/login")
def login_api(
    request: Request,
    response: Response,
    data: UserLogin,
    session: Session = Depends(get_session),
):
    user_agent = request.headers.get("user-agent")
    ip_address = _client_ip(request)
    ip_key = f"login:ip:{ip_address}"
    login_identity = (data.account or data.phone or "").strip().lower()
    user_key = f"login:user:{login_identity}"

    rate_limiter.ensure_allowed(
        ip_key,
        LOGIN_RATE_LIMIT_MAX_ATTEMPTS,
        LOGIN_RATE_LIMIT_WINDOW_SECONDS,
        "Too many login attempts, please try again later",
    )
    rate_limiter.ensure_allowed(
        user_key,
        LOGIN_USER_RATE_LIMIT_MAX_ATTEMPTS,
        LOGIN_RATE_LIMIT_WINDOW_SECONDS,
        "Account temporarily locked due to too many failed logins",
    )

    try:
        user_token = login_user(session, data, user_agent=user_agent, ip_address=ip_address)
    except HTTPException as exc:
        if exc.status_code == 401:
            rate_limiter.register_failure(
                ip_key,
                LOGIN_BLOCK_SECONDS,
                LOGIN_RATE_LIMIT_MAX_ATTEMPTS,
                LOGIN_RATE_LIMIT_WINDOW_SECONDS,
            )
            rate_limiter.register_failure(
                user_key,
                LOGIN_BLOCK_SECONDS,
                LOGIN_USER_RATE_LIMIT_MAX_ATTEMPTS,
                LOGIN_RATE_LIMIT_WINDOW_SECONDS,
            )
        raise

    rate_limiter.clear(ip_key)
    rate_limiter.clear(user_key)
    _set_auth_cookies(response, user_token, data.auto_login)
    return success_response(user_token, "User logged in successfully")


@router.post("/refresh", response_model=TokenResponse)
def refresh_api(
    request: Request,
    response: Response,
    data: RefreshTokenRequest,
    session: Session = Depends(get_session),
):
    refresh_token = data.refresh_token or request.cookies.get(REFRESH_COOKIE_NAME)
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    token_payload = refresh_user_token(session, refresh_token)
    persistent_login = request.cookies.get(LOGIN_MODE_COOKIE_NAME) == "1"
    _set_auth_cookies(response, token_payload, persistent_login)
    return token_payload


@router.get("/me")
def me_api(
    current_user: User = Depends(get_current_user),
):
    user = current_user
    return success_response(user)


@router.get("/sessions", response_model=list[SessionPublic])
def list_sessions_api(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return list_user_sessions(session, current_user)


@router.post("/logout", response_model=MessageResponse)
def logout_api(
    response: Response,
    session: Session = Depends(get_session),
    session_id: int = Depends(get_current_session_id),
):
    logout_user(session, session_id)
    _clear_auth_cookies(response)
    return {"message": "Logged out successfully"}


@router.post("/logout-all", response_model=MessageResponse)
def logout_all_api(
    response: Response,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    current_session_id: int = Depends(get_current_session_id),
):
    logout_all_user_sessions(session, current_user, current_session_id)
    _clear_auth_cookies(response)
    return {"message": "Logged out all other sessions successfully"}


@router.delete("/me", response_model=UserDeleteResponse)
def delete_me_api(
    response: Response,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    delete_current_user(session, current_user)
    _clear_auth_cookies(response)
    return {"message": "User deleted successfully"}