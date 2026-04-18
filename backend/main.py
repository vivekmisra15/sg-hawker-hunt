"""
Hawker Hunt — FastAPI backend entry point.
Run: uvicorn main:app --reload
"""
import json
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from sse_starlette.sse import EventSourceResponse
from agents.orchestrator import OrchestratorAgent
from models.schemas import SearchRequest

app = FastAPI(title="Hawker Hunt API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("FRONTEND_URL", "http://localhost:5173"),
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
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
