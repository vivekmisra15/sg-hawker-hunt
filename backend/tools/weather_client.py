"""
OpenWeatherMap current weather client.
Degrades gracefully — missing API key returns a default result, never raises.
"""
import httpx
import os
from models.schemas import WeatherResult


_UNAVAILABLE = WeatherResult(
    description="unavailable",
    temp_c=0.0,
    is_raining=False,
    outdoor_recommendation="Weather data unavailable",
)


def _is_rain_code(code: int) -> bool:
    """Return True for thunderstorm (2xx), drizzle (3xx), or rain (5xx) codes."""
    return (200 <= code <= 299) or (300 <= code <= 399) or (500 <= code <= 599)


class WeatherClient:
    BASE_URL = "https://api.openweathermap.org/data/2.5"

    async def get_current_weather(self, lat: float, lng: float) -> WeatherResult:
        """
        Fetch current weather for the given coordinates.
        Returns _UNAVAILABLE if the API key is missing or the request fails.
        Never raises — weather is a non-critical signal.
        """
        key = os.getenv("OPENWEATHER_API_KEY")
        if not key:
            return _UNAVAILABLE

        params = {
            "lat": lat,
            "lon": lng,
            "appid": key,
            "units": "metric",
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.BASE_URL}/weather", params=params)
            if resp.status_code != 200:
                return _UNAVAILABLE
            data = resp.json()
            code = data["weather"][0]["id"]
            description = data["weather"][0]["description"]
            temp_c = data["main"]["temp"]
            is_raining = _is_rain_code(code)
            return WeatherResult(
                description=description,
                temp_c=round(temp_c, 1),
                is_raining=is_raining,
                outdoor_recommendation=(
                    "Rain detected — prefer covered hawker centres"
                    if is_raining
                    else "Weather clear — all centres accessible"
                ),
            )
        except Exception:
            return _UNAVAILABLE
