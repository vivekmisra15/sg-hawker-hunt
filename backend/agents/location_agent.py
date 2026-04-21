"""
LocationAgent — finds and enriches nearby hawker centres given a user location.
Single responsibility: coordinates → list[LocationResult] ranked by distance.
"""
import logging
from datetime import datetime
import pytz

from tools.places_client import PlacesClient, PlacesClientError
from tools.onemap_client import OneMapClient
from tools.weather_client import WeatherClient
from models.schemas import LocationResult

logger = logging.getLogger(__name__)

SG_LAT_MIN, SG_LAT_MAX = 1.15, 1.48
SG_LNG_MIN, SG_LNG_MAX = 103.60, 104.10
SG_TZ = pytz.timezone("Asia/Singapore")

# Hours considered busy (Singapore meal-time peaks)
_BUSY_HOURS = set(range(11, 15)) | set(range(17, 21))  # 11-14, 17-20


def _crowd_level(hour: int) -> str:
    return "busy" if hour in _BUSY_HOURS else "quiet"


def _is_sg_coordinates(lat: float, lng: float) -> bool:
    return SG_LAT_MIN <= lat <= SG_LAT_MAX and SG_LNG_MIN <= lng <= SG_LNG_MAX


class LocationAgent:
    def __init__(
        self,
        places_client: PlacesClient | None = None,
        onemap_client: OneMapClient | None = None,
        weather_client: WeatherClient | None = None,
    ):
        self._places = places_client or PlacesClient()
        self._onemap = onemap_client or OneMapClient()
        self._weather = weather_client or WeatherClient()

    async def run(
        self, lat: float, lng: float, radius_km: float = 1.5
    ) -> list[LocationResult]:
        """
        Find hawker centres near (lat, lng) within radius_km.
        Raises ValueError if coordinates are outside Singapore.
        Returns [] if no results found. Never raises on API errors.
        """
        if not _is_sg_coordinates(lat, lng):
            raise ValueError(
                f"Coordinates ({lat}, {lng}) are outside Singapore. "
                f"Expected lat {SG_LAT_MIN}–{SG_LAT_MAX}, lng {SG_LNG_MIN}–{SG_LNG_MAX}."
            )

        sg_now = datetime.now(tz=SG_TZ)
        crowd = _crowd_level(sg_now.hour)
        weather = await self._weather.get_current_weather(lat, lng)

        try:
            places = await self._places.search_nearby(lat, lng, radius_km)
        except PlacesClientError as e:
            logger.warning("Places search failed: %s", e)
            return []

        results: list[LocationResult] = []
        for place in places:
            place_name_path = place.get("name", "")
            place_id = place_name_path.split("/")[-1] if "/" in place_name_path else place_name_path
            display_name = place.get("displayName", {}).get("text", "Unknown")
            loc = place.get("location", {})
            place_lat = loc.get("latitude", lat)
            place_lng = loc.get("longitude", lng)
            distance_km = OneMapClient.calculate_distance_km(lat, lng, place_lat, place_lng)
            base_rating = place.get("rating")
            base_count = place.get("userRatingCount")
            is_open = place.get("currentOpeningHours", {}).get("openNow", False)
            price_level: str | None = place.get("priceLevel")

            # Fetch details for reviews if we have a valid place_id
            reviews_summary: str | None = None
            try:
                if place_id:
                    details = await self._places.get_place_details(place_id)
                    is_open = details.get("currentOpeningHours", {}).get("openNow", is_open)
                    base_rating = details.get("rating", base_rating)
                    base_count = details.get("userRatingCount", base_count)
                    price_level = details.get("priceLevel", price_level)
                    reviews = details.get("reviews", [])
                    if reviews:
                        snippets = [
                            r.get("text", {}).get("text", "")
                            for r in reviews[:3]
                            if r.get("text", {}).get("text")
                        ]
                        reviews_summary = " | ".join(snippets) if snippets else None
            except PlacesClientError as e:
                logger.warning("Place details fetch failed for %s: %s", place_id, e)

            # Build reasoning trace
            rain_note = ""
            if weather.is_raining:
                rain_note = " ⚠️ Rain — prefer covered centre."
            rating_str = f"rated {base_rating}/5 ({base_count} reviews), " if base_rating else ""
            open_str = "currently open" if is_open else "currently closed"
            trace = (
                f"{display_name}: {distance_km:.1f}km away, {open_str}, "
                f"{rating_str}{crowd} period.{rain_note}"
            )

            results.append(
                LocationResult(
                    centre_name=display_name,
                    address="",  # enriched by OneMap if needed in future
                    lat=place_lat,
                    lng=place_lng,
                    distance_km=round(distance_km, 3),
                    is_open=is_open,
                    google_rating=base_rating,
                    review_count=base_count,
                    reviews_summary=reviews_summary,
                    price_level=price_level,
                    crowd_level=crowd,
                    reasoning_trace=trace,
                )
            )

        results.sort(key=lambda r: r.distance_km)
        return results
