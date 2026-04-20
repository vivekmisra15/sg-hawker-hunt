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

## Milestone 3 — Streaming ✓
- [x] POST /api/search SSE endpoint
- [x] Frontend useSSE hook
- [x] AgentPanel component renders live stream
- [x] SearchBar submits and connects to SSE
- [x] ResultCard + ResultsList components
- [x] Full dark theme UI (DM Sans + JetBrains Mono)
- [x] 30/30 tests passing, zero TypeScript errors

## Data Fix (2026-04-20) ✓
- [x] NEA API auth corrected — `X-Api-Key` header (v2 key format)
- [x] NEA hygiene resource ID updated to current dataset
- [x] RAG seed expanded from 35 → 71 stalls
- [x] Full geographic coverage: central, east, west, north, north_east
- [x] `tags` as `list[str]`, new `region` field on all stall entries
- [x] ChromaDB re-seeded, all 5 diagnostic queries return correct cuisine
- [x] 30/30 tests passing
- Note: Individual hawker stall hygiene grades no longer available via public API (SFA web-only since 2025); grades show UNKNOWN — expected and honest

## Milestone 4 — UI Polish
- [ ] Framer Motion staggered card reveals
- [ ] Geolocation "use my location" button wired up
- [ ] Mobile responsive layout (375px)
- [ ] Screenshot QA

## Milestone 5 — Data + Deploy
- [x] ChromaDB seeded (71 stalls)
- [x] michelin_2025.json populated (25 stalls)
- [x] halal_stalls.json populated (15 stalls)
- [ ] README + architecture diagram + demo GIF
- [ ] Deploy backend to Railway
- [ ] Deploy frontend to Vercel
