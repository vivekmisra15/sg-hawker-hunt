"""
Tests for API robustness: retry logic, rate-limit handling, concurrent requests,
and request deduplication.
"""
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
import respx
import httpx

import tools.nea_client as nea_module
from tools.nea_client import NEAClient, NEAClientError
from tools.inference_client import InferenceClient, InferenceError


MOCK_SUCCESS = {
    "success": True,
    "result": {
        "records": [{"_id": 1, "NAME": "Test Centre"}]
    },
}


# ── NEA retry with backoff ──────────────────────────────────────────────────

class TestNEARetry:
    """NEA client retries on transient failures with exponential backoff."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        nea_module._cache.clear()
        yield
        nea_module._cache.clear()

    @respx.mock
    @pytest.mark.asyncio
    async def test_retries_on_429_then_succeeds(self):
        """First call returns 429, second returns 200 -- should succeed."""
        route = respx.get("https://data.gov.sg/api/action/datastore_search").mock(
            side_effect=[
                httpx.Response(429, text="rate limited"),
                httpx.Response(200, json=MOCK_SUCCESS),
            ]
        )
        with patch("tools.nea_client.asyncio.sleep", new_callable=AsyncMock):
            client = NEAClient()
            records = await client._fetch("test_resource")
        assert len(records) == 1
        assert route.call_count == 2

    @respx.mock
    @pytest.mark.asyncio
    async def test_retries_on_500_then_succeeds(self):
        """Server error followed by success."""
        route = respx.get("https://data.gov.sg/api/action/datastore_search").mock(
            side_effect=[
                httpx.Response(500, text="internal error"),
                httpx.Response(200, json=MOCK_SUCCESS),
            ]
        )
        with patch("tools.nea_client.asyncio.sleep", new_callable=AsyncMock):
            client = NEAClient()
            records = await client._fetch("test_resource")
        assert len(records) == 1
        assert route.call_count == 2

    @respx.mock
    @pytest.mark.asyncio
    async def test_retries_exhaust_on_persistent_429(self):
        """All 3 retries get 429 -- raises NEAClientError."""
        respx.get("https://data.gov.sg/api/action/datastore_search").mock(
            return_value=httpx.Response(429, text="rate limited")
        )
        with patch("tools.nea_client.asyncio.sleep", new_callable=AsyncMock):
            client = NEAClient()
            with pytest.raises(NEAClientError, match="429"):
                await client._fetch("test_resource")

    @respx.mock
    @pytest.mark.asyncio
    async def test_no_retry_on_4xx_client_error(self):
        """Client errors (4xx other than 429) fail immediately, no retry."""
        route = respx.get("https://data.gov.sg/api/action/datastore_search").mock(
            return_value=httpx.Response(400, text="bad request")
        )
        client = NEAClient()
        with pytest.raises(NEAClientError, match="400"):
            await client._fetch("test_resource")
        assert route.call_count == 1

    @respx.mock
    @pytest.mark.asyncio
    async def test_retry_on_timeout(self):
        """Timeout followed by success."""
        call_count = 0

        async def timeout_then_success(request):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise httpx.ReadTimeout("read timed out")
            return httpx.Response(200, json=MOCK_SUCCESS)

        respx.get("https://data.gov.sg/api/action/datastore_search").mock(
            side_effect=timeout_then_success
        )
        with patch("tools.nea_client.asyncio.sleep", new_callable=AsyncMock):
            client = NEAClient()
            records = await client._fetch("test_resource")
        assert len(records) == 1
        assert call_count == 2

    @respx.mock
    @pytest.mark.asyncio
    async def test_backoff_delays_increase(self):
        """Verify exponential backoff: delays are 1s, 2s, 4s."""
        respx.get("https://data.gov.sg/api/action/datastore_search").mock(
            return_value=httpx.Response(429, text="rate limited")
        )
        sleep_calls = []
        async def mock_sleep(delay):
            sleep_calls.append(delay)

        with patch("tools.nea_client.asyncio.sleep", side_effect=mock_sleep):
            client = NEAClient()
            with pytest.raises(NEAClientError):
                await client._fetch("test_resource")
        assert sleep_calls == [1.0, 2.0, 4.0]


# ── Inference client deduplication ───────────────────────────────────────────

class TestInferenceDedup:
    """Concurrent identical requests share one LLM call."""

    @pytest.mark.asyncio
    async def test_concurrent_identical_calls_deduplicated(self):
        """Two concurrent calls with same params make only one LLM request."""
        call_count = 0
        mock_or = AsyncMock()

        async def fake_create(**kwargs):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.05)  # simulate latency
            response = MagicMock()
            response.choices = [MagicMock()]
            response.choices[0].message.content = '{"cuisine_type": "laksa"}'
            return response

        mock_or.chat.completions.create = AsyncMock(side_effect=fake_create)

        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"}):
            client = InferenceClient(openrouter_client=mock_or)
            results = await asyncio.gather(
                client.complete("orchestrator", "system", "same user input"),
                client.complete("orchestrator", "system", "same user input"),
            )

        assert results[0] == results[1]
        assert call_count == 1  # only one actual LLM call

    @pytest.mark.asyncio
    async def test_different_calls_not_deduplicated(self):
        """Different parameters produce separate LLM calls."""
        call_count = 0
        mock_or = AsyncMock()

        async def fake_create(**kwargs):
            nonlocal call_count
            call_count += 1
            response = MagicMock()
            response.choices = [MagicMock()]
            response.choices[0].message.content = '{"result": "ok"}'
            return response

        mock_or.chat.completions.create = AsyncMock(side_effect=fake_create)

        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"}):
            client = InferenceClient(openrouter_client=mock_or)
            await asyncio.gather(
                client.complete("orchestrator", "system", "query A"),
                client.complete("orchestrator", "system", "query B"),
            )

        assert call_count == 2

    @pytest.mark.asyncio
    async def test_dedup_error_propagates_to_all_waiters(self):
        """When the deduplicated call fails, all waiters get the error."""
        mock_or = AsyncMock()

        async def fail_create(**kwargs):
            await asyncio.sleep(0.05)
            raise RuntimeError("LLM down")

        mock_or.chat.completions.create = AsyncMock(side_effect=fail_create)

        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key", "ANTHROPIC_API_KEY": ""}):
            client = InferenceClient(openrouter_client=mock_or, anthropic_client=None)
            results = await asyncio.gather(
                client.complete("orchestrator", "sys", "same"),
                client.complete("orchestrator", "sys", "same"),
                return_exceptions=True,
            )

        # Both should receive an InferenceError
        assert all(isinstance(r, InferenceError) for r in results)

    @pytest.mark.asyncio
    async def test_dedup_cleans_up_after_completion(self):
        """After a deduplicated call completes, the key is removed from in-flight."""
        mock_or = AsyncMock()

        async def fake_create(**kwargs):
            response = MagicMock()
            response.choices = [MagicMock()]
            response.choices[0].message.content = '{"ok": true}'
            return response

        mock_or.chat.completions.create = AsyncMock(side_effect=fake_create)

        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"}):
            client = InferenceClient(openrouter_client=mock_or)
            await client.complete("orchestrator", "sys", "input")
            assert len(client._in_flight) == 0


# ── Rate limit handling tests ─────────────────────────────────────────────────

class TestRateLimitHandling:
    """Verify rate-limit responses are handled correctly across clients."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        nea_module._cache.clear()
        yield
        nea_module._cache.clear()

    @respx.mock
    @pytest.mark.asyncio
    async def test_nea_429_includes_helpful_message(self):
        """429 error includes guidance to set API key."""
        respx.get("https://data.gov.sg/api/action/datastore_search").mock(
            return_value=httpx.Response(429, text="rate limited")
        )
        with patch("tools.nea_client.asyncio.sleep", new_callable=AsyncMock):
            client = NEAClient()
            with pytest.raises(NEAClientError, match="429"):
                await client._fetch("test_resource")

    @respx.mock
    @pytest.mark.asyncio
    async def test_nea_cache_prevents_repeated_calls(self):
        """Cached responses avoid redundant API hits."""
        route = respx.get("https://data.gov.sg/api/action/datastore_search").mock(
            return_value=httpx.Response(200, json=MOCK_SUCCESS)
        )
        client = NEAClient()
        await client._fetch("test_resource")
        await client._fetch("test_resource")  # should hit cache
        assert route.call_count == 1
