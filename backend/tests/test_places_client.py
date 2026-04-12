"""Tests for Google Places API client."""
import pytest
import respx
import httpx
import os
from unittest.mock import patch
from tools.places_client import PlacesClient, PlacesClientError

MOCK_SEARCH_RESPONSE = {
    "places": [
        {
            "name": "places/ChIJrTLr-GyuEmsRBfy61i59si0",
            "displayName": {"text": "Toa Payoh West Market", "languageCode": "en"},
            "location": {"latitude": 1.3329, "longitude": 103.8481},
            "rating": 4.2,
            "userRatingCount": 843,
            "currentOpeningHours": {"openNow": True},
        }
    ]
}

MOCK_DETAILS_RESPONSE = {
    "name": "places/ChIJrTLr-GyuEmsRBfy61i59si0",
    "displayName": {"text": "Toa Payoh West Market"},
    "rating": 4.2,
    "userRatingCount": 843,
    "currentOpeningHours": {"openNow": True},
    "reviews": [
        {"text": {"text": "Great char kway teow!", "languageCode": "en"}},
        {"text": {"text": "Always a queue but worth it.", "languageCode": "en"}},
    ],
}


@pytest.mark.asyncio
async def test_search_nearby_returns_places():
    with patch.dict(os.environ, {"GOOGLE_PLACES_API_KEY": "test-key"}):
        with respx.mock:
            respx.post(
                "https://places.googleapis.com/v1/places:searchNearby"
            ).mock(return_value=httpx.Response(200, json=MOCK_SEARCH_RESPONSE))
            client = PlacesClient()
            results = await client.search_nearby(1.3329, 103.8481)
            assert len(results) == 1
            assert results[0]["displayName"]["text"] == "Toa Payoh West Market"
            assert results[0]["currentOpeningHours"]["openNow"] is True


@pytest.mark.asyncio
async def test_get_place_details_open_now():
    with patch.dict(os.environ, {"GOOGLE_PLACES_API_KEY": "test-key"}):
        with respx.mock:
            respx.get(
                "https://places.googleapis.com/v1/places/ChIJrTLr-GyuEmsRBfy61i59si0"
            ).mock(return_value=httpx.Response(200, json=MOCK_DETAILS_RESPONSE))
            client = PlacesClient()
            details = await client.get_place_details("ChIJrTLr-GyuEmsRBfy61i59si0")
            assert details["currentOpeningHours"]["openNow"] is True
            assert len(details["reviews"]) == 2
            assert details["reviews"][0]["text"]["text"] == "Great char kway teow!"


@pytest.mark.asyncio
async def test_missing_key_raises_before_http_call():
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("GOOGLE_PLACES_API_KEY", None)
        with respx.mock:
            # No routes registered — any HTTP call would raise MockError
            client = PlacesClient()
            with pytest.raises(PlacesClientError, match="GOOGLE_PLACES_API_KEY not set"):
                await client.search_nearby(1.3329, 103.8481)
