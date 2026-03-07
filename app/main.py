from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.routes.notes import router as notes_router
from app.db.database import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(title="Random Notes API",lifespan=lifespan)
app.include_router(notes_router,prefix="/api")
