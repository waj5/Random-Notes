import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BASE_DIR.parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))
SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() == "true"
APP_ENV = os.getenv("APP_ENV", "development").lower()
ENFORCE_HTTPS = os.getenv("ENFORCE_HTTPS", "false").lower() == "true"
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true" if ENFORCE_HTTPS else "false").lower() == "true"
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax").lower()
REFRESH_COOKIE_NAME = os.getenv("REFRESH_COOKIE_NAME", "refresh_token")
ACCESS_COOKIE_NAME = os.getenv("ACCESS_COOKIE_NAME", "access_token")
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origin.strip()
]

# 子路径部署时设为与前端一致，如 /notes（勿带尾部斜杠）；根路径部署留空
_cookie_prefix = os.getenv("COOKIE_PATH_PREFIX", "").strip().rstrip("/")
ACCESS_COOKIE_PATH = _cookie_prefix if _cookie_prefix else "/"
REFRESH_COOKIE_PATH = f"{_cookie_prefix}/api/auth" if _cookie_prefix else "/api/auth"

PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(PROJECT_DIR / "uploads")))
IMAGE_UPLOAD_DIR = UPLOAD_DIR / "images"
IMAGE_UPLOAD_URL_PREFIX = os.getenv("IMAGE_UPLOAD_URL_PREFIX", "/uploads/images").rstrip("/")
MAX_IMAGE_SIZE = int(os.getenv("MAX_IMAGE_SIZE", str(5 * 1024 * 1024)))
MEDIA_URL_EXPIRE_SECONDS = int(os.getenv("MEDIA_URL_EXPIRE_SECONDS", "1800"))
MEDIA_SIGNATURE_SECRET = os.getenv("MEDIA_SIGNATURE_SECRET", SECRET_KEY or "dev-media-secret")
WATERMARK_TEXT_PREFIX = os.getenv("WATERMARK_TEXT_PREFIX", "Random Notes")
LOGIN_RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("LOGIN_RATE_LIMIT_WINDOW_SECONDS", "300"))
LOGIN_RATE_LIMIT_MAX_ATTEMPTS = int(os.getenv("LOGIN_RATE_LIMIT_MAX_ATTEMPTS", "8"))
LOGIN_USER_RATE_LIMIT_MAX_ATTEMPTS = int(os.getenv("LOGIN_USER_RATE_LIMIT_MAX_ATTEMPTS", "5"))
LOGIN_BLOCK_SECONDS = int(os.getenv("LOGIN_BLOCK_SECONDS", "900"))
MEDIA_RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("MEDIA_RATE_LIMIT_WINDOW_SECONDS", "60"))
MEDIA_RATE_LIMIT_MAX_REQUESTS = int(os.getenv("MEDIA_RATE_LIMIT_MAX_REQUESTS", "120"))
MEDIA_NONCE_TTL_SECONDS = int(os.getenv("MEDIA_NONCE_TTL_SECONDS", "3600"))
SMS_CODE_EXPIRE_MINUTES = int(os.getenv("SMS_CODE_EXPIRE_MINUTES", "5"))
SMS_SEND_WINDOW_SECONDS = int(os.getenv("SMS_SEND_WINDOW_SECONDS", "600"))
SMS_SEND_IP_LIMIT = int(os.getenv("SMS_SEND_IP_LIMIT", "10"))
SMS_SEND_PHONE_LIMIT = int(os.getenv("SMS_SEND_PHONE_LIMIT", "5"))
SMS_SEND_COOLDOWN_SECONDS = int(os.getenv("SMS_SEND_COOLDOWN_SECONDS", "60"))

# Storage Configuration
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "local")  # "local" or "qiniu"

# Qiniu Configuration
QINIU_ACCESS_KEY = os.getenv("QINIU_ACCESS_KEY")
QINIU_SECRET_KEY = os.getenv("QINIU_SECRET_KEY")
QINIU_BUCKET_NAME = os.getenv("QINIU_BUCKET_NAME")
QINIU_DOMAIN = os.getenv("QINIU_DOMAIN")

ALLOWED_IMAGE_MIME_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}