"""Tests for LocationAgent."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from agents.location_agent import LocationAgent
from tools.places_client import PlacesClientError
from models.schemas import WeatherResult

_CLEAR_WEATHER = WeatherResult(
    description="clear sky", temp_c=30.0, is_raining=False,
    outdoor_recommendation="Weather clear — all centres accessible"
)

_RAIN_WEATHER = WeatherResult(
    description="light rain", temp_c=27.0, is_raining=True,
    outdoor_recommendation="Rain detected — prefer covered hawker centres"
)

# Two places at different distances from (1.3521, 103.8198)
_PLACE_NEAR = {
    "name": "places/NEAR001",
    "displayName": {"text": "Toa Payoh West Market"},
    "location": {"latitude": 1.3550, "longitude": 103.8220},
    "rating": 4.3,
    "userRatingCount": 500,
    "currentOpeningHours": {"openNow": True},
}
_PLACE_FAR = {
    "name": "places/FAR002",
    "displayName": {"text": "Toa Payoh North Market"},
    "location": {"latitude": 1.3620, "longitude": 103.8310},
    "rating": 4.0,
    "userRatingCount": 200,
    "currentOpeningHours": {"openNow": False},
}
_DETAILS_NEAR = {
    "currentOpeningHours": {"openNow": True},
    "rating": 4.3,
    "userRatingCount": 500,
    "reviews": [{"text": {"text": "Great food stalls."}}],
}
_DETAILS_FAR = {
    "currentOpeningHours": {"openNow": False},
    "rating": 4.0,
    "userRatingCount": 200,
    "reviews": [],
}


def _make_mock_places(places, details_map):
    mock = MagicMock()
    mock.search_nearby = AsyncMock(return_value=places)
    async def _details(place_id):
        return details_map.get(place_id, {})
    mock.get_place_details = _details
    return mock


def _make_mock_weather(result):
    mock = MagicMock()
    mock.get_current_weather = AsyncMock(return_value=result)
    return mock


@pytest.mark.asyncio
async def test_returns_results_sorted_by_distance():
    mock_places = _make_mock_places(
        [_PLACE_FAR, _PLACE_NEAR],  # intentionally reversed
        {"NEAR001": _DETAILS_NEAR, "FAR002": _DETAILS_FAR},
    )
    agent = LocationAgent(
        places_client=mock_places,
        weather_client=_make_mock_weather(_CLEAR_WEATHER),
    )
    results = await agent.run(lat=1.3521, lng=103.8198)
    assert len(results) == 2
    assert results[0].distance_km < results[1].distance_km
    assert results[0].centre_name == "Toa Payoh West Market"


@pytest.mark.asyncio
async def test_raises_value_error_for_non_singapore_coordinates():
    agent = LocationAgent()
    with pytest.raises(ValueError, match="outside Singapore"):
        await agent.run(lat=51.5074, lng=-0.1278)  # London


@pytest.mark.asyncio
async def test_skips_centre_gracefully_when_places_error():
    mock_places = MagicMock()
    mock_places.search_nearby = AsyncMock(
        side_effect=PlacesClientError("GOOGLE_PLACES_API_KEY not set")
    )
    agent = LocationAgent(
        places_client=mock_places,
        weather_client=_make_mock_weather(_CLEAR_WEATHER),
    )
    results = await agent.run(lat=1.3521, lng=103.8198)
    assert results == []


@pytest.mark.asyncio
async def test_crowd_level_busy_during_lunch_hour():
    mock_places = _make_mock_places(
        [_PLACE_NEAR],
        {"NEAR001": _DETAILS_NEAR},
    )
    agent = LocationAgent(
        places_client=mock_places,
        weather_client=_make_mock_weather(_CLEAR_WEATHER),
    )
    # Patch datetime in location_agent to return hour=12 (lunch)
    import agents.location_agent as la_module
    import pytz
    from datetime import datetime as real_dt

    class _FakeDT(real_dt):
        @classmethod
        def now(cls, tz=None):
            return real_dt(2026, 4, 12, 12, 0, 0, tzinfo=tz)

    with patch.object(la_module, "datetime", _FakeDT):
        results = await agent.run(lat=1.3521, lng=103.8198)

    assert results[0].crowd_level == "busy"


@pytest.mark.asyncio
async def test_reasoning_trace_non_empty_for_each_result():
    mock_places = _make_mock_places(
        [_PLACE_NEAR, _PLACE_FAR],
        {"NEAR001": _DETAILS_NEAR, "FAR002": _DETAILS_FAR},
    )
    agent = LocationAgent(
        places_client=mock_places,
        weather_client=_make_mock_weather(_CLEAR_WEATHER),
    )
    results = await agent.run(lat=1.3521, lng=103.8198)
    for r in results:
        assert isinstance(r.reasoning_trace, str)
        assert len(r.reasoning_trace) > 0
