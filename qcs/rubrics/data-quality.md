# Data Quality — Rubric

## Level 1
- Hardcoded sample data
- No real API integration

## Level 2
- Live API integration (NEA, Google Places)
- Small seed dataset (< 100 stalls)

## Level 3 (Current)
- 2,511 stalls across 122 hawker centres in ChromaDB
- Cuisine normalisation with 50+ keyword mappings
- Region-based filtering
- Michelin + halal static data
- Postal code matching for hygiene grades

## Level 4 (Target)
- Stall metadata validation (no empty descriptions, valid cuisine tags)
- Duplicate detection and deduplication
- Data freshness tracking (last-updated timestamps)
- Coverage report: % of centres with complete data

## Level 5
- Automated data refresh pipeline (scheduled)
- Data quality dashboard
- User feedback loop (report incorrect data)
- Cross-validation between sources (Google vs NEA vs seed)
