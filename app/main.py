from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.block_media_relations import router as block_media_relations_router
from app.api.routes.media_assets import router as media_assets_router
from app.api.routes.note_blocks import router as note_blocks_router
from app.api.routes.notes import router as notes_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Random Notes API", lifespan=lifespan)
app.include_router(auth_router, prefix="/api")
app.include_router(notes_router, prefix="/api")
app.include_router(note_blocks_router, prefix="/api")
app.include_router(media_assets_router, prefix="/api")
app.include_router(block_media_relations_router, prefix="/api")