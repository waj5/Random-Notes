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

PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(PROJECT_DIR / "uploads")))
IMAGE_UPLOAD_DIR = UPLOAD_DIR / "images"
IMAGE_UPLOAD_URL_PREFIX = os.getenv("IMAGE_UPLOAD_URL_PREFIX", "/uploads/images").rstrip("/")
MAX_IMAGE_SIZE = int(os.getenv("MAX_IMAGE_SIZE", str(5 * 1024 * 1024)))

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