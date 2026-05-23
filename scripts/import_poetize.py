#!/usr/bin/env python3
"""
从 Poetize MySQL 导入文章到 Random-Notes PostgreSQL。

前置：先把 poetize.sql 导入临时 MySQL，例如：
  docker run -d --name poetize-mysql -e MYSQL_ROOT_PASSWORD=tmp123 -e MYSQL_DATABASE=poetize mysql:5.7
  docker exec -i poetize-mysql mysql -uroot -ptmp123 poetize < /path/to/poetize.sql

用法（在仓库根目录）：
  pip install pymysql
  set DATABASE_URL=postgresql+psycopg://notes:密码@127.0.0.1:5432/notes
  set POETIZE_MYSQL_URL=mysql+pymysql://root:tmp123@127.0.0.1:3306/poetize
  set UPLOAD_DIR=E:/workspace/Random-Notes/uploads
  python scripts/import_poetize.py --default-password "你的新密码"

服务器上（api 容器 + 临时 MySQL 同网段）：
  docker compose -f deploy/docker-compose.yml exec api python scripts/import_poetize.py ...
"""
from __future__ import annotations

import argparse
import mimetypes
import re
import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlmodel import Session, select

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.config import IMAGE_UPLOAD_DIR, UPLOAD_DIR  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.block_media_relation import BlockMediaRelation  # noqa: E402
from app.models.media_asset import MediaAsset  # noqa: E402
from app.models.note import Note, NoteStatus  # noqa: E402
from app.models.note_block import BlockType, LayoutStyle, NoteBlock, TextAlign  # noqa: E402
from app.models.user import User, UserStatus  # noqa: E402

MD_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
ALLOWED_EXT = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
DEFAULT_URL_REWRITES: list[tuple[str, str]] = [
    ("http://get.fs-hck.top/articlePicture/", "http://cdn.fs-hck.top/articlePicture/"),
    ("https://get.fs-hck.top/articlePicture/", "https://cdn.fs-hck.top/articlePicture/"),
]


def build_url_rewrites(extra: list[str] | None) -> list[tuple[str, str]]:
    rewrites = list(DEFAULT_URL_REWRITES)
    for item in extra or []:
        if "=>" not in item:
            raise ValueError(f"无效 URL 替换规则: {item}，格式为 old=>new")
        old, new = item.split("=>", 1)
        rewrites.append((old.strip(), new.strip()))
    return rewrites


def rewrite_url(url: str | None, rewrites: list[tuple[str, str]]) -> str | None:
    if not url:
        return url
    result = url
    for old, new in rewrites:
        result = result.replace(old, new)
    return result


def rewrite_text(text: str | None, rewrites: list[tuple[str, str]]) -> str:
    if not text:
        return ""
    result = text
    for old, new in rewrites:
        result = result.replace(old, new)
    return result


def fetch_rows(mysql_url: str, sql: str) -> list[dict]:
    engine = create_engine(mysql_url)
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        return [dict(row._mapping) for row in result]


def guess_mime(url: str, content: bytes) -> tuple[str, str]:
    path = urlparse(url).path.lower()
    for ext, mime in ALLOWED_EXT.items():
        if path.endswith(ext):
            return mime, ext
    if content[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png", ".png"
    if content[:2] == b"\xff\xd8":
        return "image/jpeg", ".jpg"
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "image/webp", ".webp"
    return "image/jpeg", ".jpg"


def download_image(url: str) -> tuple[bytes, str, str] | None:
    try:
        req = Request(url, headers={"User-Agent": "Random-Notes-Import/1.0"})
        with urlopen(req, timeout=30) as resp:
            content = resp.read()
        if not content or len(content) > 5 * 1024 * 1024:
            return None
        mime, ext = guess_mime(url, content)
        return content, mime, ext
    except Exception as exc:
        print(f"  [跳过图片] {url} ({exc})")
        return None


def save_media(
    session: Session,
    user_id: int,
    url: str,
    cache: dict[str, int],
    rewrites: list[tuple[str, str]],
) -> int | None:
    url = rewrite_url(url, rewrites) or url
    if url in cache:
        return cache[url]
    downloaded = download_image(url)
    if not downloaded:
        return None
    content, mime, ext = downloaded
    filename = f"{user_id}_{uuid4().hex}{ext}"
    file_key = f"images/{user_id}/{filename}"
    save_path = IMAGE_UPLOAD_DIR.parent / file_key
    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_bytes(content)

    try:
        from PIL import Image

        image = Image.open(BytesIO(content))
        width, height = image.size
    except Exception:
        width = height = None

    media = MediaAsset(
        user_id=user_id,
        file_key=file_key,
        file_url=file_key,
        file_name=Path(urlparse(url).path).name or filename,
        mime_type=mime,
        file_size=len(content),
        width=width,
        height=height,
    )
    session.add(media)
    session.flush()
    cache[url] = media.id
    return media.id


def split_content(content: str) -> list[tuple[str, str]]:
    parts: list[tuple[str, str]] = []
    last = 0
    for match in MD_IMAGE.finditer(content):
        if match.start() > last:
            text_part = content[last : match.start()].strip()
            if text_part:
                parts.append(("text", text_part))
        parts.append(("image", match.group(2).strip()))
        last = match.end()
    if last < len(content):
        tail = content[last:].strip()
        if tail:
            parts.append(("text", tail))
    return parts or [("text", content)]


def create_blocks(
    session: Session,
    note_id: int,
    user_id: int,
    content: str,
    cover_url: str | None,
    media_cache: dict[str, int],
    rewrites: list[tuple[str, str]],
) -> int | None:
    parts = split_content(content)
    sort_order = 0
    cover_media_id = None

    if cover_url:
        cover_media_id = save_media(session, user_id, cover_url, media_cache, rewrites)

    image_run: list[str] = []

    def flush_images():
        nonlocal sort_order, cover_media_id
        if not image_run:
            return
        if len(image_run) == 1:
            media_id = save_media(session, user_id, image_run[0], media_cache, rewrites)
            if media_id:
                block = NoteBlock(
                    note_id=note_id,
                    block_type=BlockType.image,
                    sort_order=sort_order,
                    layout_style=LayoutStyle.image_top,
                    text_align=TextAlign.left,
                )
                session.add(block)
                session.flush()
                session.add(
                    BlockMediaRelation(block_id=block.id, media_id=media_id, sort_order=0)
                )
                sort_order += 1
        else:
            block = NoteBlock(
                note_id=note_id,
                block_type=BlockType.gallery,
                sort_order=sort_order,
                layout_style=LayoutStyle.photo_wall,
                text_align=TextAlign.left,
            )
            session.add(block)
            session.flush()
            for idx, img_url in enumerate(image_run):
                media_id = save_media(session, user_id, img_url, media_cache, rewrites)
                if media_id:
                    session.add(
                        BlockMediaRelation(block_id=block.id, media_id=media_id, sort_order=idx)
                    )
            sort_order += 1
        image_run.clear()

    for kind, value in parts:
        if kind == "image":
            image_run.append(value)
            continue
        flush_images()
        block = NoteBlock(
            note_id=note_id,
            block_type=BlockType.text,
            sort_order=sort_order,
            text_content=value,
            text_align=TextAlign.left,
            layout_style=LayoutStyle.normal,
        )
        session.add(block)
        sort_order += 1

    flush_images()
    return cover_media_id


def import_users(session: Session, mysql_url: str, default_password: str) -> dict[int, int]:
    rows = fetch_rows(
        mysql_url,
        "SELECT id, username, email, phone_number, avatar, introduction FROM user WHERE deleted = 0",
    )
    mapping: dict[int, int] = {}
    password_hash = hash_password(default_password)
    for row in rows:
        username = (row.get("username") or f"user_{row['id']}").strip()
        existing = session.exec(select(User).where(User.username == username)).first()
        if existing:
            mapping[row["id"]] = existing.id
            print(f"用户已存在，跳过: {username} -> id={existing.id}")
            continue
        user = User(
            username=username,
            nickname=username,
            email=row.get("email") or None,
            phone=row.get("phone_number") or None,
            avatar_url=row.get("avatar") or None,
            bio=(row.get("introduction") or "")[:200] or None,
            password_hash=password_hash,
            status=UserStatus.active,
        )
        session.add(user)
        session.flush()
        mapping[row["id"]] = user.id
        print(f"导入用户: {username} poetize#{row['id']} -> users#{user.id}")
    session.commit()
    return mapping


def wipe_user_notes(session: Session, user_id: int) -> None:
    from app.models.note_comment import NoteComment
    from app.models.note_share import NoteShare

    notes = session.exec(select(Note).where(Note.user_id == user_id)).all()
    note_ids = [note.id for note in notes if note.id is not None]
    if not note_ids:
        print(f"用户 #{user_id} 无笔记，跳过清理")
        return

    comments = session.exec(select(NoteComment).where(NoteComment.note_id.in_(note_ids))).all()
    for comment in comments:
        session.delete(comment)

    shares = session.exec(select(NoteShare).where(NoteShare.note_id.in_(note_ids))).all()
    for share in shares:
        session.delete(share)

    blocks = session.exec(select(NoteBlock).where(NoteBlock.note_id.in_(note_ids))).all()
    block_ids = [block.id for block in blocks if block.id is not None]
    if block_ids:
        relations = session.exec(
            select(BlockMediaRelation).where(BlockMediaRelation.block_id.in_(block_ids))
        ).all()
        for relation in relations:
            session.delete(relation)
    for block in blocks:
        session.delete(block)

    for note in notes:
        session.delete(note)

    medias = session.exec(select(MediaAsset).where(MediaAsset.user_id == user_id)).all()
    for media in medias:
        file_path = IMAGE_UPLOAD_DIR.parent / media.file_key
        if file_path.is_file():
            file_path.unlink()
        session.delete(media)

    session.commit()
    print(f"已清除用户 #{user_id}：{len(notes)} 篇笔记、{len(medias)} 个媒体")


def import_articles(
    session: Session,
    mysql_url: str,
    user_map: dict[int, int],
    skip_existing_titles: bool,
    target_user_id: int | None = None,
    rewrites: list[tuple[str, str]] | None = None,
) -> None:
    url_rewrites = rewrites or DEFAULT_URL_REWRITES
    rows = fetch_rows(
        mysql_url,
        """
        SELECT id, user_id, article_title, article_content, article_cover,
               view_status, deleted, create_time, update_time
        FROM article
        WHERE deleted = 0
        ORDER BY id
        """,
    )
    media_cache: dict[str, int] = {}
    for row in rows:
        user_id = target_user_id or user_map.get(row["user_id"])
        if not user_id:
            print(f"跳过文章 #{row['id']}：找不到用户 poetize#{row['user_id']}")
            continue
        title = (row.get("article_title") or f"未命名-{row['id']}")[:100]
        if skip_existing_titles:
            exists = session.exec(
                select(Note).where(Note.user_id == user_id, Note.title == title, Note.deleted_at.is_(None))
            ).first()
            if exists:
                print(f"跳过已存在: {title}")
                continue

        is_public = row.get("view_status") == 1
        created_at = row.get("create_time") or datetime.utcnow()
        updated_at = row.get("update_time") or created_at
        summary_source = (row.get("article_content") or "").replace("\n", " ").strip()
        summary = summary_source[:300] if summary_source else None

        note = Note(
            user_id=user_id,
            title=title,
            summary=summary,
            status=NoteStatus.published if is_public else NoteStatus.draft,
            is_private=not is_public,
            created_at=created_at,
            updated_at=updated_at,
        )
        session.add(note)
        session.flush()

        cover_media_id = create_blocks(
            session,
            note.id,
            user_id,
            rewrite_text(row.get("article_content") or "", url_rewrites),
            rewrite_url(row.get("article_cover"), url_rewrites),
            media_cache,
            url_rewrites,
        )
        if cover_media_id:
            note.cover_media_id = cover_media_id
            session.add(note)

        session.commit()
        print(f"导入文章 #{row['id']} -> notes#{note.id} 《{title}》")


def main():
    parser = argparse.ArgumentParser(description="Poetize -> Random-Notes 数据迁移")
    parser.add_argument("--mysql-url", default=None, help="MySQL 连接，默认读 POETIZE_MYSQL_URL")
    parser.add_argument(
        "--default-password",
        default=None,
        help="新建 Poetize 用户时的登录密码（Poetize 为 MD5，无法沿用）",
    )
    parser.add_argument(
        "--target-username",
        default=None,
        help="全部文章导入到已有用户名下，不创建 Poetize 用户",
    )
    parser.add_argument("--skip-existing-titles", action="store_true", help="同名笔记已存在则跳过")
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="导入前先删除目标用户的全部笔记与媒体（用于重新导入）",
    )
    parser.add_argument(
        "--url-rewrite",
        action="append",
        default=[],
        metavar="OLD=>NEW",
        help="额外 URL 替换规则，可重复指定",
    )
    args = parser.parse_args()

    try:
        url_rewrites = build_url_rewrites(args.url_rewrite)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    if not args.target_username and not args.default_password:
        print("请指定 --target-username 或 --default-password", file=sys.stderr)
        sys.exit(1)

    mysql_url = args.mysql_url or __import__("os").getenv("POETIZE_MYSQL_URL")
    if not mysql_url:
        print("请设置 POETIZE_MYSQL_URL 或 --mysql-url", file=sys.stderr)
        sys.exit(1)

    from app.core.config import DATABASE_URL

    if not DATABASE_URL:
        print("请设置 DATABASE_URL", file=sys.stderr)
        sys.exit(1)

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    IMAGE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    pg_engine = create_engine(DATABASE_URL)
    with Session(pg_engine) as session:
        if args.target_username:
            target_user = session.exec(
                select(User).where(User.username == args.target_username)
            ).first()
            if not target_user:
                print(f"找不到用户: {args.target_username}", file=sys.stderr)
                sys.exit(1)
            print(f"全部文章导入到: {args.target_username} (id={target_user.id})")
            if args.replace_existing:
                wipe_user_notes(session, target_user.id)
            import_articles(
                session,
                mysql_url,
                {},
                args.skip_existing_titles,
                target_user_id=target_user.id,
                rewrites=url_rewrites,
            )
            print(f"完成。请用 {args.target_username} 登录查看。")
        else:
            user_map = import_users(session, mysql_url, args.default_password)
            import_articles(
                session,
                mysql_url,
                user_map,
                args.skip_existing_titles,
                rewrites=url_rewrites,
            )
            print("完成。请用迁移时设置的用户名 + --default-password 登录。")


if __name__ == "__main__":
    main()
