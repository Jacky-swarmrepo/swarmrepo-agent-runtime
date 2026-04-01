"""Reviewed `.env` discovery helpers for public starter packages."""

from __future__ import annotations

from pathlib import Path

from dotenv import find_dotenv, load_dotenv


def find_reviewed_dotenv() -> Path | None:
    """Find the reviewed starter `.env`, preferring the current working directory."""
    cwd_env = Path.cwd() / ".env"
    if cwd_env.is_file():
        return cwd_env.resolve(strict=False)

    discovered = find_dotenv(filename=".env", usecwd=True)
    if not discovered:
        return None
    return Path(discovered).resolve(strict=False)


def load_reviewed_dotenv(*, override: bool = False) -> Path | None:
    """Load a reviewed starter `.env` file when one is available."""
    dotenv_path = find_reviewed_dotenv()
    if dotenv_path is None:
        return None
    load_dotenv(dotenv_path=dotenv_path, override=override)
    return dotenv_path
