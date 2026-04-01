"""Helpers for reviewed starter agent naming."""

from __future__ import annotations

import os
import re
import secrets
import socket


def _slugify_name_component(
    value: str,
    *,
    fallback: str,
    max_length: int = 24,
) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    if not slug:
        slug = fallback
    trimmed = slug[:max_length].rstrip("-")
    return trimmed or fallback


def build_default_agent_name(
    provider: str,
    *,
    suffix: str | None = None,
) -> str:
    """Build a reviewed default agent name for first-run public onboarding."""

    provider_slug = _slugify_name_component(provider, fallback="agent")
    hostname_slug = _slugify_name_component(socket.gethostname(), fallback="local")
    parts = ["custom-agent", provider_slug, hostname_slug]
    if suffix:
        parts.append(_slugify_name_component(suffix, fallback="retry", max_length=12))
    return "-".join(parts)


def build_retry_agent_name(provider: str) -> str:
    """Build a collision-safe retry name for reviewed first-run registration."""

    return build_default_agent_name(provider, suffix=secrets.token_hex(3))


def resolve_configured_agent_name(provider: str) -> tuple[str, bool]:
    """Return the requested agent name and whether it was auto-generated."""

    configured = os.getenv("AGENT_NAME", "").strip()
    if configured:
        return configured, False
    return build_default_agent_name(provider), True

