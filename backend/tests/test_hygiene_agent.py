"""Tests for HygieneAgent."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from agents.hygiene_agent import HygieneAgent
from tools.nea_client import NEAClientError
from models.schemas import HygieneResult


def _make_mock_nea(grades: dict, closures: list[str], static_stalls: list | None = None):
    mock = MagicMock()
    mock.get_hygiene_grades = AsyncMock(return_value=grades)
    mock.get_closure_dates = AsyncMock(return_value=closures)
    mock.get_static_hygiene_for_centre = MagicMock(return_value=static_stalls or [])
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
    mock_nea.get_hygiene_grades = AsyncMock(side_effect=NEAClientError("API down"))
    mock_nea.get_closure_dates = AsyncMock(return_value=[])
    mock_nea.get_static_hygiene_for_centre = MagicMock(return_value=[])
    agent = HygieneAgent(nea_client=mock_nea)
    results = await agent.run(["Some Hawker Centre"])
    assert len(results) == 1
    assert results[0].grade == "UNKNOWN"
    assert results[0].suspended is False


@pytest.mark.asyncio
async def test_static_grades_fallback_when_live_api_no_match():
    """When live API returns no match, static grades should be used."""
    static_stall_a = HygieneResult(
        stall_name="TIAN TIAN FOOD ENTERPRISE",
        centre_name="Maxwell Food Centre",
        grade="A",
        demerit_points=0,
        suspended=False,
    )
    static_stall_b = HygieneResult(
        stall_name="ANOTHER STALL",
        centre_name="Maxwell Food Centre",
        grade="B",
        demerit_points=4,
        suspended=False,
    )
    mock_nea = _make_mock_nea(
        grades={},  # live API has no match
        closures=[],
        static_stalls=[static_stall_a, static_stall_b],
    )
    agent = HygieneAgent(nea_client=mock_nea)
    results = await agent.run(["Maxwell Food Centre"])
    assert len(results) == 1
    # Best grade from static data is A
    assert results[0].grade == "A"
    assert "SFA data" in results[0].reasoning_trace


@pytest.mark.asyncio
async def test_static_grades_suspended_flag_from_static_data():
    """Suspended flag should propagate from static grades."""
    suspended_stall = HygieneResult(
        stall_name="SUSPENDED OPERATOR",
        centre_name="Some Centre",
        grade="C",
        demerit_points=14,
        suspended=True,
    )
    mock_nea = _make_mock_nea(
        grades={},
        closures=[],
        static_stalls=[suspended_stall],
    )
    agent = HygieneAgent(nea_client=mock_nea)
    results = await agent.run(["Some Centre"])
    assert results[0].suspended is True
    assert "suspension" in results[0].reasoning_trace


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


@pytest.mark.asyncio
async def test_static_fallback_calls_get_static_only_once():
    """When live API returns no match, get_static_hygiene_for_centre should be
    called exactly once per centre — not a second time for the trace string."""
    static_stalls = [
        HygieneResult(
            stall_name="STALL A",
            centre_name="Test Centre",
            grade="A",
            demerit_points=0,
            suspended=False,
        ),
    ]
    mock_nea = _make_mock_nea(
        grades={},
        closures=[],
        static_stalls=static_stalls,
    )
    agent = HygieneAgent(nea_client=mock_nea)
    results = await agent.run(["Test Centre"])
    assert results[0].grade == "A"
    assert "SFA data" in results[0].reasoning_trace
    # The critical assertion: static fetch called exactly once, not twice
    assert mock_nea.get_static_hygiene_for_centre.call_count == 1
