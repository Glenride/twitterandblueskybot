"""Shared environment-loading utilities for scheduler CLIs."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_env_file(path: Path) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key or key in os.environ:
            continue
        if value and len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        os.environ[key] = value


def load_env_defaults() -> None:
    candidates: list[Path] = []
    override = os.environ.get("BOT_ENV_FILE")
    if override:
        candidates.append(Path(override).expanduser())
    candidates.extend(
        [
            PROJECT_ROOT / ".env.local",
            PROJECT_ROOT / ".env",
            (PROJECT_ROOT / "twikit" / ".env.local"),
            (PROJECT_ROOT / "twikit" / ".env"),
        ]
    )
    for candidate in candidates:
        if candidate.exists():
            load_env_file(candidate)


def resolve_config_path(raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if path.is_absolute() and path.exists():
        return path
    candidates = [
        path,
        PROJECT_ROOT / path,
        PROJECT_ROOT / "twikit" / path,
        PROJECT_ROOT / "twikit" / "bot" / path,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    if path.suffix in {".yml", ".yaml"}:
        fallback = path.with_suffix(".json")
        for candidate in (
            fallback,
            PROJECT_ROOT / fallback,
            PROJECT_ROOT / "twikit" / fallback,
            PROJECT_ROOT / "twikit" / "bot" / fallback,
        ):
            if candidate.exists():
                return candidate
    return candidates[1]
