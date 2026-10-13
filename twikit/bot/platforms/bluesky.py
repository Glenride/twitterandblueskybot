"""Bluesky-specific implementation of the scheduler platform interface."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable

from atproto_client import AsyncClient, models

from ..config import DMEntry, PostEntry, ReplyEntry

logger = logging.getLogger(__name__)


class BlueskyPlatform:
    """Adapter for running scheduled actions against Bluesky."""

    supports_dms = False

    def __init__(self, client: AsyncClient) -> None:
        self.client = client

    async def send_post(
        self,
        entry: PostEntry,
        *,
        dry_run: bool,
        resolve_media_path: Callable[[str], Path],
        log_dry_run: Callable[[str, str, dict[str, Any] | None], None],
    ) -> None:
        dry_payload: dict[str, Any] = {"text": entry.text}
        if entry.media:
            dry_payload["media"] = entry.media
        if dry_run:
            log_dry_run("post", entry.id, dry_payload)
            return

        embed = await self._build_images_embed(entry.media, resolve_media_path)

        await self.client.send_post(entry.text, embed=embed)

    async def send_reply(
        self,
        entry: ReplyEntry,
        *,
        dry_run: bool,
        resolve_media_path: Callable[[str], Path],
        log_dry_run: Callable[[str, str, dict[str, Any] | None], None],
    ) -> None:
        target = self._resolve_reply_target(entry)
        if target is None:
            logger.warning("No reply target available for %s", entry.id)
            return

        payload: dict[str, Any] = {"text": entry.text, "reply_to": target}
        if entry.media:
            payload["media"] = entry.media

        if dry_run:
            log_dry_run("reply", entry.id, payload)
            return

        reply_ref = await self._build_reply_ref(target)
        if reply_ref is None:
            raise RuntimeError(f"Unable to resolve Bluesky reply target for {entry.id}: {target}")

        embed = await self._build_images_embed(entry.media, resolve_media_path)

        await self.client.send_post(entry.text, reply_to=reply_ref, embed=embed)

    async def send_dm(
        self,
        entry: DMEntry,
        *,
        dry_run: bool,
        log_dry_run: Callable[[str, str, dict[str, Any] | None], None],
    ) -> None:
        logger.info("Skipping DM %s; Bluesky does not support direct messages", entry.id)

    def _resolve_reply_target(self, entry: ReplyEntry) -> str | None:
        if entry.targets.specific_tweets:
            return entry.targets.specific_tweets[0]
        if entry.targets.search_queries:
            logger.warning(
                "Reply %s uses search_queries which are not supported on Bluesky; skipping",
                entry.id,
            )
            return None
        return None

    async def aclose(self) -> None:
        await self.client.request.close()

    async def _build_images_embed(
        self,
        media_paths: list[str],
        resolve_media_path: Callable[[str], Path],
    ) -> models.AppBskyEmbedImages.Main | None:
        if not media_paths:
            return None

        images: list[models.AppBskyEmbedImages.Image] = []
        for media_path in media_paths:
            media_file = resolve_media_path(media_path)
            data = media_file.read_bytes()
            upload = await self.client.upload_blob(data)
            images.append(models.AppBskyEmbedImages.Image(alt="", image=upload.blob))
        return models.AppBskyEmbedImages.Main(images=images)

    async def _build_reply_ref(
        self,
        uri: str,
    ) -> models.AppBskyFeedPost.ReplyRef | None:
        try:
            response = await self.client.get_posts([uri])
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Failed to fetch Bluesky post %s: %s", uri, exc)
            return None

        if not response.posts:
            logger.warning("No Bluesky post found for uri %s", uri)
            return None

        post = response.posts[0]
        parent_ref = models.ComAtprotoRepoStrongRef.Main(uri=post.uri, cid=post.cid)
        if post.reply and getattr(post.reply, "root", None):
            root_view = post.reply.root
            root_uri = getattr(root_view, "uri", post.uri)
            root_cid = getattr(root_view, "cid", post.cid)
        else:
            root_uri = post.uri
            root_cid = post.cid
        root_ref = models.ComAtprotoRepoStrongRef.Main(uri=root_uri, cid=root_cid)
        return models.AppBskyFeedPost.ReplyRef(root=root_ref, parent=parent_ref)
