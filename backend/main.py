"""
Hawker Hunt — FastAPI backend entry point.
Run: uvicorn main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

from sse_starlette.sse import EventSourceResponse
from agents.orchestrator import OrchestratorAgent
from models.schemas import SearchRequest

app = FastAPI(title="Hawker Hunt API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:5173")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = OrchestratorAgent()


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "agents": ["orchestrator", "hygiene", "location", "recommendation"],
        "data_sources": ["nea", "google_places", "onemap", "openweather", "chromadb"],
    }


@app.post("/api/search")
async def search(request: SearchRequest):
    async def event_generator():
        async for event in orchestrator.run(request):
            yield {
                "event": event.type,
                "data": event.model_dump_json(),
            }
    return EventSourceResponse(event_generator())
