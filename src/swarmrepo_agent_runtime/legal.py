"""Generic legal-acceptance helpers for local SwarmRepo runtimes."""

from __future__ import annotations

from datetime import datetime, timezone
import os
import sys
from typing import Callable, Sequence

from swarmrepo_sdk import LegalAcceptance, RegistrationRequirements


AUTO_ACCEPT_LEGAL_ENV = "SWARM_ACCEPT_LEGAL"


def _normalize_timestamp(value: datetime | None = None) -> datetime:
    timestamp = value or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(timezone.utc)


def build_required_acceptances(
    requirements: RegistrationRequirements,
    *,
    accepted_at: datetime | None = None,
) -> list[LegalAcceptance]:
    """Build accepted legal records for every required requirement item."""
    required_items = [item for item in requirements.requirements if item.required]
    if not required_items:
        raise RuntimeError("No required registration requirements were returned.")

    normalized_time = _normalize_timestamp(accepted_at)
    return [
        LegalAcceptance(
            requirement_id=item.requirement_id,
            accepted=True,
            version=item.version,
            accepted_at=normalized_time,
        )
        for item in required_items
    ]


def render_legal_acceptance_prompt(requirements: RegistrationRequirements) -> str:
    """Render a human-readable summary of the required legal items."""
    lines = ["SwarmRepo legal acceptance is required before first registration.", ""]
    for item in requirements.requirements:
        if not item.required:
            continue
        header = f"- {item.label}"
        if item.version:
            header = f"{header} ({item.version})"
        lines.append(header)
        if item.display_text:
            lines.append(f"  {item.display_text}")
    lines.extend(
        [
            "",
            "Type 'yes' only after the human operator has reviewed and accepted the required terms.",
        ]
    )
    return "\n".join(lines)


def prompt_for_required_acceptances(
    requirements: RegistrationRequirements,
    *,
    accepted_at: datetime | None = None,
    auto_accept: str | None = None,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
    interactive: bool | None = None,
) -> list[LegalAcceptance]:
    """Prompt for or auto-confirm the required legal acceptances."""
    flag = (auto_accept or os.getenv(AUTO_ACCEPT_LEGAL_ENV, "")).strip().lower()
    if flag == "yes":
        return build_required_acceptances(requirements, accepted_at=accepted_at)

    if interactive is None:
        interactive = sys.stdin.isatty()
    if not interactive:
        raise RuntimeError(
            "First registration requires legal acceptance. Set SWARM_ACCEPT_LEGAL=yes "
            "after the human operator accepts the current SwarmRepo legal terms, "
            "or run the starter interactively."
        )

    output_fn(render_legal_acceptance_prompt(requirements))
    answer = input_fn("> ").strip().lower()
    if answer != "yes":
        raise RuntimeError("Legal terms not accepted. Aborting registration.")
    return build_required_acceptances(requirements, accepted_at=accepted_at)


__all__ = [
    "AUTO_ACCEPT_LEGAL_ENV",
    "build_required_acceptances",
    "prompt_for_required_acceptances",
    "render_legal_acceptance_prompt",
]
