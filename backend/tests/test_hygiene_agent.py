"""Tests for HygieneAgent."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from agents.hygiene_agent import HygieneAgent
from tools.nea_client import NEAClientError
from models.schemas import HygieneResult


def _make_mock_nea(grades: dict, closures: list[str]):
    mock = MagicMock()
    mock.get_hygiene_grades = AsyncMock(return_value=grades)
    mock.get_closure_dates = AsyncMock(return_value=closures)
    return mock


MAXWELL_GRADE = HygieneResult(
    stall_name="Tian Tian Chicken Rice",
    centre_name="Maxwell Food Centre",
    grade="A",
    demerit_points=0,
    suspended=False,
)


@pytest.mark.asyncio
async def test_returns_grade_a_for_known_centre():
    mock_nea = _make_mock_nea(
        grades={"TIAN TIAN CHICKEN RICE": MAXWELL_GRADE},
        closures=[],
    )
    agent = HygieneAgent(nea_client=mock_nea)
    results = await agent.run(["Maxwell Food Centre"])
    assert len(results) == 1
    assert results[0].grade == "A"
    assert results[0].centre_name == "Maxwell Food Centre"


@pytest.mark.asyncio
async def test_is_closed_today_when_centre_in_closure_list():
    mock_nea = _make_mock_nea(
        grades={"TIAN TIAN CHICKEN RICE": MAXWELL_GRADE},
        closures=["Maxwell Food Centre"],
    )
    agent = HygieneAgent(nea_client=mock_nea)
    results = await agent.run(["Maxwell Food Centre"])
    assert results[0].is_closed_today is True


@pytest.mark.asyncio
async def test_returns_unknown_grade_when_nea_error():
    mock_nea = MagicMock()
    mock_nea.get_hygiene_grades = AsyncMock(
        side_effect=NEAClientError("API down")
    )
    mock_nea.get_closure_dates = AsyncMock(return_value=[])
    agent = HygieneAgent(nea_client=mock_nea)
    results = await agent.run(["Some Hawker Centre"])
    assert len(results) == 1
    assert results[0].grade == "UNKNOWN"
    assert results[0].suspended is False


@pytest.mark.asyncio
async def test_reasoning_trace_is_non_empty_string():
    mock_nea = _make_mock_nea(
        grades={"TIAN TIAN CHICKEN RICE": MAXWELL_GRADE},
        closures=[],
    )
    agent = HygieneAgent(nea_client=mock_nea)
    results = await agent.run(["Maxwell Food Centre"])
    assert isinstance(results[0].reasoning_trace, str)
    assert len(results[0].reasoning_trace) > 0
    assert "Maxwell Food Centre" in results[0].reasoning_trace
