"""Tests for OpenWeatherMap client."""
import pytest
import respx
import httpx
import os
from unittest.mock import patch
from tools.weather_client import WeatherClient

MOCK_RAIN_RESPONSE = {
    "weather": [{"id": 500, "description": "light rain"}],
    "main": {"temp": 27.5},
}

MOCK_CLEAR_RESPONSE = {
    "weather": [{"id": 800, "description": "clear sky"}],
    "main": {"temp": 30.0},
}


@pytest.mark.asyncio
async def test_rain_code_500_sets_is_raining_true():
    with patch.dict(os.environ, {"OPENWEATHER_API_KEY": "test-key"}):
        with respx.mock:
            respx.get(
                "https://api.openweathermap.org/data/2.5/weather"
            ).mock(return_value=httpx.Response(200, json=MOCK_RAIN_RESPONSE))
            client = WeatherClient()
            result = await client.get_current_weather(1.3521, 103.8198)
            assert result.is_raining is True
            assert result.description == "light rain"
            assert "Rain detected" in result.outdoor_recommendation


@pytest.mark.asyncio
async def test_clear_code_800_sets_is_raining_false():
    with patch.dict(os.environ, {"OPENWEATHER_API_KEY": "test-key"}):
        with respx.mock:
            respx.get(
                "https://api.openweathermap.org/data/2.5/weather"
            ).mock(return_value=httpx.Response(200, json=MOCK_CLEAR_RESPONSE))
            client = WeatherClient()
            result = await client.get_current_weather(1.3521, 103.8198)
            assert result.is_raining is False
            assert result.temp_c == pytest.approx(30.0)
            assert "clear" in result.outdoor_recommendation.lower()


@pytest.mark.asyncio
async def test_missing_key_returns_unavailable_without_http_call():
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("OPENWEATHER_API_KEY", None)
        with respx.mock:
            # No routes registered — any accidental HTTP call raises MockError
            client = WeatherClient()
            result = await client.get_current_weather(1.3521, 103.8198)
            assert result.description == "unavailable"
            assert result.is_raining is False
            assert result.outdoor_recommendation == "Weather data unavailable"
