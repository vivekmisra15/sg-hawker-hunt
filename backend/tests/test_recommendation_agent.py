"""Tests for RecommendationAgent."""
import pytest
from unittest.mock import MagicMock, patch
from agents.recommendation_agent import RecommendationAgent
from models.schemas import LocationResult, HygieneResult

# ---- helpers ----------------------------------------------------------------

def _make_vs(rag_docs: list[dict]):
    mock = MagicMock()
    mock.query = MagicMock(return_value=rag_docs)
    return mock


def _loc(centre_name, distance_km=0.5, is_open=True, crowd="quiet", rating=4.2):
    return LocationResult(
        centre_name=centre_name, address="", lat=1.35, lng=103.82,
        distance_km=distance_km, is_open=is_open,
        google_rating=rating, review_count=100,
        crowd_level=crowd,
    )


def _hyg(centre_name, grade="A"):
    return HygieneResult(
        stall_name=centre_name, centre_name=centre_name,
        grade=grade, demerit_points=0, suspended=False,
    )


def _rag(stall, centre, is_michelin=False, is_halal=False, distance=0.3):
    return {
        "text": f"{stall} at {centre} great food.",
        "metadata": {
            "stall_name": stall,
            "centre_name": centre,
            "cuisine": "chicken rice",
            "tags": "chicken rice",
            "is_michelin": str(is_michelin),
            "is_halal": str(is_halal),
        },
        "distance": distance,
    }


# ---- tests ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_michelin_stall_scores_higher_than_non_michelin():
    vs = _make_vs([
        _rag("Stall A", "Maxwell", is_michelin=True, distance=0.3),
        _rag("Stall B", "Chinatown", is_michelin=False, distance=0.3),
    ])
    agent = RecommendationAgent(vector_store=vs)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        results = await agent.run(
            query="chicken rice",
            location_results=[_loc("Maxwell"), _loc("Chinatown")],
            hygiene_results=[_hyg("Maxwell"), _hyg("Chinatown")],
            preferences={},
        )
    assert len(results) >= 2
    michelin_result = next(r for r in results if r.stall_name == "Stall A")
    non_michelin = next(r for r in results if r.stall_name == "Stall B")
    assert michelin_result.score > non_michelin.score


@pytest.mark.asyncio
async def test_halal_filter_removes_non_halal_stalls():
    vs = _make_vs([
        _rag("Halal Stall", "Newton", is_halal=True, distance=0.3),
        _rag("Non-Halal Stall", "Maxwell", is_halal=False, distance=0.2),
    ])
    agent = RecommendationAgent(vector_store=vs)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        results = await agent.run(
            query="halal food",
            location_results=[_loc("Newton"), _loc("Maxwell")],
            hygiene_results=[_hyg("Newton"), _hyg("Maxwell")],
            preferences={"dietary": ["halal"]},
        )
    stall_names = [r.stall_name for r in results]
    assert "Non-Halal Stall" not in stall_names
    assert "Halal Stall" in stall_names


@pytest.mark.asyncio
async def test_returns_maximum_three_results():
    vs = _make_vs([
        _rag(f"Stall {i}", f"Centre {i}", distance=0.3) for i in range(8)
    ])
    agent = RecommendationAgent(vector_store=vs)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        results = await agent.run(
            query="food",
            location_results=[_loc(f"Centre {i}") for i in range(8)],
            hygiene_results=[_hyg(f"Centre {i}") for i in range(8)],
            preferences={},
        )
    assert len(results) <= 3


@pytest.mark.asyncio
async def test_each_result_has_non_empty_reasoning():
    vs = _make_vs([_rag("Test Stall", "Maxwell", distance=0.3)])
    agent = RecommendationAgent(vector_store=vs)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        results = await agent.run(
            query="chicken rice",
            location_results=[_loc("Maxwell")],
            hygiene_results=[_hyg("Maxwell")],
            preferences={},
        )
    assert len(results) > 0
    for r in results:
        assert isinstance(r.reasoning, str) and len(r.reasoning) > 0


@pytest.mark.asyncio
async def test_grade_a_stall_outscores_grade_b_stall():
    vs = _make_vs([
        _rag("Grade A Stall", "Maxwell", distance=0.3),
        _rag("Grade B Stall", "Newton", distance=0.3),
    ])
    agent = RecommendationAgent(vector_store=vs)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        results = await agent.run(
            query="food",
            location_results=[_loc("Maxwell"), _loc("Newton")],
            hygiene_results=[_hyg("Maxwell", grade="A"), _hyg("Newton", grade="B")],
            preferences={},
        )
    grade_a = next(r for r in results if r.stall_name == "Grade A Stall")
    grade_b = next(r for r in results if r.stall_name == "Grade B Stall")
    assert grade_a.score > grade_b.score
