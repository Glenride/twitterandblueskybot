"""Configuration loading helpers for the Twikit scheduler bot."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Literal, Optional

ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


class ConfigError(ValueError):
    """Raised when the content library configuration is invalid."""


@dataclass(slots=True)
class ScheduledWindow:
    earliest: datetime
    latest: Optional[datetime] = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "ScheduledWindow":
        try:
            earliest_raw = data["earliest"]
        except KeyError as exc:
            raise ConfigError("scheduled_window.earliest is required") from exc

        latest_raw = data.get("latest", earliest_raw)
        earliest = parse_timestamp(earliest_raw)
        latest = parse_timestamp(latest_raw)

        if latest < earliest:
            raise ConfigError("scheduled_window.latest must be >= earliest")

        return ScheduledWindow(earliest=earliest, latest=latest)

    def choose_timestamp(self) -> datetime:
        """Return earliest timestamp (scheduler applies jitter separately)."""
        return self.earliest


@dataclass(slots=True)
class PostEntry:
    id: str
    text: str
    scheduled_window: ScheduledWindow
    media: List[str] = field(default_factory=list)
    priority: Literal["normal", "high"] = "normal"

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "PostEntry":
        return PostEntry(
            id=ensure_str(data.get("id"), "post.id"),
            text=ensure_str(data.get("text"), "post.text"),
            media=list(map(str, data.get("media", []))),
            scheduled_window=ScheduledWindow.from_dict(
                ensure_dict(data.get("scheduled_window"), "post.scheduled_window")
            ),
            priority=ensure_literal(
                data.get("priority", "normal"),
                "post.priority",
                {"normal", "high"},
            ),
        )


@dataclass(slots=True)
class ReplyTargets:
    specific_tweets: List[str] = field(default_factory=list)
    search_queries: List[str] = field(default_factory=list)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "ReplyTargets":
        return ReplyTargets(
            specific_tweets=list(map(str, data.get("specific_tweets", []))),
            search_queries=list(map(str, data.get("search_queries", []))),
        )


@dataclass(slots=True)
class ReplyEntry:
    id: str
    text: str
    scheduled_window: ScheduledWindow
    media: List[str] = field(default_factory=list)
    targets: ReplyTargets = field(default_factory=ReplyTargets)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "ReplyEntry":
        return ReplyEntry(
            id=ensure_str(data.get("id"), "reply.id"),
            text=ensure_str(data.get("text"), "reply.text"),
            media=list(map(str, data.get("media", []))),
            scheduled_window=ScheduledWindow.from_dict(
                ensure_dict(data.get("scheduled_window"), "reply.scheduled_window")
            ),
            targets=ReplyTargets.from_dict(
                ensure_dict(data.get("targets", {}), "reply.targets")
            ),
        )


@dataclass(slots=True)
class RecipientTargets:
    handles: List[str] = field(default_factory=list)
    user_ids: List[str] = field(default_factory=list)
    dynamic_sources: List[str] = field(default_factory=list)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "RecipientTargets":
        return RecipientTargets(
            handles=list(map(str, data.get("handles", []))),
            user_ids=list(map(str, data.get("user_ids", []))),
            dynamic_sources=list(map(str, data.get("dynamic_sources", []))),
        )


@dataclass(slots=True)
class DMEntry:
    id: str
    text: str
    scheduled_window: ScheduledWindow
    recipients: RecipientTargets

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "DMEntry":
        return DMEntry(
            id=ensure_str(data.get("id"), "dm.id"),
            text=ensure_str(data.get("text"), "dm.text"),
            recipients=RecipientTargets.from_dict(
                ensure_dict(data.get("recipients"), "dm.recipients")
            ),
            scheduled_window=ScheduledWindow.from_dict(
                ensure_dict(data.get("scheduled_window"), "dm.scheduled_window")
            ),
        )


@dataclass(slots=True)
class RatePolicy:
    min_interval_minutes: int
    daily_max_tweets: Optional[int] = None
    daily_max_dms: Optional[int] = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "RatePolicy":
        mins = ensure_int(data.get("min_interval_minutes"), "rate_policy.min_interval_minutes")
        daily = ensure_dict(data.get("daily_max", {}), "rate_policy.daily_max")
        tweets = daily.get("tweets")
        dms = daily.get("dms")
        return RatePolicy(
            min_interval_minutes=mins,
            daily_max_tweets=ensure_optional_int(tweets, "rate_policy.daily_max.tweets"),
            daily_max_dms=ensure_optional_int(dms, "rate_policy.daily_max.dms"),
        )


@dataclass(slots=True)
class RetryPolicy:
    retries: int = 0
    backoff_seconds: int = 60

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "RetryPolicy":
        return RetryPolicy(
            retries=ensure_int(data.get("retries", 0), "alert_webhook.retry_policy.retries"),
            backoff_seconds=ensure_int(
                data.get("backoff_seconds", 60), "alert_webhook.retry_policy.backoff_seconds"
            ),
        )


@dataclass(slots=True)
class AlertWebhook:
    url: str
    secret: Optional[str] = None
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "AlertWebhook":
        if not data:
            raise ConfigError("alert_webhook is required")
        return AlertWebhook(
            url=ensure_str(data.get("url"), "alert_webhook.url"),
            secret=data.get("secret"),
            retry_policy=RetryPolicy.from_dict(data.get("retry_policy", {})),
        )


@dataclass(slots=True)
class ContentLibrary:
    posts: List[PostEntry] = field(default_factory=list)
    replies: List[ReplyEntry] = field(default_factory=list)
    dms: List[DMEntry] = field(default_factory=list)
    rate_policy: RatePolicy = field(default_factory=lambda: RatePolicy(min_interval_minutes=15))
    alert_webhook: Optional[AlertWebhook] = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "ContentLibrary":
        rate_policy_data = data.get("rate_policy")
        if rate_policy_data is None:
            rate_policy = RatePolicy(min_interval_minutes=15)
        else:
            rate_policy = RatePolicy.from_dict(ensure_dict(rate_policy_data, "rate_policy"))
        return ContentLibrary(
            posts=[PostEntry.from_dict(item) for item in data.get("posts", [])],
            replies=[ReplyEntry.from_dict(item) for item in data.get("replies", [])],
            dms=[DMEntry.from_dict(item) for item in data.get("dms", [])],
            rate_policy=rate_policy,
            alert_webhook=AlertWebhook.from_dict(data["alert_webhook"]) if data.get("alert_webhook") else None,
        )


def parse_timestamp(value: str) -> datetime:
    try:
        ts = datetime.strptime(value, ISO_FORMAT)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"Timestamp must be in {ISO_FORMAT} format: {value}") from exc
    return ts.replace(tzinfo=timezone.utc)


def ensure_str(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{field_name} must be a non-empty string")
    return value


def ensure_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"{field_name} must be an integer")
    return value


def ensure_optional_int(value: Any, field_name: str) -> Optional[int]:
    if value is None:
        return None
    return ensure_int(value, field_name)


def ensure_dict(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"{field_name} must be an object")
    return value


def ensure_literal(value: Any, field_name: str, allowed: set[str]) -> str:
    if value not in allowed:
        allowed_str = ", ".join(sorted(allowed))
        raise ConfigError(f"{field_name} must be one of: {allowed_str}")
    return str(value)


def load_content_library(path: Path) -> ContentLibrary:
    try:
        raw = json.loads(path.read_text("utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"Config file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON: {exc}") from exc

    return ContentLibrary.from_dict(ensure_dict(raw, "root"))
