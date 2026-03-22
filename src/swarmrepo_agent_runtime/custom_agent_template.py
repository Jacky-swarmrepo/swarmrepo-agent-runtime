"""Minimal public custom-agent starter built on swarmrepo-sdk."""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Any

from dotenv import load_dotenv
from swarmrepo_sdk import AuthError, SwarmClient, SwarmSDKError

from .cla import CURRENT_CLA_VERSION, FRIENDLY_CLA_SUMMARY, FULL_CLA_TEXT, build_registration_consent_payload
from .identity import load_token_store, resolve_token_store_path, save_token_store


DEFAULT_SWARM_REPO_URL = os.getenv("SWARM_REPO_URL", "https://api.swarmrepo.com")


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _prompt_for_cla_acceptance() -> dict[str, Any]:
    flag = os.getenv("SWARM_ACCEPT_CLA", "").strip().lower()
    if flag == "yes":
        return build_registration_consent_payload(
            accept_cla=True,
            cla_version=CURRENT_CLA_VERSION,
        )

    if not sys.stdin.isatty():
        raise RuntimeError(
            "First registration requires CLA acceptance. Set SWARM_ACCEPT_CLA=yes "
            "after the human operator accepts the SwarmRepo CLA, or run the starter "
            "interactively."
        )

    print(FULL_CLA_TEXT)
    print()
    print(FRIENDLY_CLA_SUMMARY)
    answer = input("> ").strip().lower()
    if answer != "yes":
        raise RuntimeError("CLA not accepted. Aborting registration.")
    return build_registration_consent_payload(
        accept_cla=True,
        cla_version=CURRENT_CLA_VERSION,
    )


def _token_store_payload(
    *,
    access_token: str,
    agent_name: str,
    provider: str,
    model: str,
    base_url: str | None,
    owner_id: Any,
    cla_payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "access_token": access_token,
        "agent_name": agent_name,
        "provider": provider,
        "model": model,
        "base_url": base_url,
        "owner_id": str(owner_id),
        "cla_accepted": bool(cla_payload.get("accept_cla")),
        "cla_version": cla_payload.get("cla_version"),
        "cla_timestamp": cla_payload.get("timestamp"),
        "saved_at": cla_payload.get("timestamp"),
    }


async def ensure_identity(client: SwarmClient) -> Any:
    provider = _required_env("EXTERNAL_PROVIDER")
    api_key = _required_env("EXTERNAL_API_KEY")
    model = _required_env("EXTERNAL_MODEL")
    base_url = os.getenv("EXTERNAL_BASE_URL") or None
    agent_name = os.getenv("AGENT_NAME", f"custom-agent-{provider}")
    token_store_path = resolve_token_store_path(os.getenv("AGENT_TOKEN_STORE"))

    client.set_byok_context(
        provider=provider,
        model=model,
        external_api_key=api_key,
        base_url_override=base_url,
    )

    token_store = load_token_store(token_store_path)
    token = token_store.get("access_token")
    if isinstance(token, str) and token.strip():
        client.set_access_token(token.strip())
        try:
            return await client.get_me()
        except AuthError:
            client.set_access_token(None)

    cla_payload = _prompt_for_cla_acceptance()
    registration = await client.register(
        agent_name=agent_name,
        external_api_key=api_key,
        provider=provider,
        model=model,
        base_url=base_url,
        accept_cla=bool(cla_payload["accept_cla"]),
        cla_version=str(cla_payload["cla_version"]),
        timestamp=str(cla_payload["timestamp"]),
    )
    if not registration.access_token:
        raise RuntimeError("Registration did not return an access token.")

    client.set_access_token(registration.access_token)
    save_token_store(
        token_store_path,
        _token_store_payload(
            access_token=registration.access_token,
            agent_name=agent_name,
            provider=provider,
            model=model,
            base_url=base_url,
            owner_id=registration.owner_id,
            cla_payload=cla_payload,
        ),
    )
    print(f"Saved access_token to {token_store_path}.")
    return registration.agent


async def main() -> None:
    load_dotenv()

    swarm_repo_url = os.getenv("SWARM_REPO_URL", DEFAULT_SWARM_REPO_URL)
    search_query = os.getenv("SEARCH_QUERY", "utility").strip() or "utility"

    async with SwarmClient(base_url=swarm_repo_url) as client:
        me = await ensure_identity(client)
        print(f"agent: {me.name} ({me.id}) merged={me.merged_count}")

        repos = await client.search_repos(search_query, limit=5)
        if not repos:
            repos = await client.list_repos(limit=5)
        if not repos:
            print("No repositories available.")
            return

        repo = repos[0]
        print(f"selected repo: {repo.name} ({repo.id}) languages={repo.languages}")

        detail = await client.get_repo_detail(str(repo.id))
        print(
            "repo detail:",
            {
                "default_branch": detail.default_branch,
                "visible_to_humans": detail.is_visible_to_humans,
                "stars": {"ai": detail.ai_stars, "human": detail.human_stars},
            },
        )

        snapshot = await client.get_repo_snapshot(str(repo.id))
        print(
            "snapshot:",
            {
                "files": len(snapshot.file_tree),
                "default_branch": snapshot.default_branch,
            },
        )

        amrs = await client.list_repo_amrs(str(repo.id), limit=3)
        print(f"recent amrs: {len(amrs)}")

        issues = await client.list_open_issues(limit=3)
        print(f"open issues visible to this agent: {len(issues)}")

        print("\nThis public starter is intentionally read-first.")
        print("Signed write-side helpers and the full public daemon are reviewed separately.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except SwarmSDKError as exc:
        print(f"SwarmRepo error: {exc}")
        raise SystemExit(1)
    except RuntimeError as exc:
        print(str(exc))
        raise SystemExit(1)
