"""Scheduler platform adapters."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - for type checkers only
    from .twitter import TwitterPlatform as TwitterPlatform


def __getattr__(name: str):
    if name == "TwitterPlatform":
        module = import_module("twikit.bot.platforms.twitter")
        return module.TwitterPlatform
    raise AttributeError(name)


__all__ = ["TwitterPlatform"]
