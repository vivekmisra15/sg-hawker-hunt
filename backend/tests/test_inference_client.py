"""Tests for the centralised InferenceClient — OpenRouter + Anthropic fallback."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tools.inference_client import InferenceClient, InferenceError, _clean_response, MODEL_MAP


# ── Helpers ──────────────────────────────────────────────────────────────


def _mock_openrouter(response_text: str):
    """Return a mock AsyncOpenAI whose chat.completions.create returns response_text."""
    choice = MagicMock()
    choice.message.content = response_text
    mock_response = MagicMock()
    mock_response.choices = [choice]
    client = MagicMock()
    client.chat.completions.create = AsyncMock(return_value=mock_response)
    return client


def _mock_anthropic(response_text: str):
    """Return a mock AsyncAnthropic whose messages.create returns response_text."""
    content_block = MagicMock()
    content_block.text = response_text
    mock_response = MagicMock()
    mock_response.content = [content_block]
    client = MagicMock()
    client.messages.create = AsyncMock(return_value=mock_response)
    return client


# ── OpenRouter success path ──────────────────────────────────────────────


async def test_openrouter_success_returns_cleaned_json():
    """When OpenRouter succeeds, Anthropic is never called."""
    or_client = _mock_openrouter('{"cuisine_type": "laksa"}')
    anth_client = _mock_anthropic('{"cuisine_type": "fallback"}')

    ic = InferenceClient(openrouter_client=or_client, anthropic_client=anth_client)
    result = await ic.complete("orchestrator", "system", "laksa near me")

    assert '"laksa"' in result
    or_client.chat.completions.create.assert_awaited_once()
    anth_client.messages.create.assert_not_awaited()


# ── Nemotron response cleaning ───────────────────────────────────────────


def test_clean_response_strips_think_tags():
    raw = '<think>Let me reason about this...</think>{"score": 0.8}'
    assert _clean_response(raw) == '{"score": 0.8}'


def test_clean_response_strips_multiline_think_tags():
    raw = '<think>\nStep 1: think\nStep 2: more\n</think>\n{"score": 0.8}'
    assert _clean_response(raw) == '{"score": 0.8}'


def test_clean_response_extracts_json_from_surrounding_text():
    raw = 'Here is the result: {"key": "val"} hope this helps!'
    assert _clean_response(raw) == '{"key": "val"}'


def test_clean_response_extracts_multiline_nested_json():
    raw = 'Here is the parsed query:\n{\n  "cuisine_type": "laksa",\n  "dietary": ["halal"]\n}\nHope this helps!'
    result = _clean_response(raw)
    parsed = json.loads(result)
    assert parsed["cuisine_type"] == "laksa"
    assert parsed["dietary"] == ["halal"]


def test_clean_response_returns_valid_json_unchanged():
    raw = '{"cuisine_type": "chicken rice", "budget": "cheap"}'
    assert _clean_response(raw) == raw


def test_clean_response_returns_raw_on_no_json():
    raw = "I cannot help with that request."
    assert _clean_response(raw) == raw


# ── Fallback: missing OpenRouter key ─────────────────────────────────────


async def test_fallback_when_openrouter_not_configured():
    """When no OpenRouter client, go straight to Anthropic."""
    anth_client = _mock_anthropic('{"cuisine_type": "nasi lemak"}')

    ic = InferenceClient(openrouter_client=None, anthropic_client=anth_client)
    result = await ic.complete("sentiment", "system", "reviews text")

    assert '"nasi lemak"' in result
    anth_client.messages.create.assert_awaited_once()


# ── Fallback: 429 rate limit ─────────────────────────────────────────────


async def test_fallback_on_429_rate_limit():
    or_client = MagicMock()
    or_client.chat.completions.create = AsyncMock(
        side_effect=Exception("Error code: 429 - Rate limit exceeded")
    )
    anth_client = _mock_anthropic('{"fallback": true}')

    ic = InferenceClient(openrouter_client=or_client, anthropic_client=anth_client)
    result = await ic.complete("orchestrator", "system", "query")

    assert '"fallback"' in result
    anth_client.messages.create.assert_awaited_once()


# ── Fallback: 5xx server error ───────────────────────────────────────────


async def test_fallback_on_500_server_error():
    or_client = MagicMock()
    or_client.chat.completions.create = AsyncMock(
        side_effect=Exception("Error code: 500 - Internal server error")
    )
    anth_client = _mock_anthropic('{"fallback": true}')

    ic = InferenceClient(openrouter_client=or_client, anthropic_client=anth_client)
    result = await ic.complete("sentiment", "system", "query")

    assert '"fallback"' in result


# ── Fallback: generic exception ──────────────────────────────────────────


async def test_fallback_on_generic_exception():
    or_client = MagicMock()
    or_client.chat.completions.create = AsyncMock(
        side_effect=RuntimeError("Connection reset")
    )
    anth_client = _mock_anthropic('{"ok": true}')

    ic = InferenceClient(openrouter_client=or_client, anthropic_client=anth_client)
    result = await ic.complete("orchestrator", "system", "query")

    assert '"ok"' in result


# ── Both providers fail ──────────────────────────────────────────────────


async def test_both_providers_fail_raises_inference_error():
    or_client = MagicMock()
    or_client.chat.completions.create = AsyncMock(
        side_effect=RuntimeError("OpenRouter down")
    )
    anth_client = MagicMock()
    anth_client.messages.create = AsyncMock(
        side_effect=RuntimeError("Anthropic down")
    )

    ic = InferenceClient(openrouter_client=or_client, anthropic_client=anth_client)
    with pytest.raises(InferenceError, match="Both providers failed"):
        await ic.complete("orchestrator", "system", "query")


# ── Correct model routing ────────────────────────────────────────────────


async def test_orchestrator_uses_correct_openrouter_model():
    or_client = _mock_openrouter('{"result": true}')
    anth_client = _mock_anthropic('{}')

    ic = InferenceClient(openrouter_client=or_client, anthropic_client=anth_client)
    await ic.complete("orchestrator", "system", "query")

    call_kwargs = or_client.chat.completions.create.call_args
    assert call_kwargs.kwargs["model"] == MODEL_MAP["orchestrator"]["openrouter"]


async def test_sentiment_uses_correct_openrouter_model():
    or_client = _mock_openrouter('{"score": 0.5}')
    anth_client = _mock_anthropic('{}')

    ic = InferenceClient(openrouter_client=or_client, anthropic_client=anth_client)
    await ic.complete("sentiment", "system", "reviews")

    call_kwargs = or_client.chat.completions.create.call_args
    assert call_kwargs.kwargs["model"] == MODEL_MAP["sentiment"]["openrouter"]


async def test_fallback_uses_correct_anthropic_model():
    """When OpenRouter fails, fallback uses the right Anthropic model."""
    or_client = MagicMock()
    or_client.chat.completions.create = AsyncMock(side_effect=RuntimeError("fail"))
    anth_client = _mock_anthropic('{"ok": true}')

    ic = InferenceClient(openrouter_client=or_client, anthropic_client=anth_client)
    await ic.complete("sentiment", "system", "reviews")

    call_kwargs = anth_client.messages.create.call_args
    assert call_kwargs.kwargs["model"] == MODEL_MAP["sentiment"]["anthropic"]


# ── Properties ───────────────────────────────────────────────────────────


def test_active_provider_openrouter_when_configured():
    ic = InferenceClient(
        openrouter_client=MagicMock(), anthropic_client=MagicMock()
    )
    assert ic.active_provider == "openrouter"


def test_active_provider_anthropic_when_no_openrouter():
    ic = InferenceClient(openrouter_client=None, anthropic_client=MagicMock())
    assert ic.active_provider == "anthropic"


# ── Timeout tests ───────────────────────────────────────────────────────


async def test_openrouter_timeout_falls_back_to_anthropic():
    """When OpenRouter hangs past the timeout, Anthropic fallback is used."""
    import asyncio

    async def hang_forever(**kwargs):
        await asyncio.sleep(999)

    or_client = MagicMock()
    or_client.chat.completions.create = AsyncMock(side_effect=hang_forever)
    anth_client = _mock_anthropic('{"fallback": true}')

    ic = InferenceClient(openrouter_client=or_client, anthropic_client=anth_client)

    # Temporarily reduce timeout for test speed
    import tools.inference_client as ic_mod
    original_timeout = ic_mod._REQUEST_TIMEOUT_SECONDS
    ic_mod._REQUEST_TIMEOUT_SECONDS = 0.1
    try:
        result = await ic.complete("orchestrator", "system", "query")
        assert '"fallback"' in result
        anth_client.messages.create.assert_awaited_once()
    finally:
        ic_mod._REQUEST_TIMEOUT_SECONDS = original_timeout


async def test_both_providers_timeout_raises_inference_error():
    """When both providers hang, InferenceError is raised with timeout message."""
    import asyncio

    async def hang_forever(**kwargs):
        await asyncio.sleep(999)

    or_client = MagicMock()
    or_client.chat.completions.create = AsyncMock(side_effect=hang_forever)
    anth_client = MagicMock()
    anth_client.messages.create = AsyncMock(side_effect=hang_forever)

    ic = InferenceClient(openrouter_client=or_client, anthropic_client=anth_client)

    import tools.inference_client as ic_mod
    original_timeout = ic_mod._REQUEST_TIMEOUT_SECONDS
    ic_mod._REQUEST_TIMEOUT_SECONDS = 0.1
    try:
        with pytest.raises(InferenceError, match="timed out"):
            await ic.complete("orchestrator", "system", "query")
    finally:
        ic_mod._REQUEST_TIMEOUT_SECONDS = original_timeout


# ── Anthropic key guard tests ───────────────────────────────────────────


async def test_no_anthropic_key_raises_clear_error_when_openrouter_fails():
    """When OpenRouter fails and Anthropic is not configured, error message is clear."""
    or_client = MagicMock()
    or_client.chat.completions.create = AsyncMock(
        side_effect=RuntimeError("OpenRouter down")
    )

    # Anthropic client is None (not configured)
    ic = InferenceClient(openrouter_client=or_client, anthropic_client=None)
    # Force _anthropic to None (bypassing env var init)
    ic._anthropic = None

    with pytest.raises(InferenceError, match="ANTHROPIC_API_KEY missing"):
        await ic.complete("orchestrator", "system", "query")
