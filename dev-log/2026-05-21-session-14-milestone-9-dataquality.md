# Milestone 9 -- Data Quality Fixes

**Date:** 2026-05-21
**Type:** Backend data quality + tooling
**Branch:** main
**Tests:** 106/106 (+10 from baseline 96)
**Build:** Zero TS errors, 478 KB JS bundle
**Regressions:** 0

---

## Starting State

| Metric | Value |
|--------|-------|
| Tests | 96/96 |
| Bundle | 478 KB |
| Prior work | Milestone 8B (Design Wiki Run 01) shipped 5 UX patterns |
| Problems | Wrong cuisine returned, hygiene grades missing for ~60% centres, only 71 stalls |

---

## Fix B -- Cuisine hard-filter in RAG retrieval

### Problem

ChromaDB semantic search returns "claypot rice" when user queries "chicken rice" because
all rice dishes have high cosine similarity. No metadata-level filtering was applied.

### Solution

**`backend/rag/vector_store.py`**:
- `query()` gains `cuisine_filter: Optional[str]` and `region_filter: Optional[str]`
- When provided, adds a ChromaDB `where` clause (`$eq` on metadata fields)
- Falls back to unfiltered query if filtered returns 0 results
- `_build_where()` static method constructs `$and` for multiple filters

**`backend/agents/recommendation_agent.py`**:
- New `CUISINE_KEYWORDS` dict: 50+ entries mapping Singlish/abbreviations to canonical forms
  (e.g., "orh luak" → "oyster omelette", "prata" → "roti prata", "cai fan" → "economy rice")
- `_normalise_cuisine()` function: direct match → substring match → None
- `run()` extracts `cuisine_type` and `region` from preferences, normalises, and passes to vector store

**`backend/agents/orchestrator.py`**:
- `_PARSE_SYSTEM` prompt extended to extract `region` field from user query
- Region values: "central", "east", "west", "north", "north_east", ""
- Default fallback includes `region: ""`

### ChromaDB operator note

`$contains` does **not** work for metadata string fields in chromadb 1.5.7 — returns empty.
Used `$eq` instead, which works because all cuisine values are normalised to exact canonical forms.

---

## Fix C -- Hygiene grade matching improvement

### Problem

Jaccard token similarity at 0.4 threshold failed for ~60% of centres. Centre names like
"Bedok Interchange Hawker Centre" vs "Bedok Interchange Food Centre" share key tokens
but differ at the word level. A 0.4 threshold also caused false positives.

### Solution

**`backend/models/schemas.py`**:
- `LocationResult` gains `postcode: Optional[str] = None`

**`backend/agents/location_agent.py`**:
- Extracts 6-digit postal code from Google Places `formattedAddress` via `Singapore\s+(\d{6})`
- Tries both search response and detail response

**`backend/tools/nea_client.py`**:
- `_load_static_grades()` now returns two indexes: `by_name` (keyed by centre name) and `by_postcode` (keyed by 6-digit postal code)
- New `_name_similarity()` function: returns max of `SequenceMatcher.ratio()` and `_jaccard_similarity()`, both after noise word removal
- `get_static_hygiene_for_centre()` gains `postcode: str = ""` parameter
- Match priority:
  1. **Postal code** exact match (most reliable, deterministic)
  2. Centre name **exact** match
  3. **Substring** match in either direction
  4. **Combined similarity** ≥ 0.55 (raised from 0.4)

**`backend/agents/hygiene_agent.py`**:
- `run()` gains `postcodes: dict[str, str] | None` parameter
- Passes postcode to `get_static_hygiene_for_centre()` when available

**`backend/agents/orchestrator.py`**:
- Builds `centre_postcodes = {r.centre_name: r.postcode or "" for r in location_results}`
- Passes to `hygiene.run(centre_names, postcodes=centre_postcodes)`

---

## Fix A -- Data pipeline agent

### New file: `backend/tools/data_pipeline.py`

CLI tool to expand ChromaDB from 71 to 800+ stalls. Pipeline:

1. **Fetch centres**: All 123 NEA hawker centres with lat/lng from data.gov.sg
2. **Fetch stalls**: Google Places `searchNearby` within 200m of each centre
3. **Generate descriptions**: Claude Haiku generates 50-70 word descriptions per stall
4. **Classify cuisine**: Claude Haiku classifies cuisine type, tags, halal status, best time, price range
5. **Seed ChromaDB**: Batch upsert in chunks of 50

Features:
- Checkpoint/resume: saves per-centre results to `pipeline_checkpoint.json`
- Rate limiting: 0.3s between Places calls, 0.2s between Claude calls
- Region classification from lat/lng bounding boxes
- Michelin/halal tagging from existing static JSON lists
- Output: `expanded_stalls.json` + ChromaDB seeding

**Usage:**
```bash
cd backend
python -m tools.data_pipeline --centres 3 --dry-run    # preview
python -m tools.data_pipeline --centres 10              # 10 centres
python -m tools.data_pipeline                           # all 123 centres
```

### Dry-run results

```
Centres total:     123
Centres processed: 3
Stalls total:      0 (GOOGLE_PLACES_API_KEY not set in dev environment)
Dry run:           True
```

Pipeline fetches 123 centres from NEA successfully. Stall expansion requires
production API keys (`GOOGLE_PLACES_API_KEY` + `ANTHROPIC_API_KEY`).

---

## Files changed

| File | Change |
|------|--------|
| `backend/rag/vector_store.py` | Modified -- `cuisine_filter`/`region_filter` params, `_build_where()`, fallback logic |
| `backend/agents/recommendation_agent.py` | Modified -- `CUISINE_KEYWORDS` dict, `_normalise_cuisine()`, cuisine/region filter passthrough |
| `backend/agents/orchestrator.py` | Modified -- `region` extraction in `_PARSE_SYSTEM`, postcode threading to hygiene agent |
| `backend/agents/hygiene_agent.py` | Modified -- `postcodes` parameter, postal code passthrough |
| `backend/agents/location_agent.py` | Modified -- postcode extraction from Google Places address |
| `backend/models/schemas.py` | Modified -- `postcode` field on `LocationResult` |
| `backend/tools/nea_client.py` | Modified -- postal code index, `_name_similarity()`, SequenceMatcher, threshold 0.55 |
| `backend/tools/data_pipeline.py` | **New** -- data expansion pipeline CLI |
| `backend/tests/test_vector_store.py` | +3 tests (cuisine filter, fallback, region filter) |
| `backend/tests/test_recommendation_agent.py` | +4 tests (normalise cuisine, filter passthrough) |
| `backend/tests/test_nea_client.py` | +3 tests (postcode priority, SequenceMatcher, reject unrelated) |
