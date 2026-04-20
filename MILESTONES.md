# Hawker Hunt — Build Progress

## Milestone 1 — Foundation ✓
- [x] FastAPI health endpoint
- [x] NEA client (hygiene grades + closures)
- [x] Google Places client
- [x] OneMap client
- [x] OpenWeather client
- [x] Pydantic schemas complete
- [x] All clients have passing tests

## Milestone 2 — Agents ✓
- [x] Hygiene Agent
- [x] Location Agent
- [x] Recommendation Agent + ChromaDB RAG
- [x] Orchestrator Agent
- [x] All agents have passing tests

## Milestone 3 — Streaming + Frontend ✓
- [x] POST /api/search SSE endpoint
- [x] Frontend useSSE hook
- [x] AgentPanel component renders live stream
- [x] SearchBar submits and connects to SSE
- [x] ResultCard + ResultsList components
- [x] Full dark theme UI (DM Sans + JetBrains Mono)
- [x] 30/30 tests passing, zero TypeScript errors

## Data Fix ✓ (2026-04-20)
- [x] NEA API auth corrected (X-Api-Key header, v2 key format)
- [x] NEA hygiene resource ID updated to current dataset
- [x] RAG seed expanded: 35 → 71 stalls, full island coverage
- [x] region field + list-typed tags on all stall entries
- [x] 30/30 tests passing
- Note: Individual hawker stall hygiene grades no longer available via public API (SFA web-only); grades show UNKNOWN — drives Milestones 4 & 5 below

## Milestone 4 — Quality Signals
Activate unused data already being fetched — zero new API calls except the LLM sentiment pass.

- [ ] Google Rating scoring: ≥4.5 → +2, ≥4.0 → +1, <3.5 → -1; review_count ≥200 → +1 confidence bonus
- [ ] LLM review sentiment (claude-haiku): sentiment score ±1, hygiene_concerns flag, standout_quote extracted per stall
- [ ] Time-aware scoring: best_time/avoid_time metadata matched against current SGT hour (±1)
- [ ] Demerit points nuance: clean record +0.5, high demerits -0.5 (when grade is known)
- [ ] Price range preference: detect budget keywords in query, boost/penalise accordingly
- [ ] Suspension hard filter: suspended stalls excluded before ranking (not just flagged)

## Milestone 5 — Hygiene Data Scraper
Build a one-off Playwright scraper for island-wide coverage from SFA Track Records.

- [ ] `backend/tools/sfa_scraper.py` — Playwright headless form submissions by postal code
- [ ] Covers all 120 NEA hawker centres (postal codes via OneMap)
- [ ] Output: `backend/data/hygiene_grades_full.json` (~120 centres × avg 30 stalls)
- [ ] HygieneAgent loads this file as primary source before declaring UNKNOWN
- [ ] Re-run quarterly to refresh grades

## Milestone 6 — UI Polish
- [ ] Framer Motion staggered card reveals (tuning)
- [ ] Geolocation "use my location" end-to-end test on mobile
- [ ] Mobile responsive layout audit at 375px
- [ ] Dark theme completeness QA

## Milestone 7 — Deploy
- [ ] README with architecture diagram and demo GIF
- [ ] Deploy backend to Railway
- [ ] Deploy frontend to Vercel
- [ ] Production smoke test end-to-end
