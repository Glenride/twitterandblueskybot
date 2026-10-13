"""Twitter-specific implementation of the scheduler platform interface."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Callable, Sequence, Set

from twikit import Client

from ..config import DMEntry, PostEntry, ReplyEntry
from ..dm_tracker import DMTracker

logger = logging.getLogger(__name__)


class TwitterPlatform:
    """Adapter that drives the scheduler using a Twikit client."""

    def __init__(self, client: Client, dm_tracking_file: Path | None = None) -> None:
        self.client = client
        self._enable_dms = self._read_dm_flag()
        
        # Initialize DM tracker to prevent duplicate sends
        if dm_tracking_file is None:
            dm_tracking_file = Path.cwd() / "dm_recipients_sent.json"
        self._dm_tracker = DMTracker(dm_tracking_file)

    @staticmethod
    def _read_dm_flag() -> bool:
        value = os.getenv("TWITTER_ENABLE_DMS", "").strip().lower()
        return value in {"1", "true", "yes", "on"}

    @property
    def supports_dms(self) -> bool:
        return self._enable_dms

    async def send_post(
        self,
        entry: PostEntry,
        *,
        dry_run: bool,
        resolve_media_path: Callable[[str], Path],
        log_dry_run: Callable[[str, str, dict[str, Any] | None], None],
    ) -> None:
        payload: dict[str, Any] = {"text": entry.text}
        if entry.media:
            payload["media"] = entry.media
        if dry_run:
            log_dry_run("post", entry.id, payload)
            return

        media_ids: list[str] = []
        for media_path in entry.media:
            upload_path = resolve_media_path(media_path)
            media_id = await self.client.upload_media(str(upload_path))
            media_ids.append(media_id)
        tweet_payload: dict[str, Any] = {"text": entry.text}
        if media_ids:
            tweet_payload["media_ids"] = media_ids
        await self.client.create_tweet(**tweet_payload)

    async def send_reply(
        self,
        entry: ReplyEntry,
        *,
        dry_run: bool,
        resolve_media_path: Callable[[str], Path],
        log_dry_run: Callable[[str, str, dict[str, Any] | None], None],
    ) -> None:
        if dry_run:
            target = self._select_reply_placeholder(entry)
            if target is None:
                logger.warning("[dry-run] skipping reply %s; no placeholder target", entry.id)
                return
            log_dry_run("reply", entry.id, {"text": entry.text, "target": target})
            return

        target_tweet_id = await self._resolve_reply_target(entry)
        if not target_tweet_id:
            raise RuntimeError(f"No reply targets available for {entry.id}")

        media_ids: list[str] = []
        for media_path in entry.media:
            upload_path = resolve_media_path(media_path)
            media_id = await self.client.upload_media(str(upload_path))
            media_ids.append(media_id)

        payload: dict[str, Any] = {"text": entry.text, "reply_to": target_tweet_id}
        if media_ids:
            payload["media_ids"] = media_ids
        await self.client.create_tweet(**payload)

    async def send_dm(
        self,
        entry: DMEntry,
        *,
        dry_run: bool,
        log_dry_run: Callable[[str, str, dict[str, Any] | None], None],
    ) -> None:
        if not self._enable_dms:
            logger.warning("Skipping DM %s; Twitter DM sending is currently disabled", entry.id)
            if dry_run:
                log_dry_run("dm", entry.id, {"disabled": True})
            return

        recipients = await self._resolve_dm_recipients(entry, dry_run=dry_run)
        if not recipients:
            raise RuntimeError(f"No DM recipients available for {entry.id}")

        # Filter out recipients who have already been contacted
        uncontacted_recipients = self._dm_tracker.get_uncontacted_recipients(recipients)
        
        if not uncontacted_recipients:
            logger.info("All recipients for DM %s have already been contacted, skipping", entry.id)
            return
        
        logger.info("Sending DM %s to %d uncontacted recipients (filtered %d already contacted)", 
                    entry.id, len(uncontacted_recipients), len(recipients) - len(uncontacted_recipients))

        for recipient in uncontacted_recipients:
            if dry_run:
                log_dry_run("dm", entry.id, {"recipient": recipient})
                continue
            
            # Send the DM
            await self.client.send_dm(recipient, entry.text)
            
            # Mark as contacted after successful send
            self._dm_tracker.mark_contacted(recipient)

    async def _resolve_reply_target(self, entry: ReplyEntry) -> str | None:
        for tweet_id in entry.targets.specific_tweets:
            if tweet_id:
                return tweet_id
        for query in entry.targets.search_queries:
            try:
                results = await self.client.search_tweet(query, "Latest")
            except Exception as exc:  # pylint: disable=broad-except
                logger.exception("Failed to search tweets for %s: %s", entry.id, exc)
                continue
            for tweet in results:
                candidate = getattr(tweet, "id", None)
                if candidate:
                    return candidate
        return None

    async def _resolve_dm_recipients(self, entry: DMEntry, *, dry_run: bool) -> Sequence[str]:
        recipients: Set[str] = set(entry.recipients.user_ids)

        if dry_run:
            recipients.update(entry.recipients.handles)
            if entry.recipients.dynamic_sources:
                logger.info(
                    "[dry-run] skipping dynamic recipient resolution for %s sources %s",
                    entry.id,
                    entry.recipients.dynamic_sources,
                )
            return list(recipients)

        for handle in entry.recipients.handles:
            screen_name = handle.lstrip("@")
            try:
                user = await self.client.get_user_by_screen_name(screen_name)
            except Exception as exc:  # pylint: disable=broad-except
                logger.exception("Failed to resolve handle %s for %s: %s", handle, entry.id, exc)
                continue
            user_id = getattr(user, "id", None)
            if user_id:
                recipients.add(user_id)

        for source in entry.recipients.dynamic_sources:
            if source == "new_followers":
                try:
                    user_id = await self.client.user_id()
                    followers = await self.client.get_user_followers(user_id, count=10)
                except Exception as exc:  # pylint: disable=broad-except
                    logger.exception("Failed to fetch followers for %s: %s", entry.id, exc)
                    continue
                for follower in followers:
                    follower_id = getattr(follower, "id", None)
                    if follower_id:
                        recipients.add(follower_id)
            else:
                logger.warning("Unknown dynamic source '%s' for %s", source, entry.id)

        return list(recipients)

    @staticmethod
    def _select_reply_placeholder(entry: ReplyEntry) -> str | None:
        if entry.targets.specific_tweets:
            return entry.targets.specific_tweets[0]
        if entry.targets.search_queries:
            return f"search:{entry.targets.search_queries[0]}"
        return None

    async def aclose(self) -> None:
        http = getattr(self.client, "http", None)
        if http is not None:
            await http.aclose()
