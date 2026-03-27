"""Compatibility wrappers around the structured local runtime state."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .state import (
    CREDENTIALS_FILENAME,
    LEGACY_TOKEN_STORE_FILENAME,
    credentials_path,
    legacy_token_store_path,
    load_state_document,
    migrate_legacy_token_store,
    save_state_document,
)


TOKEN_STORE_FILENAME = CREDENTIALS_FILENAME


def default_token_store_path() -> Path:
    """Return the default structured credentials path."""
    return credentials_path()


def resolve_token_store_path(path: str | Path | None = None) -> Path:
    """Resolve an explicit token-store path or fall back to the structured credentials path."""
    if path is None:
        return default_token_store_path()
    return Path(path).expanduser()


def load_token_store(path: str | Path | None = None) -> dict[str, Any]:
    """Load the structured credentials payload, migrating legacy state when possible."""
    target = resolve_token_store_path(path)
    payload = load_state_document(target)
    if payload:
        return payload

    default_target = default_token_store_path()
    if target == default_target:
        return migrate_legacy_token_store()
    return {}


def save_token_store(path: str | Path | None, payload: dict[str, Any]) -> Path:
    """Persist a token-store payload to the structured credentials path or an explicit file."""
    return save_state_document(resolve_token_store_path(path), payload)


def mask_secret(value: str | None) -> str:
    """Mask a secret for logs while still leaving enough to identify it."""
    if not value:
        return "(missing)"
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}...{value[-4:]}"


__all__ = [
    "LEGACY_TOKEN_STORE_FILENAME",
    "TOKEN_STORE_FILENAME",
    "default_token_store_path",
    "legacy_token_store_path",
    "load_token_store",
    "mask_secret",
    "resolve_token_store_path",
    "save_token_store",
]
