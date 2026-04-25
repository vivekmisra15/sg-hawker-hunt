"""
NEA (National Environment Agency) API client.
Fetches hawker centre locations, hygiene grades, and closure dates from data.gov.sg.
"""
import httpx
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from models.schemas import CentreInfo, HygieneResult

logger = logging.getLogger(__name__)


class NEAClientError(Exception):
    pass


_cache: dict = {}  # module-level singleton: {resource_id: (records, timestamp)}
CACHE_TTL_SECONDS = 3600

# ── Static grades (from sfa_scraper.py output) ───────────────────────────────
_GRADES_FILE = Path(__file__).parent.parent / "data" / "hygiene_grades_full.json"
_static_grades: dict | None = None  # lazy-loaded; None = not yet attempted

# Noise words stripped before Jaccard similarity comparison
_NAME_STOP = {
    "BLK", "BLOCK", "AVE", "AVENUE", "ST", "STREET", "RD", "ROAD",
    "MARKET", "FOOD", "CENTRE", "CENTER", "HAWKER", "AND", "&", "THE",
    "COOKED",
}


def _jaccard_similarity(a: str, b: str) -> float:
    """Token-level Jaccard similarity, ignoring noise words."""
    ta = {w for w in a.upper().split() if w not in _NAME_STOP and len(w) > 1}
    tb = {w for w in b.upper().split() if w not in _NAME_STOP and len(w) > 1}
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _load_static_grades() -> dict:
    """
    Lazy-load hygiene_grades_full.json into a dict keyed by CENTRE_NAME.upper().
    Each value is a list of stall dicts with licensee_name, grade, demerit_points, suspended.
    Returns {} if the file doesn't exist or can't be parsed.
    """
    global _static_grades
    if _static_grades is not None:
        return _static_grades
    if not _GRADES_FILE.exists():
        logger.debug("Static grades file not found at %s — run sfa_scraper.py to generate it", _GRADES_FILE)
        _static_grades = {}
        return _static_grades
    try:
        with open(_GRADES_FILE, encoding="utf-8") as f:
            data = json.load(f)
        centres = data.get("centres", {})
        # Build lookup keyed by centre_name.upper() for fuzzy matching
        by_name: dict = {}
        for postal_code, centre in centres.items():
            name_key = centre.get("centre_name", "").upper().strip()
            if name_key:
                by_name[name_key] = centre
        _static_grades = by_name
        logger.info(
            "Loaded static grades for %d centres from %s",
            len(by_name), _GRADES_FILE.name,
        )
    except (json.JSONDecodeError, OSError, KeyError) as e:
        logger.warning("Failed to load static grades file: %s", e)
        _static_grades = {}
    return _static_grades


class NEAClient:
    BASE_URL = "https://data.gov.sg/api/action/datastore_search"
    CENTRES_RESOURCE = "b80cb643-a732-480d-86b5-e03957bc82aa"
    HYGIENE_RESOURCE = "d_227473e811b09731e64725f140b77697"
    CLOSURE_RESOURCE = "d_bda4baa634dd1cc7a6c7cad5f19e2d68"

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
        params: dict = {"resource_id": resource_id, "limit": 10000}
        headers: dict = {}
        key = os.getenv("DATAGOV_API_KEY")
        if key:
            headers["X-Api-Key"] = key
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(self.BASE_URL, params=params, headers=headers)
        if resp.status_code == 429:
            raise NEAClientError("NEA API error: HTTP 429 (rate limited — set DATAGOV_API_KEY in .env)")
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
        """Return hygiene results keyed by uppercase licensee name.

        New dataset fields (as of 2025-12):
          licensee_name, licence_number, premises_address,
          grade, demerit_points, suspension_start_date, suspension_end_date
        """
        records = await self._fetch(self.HYGIENE_RESOURCE)
        grades: dict[str, HygieneResult] = {}
        for r in records:
            try:
                stall_name = r.get("licensee_name", "UNKNOWN")
                address = r.get("premises_address", "")
                demerit_raw = r.get("demerit_points", "0")
                demerit = int(demerit_raw) if str(demerit_raw).isdigit() else 0
                suspension_start = r.get("suspension_start_date", "na")
                suspended = suspension_start not in ("na", "", None)
                grades[stall_name.upper()] = HygieneResult(
                    stall_name=stall_name,
                    centre_name=address,
                    grade=r.get("grade", ""),
                    demerit_points=demerit,
                    suspended=suspended,
                )
            except (KeyError, ValueError):
                continue  # skip malformed records
        return grades

    def get_static_hygiene_for_centre(self, centre_name: str) -> list[HygieneResult]:
        """
        Return stall-level HygieneResult list from the static grades file for one centre.
        Uses fuzzy name matching (substring in either direction).
        Returns [] if static file not loaded or no match found.
        """
        by_name = _load_static_grades()
        if not by_name:
            return []
        centre_upper = centre_name.upper().strip()
        # 1. Exact match
        centre_data = by_name.get(centre_upper)
        if centre_data is None:
            # 2. Substring match in either direction
            for key, val in by_name.items():
                if centre_upper in key or key in centre_upper:
                    centre_data = val
                    break
        if centre_data is None:
            # 3. Jaccard similarity ≥ 0.4 — handles format differences like
            #    "Clementi 448 Market & Food Centre" vs "Clementi Ave 3 Blk 448"
            best_score = 0.0
            best_val = None
            for key, val in by_name.items():
                score = _jaccard_similarity(centre_upper, key)
                if score > best_score:
                    best_score = score
                    best_val = val
            if best_score >= 0.4:
                centre_data = best_val
        if centre_data is None:
            return []
        results = []
        for stall in centre_data.get("stalls", []):
            demerit = stall.get("demerit_points", 0)
            results.append(
                HygieneResult(
                    stall_name=stall.get("licensee_name", "UNKNOWN"),
                    centre_name=centre_data.get("centre_name", centre_name),
                    grade=stall.get("grade", "UNKNOWN"),
                    demerit_points=demerit if isinstance(demerit, int) else 0,
                    suspended=bool(stall.get("suspended", False)),
                )
            )
        return results

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
