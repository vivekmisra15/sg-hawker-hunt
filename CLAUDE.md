# Hawker Hunt — Claude Code Project Brief

> Read this file completely before taking any action in this project.
> This file encodes all architectural decisions made during planning.
> Do NOT deviate from patterns defined here without explicit user instruction.

---

## Project overview

Hawker Hunt is a multi-agent AI web application that helps people in Singapore find
the best hawker stall for their needs right now — factoring in hygiene grades, open
status, dietary requirements, crowd timing, and Michelin recognition.

The differentiator is a **live reasoning panel** that streams each agent's thinking
as it fires. This is an AI engineering showcase, not just a food app. The transparency
of the reasoning IS the product.

**Target user:** Anyone in Singapore wanting a smart, explained food recommendation —
not just a rating, but a reasoned argument for why this stall, right now.

---

## Output format

- **Web app** — React (Vite) frontend + FastAPI (Python) backend
- **NOT** a phone app, Telegram bot, or custom model
- Responsive — must work on mobile browser (uses browser Geolocation API for GPS)
- Deployed: frontend on Vercel, backend on Railway
- GitHub-ready: clean README, architecture diagram, demo GIF

---

## Tech stack — do not deviate without asking

| Layer | Technology | Notes |
|---|---|---|
| Frontend | React 18 + Vite | TypeScript preferred |
| Styling | Tailwind CSS + shadcn/ui | Dark mode first |
| Animations | Framer Motion | For agent panel streaming effect |
| Backend | FastAPI (Python 3.11+) | Async throughout |
| Agent orchestration | Anthropic Python SDK | claude-sonnet-4-6 model |
| Vector store | ChromaDB (local) | For RAG over hawker knowledge base |
| Embeddings | Anthropic embeddings or sentence-transformers | |
| HTTP client | httpx (async) | For external API calls |
| Testing | pytest + pytest-asyncio | Run after every implementation |
| Env management | python-dotenv | .env file, never hardcode keys |

---

## Architecture — three-layer system

```
User query
    │
    ▼
┌─────────────────────────────────────┐
│         Orchestrator Agent          │  ← Decomposes query, coordinates
│    (claude-sonnet-4-6 via SDK)      │    sub-agents, synthesises output
└──────────┬──────────────────────────┘
           │ spawns
     ┌─────┴──────┬──────────────────┐
     ▼            ▼                  ▼
┌─────────┐  ┌──────────┐  ┌─────────────────┐
│Hygiene  │  │ Location │  │ Recommendation  │
│ Agent   │  │  Agent   │  │     Agent       │
│         │  │          │  │                 │
│NEA API  │  │OneMap +  │  │RAG over Michelin│
│hygiene  │  │Google    │  │list + food blog │
│grades   │  │Places API│  │knowledge base   │
└─────────┘  └──────────┘  └─────────────────┘
     │            │                  │
     └─────┬──────┘                  │
           ▼                         ▼
    Structured results ──► Orchestrator synthesises
                                     │
                                     ▼
                          ┌──────────────────┐
                          │  Streaming SSE   │  ← React frontend
                          │  response to UI  │    receives live
                          └──────────────────┘    agent traces
```

---

## Agent responsibilities — one agent, one job

### Orchestrator Agent
- Receives raw user query ("good laksa near Toa Payoh, vegetarian, 1pm")
- Extracts: cuisine type, location, dietary needs, time context
- Calls sub-agents in parallel where possible
- Synthesises sub-agent results into ranked recommendations with reasoning
- Streams reasoning trace via SSE to frontend
- NEVER does data fetching itself — delegates to sub-agents

### Hygiene Agent (`agents/hygiene_agent.py`)
- Fetches NEA hygiene grades from data.gov.sg API
- Returns: grade (A/B/C/D), demerit points, suspension history per stall
- Also checks NEA closure schedule — flags if centre is closed for cleaning
- Input: hawker centre name or ID
- Output: structured HygieneResult dataclass

### Location Agent (`agents/location_agent.py`)
- Converts user location (coordinates or text) via OneMap API
- Finds nearest hawker centres within radius (default 1.5km)
- Fetches Google Places data per centre: rating, review count, open/closed now, hours
- Fetches up to 5 Google reviews per stall for sentiment parsing
- Applies time-of-day crowd heuristic (12–2pm and 6–8pm = busy)
- Cross-references with NEA closure dates
- Input: lat/lng or place name string
- Output: list of LocationResult dataclasses ranked by proximity

### Recommendation Agent (`agents/recommendation_agent.py`)
- RAG retrieval over pre-seeded knowledge base (see Data Sources)
- Matches user's cuisine/dietary preference against stall profiles
- Applies Michelin Bib Gourmand flag (89 stalls, 2025 list)
- Applies MUIS halal certification flag where relevant
- Parses Google review text for queue/wait-time signals
- Scores and ranks stalls with explanation
- Input: LocationResults + HygieneResults + user preferences
- Output: RankedRecommendation list with reasoning strings

---

## Data sources — real APIs, no mocking in production

| Source | What we use | API / access |
|---|---|---|
| NEA hawker centres | GeoJSON locations, 120 centres | data.gov.sg REST, free |
| NEA hygiene grades | Grade A/B/C/D + demerit points | data.gov.sg REST, free |
| NEA closure dates | Quarterly cleaning schedule | data.gov.sg REST, free |
| OneMap | Geocoding, routing | onemap.gov.sg, free |
| Google Places (New) | Rating, hours, reviews (5 max), open now | Places API v1, $200/mo free credit |
| OpenWeatherMap | Current weather (rain = avoid outdoor centres) | Free tier, 1000 calls/day |
| Michelin Bib Gourmand 2025 | 89 stalls pre-seeded as JSON | Static file `data/michelin_2025.json` |
| Halal certification | MUIS certified stalls | Static file `data/halal_stalls.json` |
| Hawker knowledge base | Stall descriptions, dish profiles, stories | Pre-seeded ChromaDB from `data/seed/` |

**IMPORTANT API rules:**
- All API keys live in `.env` — never hardcode, never log
- Google Places API: use New API (v1), NOT legacy. Endpoint: `places.googleapis.com/v1/places`
- OpenAQ v3 only — v1 and v2 were retired January 2025
- data.gov.sg rate limits enforced from Dec 2025 — cache responses, don't hammer

---

## Directory structure — follow exactly

```
hawker-hunt/
├── CLAUDE.md                    ← this file
├── README.md                    ← generated at end
├── .env                         ← API keys (gitignored)
├── .env.example                 ← committed, no real values
├── .gitignore
│
├── backend/
│   ├── main.py                  ← FastAPI app entry point
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── orchestrator.py      ← master agent
│   │   ├── hygiene_agent.py
│   │   ├── location_agent.py
│   │   └── recommendation_agent.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── nea_client.py        ← data.gov.sg API wrapper
│   │   ├── places_client.py     ← Google Places API wrapper
│   │   ├── onemap_client.py     ← OneMap geocoding
│   │   └── weather_client.py    ← OpenWeatherMap wrapper
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── vector_store.py      ← ChromaDB setup and queries
│   │   └── seed.py              ← one-time seeding script
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py           ← Pydantic models / dataclasses
│   ├── data/
│   │   ├── michelin_2025.json
│   │   ├── halal_stalls.json
│   │   └── seed/                ← markdown files for RAG seeding
│   ├── tests/
│   │   ├── test_hygiene_agent.py
│   │   ├── test_location_agent.py
│   │   └── test_recommendation_agent.py
│   └── requirements.txt
│
└── frontend/
    ├── index.html
    ├── vite.config.ts
    ├── tailwind.config.ts
    ├── tsconfig.json
    ├── package.json
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── components/
        │   ├── SearchBar.tsx        ← query input + location toggle
        │   ├── AgentPanel.tsx       ← live streaming reasoning trace
        │   ├── ResultCard.tsx       ← single stall recommendation card
        │   ├── ResultsList.tsx      ← ranked list of ResultCards
        │   └── StatusBadge.tsx      ← hygiene grade / michelin / halal badges
        ├── hooks/
        │   ├── useSSE.ts            ← Server-Sent Events streaming hook
        │   └── useGeolocation.ts    ← browser GPS hook
        ├── lib/
        │   └── api.ts               ← backend API client
        └── types/
            └── index.ts             ← shared TypeScript types
```

---

## UI design direction — slick and modern, NOT generic

The UI must feel premium and distinctive. Reference: linear.app, vercel.com, raycast.com.

**Aesthetic:** Dark-first, minimal chrome, high information density.
**NOT:** Purple gradients on white, Inter font, generic card grids.

Key UI rules:
- Dark background: `#0a0a0a` or similar near-black
- Accent: amber/orange (`#f59e0b` or similar) — Singapore hawker warmth
- Font: Geist (Vercel's font) or DM Sans — NOT Inter, NOT Roboto
- Agent panel: monospace font, subtle green text like a terminal
- Cards: glass morphism with subtle border — `backdrop-blur`, `border-white/10`
- Animations: staggered card reveals via Framer Motion, 60fps
- Badges: hygiene grade A = green, B = amber, C/D = red — always visible
- Michelin badge: gold star icon, never hidden
- The reasoning panel streams token by token — it must feel alive

The reasoning panel is the hero of the UI. It sits alongside results and shows:
```
🔍 Orchestrator: Parsing query — cuisine: laksa, location: Toa Payoh, dietary: vegetarian...
📍 Location Agent: Found 6 centres within 1.5km. Checking open status...
🧼 Hygiene Agent: Toa Payoh West Market — Grade A. No suspensions in past year.
⭐ Recommendation Agent: Querying knowledge base for vegetarian laksa...
✅ Synthesis: Ranked 3 stalls. Top pick: reasoning...
```

---

## API contracts — backend endpoints

```
POST /api/search
Body: { query: string, lat?: number, lng?: number }
Response: SSE stream of AgentEvent objects

GET /api/centres
Response: list of all hawker centres with basic info

GET /api/health
Response: { status: "ok", agents: [...], data_sources: [...] }
```

SSE event format:
```json
{ "type": "agent_update", "agent": "hygiene", "message": "...", "data": {} }
{ "type": "result", "recommendations": [...] }
{ "type": "error", "message": "..." }
```

---

## Build milestones — work in this order

### Milestone 1 — Foundation (session 1)
- [ ] Backend: FastAPI app skeleton with /health endpoint
- [ ] Backend: All tool clients (NEA, Places, OneMap, Weather) with tests
- [ ] Backend: Pydantic schemas for all data models
- [ ] Frontend: Vite + React + Tailwind + shadcn setup
- [ ] Verify: `pytest tests/` passes, `/health` returns 200

### Milestone 2 — Agents (session 2) ✓
- [x] Hygiene Agent: NEA data fetch + structured output
- [x] Location Agent: OneMap geocoding + Google Places integration
- [x] Recommendation Agent: ChromaDB RAG setup + Michelin/halal flags
- [x] Orchestrator: coordinates all three, returns structured result
- [x] Verify: each agent has passing unit tests

### Milestone 3 — Streaming + integration (session 3)
- [x] SSE endpoint: POST /api/search streams AgentEvents
- [ ] Orchestrator streams reasoning trace tokens via SSE
- [ ] Frontend AgentPanel: renders SSE stream live
- [ ] Frontend SearchBar: submits query, triggers SSE connection
- [ ] Verify: end-to-end query returns streaming results in browser

### Milestone 4 — UI polish (session 4)
- [ ] ResultCard with all badges (hygiene, michelin, halal, open/closed)
- [ ] Framer Motion staggered card reveals
- [ ] Geolocation hook: "use my location" button
- [ ] Mobile responsive layout
- [ ] Dark theme complete, no light mode needed for V1
- [ ] Verify: screenshot comparison, no layout breaks on 375px

### Milestone 5 — Data + deploy (session 5)
- [ ] Seed ChromaDB with hawker knowledge base
- [ ] Seed michelin_2025.json and halal_stalls.json
- [ ] README with architecture diagram and demo GIF
- [ ] Deploy backend to Railway
- [ ] Deploy frontend to Vercel
- [ ] Verify: production URL works end-to-end

---

## Session workflow rules — IMPORTANT

1. **Always run tests after implementing any agent or tool**: `cd backend && pytest tests/ -v`
2. **Use Plan Mode before modifying multiple files** — plan first, then implement
3. **One milestone per session** — use `/clear` between milestones
4. **Never implement UI and backend logic in the same session** — separate concerns
5. **After each agent is complete**: write the test before moving to the next agent
6. **Name each session**: `/rename hawker-hunt-milestone-N` at session start
7. **When stuck on an API**: use a subagent to investigate, keep main context clean

---

## Environment variables required

```bash
# Anthropic
ANTHROPIC_API_KEY=

# Google
GOOGLE_PLACES_API_KEY=

# OpenWeatherMap
OPENWEATHER_API_KEY=

# Data.gov.sg (register for higher rate limits)
DATAGOV_API_KEY=

# App config
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173
ENVIRONMENT=development
```

---

## What "done" looks like for V1

A user can:
1. Type "good char kway teow near me, not too crowded" and optionally share location
2. Watch the agent panel stream live reasoning from three agents
3. See 3 ranked stall cards with hygiene grade, open status, distance, Michelin badge
4. Understand WHY each stall was recommended — not just a score
5. Trust the result because the reasoning is transparent

The app deploys to a public URL, has a GitHub repo with README and demo GIF.

---

## Session Notes — Milestone 1 (2026-04-12)

### Implementation decisions
- `respx==0.23.1` added to `requirements.txt` for HTTP mocking in tests
- `sentence-transformers` removed — Anthropic SDK embeddings used for ChromaDB instead
- All tool clients use `async with httpx.AsyncClient(timeout=N)` per method (not a shared instance)
- Error class per client: `NEAClientError`, `PlacesClientError`, `OneMapClientError`
- `WeatherClient` degrades gracefully — missing key returns default `WeatherResult`, never raises
- `PlacesClient` raises `PlacesClientError` immediately if `GOOGLE_PLACES_API_KEY` not set
- Module-level `_cache` dict in `nea_client.py` is a deliberate singleton across instances (1-hour TTL)
- `backend/conftest.py` inserts `backend/` onto `sys.path` so `from tools.x import Y` works in tests
- `backend/pytest.ini` sets `asyncio_mode = auto` and `asyncio_default_fixture_loop_scope = function`

### Known spec discrepancies
- Haversine test: original spec estimated ~7.4 km for `(1.3521, 103.8198)→(1.2978, 103.8516)`; actual haversine = 7.0 km. Test uses `pytest.approx(7.0, abs=0.1)`.

### Test results — Milestone 1
- 12 tests across 4 files, all passing
- All HTTP calls mocked with `respx.mock` — no live API calls in tests
- Tests that require API keys (Places, Weather) use `unittest.mock.patch.dict` to inject/remove env vars

---

## Session Notes — Milestone 2 (2026-04-12)

### RAG + embeddings
- `DefaultEmbeddingFunction` (ChromaDB built-in, all-MiniLM-L6-v2 via ONNX) used for embeddings — no external API needed at query time
- `OpenAIEmbeddingFunction` is incompatible with Anthropic's embedding API (different request shape and auth)
- ChromaDB collection: `hawker_knowledge`, cosine similarity, 384-dim
- 20 stall seed documents covering 10 cuisines and 10 centres seeded via `python3 -m rag.seed`
- `VectorStore.query()` guards with `min(n_results, collection_size)` to avoid ChromaDB error when collection is small

### RecommendationAgent scoring weights
- Grade A: +3, Grade B: +2, Grade C: +1, Grade D/UNKNOWN: 0
- Michelin Bib Gourmand: +3
- is_open (centre open now): +2
- crowd_level == "quiet": +1
- RAG semantic relevance: 0–2 (scaled from cosine distance, closer = higher)
- Top 3 results returned; halal/vegetarian dietary filters applied before scoring

### Agent patterns
- Constructor injection on all agents: optional deps default to `None`, instantiated fresh if not provided — enables clean test mocking without patching module globals
- OrchestratorAgent uses `asyncio.create_task` for HygieneAgent (set up for future parallelism with RAG)
- LocationAgent raises `ValueError` (not a custom error) if coords are outside Singapore bounding box — orchestrator catches and yields an `error` AgentEvent
- HygieneAgent returns `UNKNOWN` grade on `NEAClientError` — never crashes the pipeline
- WeatherClient returns `_UNAVAILABLE` sentinel on missing key — never raises, no HTTP call made

### Known API gotcha — Google Places New API
- `"food"` is NOT a valid `includedType` in the Places API v1 — returns HTTP 400
- Valid types used: `["restaurant", "meal_takeaway", "cafe"]`

### pytz
- `pytz>=2024.1` added to requirements for Singapore timezone (`Asia/Singapore`) in LocationAgent crowd heuristic
- Busy hours defined as 11:00–14:59 and 17:00–20:59 SGT

### SSE endpoint
- `POST /api/search` wired in `main.py` — returns `EventSourceResponse` wrapping the orchestrator's async generator
- SSE event format: `{"event": "<type>", "data": "<model_dump_json>"}`
- Live test confirmed correct event order: orchestrator (parse) → orchestrator (location) → location → hygiene → recommendation → result

### Test results — Milestone 2
- 30 tests across 8 files, all passing (18 new tests added this milestone)
- Agent tests use constructor injection + `AsyncMock` — no live API calls or ChromaDB writes
- `_load_json_list` patched in recommendation agent tests to avoid filesystem dependency
- Crowd heuristic tested by patching `agents.location_agent.datetime` with a stub class

---

## Session Notes — Milestone 3 (2026-04-18)

### Backend hardening
- `import json` added to `main.py` (was missing — needed for error event serialisation)
- CORS `allow_origins` now explicitly lists `http://localhost:5173` and `http://127.0.0.1:5173` in addition to the env var — Vite dev server connects reliably regardless of how it resolves localhost
- SSE endpoint wrapped in `try/except` — stream errors yield an `error` event to the client instead of silently disconnecting
- `EventSourceResponse` now passed `headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}` — prevents proxy buffering of the live stream

### Frontend stack
- React 18 + Vite, Tailwind CSS, Framer Motion, TypeScript — all from existing scaffold
- Fonts: DM Sans (UI) + JetBrains Mono (agent panel terminal text) loaded from Google Fonts
- Tailwind tokens added: `surface` (#111111), `card` (#1a1a1a), `accent` (#f59e0b already existed)
- Global CSS: `--accent` CSS variable, `box-sizing: border-box`, amber `::selection`, `cursor-blink` keyframe

### SSE client pattern — no EventSource library needed
- `createSearchStream` in `lib/api.ts` uses `fetch` + `ReadableStream` + `AbortController`
- Parses SSE by splitting buffer on `\n` and extracting `data: ` lines — handles chunked delivery correctly
- Returns a cancel function; `useSSE` hook stores it in a `useRef` to cancel on re-search or unmount
- `EventSource` browser API was NOT used — it doesn't support POST requests

### useSSE hook — state machine
- States: `idle → searching → complete | error`
- `onComplete` uses functional updater `setState(s => s === 'searching' ? 'complete' : s)` to avoid stale closure — deviates from original spec which had a closure bug
- Reset (clicking the wordmark) aborts any in-flight stream and clears all state

### AgentPanel — terminal aesthetic
- JetBrains Mono, green-tinted text (`text-green-300/70`) on `#111111` background
- Traffic-light dots in header reinforce the terminal metaphor
- Framer Motion `AnimatePresence` + `motion.div` animate each new trace line from `y:10, opacity:0`
- Blinking cursor `▊` uses CSS `step-end` animation — appears only while `state === 'searching'`
- `useEffect` on traces array scrolls container to bottom on each new line

### SearchBar chips — emoji stripping
- Example chips fill the input with the text portion only, stripping the leading emoji
- Uses Unicode property escape `\p{Emoji}` which requires the `u` flag — works in all modern browsers

### Known issue — DATAGOV_API_KEY required for hygiene grades
- NEA data.gov.sg enforces a very low rate limit for unauthenticated requests → HTTP 429
- Without the key, all hygiene grades show as UNKNOWN (HygieneAgent returns UNKNOWN on NEAClientError)
- Module-level `_error_cache` added to `nea_client.py`: first 429 is logged with a clear message, then suppressed for 5 minutes to eliminate log spam
- **Fix**: register for a free API key at data.gov.sg and add `DATAGOV_API_KEY=` to `.env`

### Seed data expanded (post-testing fix)
- Initial 20-stall seed had no bak kut teh entries — wrong cuisine returned for those queries
- Expanded to 35 stalls: added bak kut teh (Song Fa Clementi, Ng Ah Sio, Founder), west-side centres (Clementi 448, ABC Brickworks, Buona Vista), claypot rice, ban mian, oyster omelette, frog porridge
- `seed.py` no longer writes `michelin_2025.json` or `halal_stalls.json` — those files are now managed as structured JSON objects separately and must not be overwritten by the seed script
- Re-seed command: `source venv/bin/activate && cd backend && python3 -m rag.seed`

### Test results — Milestone 3
- 30 tests, all passing (no new tests — Milestone 3 was a frontend implementation milestone)
- Frontend build: `npm run build` produces zero TypeScript errors, 268 KB JS bundle
- Live SSE smoke test: "chicken rice near Maxwell" → 5 agent_update events + 1 result event, correct stall ranking

---

## Session Notes — Data Fix (2026-04-20)

### NEA API — auth method corrected
- `_error_cache` and `_headers()` removed from `nea_client.py`
- Auth is now `X-Api-Key: <key>` header (not `Authorization` header, not `api_key` query param)
- data.gov.sg v2 API keys (`v2:...` format) require the `X-Api-Key` header specifically
- `CENTRES_RESOURCE` (`b80cb643-...`) confirmed working with `X-Api-Key`
- Timeout raised from 10s to 30s (new hygiene dataset is 2.5 MB but responds in ~0.3s)

### NEA hygiene grades — dataset migrated, individual stall grades unavailable
- Old resource ID `4a291f25-2d8d-4b3a-9aaf-e8b1bd0ceedb` returns 404 — dataset removed
- Responsibility transferred from NEA to SFA (Singapore Food Agency); individual stall grades now only accessible via the SFA Track Records web UI (not a public API)
- `HYGIENE_RESOURCE` updated to `d_227473e811b09731e64725f140b77697` ("List of NEA Licensed Eating Establishments") — this dataset contains 36,687 corporate eating establishment records (restaurants, hotels) but NOT individual hawker stall entries
- Hawker stall grades therefore show as UNKNOWN — this is the correct honest result given available public data
- Field names in new dataset: `licensee_name`, `premises_address`, `grade`, `demerit_points`, `suspension_start_date` (was `LICENSEE_NAME`, `BUSINESS_NAME`, `GRADE`, etc.)
- `get_hygiene_grades()` updated to use new lowercase field names

### RAG seed expanded to 71 stalls
- `seed.py` fully rewritten: 71 stalls (up from 35), rich 50-70 word descriptions
- `tags` changed from plain string to `list[str]` in seed source
- New `region` field added: `"central"`, `"east"`, `"west"`, `"north"`, `"north_east"`
- `add_documents()` in `vector_store.py` updated to join list metadata values with `", "` (ChromaDB requires primitive types)
- Geographic coverage: 15 central, 16 east, 11 west, 8 north, 7 north_east stalls
- Cuisine coverage added: popiah, yong tau foo, thunder tea rice, tau huay, kaya toast, chee cheong fun, murtabak, mee siam, biryani, oyster omelette, hor fun, char siu rice, fish head curry
- chroma_db/ deleted and re-seeded; collection confirmed at 71 documents
- Re-seed command: `rm -rf backend/chroma_db/ && source venv/bin/activate && cd backend && python3 -m rag.seed`

### RAG diagnostic results (post-expansion)
| Query | Top result | Correct? |
|---|---|---|
| "bak kut teh in the west" | Song Fa Bak Kut Teh (west) | ✓ |
| "char kway teow" | No. 18 Zion Road Fried Kway Teow (char kway teow) | ✓ |
| "halal nasi lemak" | Selera Rasa Nasi Lemak | ✓ |
| "laksa not crowded" | Sungei Road Laksa | ✓ |
| "vegetarian food near Toa Payoh" | Toa Payoh Lor 8 Porridge (geographic pull wins) | Partial |

Vegetarian query limitation: "near Toa Payoh" pulls results toward central stalls; vegetarian-tagged stalls (thunder tea rice, yong tau foo) are in NE/west. The Recommendation Agent dietary filter handles this at scoring time.

### Live SSE end-to-end test results (post data-fix)
- All 3 queries return 5 agent_update events + 1 result event ✓
- No stream errors or timeouts ✓
- Cuisine matching correct for all 3 queries ✓
- Hygiene grades UNKNOWN (expected — SFA data not publicly available via API)

### Test results — Data Fix
- 30/30 tests passing (no new tests this session — changes were data and auth fixes)

---

