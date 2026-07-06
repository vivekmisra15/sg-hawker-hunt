"""Integration tests for the POST /api/search SSE endpoint.

These tests exercise the full FastAPI route including SSE serialization,
but mock all sub-agents to avoid live API calls.

Uses pytest monkeypatch for safe orchestrator swapping — the original is always
restored even if assertions fail.
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

from models.schemas import (
    LocationResult, HygieneResult, RankedRecommendation, AgentEvent,
)


def _mock_inference_client():
    """Return a mock InferenceClient whose complete() returns a valid query parse."""
    mock = MagicMock()
    mock.complete = AsyncMock(return_value=json.dumps({
        "cuisine_type": "chicken rice",
        "location_hint": "Maxwell",
        "dietary": [],
        "avoid": [],
        "budget": "any",
        "time_context": "any",
    }))
    return mock


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


@pytest.fixture
def mocked_app(monkeypatch):
    """Yield a TestClient with the module-level orchestrator safely monkeypatched."""
    from agents.orchestrator import OrchestratorAgent
    import main

    mocked_orchestrator = OrchestratorAgent(
        location_agent=_mock_location_agent(),
        hygiene_agent=_mock_hygiene_agent(),
        recommendation_agent=_mock_recommendation_agent(),
        inference_client=_mock_inference_client(),
    )
    monkeypatch.setattr(main, "orchestrator", mocked_orchestrator)
    return TestClient(main.app)


def test_search_endpoint_returns_sse_events(mocked_app):
    """POST /api/search should return SSE events with agent_update and result types."""
    response = mocked_app.post(
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


def test_search_endpoint_validates_request_body(mocked_app):
    """POST /api/search with empty body should return 422."""
    response = mocked_app.post("/api/search", json={})
    assert response.status_code == 422


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


def test_second_search_request_returns_complete_results(monkeypatch):
    """A second SSE request verifies the orchestrator returns complete results
    independently on each call. Resets sse_starlette's global AppStatus event
    between requests to avoid event-loop binding conflicts.
    """
    from agents.orchestrator import OrchestratorAgent
    from sse_starlette.sse import AppStatus
    import asyncio
    import main

    mocked_orchestrator = OrchestratorAgent(
        location_agent=_mock_location_agent(),
        hygiene_agent=_mock_hygiene_agent(),
        recommendation_agent=_mock_recommendation_agent(),
        inference_client=_mock_inference_client(),
    )
    monkeypatch.setattr(main, "orchestrator", mocked_orchestrator)

    for i, query in enumerate(["chicken rice", "laksa near me"]):
        # Reset the global SSE exit event to avoid event-loop binding errors
        AppStatus.should_exit_event = asyncio.Event()

        client = TestClient(main.app)
        response = client.post(
            "/api/search",
            json={"query": query, "lat": 1.2805, "lng": 103.8446},
        )
        assert response.status_code == 200, f"Request {i} failed"

        events = []
        for line in response.text.strip().split("\n"):
            if line.startswith("data:"):
                data_str = line[len("data:"):].strip()
                if data_str:
                    events.append(json.loads(data_str))

        types = [e.get("type") for e in events]
        assert "agent_update" in types, f"Request {i}: expected agent_update in {types}"
        assert "result" in types, f"Request {i}: expected result in {types}"

        result_events = [e for e in events if e.get("type") == "result"]
        recs = result_events[0].get("data", {}).get("recommendations", [])
        assert len(recs) >= 1, f"Request {i}: no recommendations"
