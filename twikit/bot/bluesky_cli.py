"""Command-line interface for the Bluesky scheduler bot."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os

from atproto_client import AsyncClient

from .env import load_env_defaults, resolve_config_path
from .platforms.bluesky import BlueskyPlatform
from .scheduler import Scheduler

logger = logging.getLogger(__name__)

load_env_defaults()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Bluesky scheduler bot")

    parser.add_argument(
        "--config",
        dest="config_path",
        default=os.environ.get("BOT_CONFIG", "content-library.json"),
        help="Path to content library JSON",
    )
    parser.add_argument(
        "--base-url",
        dest="base_url",
        default=os.environ.get("BLUESKY_URL"),
        help="Optional Bluesky PDS base URL (defaults to public PDS)",
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

    parser.set_defaults(command="run")
    return parser


async def run_scheduler_command(args: argparse.Namespace) -> None:
    username = os.environ.get("BLUESKY_USERNAME")
    password = os.environ.get("BLUESKY_PASSWORD")
    if not username or not password:
        raise RuntimeError("BLUESKY_USERNAME and BLUESKY_PASSWORD environment variables are required")

    config_path = resolve_config_path(args.config_path)
    base_url = args.base_url or os.environ.get("BLUESKY_URL") or "https://bsky.social"
    if args.base_url is None and not os.environ.get("BLUESKY_URL"):
        logger.debug("No BLUESKY_URL provided; defaulting to https://bsky.social")
    client = AsyncClient(base_url=base_url)
    platform = BlueskyPlatform(client)

    scheduler = Scheduler(
        platform=platform,
        content_path=config_path,
        notifier=None,
        dry_run=args.dry_run,
    )

    try:
        if args.dry_run:
            logger.info("Running in dry-run mode; skipping Bluesky login")
        else:
            await client.login(login=username, password=password)

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


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    logging.basicConfig(level=args.log_level.upper(), format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    asyncio.run(run_scheduler_command(args))


if __name__ == "__main__":
    main()
