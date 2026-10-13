"""Command-line interface for Twikit scheduler bot."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os

from twikit import Client

from .scheduler import Scheduler
from .env import load_env_defaults, resolve_config_path
from .platforms.twitter import TwitterPlatform

logger = logging.getLogger(__name__)

load_env_defaults()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Twikit scheduler bot")

    parser.add_argument(
        "--config",
        dest="config_path",
        default=os.environ.get("BOT_CONFIG", "content-library.json"),
        help="Path to content library JSON",
    )
    parser.add_argument(
        "--language",
        dest="language",
        default=os.environ.get("TWITTER_LANGUAGE", "en-US"),
        help="Language parameter for Twikit client",
    )
    parser.add_argument(
        "--proxy",
        dest="proxy",
        default=os.environ.get("TWITTER_PROXY"),
        help="Optional proxy URL",
    )
    parser.add_argument(
        "--cookies",
        dest="cookies_file",
        default=os.environ.get("TWITTER_COOKIES"),
        help="Optional cookies file path",
    )
    parser.add_argument(
        "--totp-secret",
        dest="totp_secret",
        default=os.environ.get("TWITTER_TOTP_SECRET"),
        help="Optional TOTP secret for generating 2FA codes",
    )
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Skip network actions while logging planned operations",
    )
    parser.add_argument(
        "--log-level",
        dest="log_level",
        default=os.environ.get("BOT_LOG", "INFO"),
        help="Logging level (default: INFO)",
    )

    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Continuously run the scheduler")
    run_parser.add_argument(
        "--max-actions",
        dest="max_actions",
        type=int,
        default=None,
        help="Optional cap on number of actions to process before exiting",
    )

    once_parser = subparsers.add_parser("once", help="Process all actions that are ready right now")
    once_parser.add_argument(
        "--limit",
        dest="limit",
        type=int,
        default=None,
        help="Optional cap on actions to process in this run",
    )

    subparsers.add_parser("preview", help="Print pending actions without executing them")

    legacy_parser = subparsers.add_parser("twitter", help=argparse.SUPPRESS)
    legacy_parser.add_argument(
        "legacy_action",
        nargs="?",
        choices=("send", "run", "once", "preview"),
        default="send",
        help=argparse.SUPPRESS,
    )
    legacy_parser.add_argument(
        "--limit",
        dest="legacy_limit",
        type=int,
        default=None,
        help=argparse.SUPPRESS,
    )
    legacy_parser.add_argument(
        "--max-actions",
        dest="legacy_max_actions",
        type=int,
        default=None,
        help=argparse.SUPPRESS,
    )

    parser.set_defaults(command="run")
    return parser


async def run_scheduler_command(args: argparse.Namespace) -> None:
    username = os.environ.get("TWITTER_USERNAME")
    password = os.environ.get("TWITTER_PASSWORD")
    email = os.environ.get("TWITTER_EMAIL")
    if not username or not password:
        raise RuntimeError("TWITTER_USERNAME and TWITTER_PASSWORD environment variables are required")

    if args.command == "twitter":
        legacy_action = getattr(args, "legacy_action", "send")
        if legacy_action in {"send", "run"}:
            args.command = "run"
            if not hasattr(args, "max_actions"):
                args.max_actions = getattr(args, "legacy_max_actions", None)
        elif legacy_action == "once":
            args.command = "once"
            args.limit = getattr(args, "legacy_limit", None)
        elif legacy_action == "preview":
            args.command = "preview"
        else:
            logger.warning("Unknown legacy action '%s'; defaulting to run", legacy_action)
            args.command = "run"

    config_path = resolve_config_path(args.config_path)
    client = Client(language=args.language, proxy=args.proxy)
    platform = TwitterPlatform(client)

    scheduler = Scheduler(
        platform=platform,
        content_path=config_path,
        notifier=None,
        dry_run=args.dry_run,
    )

    try:
        if args.dry_run:
            logger.info("Running in dry-run mode; skipping Twitter login")
        else:
            totp_secret = args.totp_secret or None
            await client.login(
                auth_info_1=username,
                auth_info_2=email,
                password=password,
                cookies_file=args.cookies_file,
                totp_secret=totp_secret,
            )

        await scheduler.load()
        if args.command == "preview":
            for action in scheduler._actions:  # noqa: SLF001 - internal state for CLI preview only
                logger.info(
                    "Scheduled %s %s at %s",
                    action.entry_type,
                    action.entry_id,
                    action.execute_at.isoformat(),
                )
            return

        if args.command == "once":
            processed = await scheduler.run_pending(limit=args.limit)
            logger.info("Processed %d actions", processed)
            return

        max_actions = getattr(args, "max_actions", None)
        processed = 0
        while True:
            processed += await scheduler.run_pending()
            if max_actions is not None and processed >= max_actions:
                logger.info("Reached max actions limit (%d)", max_actions)
                break
            if not scheduler._actions:  # noqa: SLF001
                break
            next_action = scheduler._actions[0]  # noqa: SLF001
            now = scheduler._clock()
            sleep_for = max(0.0, (next_action.execute_at - now).total_seconds())
            if sleep_for <= 0:
                continue
            await asyncio.sleep(min(sleep_for, 60))
    finally:
        await scheduler.aclose()
        await platform.aclose()


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    logging.basicConfig(level=args.log_level.upper(), format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    asyncio.run(run_scheduler_command(args))


if __name__ == "__main__":
    main()
