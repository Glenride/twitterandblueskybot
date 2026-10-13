"""Tests for the Bluesky scheduler platform adapter."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from atproto_client.models.blob_ref import BlobRef
from twikit.bot.config import (
    DMEntry,
    PostEntry,
    ReplyEntry,
    ReplyTargets,
    RecipientTargets,
    ScheduledWindow,
)
from twikit.bot.platforms.bluesky import BlueskyPlatform


class FakeClient:
    def __init__(self) -> None:
        self.uploaded: list[bytes] = []
        self.sent: list[dict] = []
        self.post_lookup: dict[str, tuple[str, tuple[str, str] | None]] = {}
        self._closed = False
        self.request = SimpleNamespace(close=self._close_async)

    async def upload_blob(self, data: bytes):
        index = len(self.uploaded)
        self.uploaded.append(data)
        blob = BlobRef(mime_type="image/png", size=len(data), ref=f"cid-{index}")
        return SimpleNamespace(blob=blob)

    async def send_post(self, text: str, embed=None, reply_to=None):
        self.sent.append({"text": text, "embed": embed, "reply_to": reply_to})

    async def get_posts(self, uris: list[str]):
        posts = []
        for uri in uris:
            info = self.post_lookup.get(uri)
            if info is None:
                continue
            cid, root = info
            if root is None:
                reply = None
            else:
                root_uri, root_cid = root
                reply = SimpleNamespace(root=SimpleNamespace(uri=root_uri, cid=root_cid))
            posts.append(SimpleNamespace(uri=uri, cid=cid, reply=reply))
        return SimpleNamespace(posts=posts)

    async def _close_async(self):
        self._closed = True

    def set_post(self, uri: str, *, cid: str, root: tuple[str, str] | None = None) -> None:
        self.post_lookup[uri] = (cid, root)


class BlueskyPlatformTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:  # noqa: D401
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="bluesky-platform-tests"))

    def tearDown(self) -> None:  # noqa: D401
        shutil.rmtree(self.tmp_dir)

    def _make_window(self) -> ScheduledWindow:
        now = datetime.now(timezone.utc)
        return ScheduledWindow(earliest=now, latest=now)

    def _resolve_media_path(self, name: str) -> Path:
        path = self.tmp_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    async def test_send_post_dry_run_skips_network_calls(self) -> None:
        client = FakeClient()
        platform = BlueskyPlatform(client)

        entry = PostEntry(
            id="post-1",
            text="Hello Bluesky",
            media=["image.png"],
            scheduled_window=self._make_window(),
        )

        events: list[dict] = []

        def log_dry_run(action_type: str, action_id: str, details: dict | None = None) -> None:
            events.append({"action": action_type, "id": action_id, "details": details})

        await platform.send_post(
            entry,
            dry_run=True,
            resolve_media_path=self._resolve_media_path,
            log_dry_run=log_dry_run,
        )

        self.assertEqual(client.uploaded, [])
        self.assertEqual(client.sent, [])
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["action"], "post")

    async def test_send_reply_uploads_media_and_sets_reply_ref(self) -> None:
        client = FakeClient()
        post_uri = "at://example.com/app.bsky.feed.post/123"
        client.set_post(post_uri, cid="cid123")
        platform = BlueskyPlatform(client)

        media_name = "reply.png"
        (self.tmp_dir / media_name).write_bytes(b"fake image data")

        entry = ReplyEntry(
            id="reply-1",
            text="Reply text",
            media=[media_name],
            scheduled_window=self._make_window(),
            targets=ReplyTargets(specific_tweets=[post_uri]),
        )

        await platform.send_reply(
            entry,
            dry_run=False,
            resolve_media_path=self._resolve_media_path,
            log_dry_run=lambda *_: None,
        )

        self.assertEqual(len(client.uploaded), 1)
        self.assertEqual(client.uploaded[0], b"fake image data")
        self.assertEqual(len(client.sent), 1)
        call = client.sent[0]
        self.assertEqual(call["text"], "Reply text")
        self.assertIsNotNone(call["reply_to"])
        self.assertEqual(call["reply_to"].parent.uri, post_uri)
        self.assertEqual(call["reply_to"].parent.cid, "cid123")
        self.assertIsNotNone(call["embed"])
        self.assertEqual(len(call["embed"].images), 1)

    async def test_send_reply_with_search_query_is_skipped(self) -> None:
        client = FakeClient()
        platform = BlueskyPlatform(client)

        entry = ReplyEntry(
            id="reply-unsupported",
            text="Should skip",
            media=[],
            scheduled_window=self._make_window(),
            targets=ReplyTargets(search_queries=["some query"]),
        )

        await platform.send_reply(
            entry,
            dry_run=False,
            resolve_media_path=self._resolve_media_path,
            log_dry_run=lambda *_: None,
        )

        self.assertEqual(client.sent, [])

    async def test_send_dm_logs_skip(self) -> None:
        client = FakeClient()
        platform = BlueskyPlatform(client)

        entry = DMEntry(
            id="dm-1",
            text="Hello",
            scheduled_window=self._make_window(),
            recipients=RecipientTargets(),
        )

        events: list[dict] = []

        def log_dry_run(action_type: str, action_id: str, details: dict | None = None) -> None:
            events.append({"action": action_type, "id": action_id, "details": details})

        await platform.send_dm(
            entry,
            dry_run=True,
            log_dry_run=log_dry_run,
        )

        self.assertEqual(client.sent, [])
        self.assertEqual(client.uploaded, [])
        self.assertEqual(events, [])


if __name__ == "__main__":
    unittest.main()
