from sqlmodel import SQLModel, create_engine

from app.core.config import DATABASE_URL, SQL_ECHO
from app.models import User, UserSession, Note, NoteBlock, MediaAsset, BlockMediaRelation

engine = create_engine(DATABASE_URL, echo=SQL_ECHO)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)