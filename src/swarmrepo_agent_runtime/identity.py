"""Shared local identity helpers for SwarmRepo-compatible clients."""

from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any


TOKEN_STORE_FILENAME = ".swrepo"


def default_token_store_path() -> Path:
    """Return the standard client-local token file path."""
    override = os.getenv("AGENT_TOKEN_STORE")
    if override:
        return Path(override).expanduser()
    return Path.home() / TOKEN_STORE_FILENAME


def resolve_token_store_path(path: str | Path | None = None) -> Path:
    """Resolve an explicit token-store path or fall back to `~/.swrepo`."""
    if path is None:
        return default_token_store_path()
    return Path(path).expanduser()


def load_token_store(path: str | Path) -> dict[str, Any]:
    """Load a JSON token-store payload from disk."""
    target = resolve_token_store_path(path)
    try:
        raw = target.read_text(encoding="utf-8").strip()
    except OSError:
        return {}
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def save_token_store(path: str | Path, payload: dict[str, Any]) -> Path:
    """Persist a token-store payload with owner-only permissions when possible."""
    target = resolve_token_store_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=str(target.parent),
        prefix=f".{target.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        handle.write(json.dumps(payload, indent=2, ensure_ascii=False))
        handle.flush()
        os.fsync(handle.fileno())
        temp_path = Path(handle.name)
    try:
        os.replace(temp_path, target)
        try:
            os.chmod(target, 0o600)
        except OSError:
            pass
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
    return target


def mask_secret(value: str | None) -> str:
    """Mask a secret for logs while still leaving enough to identify it."""
    if not value:
        return "(missing)"
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}...{value[-4:]}"
