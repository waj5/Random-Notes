from sqlalchemy import inspect, text
from sqlmodel import SQLModel, create_engine

from app.core.config import DATABASE_URL, SQL_ECHO
from app.models import User, UserSession, Note, NoteComment, NoteBlock, MediaAsset, BlockMediaRelation, UserFollow, SmsVerificationCode, NoteShare

engine = create_engine(DATABASE_URL, echo=SQL_ECHO)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    inspector = inspect(engine)
    user_columns = {column["name"] for column in inspector.get_columns("users")}
    note_columns = {column["name"] for column in inspector.get_columns("notes")} if inspector.has_table("notes") else set()
    note_share_columns = {column["name"] for column in inspector.get_columns("note_shares")} if inspector.has_table("note_shares") else set()
    note_comment_columns = {column["name"] for column in inspector.get_columns("note_comments")} if inspector.has_table("note_comments") else set()
    with engine.begin() as connection:
        if "phone" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN phone VARCHAR(20)"))
        if "profile_background_url" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN profile_background_url VARCHAR(500)"))
        if "cover_media_id" not in note_share_columns:
            connection.execute(text("ALTER TABLE note_shares ADD COLUMN cover_media_id INTEGER"))
        if "parent_id" not in note_comment_columns:
            connection.execute(text("ALTER TABLE note_comments ADD COLUMN parent_id INTEGER"))
        if "weather_wmo_code" not in note_columns:
            connection.execute(text("ALTER TABLE notes ADD COLUMN weather_wmo_code INTEGER"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_phone_unique ON users (phone)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_note_comments_parent_id ON note_comments (parent_id)"))