"""User-facing error formatting for the reviewed public starter surface."""

from __future__ import annotations

from swarmrepo_sdk import SwarmSDKError


def format_user_facing_error(exc: Exception) -> str:
    """Return a concise operator-facing error message."""

    if isinstance(exc, SwarmSDKError):
        message = str(exc).strip() or "SwarmRepo request failed."
        normalized = message.lower()
        if exc.error_code == "AUTH_005" or (
            exc.status_code == 409
            and "agent name" in normalized
            and "already registered" in normalized
        ):
            return "Registration failed: this deployment still requires a unique agent name."
        return message

    if isinstance(exc, RuntimeError):
        message = str(exc).strip()
        if message.startswith("Missing required environment variable: "):
            missing_name = message.removeprefix("Missing required environment variable: ").strip()
            return f"Configuration error: missing required environment variable {missing_name}."
        return message or "Runtime configuration failed."

    return str(exc).strip() or "Unexpected error."


__all__ = ["format_user_facing_error"]
