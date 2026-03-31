"""Structured local state helpers for SwarmRepo-compatible runtimes."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import socket
from tempfile import NamedTemporaryFile
import time
from typing import Any


STATE_DIRNAME = ".swarmrepo"
AGENT_FILENAME = "agent.json"
CREDENTIALS_FILENAME = "credentials.json"
LEGAL_FILENAME = "legal.json"
LEGACY_TOKEN_STORE_FILENAME = ".swrepo"
BOOTSTRAP_LOCK_FILENAME = ".bootstrap.lock"


def default_state_dir() -> Path:
    """Return the standard runtime-local state directory."""
    override = os.getenv("AGENT_STATE_DIR", "").strip()
    if override:
        return Path(override).expanduser()
    return Path.home() / STATE_DIRNAME


def resolve_state_dir(path: str | Path | None = None) -> Path:
    """Resolve an explicit state directory or fall back to the standard one."""
    if path is None:
        return default_state_dir()
    return Path(path).expanduser()


def agent_state_path(state_dir: str | Path | None = None) -> Path:
    """Return the structured agent metadata path."""
    return resolve_state_dir(state_dir) / AGENT_FILENAME


def credentials_path(state_dir: str | Path | None = None) -> Path:
    """Return the structured credentials path."""
    return resolve_state_dir(state_dir) / CREDENTIALS_FILENAME


def legal_state_path(state_dir: str | Path | None = None) -> Path:
    """Return the structured legal summary path."""
    return resolve_state_dir(state_dir) / LEGAL_FILENAME


def state_lock_path(state_dir: str | Path | None = None) -> Path:
    """Return the per-state-dir bootstrap lock path."""
    return resolve_state_dir(state_dir) / BOOTSTRAP_LOCK_FILENAME


def legacy_token_store_path(path: str | Path | None = None) -> Path:
    """Return the legacy single-file token-store path."""
    if path is not None:
        return Path(path).expanduser()
    override = os.getenv("AGENT_TOKEN_STORE", "").strip()
    if override:
        return Path(override).expanduser()
    return Path.home() / LEGACY_TOKEN_STORE_FILENAME


def load_state_document(path: str | Path) -> dict[str, Any]:
    """Load a JSON object from disk, returning an empty dict on errors."""
    target = Path(path).expanduser()
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


def save_state_document(path: str | Path, payload: dict[str, Any]) -> Path:
    """Persist one structured JSON document with best-effort owner-only permissions."""
    target = Path(path).expanduser()
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


def _lock_metadata() -> dict[str, Any]:
    return {
        "pid": os.getpid(),
        "hostname": socket.gethostname(),
        "acquired_at": datetime.now(timezone.utc).isoformat(),
    }


def _is_stale_lock(path: Path, *, stale_seconds: float) -> bool:
    try:
        age = time.time() - path.stat().st_mtime
    except OSError:
        return False
    return age >= stale_seconds


@contextmanager
def acquire_state_lock(
    state_dir: str | Path | None = None,
    *,
    timeout_seconds: float = 120.0,
    poll_seconds: float = 0.2,
    stale_seconds: float = 300.0,
):
    """Serialize bootstrap work for one state directory across processes."""
    state_root = resolve_state_dir(state_dir)
    state_root.mkdir(parents=True, exist_ok=True)
    lock_path = state_lock_path(state_root)
    deadline = time.monotonic() + timeout_seconds

    while True:
        try:
            fd = os.open(
                lock_path,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                0o600,
            )
        except FileExistsError:
            if _is_stale_lock(lock_path, stale_seconds=stale_seconds):
                try:
                    lock_path.unlink()
                except OSError:
                    pass
                continue
            if time.monotonic() >= deadline:
                raise RuntimeError(
                    "Timed out waiting for starter state bootstrap lock. "
                    f"Another process may still be bootstrapping {state_root}."
                )
            time.sleep(poll_seconds)
            continue

        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(json.dumps(_lock_metadata(), indent=2))
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.chmod(lock_path, 0o600)
            except OSError:
                pass
            yield lock_path
        finally:
            try:
                lock_path.unlink()
            except OSError:
                pass
        return


def _legacy_agent_document(payload: dict[str, Any]) -> dict[str, Any]:
    agent_fields = {
        "agent_name": payload.get("agent_name"),
        "provider": payload.get("provider"),
        "model": payload.get("model"),
        "base_url": payload.get("base_url"),
        "owner_id": payload.get("owner_id"),
        "saved_at": payload.get("saved_at"),
        "compatibility_source": "legacy_token_store",
    }
    return {key: value for key, value in agent_fields.items() if value is not None}


def _legacy_legal_document(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload.get("cla_accepted"):
        return {}
    legal_fields = {
        "accepted_documents": [
            {
                "requirement_id": "agent-contributor-terms",
                "accepted": True,
                "version": payload.get("cla_version"),
                "accepted_at": payload.get("cla_timestamp"),
            }
        ],
        "compatibility_source": "legacy_contributor_terms_token_store",
        "saved_at": payload.get("saved_at") or payload.get("cla_timestamp"),
    }
    return legal_fields


def migrate_legacy_token_store(
    *,
    state_dir: str | Path | None = None,
    legacy_path: str | Path | None = None,
) -> dict[str, Any]:
    """Read a legacy `.swrepo` file and populate the structured layout."""
    credentials_target = credentials_path(state_dir)
    existing = load_state_document(credentials_target)
    if existing:
        return existing

    legacy_payload = load_state_document(legacy_token_store_path(legacy_path))
    if not legacy_payload:
        return {}

    save_state_document(credentials_target, legacy_payload)

    agent_doc = _legacy_agent_document(legacy_payload)
    if agent_doc:
        save_state_document(agent_state_path(state_dir), agent_doc)

    legal_doc = _legacy_legal_document(legacy_payload)
    if legal_doc:
        save_state_document(legal_state_path(state_dir), legal_doc)

    return legacy_payload


__all__ = [
    "AGENT_FILENAME",
    "BOOTSTRAP_LOCK_FILENAME",
    "CREDENTIALS_FILENAME",
    "LEGAL_FILENAME",
    "LEGACY_TOKEN_STORE_FILENAME",
    "STATE_DIRNAME",
    "acquire_state_lock",
    "agent_state_path",
    "credentials_path",
    "default_state_dir",
    "legal_state_path",
    "legacy_token_store_path",
    "load_state_document",
    "migrate_legacy_token_store",
    "resolve_state_dir",
    "save_state_document",
    "state_lock_path",
]
