"""
Centralised LLM inference client — the sole gateway for all agent LLM calls.

Routes requests through OpenRouter (free-tier Nemotron models) with automatic
fallback to Anthropic on any failure. Agents must never call LLM SDKs directly.
"""

import asyncio
import hashlib
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
_REQUEST_TIMEOUT_SECONDS = 30  # Per-provider timeout — prevents hanging SSE streams

MODEL_MAP: dict[str, dict[str, str]] = {
    "orchestrator": {
        "openrouter": "nvidia/nemotron-3-super-120b-a12b:free",
        "anthropic": "claude-sonnet-4-6",
    },
    "sentiment": {
        "openrouter": "nvidia/nemotron-3-nano-30b-a3b:free",
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
        if self._anthropic is None and self._anthropic_key:
            self._anthropic = anthropic.AsyncAnthropic()

        # Request deduplication: concurrent identical calls share one future
        self._in_flight: dict[str, asyncio.Future[str]] = {}

    # ── Public API ───────────────────────────────────────────────────────

    @staticmethod
    def _dedup_key(call_type: str, system: str, user_content: str) -> str:
        """Hash of call parameters for deduplication."""
        raw = f"{call_type}|{system}|{user_content}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    async def complete(
        self,
        call_type: CallType,
        system: str,
        user_content: str,
        max_tokens: int = 256,
    ) -> str:
        """Try OpenRouter first, fall back to Anthropic. Returns raw text.

        Concurrent identical calls are deduplicated: the first caller executes
        the request, all others await the same future.
        """
        key = self._dedup_key(call_type, system, user_content)

        # If an identical request is already in flight, await its result
        if key in self._in_flight:
            return await self._in_flight[key]

        # Create a future so other callers can attach
        loop = asyncio.get_event_loop()
        future: asyncio.Future[str] = loop.create_future()
        self._in_flight[key] = future

        try:
            result = await self._do_complete(call_type, system, user_content, max_tokens)
            future.set_result(result)
            return result
        except Exception as exc:
            future.set_exception(exc)
            raise
        finally:
            self._in_flight.pop(key, None)

    async def _do_complete(
        self,
        call_type: CallType,
        system: str,
        user_content: str,
        max_tokens: int = 256,
    ) -> str:
        """Internal: execute the actual LLM call with provider fallback."""
        models = MODEL_MAP[call_type]

        # --- Primary: OpenRouter ---
        if self._openrouter is not None:
            try:
                raw = await asyncio.wait_for(
                    self._call_openrouter(
                        model=models["openrouter"],
                        system=system,
                        user_content=user_content,
                        max_tokens=max_tokens,
                    ),
                    timeout=_REQUEST_TIMEOUT_SECONDS,
                )
                return _clean_response(raw)
            except asyncio.TimeoutError:
                logger.warning(
                    "OpenRouter %s timed out after %ds — falling back to Anthropic",
                    call_type,
                    _REQUEST_TIMEOUT_SECONDS,
                )
            except Exception as exc:
                logger.warning(
                    "OpenRouter %s failed (%s: %s) — falling back to Anthropic",
                    call_type,
                    type(exc).__name__,
                    exc,
                )

        # --- Fallback: Anthropic ---
        if self._anthropic is None:
            raise InferenceError(
                f"Both providers failed for {call_type}. "
                f"Anthropic not configured (ANTHROPIC_API_KEY missing)"
            )
        try:
            return await asyncio.wait_for(
                self._call_anthropic(
                    model=models["anthropic"],
                    system=system,
                    user_content=user_content,
                    max_tokens=max_tokens,
                ),
                timeout=_REQUEST_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError as exc:
            raise InferenceError(
                f"Both providers failed for {call_type}. "
                f"Anthropic timed out after {_REQUEST_TIMEOUT_SECONDS}s"
            ) from exc
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


def _extract_json_block(text: str) -> str | None:
    """Extract the first top-level {...} JSON block, handling nesting."""
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def _clean_response(raw: str) -> str:
    """Strip Nemotron <think> blocks and extract JSON if needed."""
    cleaned = _THINK_RE.sub("", raw).strip()

    # If it already parses as JSON, return it
    try:
        json.loads(cleaned)
        return cleaned
    except (json.JSONDecodeError, ValueError):
        pass

    # Try extracting the first {...} JSON block (handles nesting + multiline)
    block = _extract_json_block(cleaned)
    if block:
        return block

    # Return as-is — caller's json.loads will fail and use defaults
    return cleaned
