"""Tests for OneMap API client."""
import pytest
import respx
import httpx
from tools.onemap_client import OneMapClient, OneMapClientError

MOCK_GEOCODE_RESPONSE = {
    "results": [
        {
            "SEARCHVAL": "Toa Payoh",
            "LATITUDE": "1.3329",
            "LONGITUDE": "103.8481",
            "ADDRESS": "100 TOA PAYOH CENTRAL SINGAPORE 310100",
        }
    ]
}


def test_haversine_known_distance():
    # (1.3521, 103.8198) → (1.2978, 103.8516)
    # Actual haversine = ~7.0 km (spec comment of 7.4 was approximate)
    dist = OneMapClient.calculate_distance_km(1.3521, 103.8198, 1.2978, 103.8516)
    assert dist == pytest.approx(7.0, abs=0.1)


@pytest.mark.asyncio
async def test_geocode_returns_singapore_coordinates():
    with respx.mock:
        respx.get(
            "https://www.onemap.gov.sg/api/common/elastic/search"
        ).mock(return_value=httpx.Response(200, json=MOCK_GEOCODE_RESPONSE))
        client = OneMapClient()
        lat, lng, address = await client.geocode("Toa Payoh")
        assert 1.0 < lat < 1.5, "Latitude should be in Singapore range"
        assert 103.5 < lng < 104.2, "Longitude should be in Singapore range"
        assert isinstance(address, str)
        assert len(address) > 0


@pytest.mark.asyncio
async def test_geocode_empty_results_raises_error():
    with respx.mock:
        respx.get(
            "https://www.onemap.gov.sg/api/common/elastic/search"
        ).mock(return_value=httpx.Response(200, json={"results": []}))
        client = OneMapClient()
        with pytest.raises(OneMapClientError, match="No geocoding results"):
            await client.geocode("nonexistent place xyzzy abc123")
