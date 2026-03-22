from sqlalchemy import inspect, text
from sqlmodel import SQLModel, create_engine

from app.core.config import DATABASE_URL, SQL_ECHO
from app.models import User, UserSession, Note, NoteComment, NoteBlock, MediaAsset, BlockMediaRelation, UserFollow, SmsVerificationCode

engine = create_engine(DATABASE_URL, echo=SQL_ECHO)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    inspector = inspect(engine)
    user_columns = {column["name"] for column in inspector.get_columns("users")}
    with engine.begin() as connection:
        if "phone" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN phone VARCHAR(20)"))
        if "profile_background_url" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN profile_background_url VARCHAR(500)"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_phone_unique ON users (phone)"))