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

## Session Notes — Milestone 4 (2026-04-21)

### Six quality signals activated in `RecommendationAgent`

Max possible score raised from 11 to ~17.5. All signals degrade gracefully when data is absent.

| Signal | Mechanism | Breadth |
|---|---|---|
| Google rating | ≥4.5→+2, ≥4.0→+1, <3.5→-1; review_count≥200→+1 | All 20 Places results |
| LLM sentiment | `claude-haiku-4-5-20251001` structured JSON; ±1 sentiment, −0.5 hygiene concern | All 20 Places results with reviews |
| Time-aware | `_parse_time_range()` regex normaliser vs current SGT hour; ±1 | 71 seeded stalls |
| Demerit nuance | 0 demerits +0.5, ≥12 demerits −0.5 (grade known only) | NEA-matched centres |
| Price preference | Budget keyword → "cheap"/"moderate"/"any"; upper price bound matched | 71 seeded stalls |
| Suspension filter | Hard exclude before scoring (was trace-only before) | All centres |

### New Pydantic model: `SentimentResult`

Added to `models/schemas.py`: `sentiment_score`, `hygiene_concerns`, `queue_signal`, `standout_quote`.
`RankedRecommendation` gains `standout_quote: Optional[str]`.

### Orchestrator query parsing extended

`_PARSE_SYSTEM` prompt now extracts `budget: "cheap" | "moderate" | "any"` from user query.
Fallback default is `"any"`.

### LLM sentiment implementation details

- `_build_sentiment_map()` in `RecommendationAgent` runs all centre sentiment calls via `asyncio.gather` before scoring loop
- Module-level `_SENTIMENT_CACHE` keyed by SHA-256 of first 500 chars of reviews, 24h TTL
- Empty Haiku response (`raw == ""`) caught before `json.loads` → neutral, DEBUG log
- `json.JSONDecodeError` caught at DEBUG level (not WARNING) — live testing showed Haiku returning empty responses for centres with sparse reviews, causing log spam
- Genuine network errors still log at WARNING
- `_NEUTRAL_SENTIMENT` singleton returned on any failure path

### `_parse_time_range()` helper

Free-text time normaliser for ChromaDB metadata. Handles: range patterns (`"12pm-2pm"`),
before/after patterns (`"before 11:30am"`, `"after 2pm"`), named periods (`"early morning"`).
Returns `[]` for unrecognised strings — safe fallback.

### `_parse_price_upper()` helper

Extracts upper price bound from strings like `"S$5-7"`, `"$3-5"`, `"S$18"`. Returns `None` on
failure — scoring skipped.

### Frontend fixes

- `frontend/src/types/index.ts`: Added `standout_quote?: string | null` to `RankedRecommendation`
- `frontend/src/components/StatusBadge.tsx`: `Grade UNKNOWN` now renders neutral grey with label
  `"Grade —"` instead of red `"Grade UNKNOWN"` — prevents false alarm for missing data
- C and D grades remain red (genuine hygiene concern)

### Test results — Milestone 4
- 58/58 tests passing (28 new tests added this milestone)
- Signals 1/3/4/5/6: sync scoring tests with mock location/hygiene data
- Signal 2: async tests with `AsyncMock` Anthropic client; cache behaviour verified
- Time-aware tests: patch `agents.recommendation_agent.datetime` (same pattern as location agent)

### Live test observation (from screenshot)
- `"laksa in the east"` → correct top 3 (328 Katong Laksa, Selera Rasa Nasi Lemak, Sungei Road Laksa)
- `google_rating` absent for these results (Places API not returning ratings for these centres) — handled gracefully
- Sentiment analysis triggered empty Haiku responses (sparse reviews) → fixed by empty-guard + DEBUG log level

---

## Session Notes — Milestone 4 Signal Expansion (2026-04-21)

### Problem addressed
Signal 3 (time-aware) and Signal 5 (price) had limited breadth — both depended solely on
ChromaDB seed metadata, covering only 71 stalls. This session expanded both signals to
near-island-wide coverage without any new API integrations.

### Signal 3 expansion — two additional fallback tiers

**Signal 3A: Haiku `peak_time_hint`**
- Added `peak_time_hint: str = "unknown"` to `SentimentResult` schema
- Haiku prompt extended to extract when reviews say a stall is best visited
  (e.g. "always packed at lunch", "great for late-night supper")
- In scoring: if `peak_time_hint` matches `time_context` from user query → `+0.5`
- Fires for all 20 Places results that have reviews — no extra API call

**Signal 3B: Cuisine-based time priors**
- `_cuisine_time_score()` helper added to `recommendation_agent.py`
- `_TIME_CUISINE_MAP` maps cuisine keywords to time buckets:
  - breakfast: kaya toast, congee, dim sum, you tiao, teh tarik, roti prata
  - supper: bak kut teh, frog porridge, bbq stingray, oyster omelette
  - lunch: chicken rice, char kway teow, laksa, duck rice, mixed rice
  - dinner: bbq, satay, steamboat, seafood, fish head curry
- Scoring: cuisine matches `time_context` → `+0.5`; opposite slot → `−0.5`
- Fires for all 71 seeded stalls (cuisine/tags are always present in metadata)
- Tiering: seeded `best_time`/`avoid_time` (±1) → Haiku hint (±0.5) → cuisine prior (±0.5)
  Only the first matching tier fires — prevents double-counting

**`time_context` extraction added to OrchestratorAgent `_PARSE_SYSTEM`**
- New key: `time_context: "breakfast" | "lunch" | "dinner" | "supper" | "any"`
- Fallback default: `"any"`

### Signal 5 expansion — two additional fallback tiers

**Signal 5A: Google Places `priceLevel`**
- `priceLevel` added to `fieldMask` in both `PlacesClient.search_nearby()` and `get_place_details()`
- `price_level: Optional[str]` added to `LocationResult` schema
- `LocationAgent` extracts and stores `priceLevel` from both search and detail responses
- `_PRICE_LEVEL_MAP` in `recommendation_agent.py` converts enum strings to proxy upper bounds:
  - `PRICE_LEVEL_INEXPENSIVE` → S$5 | `PRICE_LEVEL_MODERATE` → S$12 | `PRICE_LEVEL_EXPENSIVE` → S$25
- Fires for all 20 Places results — zero extra quota cost (field already returned in existing call)

**Signal 5B: Haiku `price_signal`**
- Added `price_signal: str = "unknown"` to `SentimentResult` schema
- Haiku prompt extended to extract "cheap"/"moderate"/"expensive" from review text
- `_PRICE_SIGNAL_MAP` converts to proxy upper bound for existing budget scoring
- Fires as final fallback when neither seeded `price_range` nor Places `priceLevel` available

**Price scoring priority order (tiered):**
1. Seeded `price_range` metadata (71 stalls, most precise)
2. Google Places `priceLevel` (all 20 Places results per query)
3. Haiku `price_signal` from reviews (all results with reviews)

### Signal 2 — Singlish-aware prompt rewrite

`_SENTIMENT_SYSTEM` in `recommendation_agent.py` fully rewritten:
- **Explicit Singlish glossary**: shiok, ho jiak, sedap, confirm plus chop, die die must try,
  power, steady, jialat mapped to positive/negative sentiment
- **Queue inversion**: long queues at hawker stalls = quality signal → positive, not negative.
  Haiku was previously treating "always packed" as a complaint.
- **Terse review calibration**: "good", "nice", "ok lah" scored ≥ +0.3 (Singapore review culture)
- **Particle awareness**: lah, lor, leh, sia, meh, wah treated as tone markers, not sentiment
- `standout_quote` instruction updated to preserve original language (Singlish quotes kept intact)

### Schema changes
- `LocationResult`: added `price_level: Optional[str]`
- `SentimentResult`: added `peak_time_hint: str`, `price_signal: str`
- No changes to `RankedRecommendation` (new signals feed into `reasoning` string)

### Test mock fix
- `_make_anthropic()` helper in tests was manually serialising `SentimentResult` fields,
  missing `peak_time_hint` and `price_signal` → both always returned `"unknown"` in mocks
- Fixed to use `sentiment.model_dump_json()` — serialises all fields automatically,
  future-proof against further schema additions

### Test results — Signal Expansion
- 66/66 tests passing (8 new tests added)
- New tests: Signal 3A (peak_time_hint match/mismatch), Signal 3B (breakfast boost, supper penalty),
  Signal 5A (priceLevel boost, seeded metadata priority), Signal 5B (review price_signal fallback),
  Signal 2 (Singlish prompt structure assertion)

---

## Session Notes — Milestone 5 (2026-04-21)

### SFA hygiene data — background

SFA (Singapore Food Agency) replaced NEA as the hygiene grading authority in Jan 2026 under
the **SAFE** framework. Grades are only accessible via the SFA Track Records web UI — no public
API. All stalls show UNKNOWN in live operation; this milestone generates a static fallback file.

### New grade values under SAFE framework

| Raw grade | Normalised |
|---|---|
| A, B, C, D | Same |
| NEW | B (new operator, no violations yet) |
| NOT_UNDER_SAFE | UNKNOWN (exempt premises) |
| A_UNDER_REVIEW | A |
| B_UNDER_REVIEW | B |
| NEW_UNDER_REVIEW | B |

### `backend/tools/sfa_scraper.py` — NEW

Playwright headless browser scraper. One-off CLI tool; **not** part of the app runtime.

- Fetches all NEA hawker centre postal codes from data.gov.sg
- For each centre, searches SFA Track Records by postal code and extracts grade table
- Checkpoint pattern: writes per-centre result immediately so crashes can resume
- Exponential backoff: 3 retries at 5s, 15s, 45s (±2s jitter) per centre
- One browser instance reused across all centres to minimise overhead
- CLI: `--fresh`, `--postal-codes`, `--delay`, `--dry-run`

**Usage after installing tools:**
```bash
pip install -r requirements-tools.txt && playwright install chromium
cd backend
python -m tools.sfa_scraper --dry-run        # preview
python -m tools.sfa_scraper --postal-codes 068805  # test one centre
python -m tools.sfa_scraper                  # full run (~10–15 min)
```

**Output** (both gitignored via `backend/data/`):
- `backend/data/hygiene_grades_full.json` — consolidated grades by postal code
- `backend/data/scrape_checkpoint.json` — per-centre progress for crash recovery

### `requirements-tools.txt` — NEW

`playwright>=1.40.0`, `beautifulsoup4>=4.12.0` — separate from `requirements.txt`
so the main app has no Playwright dependency.

### `backend/tools/nea_client.py` — modified

- `_GRADES_FILE` path constant pointing to `backend/data/hygiene_grades_full.json`
- `_load_static_grades()` lazy-loads the file once, builds a dict keyed by `CENTRE_NAME.upper()`
  Returns `{}` if file doesn't exist — zero crash risk
- `NEAClient.get_static_hygiene_for_centre(name)` — synchronous; fuzzy name match (exact then substring)
  Returns `list[HygieneResult]` or `[]`

### `backend/agents/hygiene_agent.py` — modified

**Tiered data source:**
1. Live data.gov.sg API (existing)
2. Static `hygiene_grades_full.json` (new fallback, triggered when live API has no match)
3. UNKNOWN (graceful degradation when neither available)

**Enhanced trace when static data used:**
```
Maxwell Food Centre: 58/72 stalls Grade A (SFA data), open today.
```

### Test results — Milestone 5
- 68/68 passing (+2 new tests)
- `test_static_grades_fallback_when_live_api_no_match` — static grades used when live returns empty
- `test_static_grades_suspended_flag_from_static_data` — suspended propagates from static stall
- `_make_mock_nea()` updated to stub `get_static_hygiene_for_centre` — prevents MagicMock iterator
  bug where `min()` on a truthy but empty-iterating mock would raise ValueError

---

## Session Notes — Post-Milestone 5 Fixes (2026-04-24)

### Three bugs fixed from live testing

#### Fix 1 — Result count: 3 → 5
`candidates[:3]` → `candidates[:5]` in `recommendation_agent.py`. Test updated to match.

#### Fix 2 — SFA scraper rewritten (Playwright → direct REST API)

The original Playwright scraper failed at every layer:
- SFA URL changed: `/food-safety/food-hygiene/track-records` → 404. Correct: `/tools-and-resources/track-records`
- NEA dataset uses lowercase fields (`name`, `address_myenv`) — not `NAME`, `ADDRESSPOSTALCODE`
- Postal code must be extracted from `address_myenv` via `Singapore\s+(\d{6})` regex
- Playwright installed into system Python, not venv

**Key discovery:** JS inspection of `track-record.js` revealed a direct REST API:
```
GET https://www.sfa.gov.sg/api/TrackRecord/GetTrackRecord?postalCode=069184&...
```
Load the page once for `ASP.NET_SessionId` cookie, then all subsequent calls are plain httpx GETs.
- 0.2s per centre (was ~90s with Playwright) — 122 centres in ~2 minutes
- No Playwright/Chromium needed — `httpx` is sufficient
- 404 response triggers session re-init + retry (handles expired cookies mid-run)

**Live scrape result (2026-04-24):** 122/122 centres, ~4,800+ stalls.
Maxwell Food Centre: `100 stalls (A:73, B:25, UNKNOWN:2)`

Note: SFA API does not return `demerit_points` or `suspended` — both default to 0/false.

#### Fix 3 — "Closed + good time to visit" contradiction
`crowd_note` was unconditionally appended regardless of open status.
Fixed: `crowd_note = ""` when `is_open is False`. Only shown when open AND crowd data present.

### Test results — Session 09
68/68 passing (no new tests — fixes covered by existing test surface).

---

## Session Notes — Milestone 6 (2026-04-25)

### Design vision: "Premium Hawker Terminal"

Three reference products drove every pixel decision:

| Influence | Pattern adopted |
|---|---|
| Perplexity | Agent panel as 280px left sidebar; results canvas on the right |
| Linear | 1px borders at 15% opacity, opacity-based text hierarchy, tabular numbers everywhere |
| Raycast | Glass morphism only on elevated surfaces (search bar, map popup) |
| Warp Terminal | Block-based agent trace with named sections and typewriter character reveal |
| Luma | Mesh gradient ambient warmth — amber 4% + Singapore red 2.5% in dark mode |
| Vercel | Geist font, pixel-grid alignment |

### Token foundation

- `frontend/src/index.css`: full CSS custom property set as **RGB channel triples** — enables Tailwind slash-opacity (`bg-background/50`)
- Light palette: warm stone (`#faf9f7`); dark palette: warm black (`#0a0907`) — neither is a pure neutral
- Semantic roles: `--background`, `--card`, `--foreground`, `--border`, `--accent`, `--success/warning/danger/neutral` (each with a `-bg` variant)
- Theme transitions: `background-color` and `border-color` only (not `color` — avoids readability flash)
- `frontend/tailwind.config.ts`: `darkMode: 'class'`, full token map, Geist font family
- `frontend/src/lib/utils.ts` (NEW): `cn()` utility wrapping `clsx` + `tailwind-merge`
- `frontend/src/vite-env.d.ts` (NEW): `/// <reference types="vite/client" />` for `import.meta.env`

### Theme system

- `frontend/src/context/ThemeContext.tsx` (NEW): reads `localStorage` → `prefers-color-scheme` → default dark; applies/removes `.dark` on `document.documentElement`
- `frontend/src/components/ThemeToggle.tsx` (NEW): animated sun/moon icon swap via `AnimatePresence mode="wait"` with spring transition
- `frontend/src/main.tsx`: `<ThemeProvider>` wrapper added

### Layout restructure (Perplexity-inspired)

`App.tsx` restructured to a three-panel layout when search is active:
1. **Agent sidebar** — `w-64 shrink-0 sticky top-8` on desktop
2. **Results column** — `flex-1 min-w-0`
3. **Map column** — `w-80 xl:w-96 shrink-0 sticky top-8`

All three panels animate in with staggered springs. Idle state stays single-column. Mobile: vertical stack.

### Component redesigns

- **AgentPanel**: Warp-style named blocks (ORCHESTRATOR / LOCATION / HYGIENE / RECOMMENDATION), each with a 1px separator; `TypewriterText` sub-component reveals newest line character by character at 18ms/char
- **ResultCard**: spring entrance `y:16, scale:0.96`; `whileHover: y:-2, scale:1.01`; SVG star ratings replace ★/☆ text; `tabular-nums` on all numbers
- **ResultsList**: animated `motion.path` SVG underline on "Top picks" label
- **SearchBar**: glass morphism input; arrow ↔ spinner morph on submit via `AnimatePresence mode="wait"`
- **StatusBadge**: semantic success/warning/danger/neutral tokens; Michelin badge gains amber text-shadow glow

### Map feature (initial — Mapbox)

Initial implementation used `react-map-gl` + `mapbox-gl`. Three new components:
- `HawkerMap.tsx`: token guard (`VITE_MAPBOX_TOKEN` required), `fitBounds`, theme-aware style switching
- `MapMarker.tsx`: amber rank pin with spring drop entrance and selected pulse animation
- `MapDetailPanel.tsx`: glassmorphic Raycast-style popup with spring entrance/exit, closes on Escape/outside-click

**Note:** this Mapbox implementation was replaced in the following session — see Milestone 6 Refactor below.

### Test results — Milestone 6
- 68/68 backend tests passing (no backend changes this milestone)
- Frontend build: zero TypeScript errors, 295 KB JS + 1.77 MB mapbox-gl bundle

---

## Session Notes — Milestone 6 Refactor (2026-04-26)

### Seven issues addressed from live testing

| # | Symptom | Root cause | Fix |
|---|---------|------------|-----|
| 1 | Green agent text invisible in light mode | `text-green-300/70` hardcoded, too light on stone | `dark:text-green-300/70 text-emerald-800/70` |
| 2 | Signal data (ratings, crowd) missing from most cards | `review_count` and `crowd_level` not included in `RankedRecommendation` output | Added both fields to schema and agent output |
| 3 | Hygiene grades UNKNOWN on most stalls | Static SFA file uses long names ("Clementi Ave 3 Blk 448") that substring-match fails for short names ("Clementi 448 Market & Food Centre") | Jaccard token-similarity fallback at threshold 0.4 |
| 4 | Only 5 results, no way to get more | Backend capped at 5; no frontend pagination | Backend → 10; frontend IntersectionObserver reveals 5 at a time |
| 5 | Cards not clickable | No `onClick` on `ResultCard` | Click opens Google Maps search for stall in new tab |
| 6 & 7 | No map / blank right panel | `HawkerMap` returned `null` without `VITE_MAPBOX_TOKEN`; `lat`/`lng` not in output | Replaced Mapbox with Leaflet + CartoDB (no token); wired coordinates through |

### Backend changes

**`backend/models/schemas.py`** — `RankedRecommendation` gains four new fields:
- `review_count: Optional[int]`
- `crowd_level: str = "unknown"`
- `lat: Optional[float]`
- `lng: Optional[float]`

**`backend/agents/recommendation_agent.py`**:
- Populates all four new fields from `LocationResult` at candidate construction
- RAG fetch: `n_results=10` → `n_results=15`
- Result cap: `candidates[:5]` → `candidates[:10]`

**`backend/tools/nea_client.py`** — `get_static_hygiene_for_centre()` now has a three-tier match:
1. Exact match (unchanged)
2. Substring in either direction (unchanged)
3. **New:** Jaccard token similarity ≥ 0.4, ignoring noise words (BLK, AVE, MARKET, FOOD, CENTRE, etc.)

This recovers grades for centres whose short display name ("Clementi 448") shares key tokens with the SFA file's long name ("Clementi Ave 3 Blk 448") but has no substring overlap.

### Frontend changes

**`AgentPanel.tsx`**: terminal text changed from hardcoded `text-green-300/70` to `dark:text-green-300/70 text-emerald-800/70` — readable in both modes.

**`ResultCard.tsx`**:
- `onClick` opens `https://www.google.com/maps/search/?api=1&query=STALL+CENTRE+Singapore` in a new tab
- "Maps ↗" hint appears bottom-right on hover (`group-hover:opacity-100`)
- Review count displayed alongside rating: `4.4 ★ (23,090)`
- Crowd badge shown when `crowd_level` is "busy" or "quiet" and stall is open

**`ResultsList.tsx`** — infinite scroll via `IntersectionObserver`:
- `visibleCount` state starts at 5, resets on new results
- Sentinel `<div>` below visible cards triggers `+5` reveal when it enters viewport
- "X of Y results" counter in top-right of section header

**`HawkerMap.tsx`** — complete rewrite replacing Mapbox with Leaflet:
- `react-map-gl` / `mapbox-gl` / `@types/mapbox-gl` removed (bundle: 2 MB → 430 KB)
- `react-leaflet@4` + `leaflet` + `@types/leaflet` added (React 18 compatible)
- Tiles: CartoDB Positron (light) / CartoDB DarkMatter (dark) — free, no token
- Markers: `L.divIcon` with inline SVG amber circles — same visual design as before
- Popups: Leaflet `<Popup>` replaces the custom `MapDetailPanel` component
- Map always renders when results have coordinates — no token guard
- `MapMarker.tsx` and `MapDetailPanel.tsx` deleted

**`App.tsx`**: map token guard removed; mobile map rendered below results via a separate `<HawkerMap>` instance inside a fixed-height `div`.

### Known issue — Leaflet default icon missing
Leaflet's default marker icons rely on `marker-icon.png` bundled with the package. Since we use custom `divIcon` markers exclusively, no fix needed — default icons never appear.

### Test results — Milestone 6 Refactor
- 69/69 backend tests passing (+1 new test: `test_result_carries_location_signals`)
- Frontend build: zero TypeScript errors, 430 KB JS bundle (no mapbox-gl)
- `test_returns_maximum_ten_results` replaces `test_returns_maximum_five_results`

---

## Session Notes — RQA Run 01 (2026-04-26)

### What is RQA?

Recursive Quality Agent: an autonomous improvement loop run via `.claude/agents/rqa.md`.
Each run executes 3 cycles of CRITIQUE → PRIORITISE → EXECUTE → VERIFY → REFLECT.
Each cycle selects 3 improvements scored by Impact × Feasibility × Breadth (≥1 user-facing, ≥1 backend).

### Cycle 1 — Foundations

**C1-1: Error boundary + error state UI**
- Created `frontend/src/components/ErrorBoundary.tsx` — catches render crashes, shows retry
- Wired into `main.tsx`; error banner added to `App.tsx` using `error` from `useSSE`
- Previously: unhandled throw → white screen; SSE errors silently swallowed

**C1-2: IntersectionObserver dependency fix**
- `ResultsList.tsx`: removed `visibleCount` from `useEffect` deps, used `totalRef` (ref) instead
- Observer now created once per result set, not re-created on every scroll trigger
- Sentinel div always mounted for stable observer target

**C1-3: Jaccard similarity tests + docstring fix**
- 5 new tests in `test_nea_client.py` covering exact, fuzzy, different, empty, and real-world matches
- Fixed stale docstring in `recommendation_agent.py`: "top 3" → "top 10"

### Cycle 2 — Accessibility + Cache Correctness

**C2-1: prefers-reduced-motion**
- `@media (prefers-reduced-motion: reduce)` in `index.css` — collapses all animation/transition durations globally

**C2-2: ResultCard keyboard accessibility**
- `tabIndex={0}`, `role="link"`, `aria-label`, `onKeyDown` (Enter/Space)
- `focus-visible:ring-2` focus ring; "Maps ↗" always partially visible (opacity-50)

**C2-3: Sentiment cache key collision fix**
- `recommendation_agent.py`: `sha256(reviews[:500])` → `sha256(reviews)` — full text hash

### Cycle 3 — Screen Readers, Map Performance, RAG Tests

**C3-1: AgentPanel aria-live**
- `role="log"`, `aria-live="polite"`, `aria-label` on trace container

**C3-2: HawkerMap marker diffing**
- Replaced clear-all-and-recreate with `Map<string, L.Marker>` ref-based diffing
- Stale markers removed, existing updated in-place, new ones added — eliminates DOM thrash

**C3-3: vector_store.py tests**
- 9 new tests in `test_vector_store.py`: empty query, add+query, semantic ordering, n_results cap, upsert, metadata conversion

### Test results — RQA Run 01
- 83/83 passing (+14 from pre-RQA baseline of 69)
- Frontend build: zero TypeScript errors, 433 KB JS bundle
- Zero regressions across all 3 cycles

### Carry-forward to RQA Run 02
- ResultCard not memoized (React.memo)
- Double static hygiene fetch in hygiene_agent
- No concurrent request / rate limiting tests
- No end-to-end integration test
- TypewriterText Framer Motion inline styles may bypass CSS reduced-motion

---

## Session Notes — RQA Run 02 (2026-04-29)

### Cycle 1 — Reduced Motion, Double Fetch, Cache Eviction

**C1-1: TypewriterText respects prefers-reduced-motion**
- Added `usePrefersReducedMotion()` hook to `AgentPanel.tsx` using `window.matchMedia`
- When reduced motion is preferred, TypewriterText renders plain text with zero Framer Motion overhead
- Closes the last animation escape hatch from the CSS-only approach in RQA-01

**C1-2: Eliminate double static hygiene fetch**
- `hygiene_agent.py`: declared `static_stalls` before the if/else block, reused from first fetch
- Previously called `get_static_hygiene_for_centre()` twice per centre when using static data
- New test asserts exactly 1 call per centre

**C1-3: Bound sentiment cache with LRU eviction**
- `_SENTIMENT_CACHE_MAX_SIZE = 500` added to `recommendation_agent.py`
- After each new entry, oldest entries evicted by timestamp if size exceeds max
- Prevents unbounded memory growth in long-running processes

### Cycle 2 — SearchBar A11y, SVG Id Collision, Orchestrator Error Tests

**C2-1: SearchBar accessibility**
- `<input>`: `aria-label="Search for hawker food in Singapore"`
- Location button: dynamic `aria-label` for loading/acquired/default states
- Submit button: `aria-label` toggling between "Searching..." and "Search"

**C2-2: Fix StarRating shared clipPath id**
- Replaced static `id="half"` with `useId()` hook for unique per-instance ids
- Fixes rendering bugs when multiple cards have half-star ratings

**C2-3: Orchestrator error-wrapper tests**
- `test_outer_run_catches_unexpected_exception_and_yields_error`: RuntimeError from sub-agent caught
- `test_outer_run_catches_query_parse_crash`: Anthropic API crash falls back to defaults

### Cycle 3 — React.memo, Display Bug Fix, SSE Integration Test

**C3-1: Memoize ResultCard with React.memo**
- `ResultCard` wrapped in `memo()` — avoids re-renders during search phase when results are unchanged
- Carry-forward item from RQA-01 resolved

**C3-2: Fix visibleCount display in ResultsList**
- Counter now shows `Math.min(visibleCount, total)` instead of raw `visibleCount`
- Previously displayed "10 of 8" when observer triggered with fewer results

**C3-3: SSE endpoint integration test**
- Created `backend/tests/test_sse_endpoint.py` with 3 tests using FastAPI TestClient
- Covers: full SSE event flow, request validation (422), health endpoint
- First integration test in the codebase — catches routing and serialization issues

### Test results — RQA Run 02
- 90/90 passing (+7 from pre-RQA-02 baseline of 83)
- Frontend build: zero TypeScript errors, 433 KB JS bundle
- Zero regressions across all 3 cycles

### Carry-forward to RQA Run 03
- `_load_json_list` called per-request instead of cached at module level
- Header "Hawker Hunt" button lacks `role="button"` and `aria-label`
- Orchestrator creates new `OneMapClient()` per geocode instead of reusing injected one
- No rate-limiting or concurrent request protection tests
- Recommendation agent docstring still says "top 3" (line 208)

---

## Session Notes -- RQA Run 03 (2026-05-03)

### Cycle 1 -- JSON Cache, Header A11y, OneMapClient Reuse

**C1-1: Cache `_load_json_list` at module level**
- Added `_json_list_cache: dict[str, list[str]]` in `recommendation_agent.py`
- First disk read cached; subsequent calls return cached result
- Eliminates redundant file I/O on every search request for static JSON files
- Also fixed stale docstring: "Return up to 3" -> "Return up to 10"

**C1-2: Header reset button accessibility**
- `App.tsx`: added `role="button"`, `tabIndex={0}`, `aria-label`, `onKeyDown` (Enter/Space)
- Focus ring with `focus-visible:ring-2`; decorative dot marked `aria-hidden="true"`

**C1-3: Reuse OneMapClient in orchestrator**
- Added `onemap_client` parameter to `OrchestratorAgent.__init__`; stored as `self._onemap`
- `_resolve_location` uses injected client instead of creating a new one per call
- Test verifies injected mock is called exactly once

### Cycle 2 -- SSE Resilience, Reduced-Motion Perf, NEA Cache Bound

**C2-1: SSE stream timeout and mid-stream error resilience**
- `api.ts`: 120s `setTimeout` auto-aborts hung streams
- `try/finally` around reader loop ensures `onComplete()` always fires
- `userCancelled` flag distinguishes user abort (silent) from timeout abort (error message)

**C2-2: Lift usePrefersReducedMotion from TypewriterText**
- Hook moved from `TypewriterText` to `AgentPanel` parent; passed as `reducedMotion` prop
- One `matchMedia` listener per panel instead of one per trace line

**C2-3: Bound NEA client cache**
- `_CACHE_MAX_ENTRIES = 10` added to `nea_client.py`
- Eviction logic in `_fetch()` removes oldest entries above max
- Same pattern as sentiment cache eviction from RQA-02

### Cycle 3 -- Map A11y, Closure Tests, Chip Labels

**C3-1: Map section landmarks and labels**
- Desktop: `motion.div` -> `motion.section` with `aria-label="Map of recommended hawker centres"`
- Mobile: `<div>` -> `<section>` with same aria-label
- Both are now identifiable landmarks in accessibility tree

**C3-2: Hygiene closure date test coverage**
- 3 new tests: centre absent from closures, closure API failure, substring match
- Previously only exact-match happy path was tested

**C3-3: SearchBar example chips accessibility**
- Each chip: `aria-label="Try search: {text}"`
- Container: `role="group"`, `aria-label="Example searches"`

### Test results -- RQA Run 03
- 96/96 passing (+6 from pre-RQA-03 baseline of 90)
- Frontend build: zero TypeScript errors, 434 KB JS bundle
- Zero regressions across all 3 cycles

### Carry-forward to RQA Run 04
- No rate-limiting or concurrent request safety tests
- `_cuisine_time_score` substring matching could produce false positives
- `ResultsList` empty state uses emoji instead of SVG icon
- `test_sse_endpoint.py` uses `try/finally` instead of `monkeypatch` for orchestrator swap
- `HawkerMap` DivIcon instances not cached by rank number

---

## Session Notes — Milestone 8A: ChromaDB Production Fix (2026-05-21)

### Problem

Render's ephemeral filesystem wipes new writes on redeploy. The `chroma_db/` vector data was
committed to git (workaround), but the ONNX embedding model (~80MB, all-MiniLM-L6-v2) was
downloaded at first query time — not at startup. This caused the first search to timeout on Render.

### Solution: Pre-download ONNX model at Render build time

Three changes bake the model into the deployment image:

**`backend/nixpacks.toml`** — Added `[phases.build]` section with two commands:
1. `pip install -r requirements.txt`
2. `python -c "from chromadb.utils.embedding_functions import DefaultEmbeddingFunction; ef = DefaultEmbeddingFunction(); ef(['warmup']); print('Embedding model cached.')"` — forces 80MB download during build

**`backend/rag/vector_store.py`** — New `warmup()` method:
- `self._ef(["warmup"])` — triggers model load at startup (instant if already cached from build)

**`backend/main.py`** — Lifespan calls `vs.warmup()` immediately after `VectorStore()` instantiation:
- Seeding disabled on production (`ENVIRONMENT=production`) to prevent startup timeout
- `chroma_db/` data is committed to git and present at startup

### Deployment

- Frontend: Vercel (set `VITE_API_URL` env var to Render backend URL)
- Backend: Render (auto-deploys from `main` branch via nixpacks)

### Verification
- `curl https://sg-hawker-hunt.onrender.com/api/health` → 200, all systems ready
- `POST /api/search {"query":"laksa"}` → 10 ranked stalls, SSE streaming, no timeout

### Test results — Milestone 8A
- 96/96 passing (no new tests — infrastructure change only)

---

## Session Notes — Milestone 8B: Design Wiki (2026-05-21)

### Part 1: Design Wiki Infrastructure

**New agent: `.claude/agents/design-wiki.md`**
- Protocol: 3 cycles per run, each cycle SCAN → SCORE → EXECUTE → EXPAND → DOCUMENT
- Scoring: User Delight × Feasibility × Differentiation (1-5 each)
- Self-expanding: EXPAND phase discovers sub-patterns from what was just built
- Trigger: `run design-wiki`

**New directory: `design-wiki/`**
- `inspirations/` — 4 seed entries with 19 total patterns:
  - `hotels-com-map.md` (5 patterns): detail panel, card↔pin sync, distance context, time banner, amenity chips
  - `zillow-map-grid.md` (6 patterns): split pane, grade pins, 2-col grid, viewport counter, map controls, filter bar
  - `linear-density.md` (5 patterns): tabular nums, opacity hierarchy, subtle borders, keyboard nav, activity indicators
  - `perplexity-sources.md` (3 patterns): inline citations, collapsible reasoning, structured trace blocks
- `run-log/` — auto-written after each agent run

### Part 2: Design Wiki Run 01 — 5 patterns implemented

**Cycle 1 — Map interaction (highest delight)**

| Pattern | Score | Implementation |
|---------|-------|----------------|
| hotels-02 (card↔pin sync) | 14 | `App.tsx`: `selectedKey` state. `ResultCard`: `onSelect` callback + `isSelected` highlight. `HawkerMap`: `selectedKey` prop + `onMarkerClick` callback. `ResultsList`: scroll-to-card via `data-key` + `scrollIntoView`. |
| zillow-02 (grade pins) | 14 | `HawkerMap`: markers now show hygiene grade letter (A/B/C/D/—) colour-coded green/amber/red/grey. Selected marker scales 34→42px with glow ring. Replaces rank-number markers. |

**Cycle 2 — Information richness**

| Pattern | Score | Implementation |
|---------|-------|----------------|
| hotels-01 (detail panel) | 13 | New `StallDetailPanel.tsx`: slides from right (desktop, max-w-md) / bottom sheet (mobile, 75vh). Rank badge, all status badges, stats grid (distance/rating/score), standout quote, full reasoning, Google Maps CTA. Closes on Escape / outside click / close button. ARIA dialog with modal. |

**Cycle 3 — Filters + context**

| Pattern | Score | Implementation |
|---------|-------|----------------|
| zillow-06 (filter strip) | 12 | New `FilterStrip.tsx`: 5 toggle pills (Michelin, Halal, Open now, Grade A, Under $5). Active: filled amber. Inactive: outlined. Client-side filtering in `App.tsx` via `applyFilters()`. Count indicator when filters active. |
| hotels-04 (time banner) | 12 | `App.tsx`: `getTimeContext()` checks SGT hour (UTC+8). Breakfast 6-11, Lunch 11-15, Dinner 17-21, Supper 21-3. Amber-tinted banner with clock emoji. |

### Interaction model change

`ResultCard` click no longer opens Google Maps directly. Instead:
- Click → `onSelect(key)` → opens `StallDetailPanel` with full details
- Google Maps link moved inside the detail panel as a prominent CTA button
- `role` changed from `"link"` to `"button"`, `aria-pressed` for selected state
- Reasoning text truncated to 2 lines (`line-clamp-2`) on card; full text in panel

### EXPAND phase — 12 sub-patterns discovered

From detail panel: swipe between stalls, share stall link, panel scroll memory
From card↔pin sync: hover preview, smooth animated pan
From grade pins: cluster at low zoom, cuisine label on hover
From filter strip: count badges, animate transitions, persist to URL
From time banner: dismiss for session, actionable click-to-filter

### Files changed

| File | Change |
|------|--------|
| `frontend/src/App.tsx` | Rewritten — selectedKey, filters, time banner, detail panel, layout wiring |
| `frontend/src/components/HawkerMap.tsx` | Rewritten — grade-coloured pins, selectedKey, onMarkerClick, exported `markerKey` |
| `frontend/src/components/ResultCard.tsx` | Modified — onSelect, isSelected, data-key, line-clamp, role=button |
| `frontend/src/components/ResultsList.tsx` | Modified — selectedKey, onSelect passthrough, scroll-to-card, SVG empty state |
| `frontend/src/components/StallDetailPanel.tsx` | **New** — slide-in detail panel |
| `frontend/src/components/FilterStrip.tsx` | **New** — filter toggle pills with FilterKey type |
| `design-wiki/` | **New** — full directory structure with 4 inspirations + run log |
| `.claude/agents/design-wiki.md` | **New** — agent definition |

### Test results — Milestone 8B
- 96/96 backend tests passing (no backend changes this milestone)
- Frontend build: zero TypeScript errors, 478 KB JS bundle
- Run log: `design-wiki/run-log/2026-05-21-run-01.md`

### Carry-forward to Design Wiki Run 02
- zillow-01 (persistent 50/50 split pane) — partially done, not true 50/50
- zillow-03 (2-column card grid)
- zillow-05 (floating map controls)
- perplexity-02 (collapsible reasoning with expand toggle)
- linear-04 (keyboard navigation j/k/Enter/Escape)
- 12 sub-patterns from Run 01 EXPAND phase

---

## Session Notes — Milestone 9: Data Quality Fixes (2026-05-21)

### Three critical data quality problems fixed

#### Fix B — Cuisine hard-filter in RAG retrieval

**Problem:** Querying "chicken rice" returned "claypot rice" because ChromaDB semantic similarity
treats all rice dishes as similar. No metadata-level filtering was applied.

**Solution: ChromaDB `where`-clause filtering with cuisine normalisation**

- `backend/rag/vector_store.py`: `query()` now accepts `cuisine_filter` and `region_filter` params.
  When provided, a `where` clause (`$eq` on cuisine/region metadata) restricts results.
  Falls back to unfiltered query if filtered returns 0 results.
- `backend/agents/recommendation_agent.py`: New `CUISINE_KEYWORDS` dict maps 50+ variants
  (Singlish/abbreviations) to canonical forms. `_normalise_cuisine()` resolves user input.
  `run()` extracts `cuisine_type` and `region` from preferences and passes to vector store.
- `backend/agents/orchestrator.py`: `_PARSE_SYSTEM` prompt now extracts `region` field
  ("central"/"east"/"west"/"north"/"north_east") from user query.

**ChromaDB operator note:** `$contains` does not work for metadata fields in chromadb 1.5.7.
Used `$eq` instead — works because cuisine values are normalised to exact canonical forms.

#### Fix C — Hygiene grade matching improvement

**Problem:** Jaccard matching at 0.4 threshold failed for ~60% of centres. Names like
"Bedok Interchange Hawker Centre" vs "Bedok Interchange Food Centre" had high Jaccard
(shared tokens) but also needed SequenceMatcher for substring-level similarity.

**Solution: Postal code as primary key + combined similarity at 0.55**

- `backend/models/schemas.py`: `LocationResult` gains `postcode: Optional[str]` field.
- `backend/agents/location_agent.py`: Extracts 6-digit postal code from Google Places
  `formattedAddress` via regex `Singapore\s+(\d{6})`. Tries both search and detail responses.
- `backend/tools/nea_client.py`:
  - `_load_static_grades()` now returns two indexes: `by_name` and `by_postcode`
  - New `_name_similarity()` function: max of `SequenceMatcher.ratio()` and Jaccard similarity
  - `get_static_hygiene_for_centre()` now accepts `postcode` parameter
  - Match priority: postal code exact → name exact → substring → combined similarity ≥ 0.55
- `backend/agents/hygiene_agent.py`: `run()` accepts `postcodes: dict[str, str]` parameter,
  passes postcode to `get_static_hygiene_for_centre()`.
- `backend/agents/orchestrator.py`: Builds `centre_postcodes` dict from location results,
  passes to hygiene agent.

#### Fix A — Data pipeline agent

**New file: `backend/tools/data_pipeline.py`**

CLI tool to expand the ChromaDB knowledge base from 71 to 800+ stalls:
1. Fetches all NEA hawker centres (123 centres with lat/lng)
2. For each centre, searches Google Places for food stalls within 200m
3. Generates rich 50-70 word descriptions via Claude Haiku
4. Classifies cuisine type, tags, halal status, best time, price range via Claude Haiku
5. Seeds ChromaDB with the expanded dataset

Features:
- Checkpoint pattern: saves per-centre results to `pipeline_checkpoint.json`
- Rate limiting: 0.3s between Places calls, 0.2s between Claude calls
- Region classification from lat/lng bounding boxes
- Michelin/halal tagging from existing static JSON lists
- Resume support: skips already-processed centres

**Usage:**
```bash
cd backend
python -m tools.data_pipeline --centres 3 --dry-run    # preview 3 centres
python -m tools.data_pipeline --centres 10              # process 10 centres
python -m tools.data_pipeline                           # full run (~120 centres)
```

**Dry-run result:** 123 centres fetched from NEA API. Stall expansion requires
`GOOGLE_PLACES_API_KEY` and `ANTHROPIC_API_KEY` to be set.

### Test results — Milestone 9
- 106/106 passing (+10 from pre-M9 baseline of 96)
- Frontend build: zero TypeScript errors, 478 KB JS bundle
- Zero regressions

### New tests added
- `test_cuisine_filter_narrows_results` — ChromaDB where-clause filters correctly
- `test_cuisine_filter_fallback_on_no_match` — falls back to unfiltered on 0 results
- `test_region_filter_narrows_results` — region filter works
- `test_normalise_cuisine_direct_match` — exact keyword matching
- `test_normalise_cuisine_singlish_variants` — Singlish/abbreviation mapping
- `test_normalise_cuisine_unknown_returns_none` — unknown cuisines return None
- `test_cuisine_filter_passed_to_vector_store` — integration: filter reaches vector store
- `test_postcode_match_takes_priority_over_name` — postal code > name matching
- `test_sequence_matcher_matches_bedok_variants` — SequenceMatcher catches near-misses
- `test_name_similarity_rejects_unrelated` — unrelated names score below threshold

---

## Session Notes — OpenRouter Integration (2026-05-23)

### Problem
All LLM calls (orchestrator query parsing + sentiment analysis) went through Anthropic SDK,
incurring real costs per request. Free-tier models on OpenRouter can handle these structured
JSON extraction tasks adequately.

### Solution: Central inference abstraction with OpenRouter primary + Anthropic fallback

**New file: `backend/tools/inference_client.py`**
- `InferenceClient` class: single `complete(call_type, system, user_content)` method
- `InferenceError` exception: raised only when both providers fail
- `_clean_response()`: strips `<think>...</think>` blocks from Nemotron, extracts `{...}` JSON
- Properties: `active_provider`, `openrouter_configured`, `anthropic_configured`

**Model routing:**

| Call type | OpenRouter (primary) | Anthropic (fallback) |
|-----------|---------------------|---------------------|
| orchestrator | `nvidia/nemotron-3-super-120b-a12b:free` | `claude-sonnet-4-6` |
| sentiment | `nvidia/llama-3.3-nemotron-super-49b-v1:free` | `claude-haiku-4-5-20251001` |

**OpenRouter integration:**
- Uses `openai` Python SDK pointed at `https://openrouter.ai/api/v1`
- Required headers: `HTTP-Referer` (from `FRONTEND_URL` env var) and `X-Title: Hawker Hunt`
- `openai>=1.40.0` added to `requirements.txt`

**Fallback triggers (any of these → silent fallback to Anthropic):**
- Missing `OPENROUTER_API_KEY` → OpenRouter skipped entirely
- HTTP 429 rate limit, HTTP 5xx server error, timeout, any unhandled exception
- All triggers log at WARNING level

**Nemotron response cleaning:**
- `<think>...</think>` blocks stripped via regex (Nemotron emits reasoning tokens)
- If result isn't valid JSON, first `{...}` block extracted via regex
- If no JSON found, raw text returned (caller's `json.loads` fails and uses defaults)

### Agent changes

**`backend/agents/orchestrator.py`:**
- `import anthropic` removed; `from tools.inference_client import InferenceClient` added
- Constructor: `anthropic_client` → `inference_client: InferenceClient | None`
- `_parse_query()`: `self._anthropic.messages.create(...)` → `self._inference.complete("orchestrator", ...)`

**`backend/agents/recommendation_agent.py`:**
- Same pattern: `anthropic_client` → `inference_client`
- `_analyse_sentiment()`: `self._anthropic.messages.create(...)` → `self._inference.complete("sentiment", ...)`
- Cache, eviction, and error handling unchanged

**`backend/main.py`:**
- `/api/health` now reports `llm_provider`, `openrouter_configured`, `anthropic_configured`

### Data pipeline not changed
`backend/tools/data_pipeline.py` (CLI batch tool) still uses Anthropic directly — it's a
one-off tool for knowledge base expansion, not part of the runtime request path.

### New env var
`OPENROUTER_API_KEY` added to `.env.example` with comment.

### Test results — OpenRouter Integration
- 122/122 passing (+16 new tests, 0 regressions)
- New `test_inference_client.py`: 16 tests covering success path, think tag stripping,
  JSON extraction, all fallback triggers, both-fail error, model routing, provider properties
- All existing agent tests updated: `anthropic_client=` → `inference_client=`
- Mock pattern: `_mock_inference_client(response_json)` returns mock with `complete = AsyncMock`

---

## Session Notes -- RQA Run 04 (2026-07-06)

### Cycle 1 -- Filter Fix, Inference Timeout, Focus Trap

**C1-1: Fix "Under $5" filter end-to-end**
- Added `price_category` field to `RankedRecommendation` schema ("cheap"/"moderate"/"expensive")
- Populated from existing three-tier price computation in `recommendation_agent.py`
- Added to TypeScript types; replaced no-op `return true` with actual filter logic in `applyFilters()`
- Previously: clicking "Under $5" toggled visually but never filtered results

**C1-2: Add 30-second timeout to inference client**
- Both OpenRouter and Anthropic calls wrapped in `asyncio.wait_for(timeout=30)`
- OpenRouter timeout silently falls back to Anthropic; Anthropic timeout raises `InferenceError`
- Prevents backend worker from blocking indefinitely on a hung LLM provider

**C1-3: Add focus trap to StallDetailPanel**
- Tab cycles within the dialog; focus moves to close button on open; restored on close
- Keyboard listener only active when panel is open (WCAG 2.1 SC 2.4.3)

Tests after C1: 128/128 (+5 new)

### Cycle 2 -- Price Badge UI, SSE Test Rewrite, Anthropic Key Guard

**C2-1: Display price badge in ResultCard and StallDetailPanel**
- Added `price` type to `StatusBadge`: green "$ Under $6", neutral "$$ Moderate", amber "$$$ Pricey"
- Badge shown in both card and detail panel; `null` for undefined price_category

**C2-2: Rewrite SSE endpoint tests with monkeypatch (carry-forward CF-4)**
- Replaced fragile `try/finally` with `@pytest.fixture` using `monkeypatch.setattr`
- Original orchestrator auto-restored regardless of test outcome

**C2-3: Guard Anthropic client creation**
- `AsyncAnthropic()` only created when `ANTHROPIC_API_KEY` is set (mirrors OpenRouter guard)
- Fallback path raises clear `InferenceError` with "ANTHROPIC_API_KEY missing" message

Tests after C2: 129/129 (+1 new)

### Cycle 3 -- Filter Label, Cuisine Matching, Concurrent Test

**C3-1: Fix filter label and time banner accessibility**
- "Under $5" renamed to "Budget" (matches actual $6 threshold)
- Clock emoji replaced with SVG icon; `role="status"` and `aria-live="polite"` added

**C3-2: Fix _cuisine_time_score word-boundary matching (carry-forward CF-2)**
- Created `_cuisine_word_match()` with regex `\b...\b` word-boundary matching
- Removed ambiguous "porridge" from breakfast set (congee covers it; frog porridge is supper)

**C3-3: Concurrent SSE request test**
- Two sequential requests through full FastAPI pipeline, both verified complete
- Resets `sse_starlette` global `AppStatus.should_exit_event` between requests

Tests after C3: 137/137 (+8 new)

### Test results -- RQA Run 04
- 137/137 passing (+14 from pre-RQA-04 baseline of 123)
- Frontend build: zero TypeScript errors, 443 KB JS bundle
- Zero regressions across all 3 cycles

### Carry-forward to RQA Run 05
- `HawkerMap` DivIcon instances not cached by grade+isSelected
- No true concurrent request test (current is sequential due to TestClient limitations)
- Sentiment cache key uses full review text hash but only sends first 2000 chars to LLM
- `_cuisine_time_score` has overlapping entries ("bak chor mee" in both breakfast and supper)
- `ResultsList` empty state uses emoji instead of SVG icon

