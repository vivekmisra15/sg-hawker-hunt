"""
sfa_scraper.py — Fetches SFA Track Records hygiene grades for all NEA hawker centres.

SFA exposes a REST API at /api/TrackRecord/GetTrackRecord (discovered by inspecting the
Track Records page JS). A single page load obtains the ASP.NET session cookie; subsequent
calls are plain httpx GETs — no Playwright required.

Usage:
    cd backend
    python -m tools.sfa_scraper                               # fetch all centres
    python -m tools.sfa_scraper --fresh                       # ignore checkpoint, re-fetch all
    python -m tools.sfa_scraper --postal-codes 069184,289876  # specific centres only
    python -m tools.sfa_scraper --delay 1.0                   # seconds between requests (default 1.0)
    python -m tools.sfa_scraper --dry-run                     # list centres without fetching

Output files (both gitignored via backend/data/ in .gitignore):
    backend/data/hygiene_grades_full.json   final consolidated output
    backend/data/scrape_checkpoint.json     per-centre progress for crash recovery
"""

import argparse
import asyncio
import json
import logging
import os
import random
import re
import time
from datetime import datetime, timezone
from pathlib import Path

# Load .env from project root so DATAGOV_API_KEY is available
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / ".env")
except ImportError:
    pass

import httpx

logger = logging.getLogger(__name__)

# ── File paths ────────────────────────────────────────────────────────────────
_DATA_DIR = Path(__file__).parent.parent / "data"
_CHECKPOINT_FILE = _DATA_DIR / "scrape_checkpoint.json"
_OUTPUT_FILE = _DATA_DIR / "hygiene_grades_full.json"

# ── SFA API config ────────────────────────────────────────────────────────────
SFA_PAGE_URL = "https://www.sfa.gov.sg/tools-and-resources/track-records"
SFA_API_URL = "https://www.sfa.gov.sg/api/TrackRecord/GetTrackRecord"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": SFA_PAGE_URL,
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
}

# Retry config
_RETRY_DELAYS = [5, 15, 45]  # seconds between retries (±2s jitter added)
_CHECKPOINT_FRESHNESS_HOURS = 24

# ── Grade normalisation ───────────────────────────────────────────────────────
_GRADE_NORMALISE = {
    "A": "A",
    "B": "B",
    "C": "C",
    "D": "D",
    "NEW": "B",
    "NOT_UNDER_SAFE": "UNKNOWN",
    "A_UNDER_REVIEW": "A",
    "B_UNDER_REVIEW": "B",
    "C_UNDER_REVIEW": "C",
    "NEW_UNDER_REVIEW": "B",
}


def _normalise_grade(raw: str) -> str:
    cleaned = raw.strip().upper().replace(" ", "_").replace("-", "_")
    return _GRADE_NORMALISE.get(cleaned, "UNKNOWN")


def _jitter(seconds: float) -> float:
    return max(0.5, seconds + random.uniform(-1.0, 1.0))


# ── NEA centre list ───────────────────────────────────────────────────────────

async def _fetch_nea_centres(client: httpx.AsyncClient) -> list[dict]:
    """Return list of {name, postal_code} from the NEA hawker centre dataset."""
    params = {"resource_id": "b80cb643-a732-480d-86b5-e03957bc82aa", "limit": 200}
    headers: dict = {}
    key = os.getenv("DATAGOV_API_KEY")
    if key:
        headers["X-Api-Key"] = key
    try:
        resp = await client.get(
            "https://data.gov.sg/api/action/datastore_search",
            params=params, headers=headers,
        )
        resp.raise_for_status()
        records = resp.json()["result"]["records"]
    except Exception as e:
        logger.error("Failed to fetch NEA centre list: %s", e)
        return []
    centres = []
    for r in records:
        name = (r.get("name") or r.get("NAME") or "").strip()
        address = r.get("address_myenv") or ""
        m = re.search(r"Singapore\s+(\d{6})", address, re.IGNORECASE)
        postal = m.group(1) if m else str(r.get("ADDRESSPOSTALCODE", "")).strip().zfill(6)
        if postal and postal != "000000" and name:
            centres.append({"name": name, "postal_code": postal})
    return centres


# ── Session management ─────────────────────────────────────────────────────────

async def _init_session(client: httpx.AsyncClient) -> bool:
    """Load the SFA page once to acquire an ASP.NET session cookie."""
    try:
        resp = await client.get(SFA_PAGE_URL, headers={"User-Agent": _HEADERS["User-Agent"]})
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error("Failed to initialise SFA session: %s", e)
        return False


# ── Per-centre fetch ──────────────────────────────────────────────────────────

async def _fetch_centre_with_retry(
    client: httpx.AsyncClient, postal_code: str, centre_name: str, max_retries: int = 3
) -> dict:
    for attempt in range(max_retries + 1):
        try:
            return await _fetch_one_centre(client, postal_code, centre_name)
        except Exception as e:
            if attempt < max_retries:
                delay = _jitter(_RETRY_DELAYS[min(attempt, len(_RETRY_DELAYS) - 1)])
                logger.warning(
                    "[%s] attempt %d/%d failed: %s — retrying in %.1fs",
                    postal_code, attempt + 1, max_retries + 1, e, delay,
                )
                await asyncio.sleep(delay)
            else:
                logger.error("[%s] all %d attempts failed: %s", postal_code, max_retries + 1, e)
                return _error_result(postal_code, centre_name, str(e))
    return _error_result(postal_code, centre_name, "exhausted retries")


async def _fetch_one_centre(
    client: httpx.AsyncClient, postal_code: str, centre_name: str
) -> dict:
    resp = await client.get(
        SFA_API_URL,
        params={
            "postalCode": postal_code,
            "establishmentAddress": "",
            "licenceNumber": "",
            "businessName": "",
            "licenseeName": "",
            "typeOfFoodBussiness": "",
            "isShowLicenceSuspended": "false",
            "grades": "",
        },
        headers=_HEADERS,
    )
    if resp.status_code == 404:
        # Session expired — re-initialise and raise so retry logic picks it up
        await _init_session(client)
        raise RuntimeError("Session expired (got 404), re-initialised")
    resp.raise_for_status()
    records = resp.json().get("data", [])
    stalls = [_parse_record(r) for r in records]
    return _build_result(postal_code, centre_name, stalls=stalls, error=None)


def _parse_record(r: dict) -> dict:
    """Convert one SFA API record to our stall dict."""
    return {
        "licensee_name": (r.get("licenseeName") or "").upper(),
        "licence_number": r.get("licenceNumber") or "",
        "business_name": r.get("businessName") or "",
        "grade": _normalise_grade(r.get("grades") or ""),
        "demerit_points": 0,   # API doesn't return demerit points
        "suspended": False,    # suspension data not available in this endpoint
    }


# ── Result helpers ────────────────────────────────────────────────────────────

def _build_result(postal_code: str, centre_name: str, stalls: list, error: str | None) -> dict:
    now = datetime.now(tz=timezone.utc).isoformat()
    grade_counts: dict[str, int] = {}
    for s in stalls:
        g = s.get("grade", "UNKNOWN")
        grade_counts[g] = grade_counts.get(g, 0) + 1
    return {
        "centre_name": centre_name,
        "postal_code": postal_code,
        "stall_count": len(stalls),
        "grade_counts": grade_counts,
        "scraped_at": now,
        "error": error,
        "stalls": stalls,
    }


def _error_result(postal_code: str, centre_name: str, message: str) -> dict:
    return _build_result(postal_code, centre_name, stalls=[], error=message)


# ── Checkpoint helpers ────────────────────────────────────────────────────────

def _load_checkpoint() -> dict:
    if _CHECKPOINT_FILE.exists():
        try:
            with open(_CHECKPOINT_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_checkpoint(checkpoint: dict, postal_code: str, result: dict) -> None:
    checkpoint[postal_code] = result
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(_CHECKPOINT_FILE, "w") as f:
        json.dump(checkpoint, f, indent=2, ensure_ascii=False)


def _is_fresh(result: dict) -> bool:
    scraped_at = result.get("scraped_at", "")
    if not scraped_at:
        return False
    try:
        ts = datetime.fromisoformat(scraped_at)
        age_hours = (datetime.now(tz=timezone.utc) - ts).total_seconds() / 3600
        return age_hours < _CHECKPOINT_FRESHNESS_HOURS
    except ValueError:
        return False


# ── Output consolidation ──────────────────────────────────────────────────────

def _write_output(checkpoint: dict) -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    total_stalls = sum(v.get("stall_count", 0) for v in checkpoint.values())
    attempted = len(checkpoint)
    scraped = sum(1 for v in checkpoint.values() if not v.get("error"))
    grade_totals: dict[str, int] = {}
    for v in checkpoint.values():
        for g, c in v.get("grade_counts", {}).items():
            grade_totals[g] = grade_totals.get(g, 0) + c

    output = {
        "metadata": {
            "version": datetime.now(tz=timezone.utc).strftime("%Y-%m-%d"),
            "total_centres_scraped": scraped,
            "total_centres_attempted": attempted,
            "total_stalls": total_stalls,
            "grade_totals": grade_totals,
            "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        },
        "centres": checkpoint,
    }
    with open(_OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Output written to {_OUTPUT_FILE}")
    print(f"  Centres: {scraped}/{attempted} successful")
    print(f"  Total stalls: {total_stalls}")
    print(f"  Grade breakdown: {grade_totals}")


# ── Main entry point ──────────────────────────────────────────────────────────

async def run(
    fresh: bool = False,
    postal_codes_filter: list[str] | None = None,
    delay: float = 1.0,
    dry_run: bool = False,
) -> None:
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        centres = await _fetch_nea_centres(client)
        if not centres:
            print("ERROR: Could not fetch NEA centre list. Check DATAGOV_API_KEY in .env.")
            return

        if postal_codes_filter:
            filter_set = set(p.strip().zfill(6) for p in postal_codes_filter)
            centres = [c for c in centres if c["postal_code"] in filter_set]
            if not centres:
                print(f"No centres matched postal codes: {postal_codes_filter}")
                return

        # Deduplicate by postal code
        seen: set[str] = set()
        centres = [c for c in centres if not (c["postal_code"] in seen or seen.add(c["postal_code"]))]  # type: ignore[func-returns-value]

        total = len(centres)
        print(f"SFA Track Records fetcher — {total} centres to process")

        if dry_run:
            for i, c in enumerate(centres, 1):
                print(f"  [{i}/{total}] {c['name']} ({c['postal_code']})")
            return

        # Acquire session cookie
        print("Initialising SFA session...", end=" ", flush=True)
        if not await _init_session(client):
            print("FAILED")
            return
        print("OK")

        checkpoint = {} if fresh else _load_checkpoint()
        skipped = 0

        for i, centre in enumerate(centres, 1):
            postal = centre["postal_code"]
            name = centre["name"]
            prefix = f"[{i}/{total}] {name} ({postal})"

            if postal in checkpoint and _is_fresh(checkpoint[postal]):
                skipped += 1
                print(f"{prefix} ↩ skipped (fresh checkpoint)")
                continue

            print(f"{prefix} ...", end=" ", flush=True)
            t0 = time.monotonic()
            result = await _fetch_centre_with_retry(client, postal, name)
            elapsed = time.monotonic() - t0

            stall_count = result.get("stall_count", 0)
            gc = result.get("grade_counts", {})
            gc_str = ", ".join(f"{g}:{n}" for g, n in sorted(gc.items())) or "—"
            status = "✓" if not result.get("error") else "✗"
            print(f"{stall_count} stalls ({gc_str}) {status} {elapsed:.1f}s")

            _save_checkpoint(checkpoint, postal, result)

            if i < total:
                await asyncio.sleep(_jitter(delay))

    print(f"\nDone. {skipped} centres skipped (fresh checkpoint).")
    _write_output(checkpoint)


def main() -> None:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Fetch SFA Track Records hygiene grades")
    parser.add_argument("--fresh", action="store_true",
                        help="Ignore existing checkpoint and re-fetch all centres")
    parser.add_argument("--postal-codes", metavar="CODES",
                        help="Comma-separated postal codes (e.g. 069184,289876)")
    parser.add_argument("--delay", type=float, default=1.0, metavar="SECONDS",
                        help="Base delay between requests in seconds (default: 1.0)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print centres without fetching")
    args = parser.parse_args()

    postal_codes_filter: list[str] | None = None
    if args.postal_codes:
        postal_codes_filter = [p.strip() for p in args.postal_codes.split(",") if p.strip()]

    asyncio.run(run(
        fresh=args.fresh,
        postal_codes_filter=postal_codes_filter,
        delay=args.delay,
        dry_run=args.dry_run,
    ))


if __name__ == "__main__":
    main()
