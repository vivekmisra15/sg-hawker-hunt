"""
Data pipeline: expand the ChromaDB knowledge base from 71 to 800+ stalls.

Steps:
  1. Fetch all NEA hawker centres (120+ centres with lat/lng)
  2. For each centre, search Google Places for food stalls nearby
  3. Generate rich descriptions via Claude Haiku
  4. Seed ChromaDB with the expanded dataset

Usage:
  cd backend
  python -m tools.data_pipeline                    # full run
  python -m tools.data_pipeline --centres 3        # dry run: 3 centres
  python -m tools.data_pipeline --dry-run          # preview only, no ChromaDB writes
"""
import argparse
import asyncio
import hashlib
import json
import logging
import os
import re
import sys
import time
from pathlib import Path

import anthropic
import httpx

# Ensure backend/ is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.schemas import CentreInfo
from rag.vector_store import VectorStore
from tools.nea_client import NEAClient, NEAClientError
from tools.places_client import PlacesClient, PlacesClientError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Output file for generated stall data (can be re-seeded without re-fetching)
_OUTPUT_DIR = Path(__file__).parent.parent / "data"
_OUTPUT_FILE = _OUTPUT_DIR / "expanded_stalls.json"
_CHECKPOINT_FILE = _OUTPUT_DIR / "pipeline_checkpoint.json"

# Michelin and halal lists for tagging
_DATA_DIR = Path(__file__).parent.parent / "data"

# Rate limiting
_PLACES_DELAY = 0.3  # seconds between Places API calls
_CLAUDE_DELAY = 0.2  # seconds between Claude calls

# Singapore regions by approximate lat/lng bounding boxes
_REGION_BOUNDS = {
    "central": (1.26, 1.32, 103.80, 103.88),
    "east": (1.28, 1.36, 103.88, 104.05),
    "west": (1.28, 1.36, 103.60, 103.76),
    "north": (1.36, 1.48, 103.72, 103.88),
    "north_east": (1.32, 1.42, 103.84, 103.96),
}


def _classify_region(lat: float, lng: float) -> str:
    """Classify a lat/lng into a Singapore region."""
    for region, (lat_min, lat_max, lng_min, lng_max) in _REGION_BOUNDS.items():
        if lat_min <= lat <= lat_max and lng_min <= lng <= lng_max:
            return region
    # Fallback: pick closest region by centre distance
    return "central"


def _load_json_set(filename: str) -> set[str]:
    """Load a JSON list file as an uppercase set."""
    path = _DATA_DIR / filename
    try:
        with open(path) as f:
            return {s.upper() for s in json.load(f)}
    except Exception:
        return set()


def _make_stall_id(centre_name: str, stall_name: str) -> str:
    """Generate a stable, unique stall ID."""
    raw = f"{centre_name}::{stall_name}".lower().strip()
    short_hash = hashlib.md5(raw.encode()).hexdigest()[:8]
    slug = re.sub(r"[^a-z0-9]+", "_", raw)[:60]
    return f"{slug}_{short_hash}"


def _load_checkpoint() -> dict:
    """Load checkpoint: {centre_name: [stall_dicts]}."""
    if _CHECKPOINT_FILE.exists():
        try:
            with open(_CHECKPOINT_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_checkpoint(data: dict) -> None:
    """Save checkpoint incrementally."""
    with open(_CHECKPOINT_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


_DESCRIPTION_SYSTEM = """You are a Singapore hawker food expert. Generate a 50-70 word description
for a hawker stall. Include: signature dishes, cooking style, what makes it special,
typical price range if known, and any notable features (queue length, awards, etc).
Write in an informative, appetising style. Do NOT include the stall name or centre name
in the description — those are provided separately.
Return ONLY the description text, no quotes, no markdown."""

_CUISINE_SYSTEM = """You are a Singapore food classifier. Given a stall name, return ONLY
a JSON object with:
  cuisine: the primary cuisine type (e.g. "chicken rice", "laksa", "nasi lemak", "roti prata")
  tags: list of 3-5 relevant tags
  is_halal: true/false based on the stall name (e.g. if it mentions "Muslim", "Halal", "Nasi Padang")
  best_time: suggested best time to visit (e.g. "Before 11am", "12pm-2pm", "7pm-9pm", "any")
  price_range: estimated price range (e.g. "S$3-5", "S$5-8", "S$8-12")
No markdown, no explanation — just the JSON object."""


async def fetch_centres(nea: NEAClient) -> list[CentreInfo]:
    """Fetch all NEA hawker centres.

    Note: the data.gov.sg fields are lowercase (name, latitude_hc, longitude_hc)
    but NEAClient.get_centres() expects uppercase. We fetch raw records and parse
    ourselves to handle both cases.
    """
    records = await nea._fetch(nea.CENTRES_RESOURCE)
    centres = []
    for r in records:
        try:
            name = r.get("name") or r.get("NAME") or ""
            lat_raw = r.get("latitude_hc") or r.get("LATITUDE") or r.get("latitude")
            lng_raw = r.get("longitude_hc") or r.get("LONGITUDE") or r.get("longitude")
            address = r.get("address_myenv") or r.get("ADDRESSSTREETNAME") or ""
            if not name or not lat_raw or not lng_raw:
                continue
            centres.append(CentreInfo(
                centre_id=str(r.get("_id", "")),
                name=name,
                address=address,
                lat=float(lat_raw),
                lng=float(lng_raw),
            ))
        except (ValueError, TypeError) as e:
            logger.warning("Skipping centre record: %s", e)
    logger.info("Fetched %d NEA hawker centres", len(centres))
    return centres


async def fetch_stalls_for_centre(
    places: PlacesClient, centre: CentreInfo, delay: float = _PLACES_DELAY
) -> list[dict]:
    """Search Google Places for food stalls near a hawker centre."""
    await asyncio.sleep(delay)
    try:
        # Search within 200m of the centre — catches stalls inside the complex
        results = await places.search_nearby(centre.lat, centre.lng, radius_km=0.2)
        stalls = []
        for place in results:
            display_name = place.get("displayName", {}).get("text", "")
            if not display_name:
                continue
            loc = place.get("location", {})
            stalls.append({
                "name": display_name,
                "rating": place.get("rating"),
                "review_count": place.get("userRatingCount"),
                "price_level": place.get("priceLevel"),
                "lat": loc.get("latitude"),
                "lng": loc.get("longitude"),
            })
        return stalls
    except PlacesClientError as e:
        logger.warning("Places search failed for %s: %s", centre.name, e)
        return []


async def generate_description(
    client: anthropic.AsyncAnthropic, stall_name: str, centre_name: str
) -> str:
    """Generate a rich description via Claude Haiku."""
    try:
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            system=_DESCRIPTION_SYSTEM,
            messages=[{"role": "user", "content": f"Stall: {stall_name}\nCentre: {centre_name}"}],
        )
        return response.content[0].text.strip()
    except Exception as e:
        logger.warning("Description generation failed for %s: %s", stall_name, e)
        return f"A popular hawker stall at {centre_name} serving local dishes."


async def classify_cuisine(
    client: anthropic.AsyncAnthropic, stall_name: str
) -> dict:
    """Classify cuisine type and tags via Claude Haiku."""
    try:
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            system=_CUISINE_SYSTEM,
            messages=[{"role": "user", "content": stall_name}],
        )
        raw = response.content[0].text.strip()
        return json.loads(raw)
    except Exception as e:
        logger.warning("Cuisine classification failed for %s: %s", stall_name, e)
        return {
            "cuisine": "mixed",
            "tags": ["hawker"],
            "is_halal": False,
            "best_time": "any",
            "price_range": "S$3-8",
        }


async def process_centre(
    centre: CentreInfo,
    places: PlacesClient,
    claude: anthropic.AsyncAnthropic,
    michelin_names: set[str],
    halal_names: set[str],
) -> list[dict]:
    """Process one centre: fetch stalls, generate descriptions, classify cuisines."""
    stalls_raw = await fetch_stalls_for_centre(places, centre)
    if not stalls_raw:
        logger.info("  %s: no stalls found via Places API", centre.name)
        return []

    region = _classify_region(centre.lat, centre.lng)
    processed = []

    for stall in stalls_raw:
        stall_name = stall["name"]

        # Generate description and classify in parallel
        await asyncio.sleep(_CLAUDE_DELAY)
        desc, cuisine_info = await asyncio.gather(
            generate_description(claude, stall_name, centre.name),
            classify_cuisine(claude, stall_name),
        )

        is_michelin = stall_name.upper() in michelin_names
        is_halal = (
            stall_name.upper() in halal_names
            or cuisine_info.get("is_halal", False)
        )

        stall_doc = {
            "id": _make_stall_id(centre.name, stall_name),
            "text": f"{stall_name} at {centre.name}. {desc}",
            "metadata": {
                "centre_name": centre.name,
                "stall_name": stall_name,
                "cuisine": cuisine_info.get("cuisine", "mixed"),
                "region": region,
                "tags": cuisine_info.get("tags", ["hawker"]),
                "is_michelin": is_michelin,
                "is_halal": is_halal,
                "best_time": cuisine_info.get("best_time", "any"),
                "avoid_time": "",
                "price_range": cuisine_info.get("price_range", "S$3-8"),
            },
        }
        processed.append(stall_doc)

    logger.info("  %s: %d stalls processed (region=%s)", centre.name, len(processed), region)
    return processed


async def run_pipeline(
    max_centres: int | None = None,
    dry_run: bool = False,
    resume: bool = True,
) -> dict:
    """
    Main pipeline entry point.
    Returns summary dict with counts.
    """
    nea = NEAClient()
    places = PlacesClient()
    claude = anthropic.AsyncAnthropic()

    michelin_names = _load_json_set("michelin_2025.json")
    halal_names = _load_json_set("halal_stalls.json")

    # Fetch centres
    centres = await fetch_centres(nea)
    if max_centres:
        centres = centres[:max_centres]

    # Load checkpoint for resume
    checkpoint = _load_checkpoint() if resume else {}
    skipped = 0

    all_stalls: list[dict] = []

    # Include already-checkpointed stalls
    for centre_name, stalls in checkpoint.items():
        all_stalls.extend(stalls)

    for i, centre in enumerate(centres, 1):
        if centre.name in checkpoint:
            skipped += 1
            continue

        logger.info("[%d/%d] Processing %s...", i, len(centres), centre.name)
        stalls = await process_centre(centre, places, claude, michelin_names, halal_names)

        checkpoint[centre.name] = stalls
        all_stalls.extend(stalls)
        _save_checkpoint(checkpoint)

    # Save expanded stalls to JSON
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(_OUTPUT_FILE, "w") as f:
        json.dump(all_stalls, f, indent=2, ensure_ascii=False)
    logger.info("Saved %d stalls to %s", len(all_stalls), _OUTPUT_FILE.name)

    # Seed ChromaDB
    if not dry_run and all_stalls:
        logger.info("Seeding ChromaDB with %d stalls...", len(all_stalls))
        vs = VectorStore()
        # Batch in chunks of 50
        for chunk_start in range(0, len(all_stalls), 50):
            chunk = all_stalls[chunk_start:chunk_start + 50]
            vs.add_documents(chunk)
        logger.info("ChromaDB seeded. Collection size: %d", vs.collection_size())

    summary = {
        "centres_total": len(centres),
        "centres_processed": len(centres) - skipped,
        "centres_skipped": skipped,
        "stalls_total": len(all_stalls),
        "dry_run": dry_run,
    }
    logger.info("Pipeline complete: %s", json.dumps(summary))
    return summary


def main():
    parser = argparse.ArgumentParser(description="Expand hawker stall knowledge base")
    parser.add_argument("--centres", type=int, default=None,
                        help="Max centres to process (default: all)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview only — do not write to ChromaDB")
    parser.add_argument("--no-resume", action="store_true",
                        help="Ignore checkpoint, start fresh")
    args = parser.parse_args()

    summary = asyncio.run(run_pipeline(
        max_centres=args.centres,
        dry_run=args.dry_run,
        resume=not args.no_resume,
    ))

    print(f"\n{'='*50}")
    print(f"Pipeline Summary")
    print(f"{'='*50}")
    print(f"Centres total:     {summary['centres_total']}")
    print(f"Centres processed: {summary['centres_processed']}")
    print(f"Centres skipped:   {summary['centres_skipped']}")
    print(f"Stalls total:      {summary['stalls_total']}")
    print(f"Dry run:           {summary['dry_run']}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
