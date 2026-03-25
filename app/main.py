from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.block_media_relations import router as block_media_relations_router
from app.api.routes.follows import router as follows_router
from app.api.routes.media_assets import router as media_assets_router
from app.api.routes.note_blocks import router as note_blocks_router
from app.api.routes.note_comments import router as note_comments_router
from app.api.routes.notes import router as notes_router
from app.api.routes.note_shares import router as note_shares_router
from app.core.config import CORS_ALLOWED_ORIGINS, ENFORCE_HTTPS, IMAGE_UPLOAD_DIR, UPLOAD_DIR
from app.core.exception_handlers import register_exception_handlers
from app.core.http_security import SecurityHeadersMiddleware
from app.db.database import create_db_and_tables

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
IMAGE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="Random Notes API", lifespan=lifespan)

if ENFORCE_HTTPS:
    app.add_middleware(HTTPSRedirectMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SecurityHeadersMiddleware)

register_exception_handlers(app)

app.include_router(auth_router, prefix="/api")
app.include_router(notes_router, prefix="/api")
app.include_router(note_shares_router, prefix="/api")
app.include_router(note_comments_router, prefix="/api")
app.include_router(follows_router, prefix="/api")
app.include_router(note_blocks_router, prefix="/api")
app.include_router(media_assets_router, prefix="/api")
app.include_router(block_media_relations_router, prefix="/api")