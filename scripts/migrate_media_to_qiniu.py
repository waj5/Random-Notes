#!/usr/bin/env python3
"""
将本地磁盘上的 media_assets 上传到七牛云并更新数据库。

在服务器 api 容器内执行（需能访问 uploads 卷与数据库）：
  cd deploy
  docker compose exec api python scripts/migrate_media_to_qiniu.py --dry-run
  docker compose exec api python scripts/migrate_media_to_qiniu.py
  docker compose exec api python scripts/migrate_media_to_qiniu.py --delete-local

迁移完成后在 deploy/.env 设置 STORAGE_TYPE=qiniu 并重启 api。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from qiniu import Auth, put_data
from sqlmodel import Session, select

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.config import (  # noqa: E402
    IMAGE_UPLOAD_DIR,
    QINIU_ACCESS_KEY,
    QINIU_BUCKET_NAME,
    QINIU_DOMAIN,
    QINIU_SECRET_KEY,
)
from app.db.database import engine  # noqa: E402
from app.models.media_asset import MediaAsset  # noqa: E402


def _require_qiniu_config():
    missing = [
        name
        for name, value in {
            "QINIU_ACCESS_KEY": QINIU_ACCESS_KEY,
            "QINIU_SECRET_KEY": QINIU_SECRET_KEY,
            "QINIU_BUCKET_NAME": QINIU_BUCKET_NAME,
            "QINIU_DOMAIN": QINIU_DOMAIN,
        }.items()
        if not value
    ]
    if missing:
        raise SystemExit(f"缺少七牛配置: {', '.join(missing)}")


def _is_local_media(media: MediaAsset) -> bool:
    return media.file_key.startswith("images/") or not media.file_url.startswith(("http://", "https://"))


def _upload_to_qiniu(key: str, content: bytes) -> str:
    auth = Auth(QINIU_ACCESS_KEY, QINIU_SECRET_KEY)
    token = auth.upload_token(QINIU_BUCKET_NAME, key, 3600)
    _, info = put_data(token, key, content)
    if info.status_code != 200:
        raise RuntimeError(f"七牛上传失败 key={key} status={info.status_code} {info.error}")
    domain = QINIU_DOMAIN.rstrip("/")
    if not domain.startswith("http"):
        domain = f"http://{domain}"
    return f"{domain}/{key}"


def migrate(*, dry_run: bool, delete_local: bool) -> None:
    _require_qiniu_config()

    with Session(engine) as session:
        media_list = session.exec(select(MediaAsset).order_by(MediaAsset.id)).all()
        local_items = [media for media in media_list if _is_local_media(media)]

        print(f"共 {len(media_list)} 条 media，待迁移 {len(local_items)} 条")
        if not local_items:
            return

        ok = 0
        skipped = 0
        failed = 0

        for media in local_items:
            file_path = IMAGE_UPLOAD_DIR.parent / media.file_key
            if not file_path.is_file():
                print(f"[跳过] id={media.id} 文件不存在: {file_path}")
                skipped += 1
                continue

            qiniu_key = file_path.name
            if dry_run:
                print(f"[dry-run] id={media.id} {media.file_key} -> {qiniu_key}")
                ok += 1
                continue

            try:
                content = file_path.read_bytes()
                file_url = _upload_to_qiniu(qiniu_key, content)
                media.file_key = qiniu_key
                media.file_url = file_url
                session.add(media)
                session.commit()
                if delete_local:
                    file_path.unlink(missing_ok=True)
                print(f"[完成] id={media.id} -> {file_url}")
                ok += 1
            except Exception as exc:
                session.rollback()
                print(f"[失败] id={media.id} {exc}")
                failed += 1

        print(f"完成: 成功 {ok}，跳过 {skipped}，失败 {failed}")


def main():
    parser = argparse.ArgumentParser(description="迁移本地图片到七牛云")
    parser.add_argument("--dry-run", action="store_true", help="只预览，不上传")
    parser.add_argument("--delete-local", action="store_true", help="迁移成功后删除本地文件")
    args = parser.parse_args()
    migrate(dry_run=args.dry_run, delete_local=args.delete_local)


if __name__ == "__main__":
    main()
