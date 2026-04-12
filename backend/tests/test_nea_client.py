"""Tests for NEA API client."""
import pytest
import respx
import httpx
import tools.nea_client as nea_module
from tools.nea_client import NEAClient, NEAClientError

MOCK_CENTRES_RESPONSE = {
    "success": True,
    "result": {
        "records": [
            {
                "_id": 1,
                "NAME": "Toa Payoh West Market",
                "ADDRESSSTREETNAME": "100 Lorong 1 Toa Payoh",
                "LATITUDE": "1.3329",
                "LONGITUDE": "103.8481",
            }
        ]
    },
}

MOCK_HYGIENE_RESPONSE = {
    "success": True,
    "result": {
        "records": [
            {
                "_id": 1,
                "LICENSEE_NAME": "Chan Kee Wanton Mee",
                "BUSINESS_NAME": "Toa Payoh West Market",
                "GRADE": "A",
                "DEMERIT_POINTS": "0",
                "STATUS": "ACTIVE",
            }
        ]
    },
}


@pytest.mark.asyncio
async def test_get_centres_success():
    nea_module._cache.clear()
    with respx.mock:
        respx.get(NEAClient.BASE_URL).mock(
            return_value=httpx.Response(200, json=MOCK_CENTRES_RESPONSE)
        )
        client = NEAClient()
        centres = await client.get_centres()
        assert len(centres) == 1
        assert centres[0].name == "Toa Payoh West Market"
        assert centres[0].lat == pytest.approx(1.3329)
        assert centres[0].lng == pytest.approx(103.8481)


@pytest.mark.asyncio
async def test_cache_hit_makes_only_one_http_call():
    nea_module._cache.clear()
    with respx.mock:
        route = respx.get(NEAClient.BASE_URL).mock(
            return_value=httpx.Response(200, json=MOCK_CENTRES_RESPONSE)
        )
        client = NEAClient()
        await client.get_centres()
        await client.get_centres()  # second call should hit cache
        assert route.call_count == 1


@pytest.mark.asyncio
async def test_nea_client_error_on_http_500():
    nea_module._cache.clear()
    with respx.mock:
        respx.get(NEAClient.BASE_URL).mock(
            return_value=httpx.Response(500)
        )
        client = NEAClient()
        with pytest.raises(NEAClientError, match="HTTP 500"):
            await client.get_centres()
