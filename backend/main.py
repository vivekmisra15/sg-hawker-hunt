"""
Hawker Hunt — FastAPI backend entry point.
Run: uvicorn main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="Hawker Hunt API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:5173")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "agents": ["orchestrator", "hygiene", "location", "recommendation"],
        "data_sources": ["nea", "google_places", "onemap", "openweather", "chromadb"],
    }


# TODO Milestone 1: import and mount agent router
# TODO Milestone 3: mount SSE search endpoint
