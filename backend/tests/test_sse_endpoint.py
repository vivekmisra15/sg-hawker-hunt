"""Integration tests for the POST /api/search SSE endpoint.

These tests exercise the full FastAPI route including SSE serialization,
but mock all sub-agents to avoid live API calls.
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from models.schemas import (
    LocationResult, HygieneResult, RankedRecommendation, AgentEvent,
)


def _mock_anthropic_client():
    """Return a mock AsyncAnthropic that returns a valid query parse."""
    content_block = MagicMock()
    content_block.text = json.dumps({
        "cuisine_type": "chicken rice",
        "location_hint": "Maxwell",
        "dietary": [],
        "avoid": [],
        "budget": "any",
        "time_context": "any",
    })
    mock_response = MagicMock()
    mock_response.content = [content_block]
    mock_messages = MagicMock()
    mock_messages.create = AsyncMock(return_value=mock_response)
    mock_client = MagicMock()
    mock_client.messages = mock_messages
    return mock_client


def _mock_location_agent():
    mock = MagicMock()
    mock.run = AsyncMock(return_value=[
        LocationResult(
            centre_name="Maxwell Food Centre",
            address="1 Kadayanallur St",
            lat=1.2805, lng=103.8446,
            distance_km=0.5, is_open=True,
            crowd_level="quiet",
        )
    ])
    return mock


def _mock_hygiene_agent():
    mock = MagicMock()
    mock.run = AsyncMock(return_value=[
        HygieneResult(
            stall_name="Maxwell Food Centre",
            centre_name="Maxwell Food Centre",
            grade="A", demerit_points=0, suspended=False,
            reasoning_trace="Grade A, open today.",
        )
    ])
    return mock


def _mock_recommendation_agent():
    mock = MagicMock()
    mock.run = AsyncMock(return_value=[
        RankedRecommendation(
            stall_name="Tian Tian Chicken Rice",
            centre_name="Maxwell Food Centre",
            rank=1,
            reasoning="Top pick.",
            hygiene_grade="A",
            is_michelin=True,
            is_halal=False,
            is_open=True,
            distance_km=0.5,
            score=9.5,
            lat=1.2805,
            lng=103.8446,
        )
    ])
    return mock


def _get_test_client():
    """Create a TestClient with fully mocked orchestrator."""
    from agents.orchestrator import OrchestratorAgent
    import main

    # Replace the module-level orchestrator with a fully mocked one
    mocked_orchestrator = OrchestratorAgent(
        location_agent=_mock_location_agent(),
        hygiene_agent=_mock_hygiene_agent(),
        recommendation_agent=_mock_recommendation_agent(),
        anthropic_client=_mock_anthropic_client(),
    )
    original = main.orchestrator
    main.orchestrator = mocked_orchestrator
    client = TestClient(main.app)
    return client, original


def test_search_endpoint_returns_sse_events():
    """POST /api/search should return SSE events with agent_update and result types."""
    client, original_orchestrator = _get_test_client()
    try:
        response = client.post(
            "/api/search",
            json={"query": "chicken rice near Maxwell", "lat": 1.2805, "lng": 103.8446},
        )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

        # Parse SSE events from the response body
        body = response.text
        events = []
        for line in body.strip().split("\n"):
            if line.startswith("data:"):
                data_str = line[len("data:"):].strip()
                if data_str:
                    events.append(json.loads(data_str))

        # Should have at least one agent_update and one result event
        types = [e.get("type") for e in events]
        assert "agent_update" in types, f"Expected agent_update in {types}"
        assert "result" in types, f"Expected result in {types}"

        # The result event should contain recommendations
        result_events = [e for e in events if e.get("type") == "result"]
        assert len(result_events) >= 1
        result_data = result_events[0].get("data", {})
        recs = result_data.get("recommendations", [])
        assert len(recs) >= 1
        assert recs[0]["stall_name"] == "Tian Tian Chicken Rice"
    finally:
        import main
        main.orchestrator = original_orchestrator


def test_search_endpoint_validates_request_body():
    """POST /api/search with empty body should return 422."""
    client, original_orchestrator = _get_test_client()
    try:
        response = client.post("/api/search", json={})
        assert response.status_code == 422
    finally:
        import main
        main.orchestrator = original_orchestrator


def test_health_endpoint():
    """GET /api/health should return status ok."""
    import main
    client = TestClient(main.app)
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "agents" in data
    assert len(data["agents"]) == 4
