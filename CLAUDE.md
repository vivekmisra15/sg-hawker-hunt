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

### Milestone 2 — Agents (session 2)
- [ ] Hygiene Agent: NEA data fetch + structured output
- [ ] Location Agent: OneMap geocoding + Google Places integration
- [ ] Recommendation Agent: ChromaDB RAG setup + Michelin/halal flags
- [ ] Orchestrator: coordinates all three, returns structured result
- [ ] Verify: each agent has passing unit tests

### Milestone 3 — Streaming + integration (session 3)
- [ ] SSE endpoint: POST /api/search streams AgentEvents
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

## Kaggle / Gemma 4 parallel context

This project is also the foundation for a Kaggle Gemma 4 Good Hackathon entry
(deadline May 18, 2026). The AQI Advisor project ("Vayu") reuses this same
multi-agent architecture with Gemma 4 E4B as the model backend instead of Claude.
When the Hawker Hunt architecture is proven, port it for Vayu.

Do NOT mix Kaggle work into Hawker Hunt sessions.
