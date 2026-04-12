"""Tests for OrchestratorAgent."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from agents.orchestrator import OrchestratorAgent
from models.schemas import (
    SearchRequest, LocationResult, HygieneResult, RankedRecommendation
)

# ── fixtures / helpers ────────────────────────────────────────────────────────

def _mock_anthropic_client(response_json: str):
    """Returns a mock AsyncAnthropic whose messages.create returns response_json."""
    content_block = MagicMock()
    content_block.text = response_json
    mock_response = MagicMock()
    mock_response.content = [content_block]

    mock_messages = MagicMock()
    mock_messages.create = AsyncMock(return_value=mock_response)

    mock_client = MagicMock()
    mock_client.messages = mock_messages
    return mock_client


def _mock_location_agent(results=None):
    mock = MagicMock()
    mock.run = AsyncMock(return_value=results or [
        LocationResult(
            centre_name="Maxwell Food Centre",
            address="1 Kadayanallur St",
            lat=1.2805, lng=103.8446,
            distance_km=0.5, is_open=True,
            crowd_level="quiet",
        )
    ])
    return mock


def _mock_hygiene_agent(results=None):
    mock = MagicMock()
    mock.run = AsyncMock(return_value=results or [
        HygieneResult(
            stall_name="Maxwell Food Centre",
            centre_name="Maxwell Food Centre",
            grade="A", demerit_points=0, suspended=False,
            reasoning_trace="Maxwell Food Centre: Grade A, open today.",
        )
    ])
    return mock


def _mock_recommendation_agent(results=None):
    mock = MagicMock()
    mock.run = AsyncMock(return_value=results or [
        RankedRecommendation(
            stall_name="Tian Tian Chicken Rice",
            centre_name="Maxwell Food Centre",
            rank=1,
            reasoning="Top pick — Grade A, Michelin.",
            hygiene_grade="A",
            is_michelin=True,
            is_halal=False,
            is_open=True,
            distance_km=0.5,
            score=9.5,
        )
    ])
    return mock


_PARSE_RESPONSE = '{"cuisine_type":"chicken rice","location_hint":"Maxwell","dietary":[],"avoid":[]}'


# ── tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_yields_agent_events_in_correct_order():
    orchestrator = OrchestratorAgent(
        location_agent=_mock_location_agent(),
        hygiene_agent=_mock_hygiene_agent(),
        recommendation_agent=_mock_recommendation_agent(),
        anthropic_client=_mock_anthropic_client(_PARSE_RESPONSE),
    )
    request = SearchRequest(query="chicken rice near Maxwell", lat=1.2805, lng=103.8446)
    events = [e async for e in orchestrator.run(request)]

    agents_seen = [e.agent for e in events]
    # Must see orchestrator (parse), orchestrator (location resolved), location, hygiene, recommendation, result
    assert agents_seen.index("location") > agents_seen.index("orchestrator")
    assert agents_seen.index("hygiene") > agents_seen.index("location")
    assert agents_seen.index("recommendation") > agents_seen.index("hygiene")


@pytest.mark.asyncio
async def test_final_event_is_result_with_recommendations():
    orchestrator = OrchestratorAgent(
        location_agent=_mock_location_agent(),
        hygiene_agent=_mock_hygiene_agent(),
        recommendation_agent=_mock_recommendation_agent(),
        anthropic_client=_mock_anthropic_client(_PARSE_RESPONSE),
    )
    request = SearchRequest(query="chicken rice", lat=1.2805, lng=103.8446)
    events = [e async for e in orchestrator.run(request)]

    final = events[-1]
    assert final.type == "result"
    assert "recommendations" in final.data
    assert isinstance(final.data["recommendations"], list)
    assert len(final.data["recommendations"]) >= 1


@pytest.mark.asyncio
async def test_yields_error_event_when_location_agent_raises():
    mock_loc = MagicMock()
    mock_loc.run = AsyncMock(side_effect=ValueError("outside Singapore"))
    orchestrator = OrchestratorAgent(
        location_agent=mock_loc,
        hygiene_agent=_mock_hygiene_agent(),
        recommendation_agent=_mock_recommendation_agent(),
        anthropic_client=_mock_anthropic_client(_PARSE_RESPONSE),
    )
    request = SearchRequest(query="food", lat=51.5, lng=-0.1)  # London
    events = [e async for e in orchestrator.run(request)]

    error_events = [e for e in events if e.type == "error"]
    assert len(error_events) >= 1
    assert "outside Singapore" in error_events[0].message


@pytest.mark.asyncio
async def test_uses_default_singapore_coords_when_no_location_provided():
    orchestrator = OrchestratorAgent(
        location_agent=_mock_location_agent(),
        hygiene_agent=_mock_hygiene_agent(),
        recommendation_agent=_mock_recommendation_agent(),
        anthropic_client=_mock_anthropic_client(
            '{"cuisine_type":"laksa","location_hint":"","dietary":[],"avoid":[]}'
        ),
    )
    # No lat/lng in request
    request = SearchRequest(query="good laksa")
    events = [e async for e in orchestrator.run(request)]
    location_events = [e for e in events if e.agent == "orchestrator" and "default" in e.message.lower()]
    assert len(location_events) >= 1
