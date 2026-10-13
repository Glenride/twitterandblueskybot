"""Unit tests for bot.config module."""

from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from bot.config import ContentLibrary, ConfigError, load_content_library


class ConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = Path(__file__).parent / "tmp"
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        for child in self.tmp_dir.glob("*"):
            child.unlink()

    def _write_config(self, data: dict) -> Path:
        path = self.tmp_dir / "config.json"
        path.write_text(json.dumps(data), "utf-8")
        return path

    def test_load_content_library(self) -> None:
        now = datetime.now(timezone.utc).replace(microsecond=0)
        iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        data = {
            "posts": [
                {
                    "id": "post-1",
                    "text": "Hello world",
                    "media": ["assets/img.png"],
                    "scheduled_window": {"earliest": iso, "latest": iso},
                }
            ],
            "replies": [],
            "dms": [],
            "rate_policy": {"min_interval_minutes": 15, "daily_max": {"tweets": 10, "dms": 5}},
            "alert_webhook": {
                "url": "https://example.com/webhook",
                "secret": "secret",
                "retry_policy": {"retries": 2, "backoff_seconds": 30},
            },
        }
        path = self._write_config(data)

        library = load_content_library(path)

        self.assertEqual(len(library.posts), 1)
        post = library.posts[0]
        self.assertEqual(post.id, "post-1")
        self.assertEqual(post.media, ["assets/img.png"])
        self.assertEqual(library.rate_policy.min_interval_minutes, 15)
        self.assertIsNotNone(library.alert_webhook)
        self.assertEqual(library.alert_webhook.url, "https://example.com/webhook")

    def test_invalid_timestamp_raises(self) -> None:
        data = {
            "posts": [
                {
                    "id": "post-1",
                    "text": "Hello world",
                    "scheduled_window": {"earliest": "invalid"},
                }
            ],
            "replies": [],
            "dms": [],
            "rate_policy": {"min_interval_minutes": 15, "daily_max": {}},
        }
        path = self._write_config(data)

        with self.assertRaises(ConfigError):
            load_content_library(path)


if __name__ == "__main__":
    unittest.main()
