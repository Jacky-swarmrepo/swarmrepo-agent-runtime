"""Shared patch-generation helpers for SwarmRepo-compatible local runtimes."""

from __future__ import annotations

import json
from typing import Any


class PatchValidationError(ValueError):
    """Raised when a model returns an invalid or unsafe patch payload."""


def render_file_tree(file_tree: dict[str, Any] | None) -> str:
    """Render a file tree into a deterministic multi-file text snapshot."""
    if not file_tree:
        return ""
    chunks: list[str] = []
    for path in sorted(file_tree):
        content = file_tree[path]
        if content is None:
            chunks.append(f"# {path}\n<deleted>")
        else:
            chunks.append(f"# {path}\n{str(content).rstrip()}")
    return "\n\n".join(chunks)


def manifest_test_command(manifest: dict[str, Any] | None) -> str:
    """Extract the sandbox test command from a manifest payload."""
    if not isinstance(manifest, dict):
        return ""
    test_command = manifest.get("test_command")
    return str(test_command or "").strip()


def requires_pytest(manifest: dict[str, Any] | None) -> bool:
    """Return True when the repo's verification flow depends on pytest."""
    return "pytest" in manifest_test_command(manifest)


def contains_pytest_files(file_tree: dict[str, Any] | None) -> bool:
    """Detect whether a file tree already contains pytest-style test files."""
    if not file_tree:
        return False
    for path, content in file_tree.items():
        if content is None:
            continue
        normalized = str(path).replace("\\", "/")
        filename = normalized.rsplit("/", 1)[-1]
        if normalized.startswith("tests/") and filename.startswith("test_") and filename.endswith(".py"):
            return True
        if filename.endswith("_test.py"):
            return True
    return False


def extract_json_payload(raw_text: str) -> dict[str, Any]:
    """Recover a single JSON object from a model response."""
    text = (raw_text or "").strip()
    if text.startswith("```"):
        lines = [line for line in text.splitlines() if not line.strip().startswith("```")]
        text = "\n".join(lines).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise PatchValidationError("Model output did not contain a JSON object.")
    try:
        payload = json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise PatchValidationError(f"Model output was not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise PatchValidationError("Model output must be a JSON object.")
    return payload


def normalize_patch(
    *,
    current_tree: dict[str, str],
    proposed: dict[str, Any] | None,
) -> dict[str, str | None]:
    """Normalize an LLM patch into ``proposed_file_changes`` format."""
    if not isinstance(proposed, dict):
        raise PatchValidationError("LLM response must include proposed_file_changes as an object.")

    normalized: dict[str, str | None] = {}
    for path, content in proposed.items():
        if not isinstance(path, str) or not path.strip():
            raise PatchValidationError("LLM returned an invalid file path in proposed_file_changes.")
        if content is not None and not isinstance(content, str):
            raise PatchValidationError(
                f"LLM returned non-string content for {path!r} in proposed_file_changes."
            )
        existing = current_tree.get(path)
        if content == existing:
            continue
        normalized[path] = content
    return normalized


def merge_manifest_update(
    manifest: dict[str, Any] | None,
    patch: dict[str, str | None],
    manifest_update: Any,
) -> None:
    """Apply an optional manifest update by projecting swarm.manifest.json into the patch."""
    if manifest_update is None:
        return
    if not isinstance(manifest_update, dict):
        raise PatchValidationError("manifest_update must be an object when present.")
    merged_manifest = dict(manifest or {})
    merged_manifest.update(manifest_update)
    patch["swarm.manifest.json"] = json.dumps(
        merged_manifest,
        indent=2,
        ensure_ascii=False,
        sort_keys=True,
    )


def patch_satisfies_pytest_requirement(
    *,
    manifest: dict[str, Any] | None,
    current_tree: dict[str, str],
    patch: dict[str, str | None],
) -> bool:
    """Return True when pytest requirements are already met or newly provided."""
    if not requires_pytest(manifest):
        return True
    if contains_pytest_files(current_tree):
        return True
    generated_tests = {
        path: content
        for path, content in patch.items()
        if content is not None
    }
    return contains_pytest_files(generated_tests)


def pytest_requirement_note(manifest: dict[str, Any] | None, current_tree: dict[str, str]) -> str:
    """Return an extra prompt instruction when the repo needs generated pytest coverage."""
    if not requires_pytest(manifest):
        return ""
    if contains_pytest_files(current_tree):
        return ""
    return (
        "This repository uses pytest for verification and currently has no pytest test files. "
        "You must include at least one runnable pytest-compatible file under tests/ in "
        "proposed_file_changes.\n"
    )
