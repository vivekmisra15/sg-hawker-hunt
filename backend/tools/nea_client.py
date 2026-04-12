"""
NEA (National Environment Agency) API client.
Fetches hawker centre locations, hygiene grades, and closure dates from data.gov.sg.
"""
import httpx
import os
import time
from datetime import datetime
from models.schemas import CentreInfo, HygieneResult


class NEAClientError(Exception):
    pass


_cache: dict = {}  # module-level singleton: {resource_id: (records, timestamp)}
CACHE_TTL_SECONDS = 3600


class NEAClient:
    BASE_URL = "https://data.gov.sg/api/action/datastore_search"
    CENTRES_RESOURCE = "b80cb643-a732-480d-86b5-e03957bc82aa"
    HYGIENE_RESOURCE = "4a291f25-2d8d-4b3a-9aaf-e8b1bd0ceedb"
    CLOSURE_RESOURCE = "d_bda4baa634dd1cc7a6c7cad5f19e2d68"

    def _headers(self) -> dict:
        key = os.getenv("DATAGOV_API_KEY")
        return {"Authorization": key} if key else {}

    def _get_cached(self, key: str):
        if key in _cache:
            data, ts = _cache[key]
            if time.time() - ts < CACHE_TTL_SECONDS:
                return data
        return None

    async def _fetch(self, resource_id: str) -> list[dict]:
        cached = self._get_cached(resource_id)
        if cached is not None:
            return cached
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                self.BASE_URL,
                params={"resource_id": resource_id, "limit": 10000},
                headers=self._headers(),
            )
        if resp.status_code != 200:
            raise NEAClientError(f"NEA API error: HTTP {resp.status_code}")
        body = resp.json()
        if not body.get("success"):
            raise NEAClientError("NEA API returned success=false")
        records = body["result"]["records"]
        _cache[resource_id] = (records, time.time())
        return records

    async def get_centres(self) -> list[CentreInfo]:
        """Return all NEA hawker centres."""
        records = await self._fetch(self.CENTRES_RESOURCE)
        centres = []
        for r in records:
            try:
                centres.append(
                    CentreInfo(
                        centre_id=str(r["_id"]),
                        name=r["NAME"],
                        address=r.get("ADDRESSSTREETNAME", ""),
                        lat=float(r["LATITUDE"]),
                        lng=float(r["LONGITUDE"]),
                    )
                )
            except (KeyError, ValueError) as e:
                raise NEAClientError(f"Failed to parse centre record: {e}") from e
        return centres

    async def get_hygiene_grades(self) -> dict[str, HygieneResult]:
        """Return hygiene results keyed by uppercase stall name."""
        records = await self._fetch(self.HYGIENE_RESOURCE)
        grades: dict[str, HygieneResult] = {}
        for r in records:
            try:
                stall_name = r.get("LICENSEE_NAME", r.get("BUSINESS_NAME", "UNKNOWN"))
                centre_name = r.get("BUSINESS_NAME", stall_name)
                status = r.get("STATUS", "")
                grades[stall_name.upper()] = HygieneResult(
                    stall_name=stall_name,
                    centre_name=centre_name,
                    grade=r.get("GRADE", ""),
                    demerit_points=int(r.get("DEMERIT_POINTS", 0)),
                    suspended="SUSPENDED" in status.upper(),
                )
            except (KeyError, ValueError):
                continue  # skip malformed records
        return grades

    async def get_closure_dates(self) -> list[str]:
        """Return centre names with closures in the current month."""
        records = await self._fetch(self.CLOSURE_RESOURCE)
        current_month = datetime.now().strftime("%Y-%m")
        closed = []
        for r in records:
            # Try various date field names the API may use
            date_val = r.get("CLOSURE_DATE", r.get("DATE", ""))
            if date_val and str(date_val).startswith(current_month):
                name = r.get("NAME", r.get("CENTRE_NAME", ""))
                if name:
                    closed.append(name)
        return closed
