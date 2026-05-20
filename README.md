# 🍜 Hawker Hunt

> AI-powered hawker food intelligence for Singapore.
>
> Ask in plain English. Watch three agents reason in real time.
> Get ranked recommendations with hygiene grades, Michelin badges, and honest explanations.

**Live Demo:** [hawker-hunt.vercel.app](https://hawker-hunt.vercel.app)

---

## What it does

Hawker Hunt is a multi-agent AI system that helps people find the best hawker stall for their needs **right now** — factoring in cuisine, location, dietary requirements, hygiene grades, open status, crowd timing, and Michelin recognition.

The differentiator is a **live reasoning panel** that streams each agent's thinking as it fires. The transparency of the reasoning IS the product — you don't just get a recommendation, you get to watch the AI think through it.

---

## Architecture

Three specialized agents coordinate via an orchestrator:

```
User query: "good laksa near Toa Payoh, vegetarian, 1pm"
    │
    ▼
┌─────────────────────────────────────────────────┐
│         Orchestrator Agent                      │
│  (claude-sonnet-4-6 via Anthropic SDK)          │
│                                                 │
│  Parses query → extracts intent, location,      │
│  cuisine, dietary needs, time context           │
│  Spawns sub-agents, synthesises output          │
└──────────┬──────────────────────────────────────┘
           │
     ┌─────┴──────┬──────────────────┐
     ▼            ▼                  ▼
┌─────────────┐ ┌──────────────┐ ┌─────────────────┐
│ Hygiene     │ │Location      │ │Recommendation   │
│Agent        │ │Agent         │ │Agent            │
│             │ │              │ │                 │
│NEA data     │ │OneMap        │ │RAG + scoring:   │
│SFA fallback │ │Google Places │ │  - Cuisine match│
│grades,      │ │Google Geoloc │ │  - Hygiene      │
│history      │ │weather       │ │  - Google rating│
│            │ │              │ │  - Sentiment    │
│             │ │              │ │  - Price tier   │
│             │ │              │ │  - Wait times   │
└─────────────┘ └──────────────┘ └─────────────────┘
     │              │                     │
     └──────┬───────┴─────────────────────┘
            ▼
    Orchestrator synthesises
    results into ranked list
            │
            ▼
    ┌──────────────────────────┐
    │ Streaming SSE response   │  ← React frontend
    │ with live agent traces   │    receives and
    │ in real time             │    renders live
    └──────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 18 + Vite | Fast, type-safe SPA with HMR |
| **Frontend Styling** | Tailwind CSS + shadcn/ui | Dark-mode-first, semantic design tokens |
| **Frontend Animation** | Framer Motion | 60fps token-reveal, card entrances, map pins |
| **Backend API** | FastAPI 0.115 | Async Python, JSON request/response |
| **Backend Streaming** | sse-starlette + SSE | Server-Sent Events for live agent traces |
| **Agent Orchestration** | Anthropic SDK (claude-sonnet-4-6) | Multi-agent reasoning with structured output |
| **Vector Store** | ChromaDB 0.5+ | In-memory RAG over hawker knowledge base |
| **Embeddings** | Anthropic embeddings API | Semantic search without external models |
| **HTTP Client** | httpx 0.27 | Async HTTP requests to external APIs |
| **Testing** | pytest + pytest-asyncio | Unit tests + integration tests |
| **Env Management** | python-dotenv | `.env` file for API keys |
| **Frontend Build** | Vite 5.4 + TypeScript | Zero-config build with tree-shaking |
| **CSS Framework** | CartoDB Tiles + Leaflet | Free map tiles, no Mapbox token needed |

---

## AI Engineering Patterns Demonstrated

- **Multi-agent orchestration** — three agents (hygiene, location, recommendation) run in parallel via `asyncio.gather()`, each with a focused domain responsibility
- **RAG pipeline** — ChromaDB vector store with 71+ seeded hawker stall profiles, semantic search on user intent
- **Server-Sent Events** — streaming agent reasoning tokens in real time to the frontend, maintaining state across 3+ agents
- **Tiered scoring** — six independent quality signals (Google rating, LLM sentiment, time-aware heuristics, demerit penalties, price tier matching, suspension filters) with graceful degradation when data is missing
- **Structured output** — Pydantic models enforce response schemas, Anthropic SDK structured outputs for sentiment and query parsing
- **Singlish-aware NLP** — sentiment analysis trained on Singapore local food culture, queue queues treated as quality signals, particle markers (lah, lor, leh) preserved
- **Production resilience** — all external API calls are wrapped in try/except, missing data sources never crash the pipeline, graceful fallbacks to static data (SFA hygiene file, ChromaDB seed)

---

## Data Sources

| Source | What we use | API / Access | Notes |
|--------|-----------|------------|-------|
| **NEA hawker centres** | GeoJSON locations, 120+ centres | data.gov.sg (free) | Centre addresses, opening hours |
| **SFA hygiene data** | Grade A/B/C/D fallback | Static file (scrape checkpoint) | SFA replaced NEA in Jan 2026; no public API for stall-level grades |
| **OneMap** | Geocoding, routing | onemap.gov.sg (free) | Convert location text → lat/lng |
| **Google Places API v1** | Rating, hours, reviews, open-now | $200/mo free credit | Rating, review sentiment, queue signals |
| **OpenWeatherMap** | Current weather (rain alert) | Free tier, 1000 calls/day | Avoid outdoor centres in rain |
| **Michelin Bib Gourmand 2025** | 89 stalls pre-seeded | Static JSON file (`data/michelin_2025.json`) | Verified manually from official list |
| **MUIS halal certification** | Halal-certified stalls | Static JSON file (`data/halal_stalls.json`) | Verified from MUIS registry |
| **Hawker knowledge base** | Stall descriptions, dish profiles, stories | ChromaDB seeded from `rag/seed.py` | 71 hand-curated stall profiles across 15 cuisines |

---

## Local Development Setup

### Prerequisites
- Python 3.11+
- Node 18+
- macOS / Linux / WSL2 (Windows)

### Step 1: Clone and enter the directory
```bash
git clone https://github.com/yourusername/hawker-hunt.git
cd hawker-hunt
```

### Step 2: Backend setup
```bash
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy env file and fill in your API keys
cp ../.env.example ../.env
# Edit .env and add:
#   - ANTHROPIC_API_KEY (get from console.anthropic.com)
#   - GOOGLE_PLACES_API_KEY (get from Google Cloud Console)
#   - OPENWEATHER_API_KEY (get from openweathermap.org)
#   - DATAGOV_API_KEY (get from data.gov.sg/developer)
```

### Step 3: Seed ChromaDB (one-time)
```bash
# From backend/ directory with venv activated
python3 -m rag.seed
# Output: "Seeded 71 documents into ChromaDB collection 'hawker_knowledge'."
```

### Step 4: Run backend server
```bash
# From backend/ with venv activated
uvicorn main:app --reload --port 8000
# Should print: "Uvicorn running on http://127.0.0.1:8000"
```

### Step 5: Frontend setup (new terminal)
```bash
cd frontend
npm install
npm run dev
# Vite will print: "Local: http://localhost:5173/"
```

### Step 6: Open the app
Navigate to **http://localhost:5173** in your browser.

### Running tests
```bash
cd backend
pytest tests/ -v
# Should show: "96 passed in 14.38s"
```

---

## Environment Variables

| Variable | Purpose | Where to get it |
|----------|---------|-----------------|
| `ANTHROPIC_API_KEY` | Claude Sonnet API key | [console.anthropic.com](https://console.anthropic.com) — free $5 credit per month |
| `GOOGLE_PLACES_API_KEY` | Google Places API v1 key | [Google Cloud Console](https://console.cloud.google.com) — Places API, $200/mo free credit |
| `OPENWEATHER_API_KEY` | OpenWeatherMap current weather | [openweathermap.org](https://openweathermap.org/api) — free tier, 1000 calls/day |
| `DATAGOV_API_KEY` | Data.gov.sg authentication | [data.gov.sg/developer](https://data.gov.sg/developer) — free registration, higher rate limits |
| `BACKEND_URL` | Backend origin for frontend calls | Dev: `http://localhost:8000` \| Prod: `https://your-railway-app.railway.app` |
| `FRONTEND_URL` | Frontend origin for CORS | Dev: `http://localhost:5173` \| Prod: `https://your-vercel-app.vercel.app` |
| `ENVIRONMENT` | Deployment context | `development` or `production` |
| `BACKEND_CORS_ORIGINS` | Extra CORS origins (comma-separated) | Leave empty for dev, or add extra domains for prod |

---

## Project Structure

```
hawker-hunt/
├── README.md                          ← This file
├── CLAUDE.md                          ← Architecture decisions and session notes
├── .env                               ← API keys (gitignored)
├── .env.example                       ← Committed template
│
├── backend/
│   ├── main.py                        ← FastAPI app entry point
│   ├── Procfile                       ← Railway start command
│   ├── railway.toml                   ← Railway deploy config
│   ├── runtime.txt                    ← Python version for Railway
│   ├── requirements.txt                ← Python dependencies
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── orchestrator.py            ← Master agent, spawns sub-agents
│   │   ├── hygiene_agent.py           ← NEA + SFA data, grade matching
│   │   ├── location_agent.py          ← OneMap, Google Places, crowd timing
│   │   └── recommendation_agent.py    ← RAG + 6-signal scoring
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── nea_client.py              ← data.gov.sg API wrapper
│   │   ├── places_client.py           ← Google Places API wrapper
│   │   ├── onemap_client.py           ← OneMap geocoding
│   │   └── weather_client.py          ← OpenWeatherMap wrapper
│   │
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── vector_store.py            ← ChromaDB interface
│   │   └── seed.py                    ← 71 stall profiles for seeding
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py                 ← Pydantic models / dataclasses
│   │
│   ├── data/
│   │   ├── michelin_2025.json         ← 89 Michelin stalls
│   │   ├── halal_stalls.json          ← MUIS halal list
│   │   ├── hygiene_grades_full.json   ← SFA fallback grades
│   │   └── seed/                      ← Seed data markdown files
│   │
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_hygiene_agent.py
│   │   ├── test_location_agent.py
│   │   ├── test_recommendation_agent.py
│   │   ├── test_orchestrator.py
│   │   ├── test_nea_client.py
│   │   ├── test_places_client.py
│   │   ├── test_sse_endpoint.py
│   │   └── test_vector_store.py
│   │
│   └── chroma_db/                     ← ChromaDB persistent storage (gitignored)
│
└── frontend/
    ├── package.json
    ├── vite.config.ts                 ← Build config with bundle splitting
    ├── tsconfig.json
    ├── tailwind.config.ts             ← Design tokens, dark mode
    ├── vercel.json                    ← Vercel deploy config
    ├── .env.production                ← Production API URL
    ├── index.html
    │
    ├── src/
    │   ├── main.tsx                   ← React entry point
    │   ├── App.tsx                    ← Main layout, state management
    │   │
    │   ├── components/
    │   │   ├── SearchBar.tsx          ← Query input + geolocation
    │   │   ├── AgentPanel.tsx         ← Live reasoning trace, typewriter effect
    │   │   ├── ResultsList.tsx        ← Infinite scroll, "X of Y" counter
    │   │   ├── ResultCard.tsx         ← Stall card with all badges
    │   │   ├── StatusBadge.tsx        ← Hygiene / Michelin / halal / open
    │   │   ├── ErrorBoundary.tsx      ← Error catch + retry
    │   │   └── ThemeToggle.tsx        ← Light / dark mode switch
    │   │
    │   ├── hooks/
    │   │   ├── useSSE.ts              ← Server-Sent Events stream parser
    │   │   └── useGeolocation.ts      ← Browser GPS consent + fetch
    │   │
    │   ├── lib/
    │   │   ├── api.ts                 ← Backend API client
    │   │   └── utils.ts               ← Utilities (cn = clsx + tailwind-merge)
    │   │
    │   ├── context/
    │   │   └── ThemeContext.tsx       ← Dark/light mode state
    │   │
    │   └── types/
    │       └── index.ts               ← Shared TypeScript types
    │
    └── dist/                          ← Production build (generated by `npm run build`)
```

---

## API Endpoints

### `POST /api/search`
Submit a query and receive a streaming response of agent reasoning.

**Request:**
```json
{
  "query": "good laksa near Toa Payoh, vegetarian, 1pm",
  "lat": 1.3521,
  "lng": 103.8198
}
```

**Response (Server-Sent Events):**
```
event: agent_update
data: {"type":"agent_update","agent":"orchestrator","message":"Parsing query...","data":{...}}

event: agent_update
data: {"type":"agent_update","agent":"location","message":"Found 6 centres...","data":{...}}

event: result
data: {"type":"result","recommendations":[...]}
```

### `GET /api/health`
Health check endpoint. Returns agent and data source status.

**Response:**
```json
{
  "status": "ok",
  "orchestrator": "ready",
  "agents": ["orchestrator", "hygiene", "location", "recommendation"],
  "data_sources": ["nea", "google_places", "onemap", "openweather", "chromadb"]
}
```

---

## Deployment

### Backend → Railway

1. Set up a Railway project at [railway.app](https://railway.app)
2. Connect your GitHub repo
3. Set root directory to `backend/`
4. Add environment variables:
   - `ANTHROPIC_API_KEY`
   - `GOOGLE_PLACES_API_KEY`
   - `OPENWEATHER_API_KEY`
   - `DATAGOV_API_KEY`
   - `ENVIRONMENT=production`
5. Deploy — Railway will auto-detect `railway.toml` and start the app

### Frontend → Vercel

1. Set up a Vercel project at [vercel.com](https://vercel.com)
2. Connect your GitHub repo
3. Set root directory to `frontend/`
4. Set build command to `npm run build`
5. Set output directory to `dist`
6. Add environment variable: `VITE_API_URL=https://your-railway-app.railway.app`
7. Deploy

---

## Testing

Run the full test suite:

```bash
cd backend
pytest tests/ -v
```

Expected output:
```
96 passed in 14.38s
```

Tests cover:
- **Agents:** query parsing, sub-agent execution, result ranking
- **Tools:** API client mocks, error handling, data transformation
- **RAG:** vector store operations, semantic search, metadata handling
- **SSE:** event streaming, error propagation, HTTP response format
- **Integration:** end-to-end orchestrator flow with mocked external APIs

---

## Known Limitations

1. **Hygiene grades are fallback-only** — SFA does not expose stall-level grades via public API. We seed a static JSON file from a one-time scrape. Real-time grade updates require manual re-scraping.

2. **ChromaDB on Railway is ephemeral** — Railway's filesystem resets on every deploy. ChromaDB is re-seeded on app startup if empty (see `main.py` lifespan).

3. **Google Places reviews cap** — We fetch max 5 reviews per stall to keep API quota usage reasonable. Full sentiment analysis would require more quota.

4. **Geolocation opt-in** — Browser requires user permission to access GPS. Fallback: user enters location as text (OneMap geocodes it).

---

## Contributing

This is a reference implementation of multi-agent AI reasoning on Hawker Hunt data. To extend:

1. **Add a new agent:** Create `backend/agents/new_agent.py`, add to orchestrator spawn list
2. **Add a data source:** Create `backend/tools/new_client.py`, wrap API calls, add to agent
3. **Expand RAG:** Add more stall profiles to `backend/rag/seed.py`, re-seed ChromaDB
4. **Improve UI:** Modify React components in `frontend/src/components/`, test with `npm run dev`

---

## License

Business Source License 1.1 — See LICENSE file.

---

## Acknowledgments

Built as an AI engineering showcase on Anthropic Claude API.
Data sourced from official Singapore government APIs (NEA, OneMap, data.gov.sg).
Michelin Bib Gourmand 2025 stalls verified from official list.
