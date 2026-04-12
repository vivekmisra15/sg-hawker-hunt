"""
Google Places API client (New API v1).
Base: https://places.googleapis.com/v1/
"""
import httpx
import os


class PlacesClientError(Exception):
    pass


class PlacesClient:
    BASE_URL = "https://places.googleapis.com/v1"

    def _get_api_key(self) -> str:
        key = os.getenv("GOOGLE_PLACES_API_KEY")
        if not key:
            raise PlacesClientError("GOOGLE_PLACES_API_KEY not set")
        return key

    async def search_nearby(
        self, lat: float, lng: float, radius_km: float = 1.5
    ) -> list[dict]:
        """
        POST /places:searchNearby
        Returns the raw `places` list from the API response.
        Each entry has: name (resource path), displayName.text, location, rating,
        userRatingCount, currentOpeningHours.openNow
        """
        key = self._get_api_key()
        body = {
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lng},
                    "radius": radius_km * 1000,
                }
            },
            "includedTypes": ["restaurant", "meal_takeaway", "cafe"],
        }
        headers = {
            "X-Goog-Api-Key": key,
            "X-Goog-FieldMask": (
                "places.name,places.displayName,places.location,"
                "places.rating,places.userRatingCount,"
                "places.currentOpeningHours"
            ),
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{self.BASE_URL}/places:searchNearby",
                json=body,
                headers=headers,
            )
        if resp.status_code != 200:
            raise PlacesClientError(
                f"Places API error: HTTP {resp.status_code} — {resp.text[:200]}"
            )
        return resp.json().get("places", [])

    async def get_place_details(self, place_id: str) -> dict:
        """
        GET /places/{place_id}
        Returns the full place object with openNow, reviews (up to 5), rating.
        Reviews are accessed at result["reviews"][i]["text"]["text"].
        """
        key = self._get_api_key()
        headers = {
            "X-Goog-Api-Key": key,
            "X-Goog-FieldMask": (
                "name,displayName,rating,userRatingCount,"
                "currentOpeningHours,reviews"
            ),
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{self.BASE_URL}/places/{place_id}",
                headers=headers,
            )
        if resp.status_code != 200:
            raise PlacesClientError(
                f"Places API error: HTTP {resp.status_code}"
            )
        return resp.json()
