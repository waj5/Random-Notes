from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.client_ip import get_client_ip
from app.core.config import GLOBAL_API_RATE_LIMIT_MAX_REQUESTS, GLOBAL_API_RATE_LIMIT_WINDOW_SECONDS
from app.core.rate_limit import rate_limiter


def _rate_limit_json_response(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "code": status_code,
            "message": message,
            "data": None,
            "errors": None,
        },
    )


class GlobalRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if GLOBAL_API_RATE_LIMIT_MAX_REQUESTS <= 0:
            return await call_next(request)
        ip = get_client_ip(request)
        try:
            rate_limiter.hit(
                f"global_api:{ip}",
                GLOBAL_API_RATE_LIMIT_MAX_REQUESTS,
                GLOBAL_API_RATE_LIMIT_WINDOW_SECONDS,
                "Too many requests, please try again later",
            )
        except HTTPException as exc:
            msg = exc.detail if isinstance(exc.detail, str) else "Too many requests"
            return _rate_limit_json_response(exc.status_code, msg)
        return await call_next(request)
