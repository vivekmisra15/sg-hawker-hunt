"""
Hawker Hunt — FastAPI backend entry point.
Run: uvicorn main:app --reload
"""
import json
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from sse_starlette.sse import EventSourceResponse
from agents.orchestrator import OrchestratorAgent
from models.schemas import SearchRequest
from rag.vector_store import VectorStore
from rag.seed import seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: check ChromaDB status. Shutdown: cleanup if needed."""
    # Startup
    environment = os.getenv("ENVIRONMENT", "development")
    vs = VectorStore()
    size = vs.collection_size()

    if size == 0:
        if environment == "production":
            print("WARNING: ChromaDB empty on production — seeding disabled to prevent startup timeout.")
            print("To seed, run: python3 -m rag.seed locally, then redeploy.")
        else:
            print("ChromaDB empty — seeding knowledge base...")
            seed()
            new_size = vs.collection_size()
            print(f"Seeded {new_size} documents into ChromaDB")
    else:
        print(f"ChromaDB ready — {size} documents")

    yield
    # Shutdown
    pass


app = FastAPI(title="Hawker Hunt API", version="0.1.0", lifespan=lifespan)

# CORS configuration: allow dev and production frontend URLs
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
cors_origins_raw = os.getenv("BACKEND_CORS_ORIGINS", "")
extra_origins = [o.strip() for o in cors_origins_raw.split(",") if o.strip()]

allow_origins = list(set([
    frontend_url,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
] + extra_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = OrchestratorAgent()


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "orchestrator": "ready",
        "agents": ["orchestrator", "hygiene", "location", "recommendation"],
        "data_sources": ["nea", "google_places", "onemap", "openweather", "chromadb"],
    }


@app.post("/api/search")
async def search(request: SearchRequest):
    async def event_generator():
        try:
            async for event in orchestrator.run(request):
                yield {
                    "event": event.type,
                    "data": event.model_dump_json(),
                }
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"message": str(e)}),
            }

    return EventSourceResponse(
        event_generator(),
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
