"""
sfa_scraper.py — One-off tool to scrape SFA Track Records hygiene grades by postal code.

The SFA Track Records page is a JavaScript-rendered page with no public API. This scraper
uses Playwright to automate a headless browser and extract stall grades for all NEA hawker
centres.

Usage:
    cd backend
    python -m tools.sfa_scraper                               # scrape all centres
    python -m tools.sfa_scraper --fresh                       # ignore checkpoint, re-scrape all
    python -m tools.sfa_scraper --postal-codes 068805,018936  # specific centres only
    python -m tools.sfa_scraper --delay 3.0                   # seconds between requests (default 3.0)
    python -m tools.sfa_scraper --dry-run                     # list centres without scraping

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
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

# ── File paths ────────────────────────────────────────────────────────────────
_DATA_DIR = Path(__file__).parent.parent / "data"
_CHECKPOINT_FILE = _DATA_DIR / "scrape_checkpoint.json"
_OUTPUT_FILE = _DATA_DIR / "hygiene_grades_full.json"

# ── SFA website config ────────────────────────────────────────────────────────
SFA_BASE_URL = "https://www.sfa.gov.sg"
SFA_TRACK_RECORDS_URL = f"{SFA_BASE_URL}/food-safety/food-hygiene/track-records"

# CSS selectors — update here if SFA redesigns the page
SELECTORS = {
    "search_input": 'input[placeholder*="postal" i], input[name*="postal" i], input[id*="postal" i], input[type="text"]',
    "search_button": 'button[type="submit"], button:has-text("Search"), input[type="submit"]',
    "results_table": "table",
    "table_rows": "tbody tr",
    "no_results_indicator": "No records",
}

# Retry config
_RETRY_DELAYS = [5, 15, 45]  # seconds between retries (±2s jitter added)
_CHECKPOINT_FRESHNESS_HOURS = 24  # skip centres scraped within this window

# ── Grade normalisation ───────────────────────────────────────────────────────
# SAFE framework grades (Jan 2026 replacement for A/B/C):
#   NEW → treat as B (new operator, no violations yet)
#   NOT_UNDER_SAFE → UNKNOWN (exempt premises)
#   *_UNDER_REVIEW → base grade (review in progress, underlying grade still applies)
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
    """Map SFA/SAFE grade string to A/B/C/D/UNKNOWN."""
    cleaned = raw.strip().upper().replace(" ", "_").replace("-", "_")
    return _GRADE_NORMALISE.get(cleaned, "UNKNOWN")


def _jitter(seconds: float) -> float:
    return seconds + random.uniform(-2.0, 2.0)


# ── NEA centre list ───────────────────────────────────────────────────────────

async def _fetch_nea_centres() -> list[dict]:
    """
    Return a list of {name, postal_code} dicts from the NEA hawker centre dataset.
    Falls back to an empty list (caller handles it) on any error.
    """
    url = "https://data.gov.sg/api/action/datastore_search"
    params = {"resource_id": "b80cb643-a732-480d-86b5-e03957bc82aa", "limit": 200}
    headers = {}
    key = os.getenv("DATAGOV_API_KEY")
    if key:
        headers["X-Api-Key"] = key
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        records = resp.json()["result"]["records"]
    except Exception as e:
        logger.error("Failed to fetch NEA centre list: %s", e)
        return []
    centres = []
    for r in records:
        postal = str(r.get("ADDRESSPOSTALCODE", "")).strip().zfill(6)
        name = r.get("NAME", "").strip()
        if postal and postal != "000000" and name:
            centres.append({"name": name, "postal_code": postal})
    return centres


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


# ── Playwright scraper ────────────────────────────────────────────────────────

async def _scrape_centre_with_retry(
    page, postal_code: str, centre_name: str, max_retries: int = 3
) -> dict:
    """
    Attempt to scrape one centre, with exponential backoff on failure.
    Returns a centre result dict (stalls may be empty on persistent failure).
    """
    for attempt in range(max_retries + 1):
        try:
            return await _scrape_one_centre(page, postal_code, centre_name)
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


async def _scrape_one_centre(page, postal_code: str, centre_name: str) -> dict:
    """Navigate to SFA Track Records, search by postal code, extract table."""
    await page.goto(SFA_TRACK_RECORDS_URL, wait_until="networkidle", timeout=30_000)

    # Locate and fill the postal code input
    search_input = page.locator(SELECTORS["search_input"]).first
    await search_input.wait_for(state="visible", timeout=10_000)
    await search_input.fill("")
    await search_input.type(postal_code, delay=80)

    # Submit
    search_btn = page.locator(SELECTORS["search_button"]).first
    await search_btn.click()

    # Wait for table or no-results indicator
    try:
        await page.wait_for_selector(
            f'{SELECTORS["results_table"]}, :text("{SELECTORS["no_results_indicator"]}")',
            timeout=15_000,
        )
    except Exception:
        # If neither appears, capture page content for debugging
        raise RuntimeError("Timed out waiting for results table or no-results indicator")

    # Check for no-results
    no_results = await page.locator(
        f':text("{SELECTORS["no_results_indicator"]}")'
    ).count()
    if no_results > 0:
        return _build_result(postal_code, centre_name, stalls=[], error=None)

    # Extract table rows
    table = page.locator(SELECTORS["results_table"]).first
    rows = await table.locator(SELECTORS["table_rows"]).all()

    stalls = []
    for row in rows:
        cells = await row.locator("td").all_text_contents()
        cells = [c.strip() for c in cells]
        if len(cells) < 3:
            continue
        stall = _parse_row(cells)
        if stall:
            stalls.append(stall)

    return _build_result(postal_code, centre_name, stalls=stalls, error=None)


def _parse_row(cells: list[str]) -> dict | None:
    """
    Parse a table row into a stall dict.
    Expected column order (SFA Track Records as of 2026-01):
      [0] Licensee Name
      [1] Licence Number
      [2] Grade
      [3] Demerit Points  (optional — may not be present)
      [4] Suspension Start Date (optional)

    Returns None for header rows or rows that can't be parsed.
    """
    if not cells or not cells[0] or cells[0].lower() in ("licensee name", "name", "operator"):
        return None  # header row
    licensee_name = cells[0].upper()
    licence_number = cells[1] if len(cells) > 1 else ""

    raw_grade = cells[2] if len(cells) > 2 else ""
    grade = _normalise_grade(raw_grade)

    demerit_raw = cells[3] if len(cells) > 3 else "0"
    try:
        demerit_points = int(demerit_raw)
    except ValueError:
        demerit_points = 0

    suspension_raw = cells[4] if len(cells) > 4 else ""
    suspended = bool(suspension_raw and suspension_raw.lower() not in ("", "na", "n/a", "-"))

    return {
        "licensee_name": licensee_name,
        "licence_number": licence_number,
        "grade": grade,
        "demerit_points": demerit_points,
        "suspended": suspended,
    }


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


# ── Final output consolidation ─────────────────────────────────────────────────

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
    delay: float = 3.0,
    dry_run: bool = False,
) -> None:
    try:
        from playwright.async_api import async_playwright  # type: ignore[import]
    except ImportError:
        print(
            "ERROR: playwright not installed.\n"
            "Run: pip install -r requirements-tools.txt && playwright install chromium"
        )
        return

    centres = await _fetch_nea_centres()
    if not centres:
        print("ERROR: Could not fetch NEA centre list. Check DATAGOV_API_KEY in .env.")
        return

    # Apply postal code filter
    if postal_codes_filter:
        filter_set = set(p.strip().zfill(6) for p in postal_codes_filter)
        centres = [c for c in centres if c["postal_code"] in filter_set]
        if not centres:
            print(f"No centres matched postal codes: {postal_codes_filter}")
            return

    # Deduplicate postal codes (some centres share a postcode in NEA data)
    seen: set[str] = set()
    unique_centres = []
    for c in centres:
        if c["postal_code"] not in seen:
            seen.add(c["postal_code"])
            unique_centres.append(c)
    centres = unique_centres

    total = len(centres)
    print(f"SFA Track Records scraper — {total} centres to process")

    if dry_run:
        for i, c in enumerate(centres, 1):
            print(f"  [{i}/{total}] {c['name']} ({c['postal_code']})")
        return

    checkpoint = {} if fresh else _load_checkpoint()
    skipped = 0

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-SG",
        )
        page = await context.new_page()

        try:
            for i, centre in enumerate(centres, 1):
                postal = centre["postal_code"]
                name = centre["name"]
                prefix = f"[{i}/{total}] {name} ({postal})"

                # Skip if fresh checkpoint entry exists
                if postal in checkpoint and _is_fresh(checkpoint[postal]):
                    skipped += 1
                    print(f"{prefix} ↩ skipped (fresh checkpoint)")
                    continue

                print(f"{prefix} ...", end=" ", flush=True)
                t0 = time.monotonic()
                result = await _scrape_centre_with_retry(page, postal, name)
                elapsed = time.monotonic() - t0

                stall_count = result.get("stall_count", 0)
                gc = result.get("grade_counts", {})
                gc_str = ", ".join(f"{g}:{n}" for g, n in sorted(gc.items())) or "—"
                status = "✓" if not result.get("error") else "✗"
                print(f"{stall_count} stalls ({gc_str}) {status} {elapsed:.1f}s")

                _save_checkpoint(checkpoint, postal, result)

                # Polite delay between requests
                if i < total:
                    await asyncio.sleep(_jitter(delay))

        finally:
            await browser.close()

    print(f"\nDone. {skipped} centres skipped (fresh checkpoint).")
    _write_output(checkpoint)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Scrape SFA Track Records hygiene grades")
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Ignore existing checkpoint and re-scrape all centres",
    )
    parser.add_argument(
        "--postal-codes",
        metavar="CODES",
        help="Comma-separated postal codes to scrape (e.g. 068805,018936)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=3.0,
        metavar="SECONDS",
        help="Base delay between requests in seconds (default: 3.0, ±2s jitter applied)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print centres that would be scraped without making any requests",
    )
    args = parser.parse_args()

    postal_codes_filter: list[str] | None = None
    if args.postal_codes:
        postal_codes_filter = [p.strip() for p in args.postal_codes.split(",") if p.strip()]

    asyncio.run(
        run(
            fresh=args.fresh,
            postal_codes_filter=postal_codes_filter,
            delay=args.delay,
            dry_run=args.dry_run,
        )
    )


if __name__ == "__main__":
    main()
