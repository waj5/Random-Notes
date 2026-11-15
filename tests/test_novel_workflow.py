import json
import os
import unittest

from fastapi import HTTPException
from sqlmodel import Session, SQLModel, create_engine

os.environ.setdefault("DATABASE_URL", "sqlite://")

from app.api.routes import novels
from app.models.user import User


class NovelWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        SQLModel.metadata.create_all(self.engine)
        self.session = Session(self.engine)
        self.addCleanup(self.engine.dispose)
        self.addCleanup(self.session.close)
        self.owner = User(username="author", nickname="Author", password_hash="unused")
        self.stranger = User(username="reader", nickname="Reader", password_hash="unused")
        self.session.add_all([self.owner, self.stranger])
        self.session.commit()
        novel = novels.create_novel(novels.NewNovel(title="  雾海  "), self.session, self.owner)["data"]
        self.novel_id = novel["id"]
        self.first_id = novel["last_chapter_id"]
        self.assertEqual(novel["title"], "雾海")

    def test_retry_and_conflict_preserve_manuscript(self):
        text = "  海面起雾。🌊\n\n她站在码头上。\n" * 1000
        draft = novels.ChapterDraft(title="第一章", body=text, version=1)
        saved = novels.save_chapter(self.novel_id, self.first_id, draft, self.session, self.owner)["data"]
        self.assertEqual(saved["body"], text)
        self.assertEqual(saved["version"], 2)
        self.assertEqual(saved["word_count"], 13000)
        repeated = novels.save_chapter(self.novel_id, self.first_id, draft, self.session, self.owner)["data"]
        self.assertEqual(repeated, saved)

        stale = novels.ChapterDraft(title="另一份初稿", body="未合并", version=1)
        conflict = novels.save_chapter(self.novel_id, self.first_id, stale, self.session, self.owner)
        self.assertEqual(conflict.status_code, 409)
        self.assertEqual(json.loads(conflict.body)["data"]["server"], saved)
        reloaded = novels.read_chapter(self.novel_id, self.first_id, self.session, self.owner)["data"]
        self.assertEqual(reloaded, saved)

    def test_directory_order_recent_chapter_and_ownership(self):
        second = novels.create_chapter(self.novel_id, self.session, self.owner)["data"]
        order = novels.ChapterOrder(chapter_ids=[second["id"], self.first_id])
        novels.reorder_chapters(self.novel_id, order, self.session, self.owner)
        manuscript = novels.read_manuscript(self.novel_id, self.session, self.owner)["data"]
        self.assertEqual([chapter["id"] for chapter in manuscript], order.chapter_ids)
        novel = novels.read_novel(self.novel_id, self.session, self.owner)["data"]
        self.assertEqual(novel["last_chapter_id"], second["id"])
        self.assertNotIn("body", novel["chapters"][0])
        self.assertEqual(novels.list_novels(self.session, self.stranger)["data"], [])
        with self.assertRaises(HTTPException) as denied:
            novels.read_chapter(self.novel_id, self.first_id, self.session, self.stranger)
        self.assertEqual(denied.exception.status_code, 404)
        with self.assertRaises(HTTPException) as invalid:
            novels.reorder_chapters(
                self.novel_id, novels.ChapterOrder(chapter_ids=[self.first_id, self.first_id]),
                self.session, self.owner,
            )
        self.assertEqual(invalid.exception.status_code, 409)
