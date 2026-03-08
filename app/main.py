from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes.auth import router as auth_router
from app.api.routes.block_media_relations import router as block_media_relations_router
from app.api.routes.media_assets import router as media_assets_router
from app.api.routes.note_blocks import router as note_blocks_router
from app.api.routes.notes import router as notes_router
from app.core.config import IMAGE_UPLOAD_DIR, UPLOAD_DIR
from app.core.exception_handlers import register_exception_handlers

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
IMAGE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Random Notes API", lifespan=lifespan)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

register_exception_handlers(app)

app.include_router(auth_router, prefix="/api")
app.include_router(notes_router, prefix="/api")
app.include_router(note_blocks_router, prefix="/api")
app.include_router(media_assets_router, prefix="/api")
app.include_router(block_media_relations_router, prefix="/api")