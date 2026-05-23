"""
Centralised LLM inference client — the sole gateway for all agent LLM calls.

Routes requests through OpenRouter (free-tier Nemotron models) with automatic
fallback to Anthropic on any failure. Agents must never call LLM SDKs directly.
"""

import json
import logging
import os
import re
from typing import Literal

import anthropic
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

CallType = Literal["orchestrator", "sentiment"]

_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

MODEL_MAP: dict[str, dict[str, str]] = {
    "orchestrator": {
        "openrouter": "nvidia/nemotron-3-super-120b-a12b:free",
        "anthropic": "claude-sonnet-4-6",
    },
    "sentiment": {
        "openrouter": "nvidia/llama-3.3-nemotron-super-49b-v1:free",
        "anthropic": "claude-haiku-4-5-20251001",
    },
}


class InferenceError(Exception):
    """Raised when both OpenRouter and Anthropic providers fail."""


class InferenceClient:
    """Unified LLM client with OpenRouter primary + Anthropic fallback."""

    def __init__(
        self,
        openrouter_client: AsyncOpenAI | None = None,
        anthropic_client: anthropic.AsyncAnthropic | None = None,
    ):
        self._or_key = os.getenv("OPENROUTER_API_KEY", "")
        self._anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")

        frontend_url = os.getenv(
            "FRONTEND_URL", "https://hawker-hunt.vercel.app"
        )
        self._or_headers = {
            "HTTP-Referer": frontend_url,
            "X-Title": "Hawker Hunt",
        }

        # Allow test injection; otherwise build from env
        self._openrouter = openrouter_client
        if self._openrouter is None and self._or_key:
            self._openrouter = AsyncOpenAI(
                base_url=_OPENROUTER_BASE_URL,
                api_key=self._or_key,
                default_headers=self._or_headers,
            )

        self._anthropic = anthropic_client
        if self._anthropic is None:
            self._anthropic = anthropic.AsyncAnthropic()

    # ── Public API ───────────────────────────────────────────────────────

    async def complete(
        self,
        call_type: CallType,
        system: str,
        user_content: str,
        max_tokens: int = 256,
    ) -> str:
        """Try OpenRouter first, fall back to Anthropic. Returns raw text."""
        models = MODEL_MAP[call_type]

        # --- Primary: OpenRouter ---
        if self._openrouter is not None:
            try:
                raw = await self._call_openrouter(
                    model=models["openrouter"],
                    system=system,
                    user_content=user_content,
                    max_tokens=max_tokens,
                )
                return _clean_response(raw)
            except Exception as exc:
                logger.warning(
                    "OpenRouter %s failed (%s: %s) — falling back to Anthropic",
                    call_type,
                    type(exc).__name__,
                    exc,
                )

        # --- Fallback: Anthropic ---
        try:
            return await self._call_anthropic(
                model=models["anthropic"],
                system=system,
                user_content=user_content,
                max_tokens=max_tokens,
            )
        except Exception as exc:
            raise InferenceError(
                f"Both providers failed for {call_type}. "
                f"Anthropic error: {type(exc).__name__}: {exc}"
            ) from exc

    @property
    def active_provider(self) -> str:
        """Which provider will be tried first."""
        return "openrouter" if self._openrouter is not None else "anthropic"

    @property
    def openrouter_configured(self) -> bool:
        return bool(self._or_key)

    @property
    def anthropic_configured(self) -> bool:
        return bool(self._anthropic_key)

    # ── Private helpers ──────────────────────────────────────────────────

    async def _call_openrouter(
        self,
        model: str,
        system: str,
        user_content: str,
        max_tokens: int,
    ) -> str:
        response = await self._openrouter.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_content},
            ],
        )
        return response.choices[0].message.content or ""

    async def _call_anthropic(
        self,
        model: str,
        system: str,
        user_content: str,
        max_tokens: int,
    ) -> str:
        response = await self._anthropic.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user_content}],
        )
        return response.content[0].text.strip()


# ── Response cleaning (module-level, stateless) ─────────────────────────

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)
_JSON_OBJECT_RE = re.compile(r"\{[^{}]*\}")


def _clean_response(raw: str) -> str:
    """Strip Nemotron <think> blocks and extract JSON if needed."""
    cleaned = _THINK_RE.sub("", raw).strip()

    # If it already parses as JSON, return it
    try:
        json.loads(cleaned)
        return cleaned
    except (json.JSONDecodeError, ValueError):
        pass

    # Try extracting the first {...} block
    match = _JSON_OBJECT_RE.search(cleaned)
    if match:
        return match.group(0)

    # Return as-is — caller's json.loads will fail and use defaults
    return cleaned
