"""Shared local LLM helpers for SwarmRepo-compatible clients."""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any

import httpx

from .patch_utils import PatchValidationError, extract_json_payload

try:
    import google.genai as genai_new
except Exception:
    genai_new = None  # type: ignore[assignment]


DEFAULT_GEMINI_BASE_URL = os.getenv(
    "GEMINI_BASE_URL",
    "https://generativelanguage.googleapis.com/v1beta",
)
DEFAULT_OPENAI_BASE_URL = os.getenv(
    "OPENAI_BASE_URL",
    "https://api.openai.com/v1",
)


def render_prompt(messages: list[dict[str, str]]) -> str:
    """Render chat-style messages into a single text prompt."""
    parts: list[str] = []
    for msg in messages:
        role = msg.get("role", "user").upper()
        content = msg.get("content", "")
        parts.append(f"{role}:\n{content}")
    return "\n\n".join(parts)


async def call_openai_compatible(
    *,
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
    base_url: str,
    timeout_sec: int,
) -> str:
    """Call an OpenAI-compatible chat completion endpoint."""
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    async with httpx.AsyncClient(timeout=timeout_sec) as client:
        resp = await client.post(url, json=payload, headers=headers)
        if resp.status_code in {400, 422}:
            payload.pop("response_format", None)
            resp = await client.post(url, json=payload, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    choices = data.get("choices", [])
    message = choices[0].get("message", {}) if choices else {}
    content = message.get("content", "")
    if isinstance(content, list):
        content = "".join(
            str(part.get("text", "")) for part in content if isinstance(part, dict)
        )
    if not content:
        content = message.get("text", "") or data.get("output_text", "")
    return str(content).strip()


async def call_gemini(
    *,
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
    base_url: str | None,
    timeout_sec: int,
) -> str:
    """Call Gemini either through the SDK or through the public HTTP API."""
    if genai_new is not None and not base_url:
        prompt = render_prompt(messages)

        def _do_call() -> str:
            client = genai_new.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config={"response_mime_type": "application/json"},
            )
            return getattr(response, "text", "") or ""

        return await asyncio.to_thread(_do_call)

    root = (base_url or DEFAULT_GEMINI_BASE_URL).rstrip("/")
    url = f"{root}/models/{model}:generateContent?key={api_key}"
    prompt = render_prompt(messages)
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
        },
    }
    async with httpx.AsyncClient(timeout=timeout_sec) as client:
        resp = await client.post(url, json=payload)
    resp.raise_for_status()
    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


async def call_llm_json(
    *,
    provider: str,
    api_key: str,
    model: str,
    base_url: str | None,
    messages: list[dict[str, str]],
    timeout_sec: int,
    max_retries: int = 2,
    schema_hint: str = "",
) -> dict[str, Any]:
    """Request JSON from a local provider and retry when the reply is malformed."""
    attempt = 0
    last_error: str | None = None
    base_messages = [dict(msg) for msg in messages]
    current_messages = [dict(msg) for msg in base_messages]

    while attempt <= max_retries:
        attempt += 1
        try:
            if provider.lower() in {"gemini", "google"}:
                raw = await call_gemini(
                    api_key=api_key,
                    model=model,
                    messages=current_messages,
                    base_url=base_url,
                    timeout_sec=timeout_sec,
                )
            else:
                base = base_url or DEFAULT_OPENAI_BASE_URL
                raw = await call_openai_compatible(
                    api_key=api_key,
                    model=model,
                    messages=current_messages,
                    base_url=base,
                    timeout_sec=timeout_sec,
                )
            return extract_json_payload(raw)
        except (json.JSONDecodeError, PatchValidationError) as exc:
            last_error = str(exc)
            current_messages = [
                *base_messages,
                {
                    "role": "user",
                    "content": (
                        "Your previous reply was not valid JSON. Keep the same task "
                        "context and return ONLY one valid JSON object.\n\n"
                        f"{schema_hint or 'Return valid JSON only.'}"
                    ),
                },
            ]
        except Exception as exc:
            last_error = str(exc)
            if attempt > max_retries:
                break
    raise RuntimeError(f"LLM JSON parse failed: {last_error}")


__all__ = [
    "DEFAULT_GEMINI_BASE_URL",
    "DEFAULT_OPENAI_BASE_URL",
    "call_gemini",
    "call_llm_json",
    "call_openai_compatible",
    "render_prompt",
]
