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
        if exc.error_code == "AUTH_014":
            return (
                "Refresh failed: the stored refresh token is expired. "
                "Run `swarmrepo-agent agent onboard --yes` to bootstrap a new session."
            )
        if exc.error_code == "AUTH_015":
            return (
                "Refresh failed: the stored refresh token has been revoked or already rotated. "
                "Use the newest local state or run `swarmrepo-agent agent onboard --yes` again."
            )
        if exc.error_code == "AUTH_016":
            return (
                "Refresh failed: legal reacceptance is required before credentials can be refreshed."
            )
        if exc.error_code == "AUTH_017":
            return (
                "Refresh failed: the current agent registration or legal binding is no longer active."
            )
        return message

    if isinstance(exc, RuntimeError):
        message = str(exc).strip()
        if message.startswith("Missing required environment variable: "):
            missing_name = message.removeprefix("Missing required environment variable: ").strip()
            return f"Configuration error: missing required environment variable {missing_name}."
        if message.startswith("No stored refresh token is available."):
            return (
                "Refresh failed: no stored refresh token is available. "
                "Run `swarmrepo-agent agent onboard --yes` first."
            )
        return message or "Runtime configuration failed."

    return str(exc).strip() or "Unexpected error."


__all__ = ["format_user_facing_error"]
