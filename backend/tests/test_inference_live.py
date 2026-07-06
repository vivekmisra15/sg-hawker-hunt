"""
Live API tests for InferenceClient — hits real OpenRouter + Anthropic endpoints.

These tests are marked with @pytest.mark.live and are excluded from default runs.
Run explicitly with: pytest tests/test_inference_live.py -v -m live
"""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from dotenv import dotenv_values
from openai import AsyncOpenAI

from tools.inference_client import (
    InferenceClient,
    _clean_response,
    _OPENROUTER_BASE_URL,
)
from agents.orchestrator import _PARSE_SYSTEM
from agents.recommendation_agent import _SENTIMENT_SYSTEM

pytestmark = pytest.mark.live

# Read .env values without polluting os.environ
_env_path = Path(__file__).resolve().parents[2] / ".env"
_env_vars = dotenv_values(_env_path)


@pytest.fixture(autouse=True)
def _inject_env_vars():
    """Temporarily set API keys from .env for live tests only."""
    keys = {
        "OPENROUTER_API_KEY": _env_vars.get("OPENROUTER_API_KEY", ""),
        "ANTHROPIC_API_KEY": _env_vars.get("ANTHROPIC_API_KEY", ""),
    }
    with patch.dict(os.environ, keys):
        yield


# ── Test 1: OpenRouter orchestrator returns valid JSON ───────────────────


async def test_openrouter_orchestrator_returns_valid_json():
    """Real OpenRouter call for query parsing returns parseable JSON with expected keys."""
    client = InferenceClient()
    assert client.openrouter_configured, "OPENROUTER_API_KEY not set"

    result = await client.complete(
        "orchestrator",
        _PARSE_SYSTEM,
        "cheap laksa near Bugis, halal please",
        max_tokens=512,
    )

    try:
        parsed = json.loads(result)
    except json.JSONDecodeError:
        pytest.fail(f"OpenRouter returned non-JSON for orchestrator:\n{result!r}")

    assert "cuisine_type" in parsed, f"Missing cuisine_type in: {parsed}"
    assert "location_hint" in parsed, f"Missing location_hint in: {parsed}"
    assert "dietary" in parsed, f"Missing dietary in: {parsed}"
    assert "laksa" in parsed["cuisine_type"].lower(), f"Expected 'laksa' in cuisine_type: {parsed}"


# ── Test 2: OpenRouter sentiment returns valid JSON ──────────────────────


async def test_openrouter_sentiment_returns_valid_json():
    """Real OpenRouter call for sentiment analysis returns parseable JSON."""
    client = InferenceClient()
    assert client.openrouter_configured, "OPENROUTER_API_KEY not set"

    review_text = (
        "Shiok lah! The chicken rice here very ho jiak. "
        "Queue quite long but die die must try. Best in Toa Payoh sia."
    )
    # Nemotron nano emits <think> reasoning before JSON — needs higher token budget
    result = await client.complete(
        "sentiment", _SENTIMENT_SYSTEM, review_text, max_tokens=1024
    )

    try:
        parsed = json.loads(result)
    except json.JSONDecodeError:
        pytest.fail(f"OpenRouter returned non-JSON for sentiment:\n{result!r}")

    assert "sentiment_score" in parsed, f"Missing sentiment_score in: {parsed}"
    score = float(parsed["sentiment_score"])
    assert -1.0 <= score <= 1.0, f"Score out of range: {score}"
    assert score > 0, f"Expected positive sentiment for glowing review, got: {score}"


# ── Test 3: Think tag stripping on real response ─────────────────────────


async def test_think_tag_stripping_on_real_response():
    """Call OpenRouter directly and verify _clean_response strips <think> tags."""
    client = InferenceClient()
    assert client._openrouter is not None, "OpenRouter client not configured"

    raw = await client._call_openrouter(
        model="nvidia/nemotron-3-super-120b-a12b:free",
        system=_PARSE_SYSTEM,
        user_content="vegetarian food near Clementi",
        max_tokens=512,
    )

    cleaned = _clean_response(raw)
    assert "<think>" not in cleaned, f"<think> tag not stripped: {cleaned}"
    assert "</think>" not in cleaned, f"</think> tag not stripped: {cleaned}"

    # The cleaned result should be valid JSON (if not truncated)
    try:
        parsed = json.loads(cleaned)
        assert "cuisine_type" in parsed
    except json.JSONDecodeError:
        # Nemotron free-tier may still truncate — the key test is <think> stripping
        assert "{" in cleaned, f"No JSON structure found in cleaned response: {cleaned!r}"


# ── Test 4: Fallback to Anthropic on bad OpenRouter key ──────────────────


async def test_fallback_to_anthropic_on_bad_openrouter_key():
    """Invalid OpenRouter key triggers fallback to Anthropic, which succeeds."""
    bad_or_client = AsyncOpenAI(
        base_url=_OPENROUTER_BASE_URL,
        api_key="sk-or-v1-invalid-key-for-testing-00000000000000000",
        default_headers={"HTTP-Referer": "http://localhost", "X-Title": "Test"},
    )
    client = InferenceClient(openrouter_client=bad_or_client)

    result = await client.complete(
        "orchestrator",
        _PARSE_SYSTEM,
        "nasi lemak near Bedok",
    )

    parsed = json.loads(result)
    assert "cuisine_type" in parsed, f"Fallback result missing cuisine_type: {parsed}"


# ── Test 5: Health endpoint reports OpenRouter ───────────────────────────


async def test_health_endpoint_reports_openrouter():
    """FastAPI health endpoint correctly reports OpenRouter as active provider."""
    from httpx import ASGITransport, AsyncClient
    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["llm_provider"] == "openrouter"
    assert data["openrouter_configured"] is True
    assert data["anthropic_configured"] is True
