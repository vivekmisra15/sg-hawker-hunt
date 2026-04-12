"""
OneMap Singapore API client.
Geocoding, reverse geocoding, and haversine distance calculation.
No API key required for public endpoints.
"""
import httpx
import math


class OneMapClientError(Exception):
    pass


class OneMapClient:
    BASE_URL = "https://www.onemap.gov.sg/api"

    async def geocode(self, search_term: str) -> tuple[float, float, str]:
        """
        Convert a place name or address to (lat, lng, formatted_address).
        Raises OneMapClientError if no results found.
        """
        params = {
            "searchVal": search_term,
            "returnGeom": "Y",
            "getAddrDetails": "Y",
            "pageNum": 1,
        }
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                f"{self.BASE_URL}/common/elastic/search",
                params=params,
            )
        if resp.status_code != 200:
            raise OneMapClientError(
                f"OneMap geocode error: HTTP {resp.status_code}"
            )
        data = resp.json()
        results = data.get("results", [])
        if not results:
            raise OneMapClientError(
                f"No geocoding results for: {search_term!r}"
            )
        first = results[0]
        return (
            float(first["LATITUDE"]),
            float(first["LONGITUDE"]),
            first.get("ADDRESS", ""),
        )

    async def reverse_geocode(self, lat: float, lng: float) -> str:
        """
        Convert (lat, lng) to a nearest address string.
        Raises OneMapClientError if no results found.
        """
        params = {
            "location": f"{lat},{lng}",
            "buffer": 40,
            "addressType": "All",
        }
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                f"{self.BASE_URL}/public/revgeocode",
                params=params,
            )
        if resp.status_code != 200:
            raise OneMapClientError(
                f"OneMap reverse geocode error: HTTP {resp.status_code}"
            )
        data = resp.json()
        info = data.get("GeocodeInfo", [])
        if not info:
            raise OneMapClientError(
                f"No reverse geocode results for ({lat}, {lng})"
            )
        block = info[0].get("BLOCK", "").strip()
        road = info[0].get("ROAD", "").strip()
        return f"{block} {road}".strip()

    @staticmethod
    def calculate_distance_km(
        lat1: float, lng1: float, lat2: float, lng2: float
    ) -> float:
        """Haversine formula — returns great-circle distance in kilometres."""
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlng / 2) ** 2
        )
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
