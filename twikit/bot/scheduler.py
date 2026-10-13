"""Async scheduler for executing content library actions."""

from __future__ import annotations

import asyncio
import logging
import random
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Deque, Optional, Protocol

from .config import ContentLibrary, DMEntry, PostEntry, ReplyEntry
from .config import load_content_library
from .notifier import NotifierConfig, WebhookNotifier

logger = logging.getLogger(__name__)


@dataclass
class ScheduledAction:
    entry_id: str
    entry_type: str  # post | reply | dm
    execute_at: datetime
    payload: object



class SchedulerPlatform(Protocol):
    supports_dms: bool

    async def send_post(
        self,
        entry: PostEntry,
        *,
        dry_run: bool,
        resolve_media_path: Callable[[str], Path],
        log_dry_run: Callable[[str, str, dict[str, Any] | None], None],
    ) -> None: ...

    async def send_reply(
        self,
        entry: ReplyEntry,
        *,
        dry_run: bool,
        resolve_media_path: Callable[[str], Path],
        log_dry_run: Callable[[str, str, dict[str, Any] | None], None],
    ) -> None: ...

    async def send_dm(
        self,
        entry: DMEntry,
        *,
        dry_run: bool,
        log_dry_run: Callable[[str, str, dict[str, Any] | None], None],
    ) -> None: ...

    async def aclose(self) -> None: ...


class Scheduler:
    def __init__(
        self,
        *,
        platform: SchedulerPlatform,
        content_path: Path,
        jitter_seconds: int = 300,
        notifier: WebhookNotifier | None = None,
        dry_run: bool = False,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.platform = platform
        self.content_path = content_path
        self.jitter_seconds = jitter_seconds
        self._actions: Deque[ScheduledAction] = deque()
        self._rate_history: Deque[datetime] = deque()
        self._type_counts: dict[str, dict[str, int]] = {"tweet": {}, "dm": {}}
        self.rate_policy = None
        self.config: Optional[ContentLibrary] = None
        self.notifier = notifier
        self._media_root = content_path.parent
        self.dry_run = dry_run
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    async def load(self) -> None:
        self.config = load_content_library(self.content_path)
        self.rate_policy = self.config.rate_policy
        if self.config.alert_webhook and not self.notifier:
            webhook = self.config.alert_webhook
            self.notifier = WebhookNotifier(
                NotifierConfig(
                    url=webhook.url,
                    secret=webhook.secret,
                    retries=webhook.retry_policy.retries,
                    backoff_seconds=webhook.retry_policy.backoff_seconds,
                )
            )
        self._build_schedule()

    def _build_schedule(self) -> None:
        assert self.config is not None
        all_actions: list[ScheduledAction] = []
        now = self._clock()
        for post in self.config.posts:
            execute_at = randomize(post.scheduled_window, self.jitter_seconds)
            if execute_at < now:
                execute_at = now + timedelta(seconds=1)
            all_actions.append(ScheduledAction(post.id, "post", execute_at, post))
        for reply in self.config.replies:
            execute_at = randomize(reply.scheduled_window, self.jitter_seconds)
            if execute_at < now:
                execute_at = now + timedelta(seconds=1)
            all_actions.append(ScheduledAction(reply.id, "reply", execute_at, reply))
        if self.platform.supports_dms:
            for dm in self.config.dms:
                execute_at = randomize(dm.scheduled_window, self.jitter_seconds)
                if execute_at < now:
                    execute_at = now + timedelta(seconds=1)
                all_actions.append(ScheduledAction(dm.id, "dm", execute_at, dm))
        elif self.config.dms:
            for dm in self.config.dms:
                logger.info("Skipping DM %s; platform does not support direct messages", dm.id)

        all_actions.sort(key=lambda a: a.execute_at)
        self._actions = deque(all_actions)
        logger.info("Scheduler loaded %d actions", len(self._actions))

    async def run(self) -> None:
        if self.config is None:
            await self.load()
        while self._actions:
            processed = await self.run_pending()
            if self._actions:
                next_action = self._actions[0]
                now = self._clock()
                next_allowed = self._next_allowed_time(now)
                wake_time = max(next_action.execute_at, next_allowed)
                sleep_for = (wake_time - now).total_seconds()
                if sleep_for > 0:
                    await asyncio.sleep(sleep_for)
            if processed == 0 and not self._actions:
                break

    def _prune_history(self, cutoff: datetime) -> None:
        while self._rate_history and self._rate_history[0] < cutoff:
            self._rate_history.popleft()

    def _min_interval_ok(self, now: datetime) -> bool:
        min_gap = timedelta(minutes=self.rate_policy.min_interval_minutes)
        self._prune_history(now - min_gap)
        return not self._rate_history or (now - self._rate_history[-1]) >= min_gap

    def _record_success(self, action: ScheduledAction, completed_at: datetime) -> None:
        self._rate_history.append(completed_at)
        bucket = "tweet" if action.entry_type in {"post", "reply"} else "dm"
        date_key = completed_at.date().isoformat()
        self._type_counts[bucket][date_key] = self._type_counts[bucket].get(date_key, 0) + 1
        self._prune_old_counts(bucket, date_key)
        logger.info(
            "Completed %s %s at %s",
            action.entry_type,
            action.entry_id,
            completed_at.isoformat(),
        )

    def _prune_old_counts(self, bucket: str, current_date_key: str) -> None:
        counts = self._type_counts[bucket]
        if len(counts) <= 7:
            return
        for date_key in list(counts.keys()):
            if date_key < current_date_key:
                del counts[date_key]

    def _next_allowed_time(self, now: datetime) -> datetime:
        if self.rate_policy is None:
            return now
        min_gap = timedelta(minutes=self.rate_policy.min_interval_minutes)
        self._prune_history(now - min_gap)
        if not self._rate_history:
            return now
        return self._rate_history[-1] + min_gap

    def _daily_limit_ok(self, action: ScheduledAction, now: datetime) -> bool:
        bucket = "tweet" if action.entry_type in {"post", "reply"} else "dm"
        date_key = now.date().isoformat()
        counts = self._type_counts.setdefault(bucket, {})
        limit = (
            self.rate_policy.daily_max_tweets if bucket == "tweet" else self.rate_policy.daily_max_dms
        )
        if limit is None:
            return True
        current = counts.get(date_key, 0)
        if current >= limit:
            logger.warning("Daily %s limit reached; deferring %s", bucket, action.entry_id)
            return False
        return True

    def _reschedule_next_day(self, action: ScheduledAction) -> None:
        self._actions.popleft()
        action.execute_at = action.execute_at + timedelta(days=1)
        self._insert_action(action)

    def _insert_action(self, action: ScheduledAction) -> None:
        if not self._actions:
            self._actions.append(action)
            return
        for idx, existing in enumerate(self._actions):
            if action.execute_at < existing.execute_at:
                self._actions.insert(idx, action)
                return
        self._actions.append(action)

    async def _execute(self, action: ScheduledAction) -> None:
        logger.info("Executing %s %s", action.entry_type, action.entry_id)
        if action.entry_type == "post":
            await self._send_post(action.payload)
        elif action.entry_type == "reply":
            await self._send_reply(action.payload)
        elif action.entry_type == "dm":
            await self._send_dm(action.payload)
        else:
            logger.error("Unknown action type %s", action.entry_type)

    async def _send_post(self, entry: PostEntry) -> None:
        await self.platform.send_post(
            entry,
            dry_run=self.dry_run,
            resolve_media_path=self._resolve_media_path,
            log_dry_run=self._log_dry_run,
        )

    async def _send_reply(self, entry: ReplyEntry) -> None:
        await self.platform.send_reply(
            entry,
            dry_run=self.dry_run,
            resolve_media_path=self._resolve_media_path,
            log_dry_run=self._log_dry_run,
        )

    async def _send_dm(self, entry: DMEntry) -> None:
        await self.platform.send_dm(
            entry,
            dry_run=self.dry_run,
            log_dry_run=self._log_dry_run,
        )

    async def _handle_failure(self, action: ScheduledAction, exc: Exception) -> None:
        logger.exception("Action %s failed: %s", action.entry_id, exc)
        if self.notifier:
            payload = {
                "id": action.entry_id,
                "type": action.entry_type,
                "error": repr(exc),
            }
            try:
                await self.notifier.send("action_failed", payload)
            except Exception as notify_exc:  # pylint: disable=broad-except
                logger.exception("Failed to send webhook alert: %s", notify_exc)
        retry_time = self._clock() + timedelta(minutes=self.rate_policy.min_interval_minutes)
        action.execute_at = retry_time
        self._insert_action(action)

    def _resolve_media_path(self, path_str: str) -> Path:
        candidate = Path(path_str)
        if not candidate.is_absolute():
            candidate = self._media_root / candidate
        return candidate

    def _log_dry_run(self, action_type: str, action_id: str, extra: dict | None = None) -> None:
        message = {"id": action_id, "type": action_type}
        if extra:
            message["details"] = extra
        logger.info("[dry-run] %s", message)

    async def run_pending(self, *, limit: int | None = None) -> int:
        processed = 0
        while self._actions and (limit is None or processed < limit):
            action = self._actions[0]
            now = self._clock()
            if action.execute_at > now:
                break
            if not self._min_interval_ok(now):
                break
            if not self._daily_limit_ok(action, now):
                self._reschedule_next_day(action)
                continue
            self._actions.popleft()
            try:
                await self._execute(action)
            except Exception as exc:  # pylint: disable=broad-except
                await self._handle_failure(action, exc)
            else:
                completed_at = self._clock()
                self._record_success(action, completed_at)
            processed += 1
        return processed

    async def aclose(self) -> None:
        if self.notifier:
            await self.notifier.aclose()
        await self.platform.aclose()


def randomize(window, jitter_seconds: int) -> datetime:
    delta = (window.latest - window.earliest).total_seconds()
    if delta < 0:
        delta = 0
    jitter = random.uniform(0, min(delta, jitter_seconds))
    return window.earliest + timedelta(seconds=jitter)


async def run_scheduler(client: Client, config_path: Path) -> None:
    sched = Scheduler(client=client, content_path=config_path)
    await sched.load()
    await sched.run()
