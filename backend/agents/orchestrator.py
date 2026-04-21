"""
OrchestratorAgent — coordinates all sub-agents and yields a streaming AgentEvent trace.
This is the entry point for every user search request.
"""
import asyncio
import json
import logging
from typing import AsyncGenerator

import anthropic

from agents.hygiene_agent import HygieneAgent
from agents.location_agent import LocationAgent
from agents.recommendation_agent import RecommendationAgent
from models.schemas import AgentEvent, SearchRequest
from tools.onemap_client import OneMapClient

logger = logging.getLogger(__name__)

_DEFAULT_LAT = 1.3521  # Singapore geographic centre
_DEFAULT_LNG = 103.8198

_PARSE_SYSTEM = """You are a query parser for a Singapore hawker food search app.
Extract from the user's query and return ONLY valid JSON with these keys:
  cuisine_type: string (e.g. "chicken rice", "laksa", "" if not specified)
  location_hint: string (a place name or area, "" if not specified)
  dietary: list of strings (e.g. ["halal", "vegetarian"], [] if none)
  avoid: list of strings (things the user wants to avoid, [] if none)
  budget: "cheap" if query contains budget/cheap/affordable/value/economical keywords,
          "moderate" if query contains splurge/premium/expensive keywords,
          "any" otherwise
  time_context: "breakfast" if query mentions morning/breakfast/before 10am/kopi/toast,
                "lunch" if query mentions lunch/midday/noon/1pm/after work,
                "dinner" if query mentions dinner/evening/tonight/7pm,
                "supper" if query mentions supper/late night/after 10pm/midnight,
                "any" otherwise
No markdown, no explanation — just the JSON object."""


class OrchestratorAgent:
    def __init__(
        self,
        location_agent: LocationAgent | None = None,
        hygiene_agent: HygieneAgent | None = None,
        recommendation_agent: RecommendationAgent | None = None,
        anthropic_client: anthropic.AsyncAnthropic | None = None,
    ):
        self._location = location_agent or LocationAgent()
        self._hygiene = hygiene_agent or HygieneAgent()
        self._recommendation = recommendation_agent or RecommendationAgent()
        self._anthropic = anthropic_client or anthropic.AsyncAnthropic()

    async def run(self, request: SearchRequest) -> AsyncGenerator[AgentEvent, None]:
        try:
            async for event in self._run(request):
                yield event
        except Exception as e:
            logger.exception("Orchestrator unhandled error")
            yield AgentEvent(type="error", agent="orchestrator", message=str(e))

    async def _run(self, request: SearchRequest) -> AsyncGenerator[AgentEvent, None]:
        # ── Step 1: Parse query with Claude ──────────────────────────────────
        preferences = await self._parse_query(request.query)
        cuisine = preferences.get("cuisine_type", "")
        dietary = preferences.get("dietary", [])
        location_hint = preferences.get("location_hint", "")

        yield AgentEvent(
            type="agent_update",
            agent="orchestrator",
            message=(
                f"Parsed query — cuisine: {cuisine or 'any'}, "
                f"dietary: {dietary or 'none'}, "
                f"location hint: {location_hint or 'none'}"
            ),
        )

        # ── Step 2: Resolve coordinates ───────────────────────────────────────
        lat, lng, address = await self._resolve_location(request, location_hint)

        yield AgentEvent(
            type="agent_update",
            agent="orchestrator",
            message=f"Location resolved: {address or f'({lat:.4f}, {lng:.4f})'}",
        )

        # ── Step 3: LocationAgent first (need centre names for hygiene) ───────
        try:
            location_results = await self._location.run(lat, lng)
        except ValueError as e:
            yield AgentEvent(type="error", agent="location", message=str(e))
            return

        yield AgentEvent(
            type="agent_update",
            agent="location",
            message=f"Found {len(location_results)} centres within 1.5km",
        )

        centre_names = [r.centre_name for r in location_results]

        # ── Step 4: HygieneAgent + RAG query in parallel ──────────────────────
        hygiene_task = asyncio.create_task(self._hygiene.run(centre_names))
        # RAG query happens inside RecommendationAgent.run — no separate parallel call needed
        hygiene_results = await hygiene_task

        yield AgentEvent(
            type="agent_update",
            agent="hygiene",
            message=f"Retrieved hygiene data for {len(hygiene_results)} centres",
        )

        # ── Step 5: RecommendationAgent ───────────────────────────────────────
        recommendations = await self._recommendation.run(
            query=request.query,
            location_results=location_results,
            hygiene_results=hygiene_results,
            preferences=preferences,
        )

        yield AgentEvent(
            type="agent_update",
            agent="recommendation",
            message=f"Ranked {len(recommendations)} stalls",
        )

        # ── Step 6: Final result ──────────────────────────────────────────────
        yield AgentEvent(
            type="result",
            agent="orchestrator",
            message="Recommendation complete",
            data={"recommendations": [r.model_dump() for r in recommendations]},
        )

    async def _parse_query(self, query: str) -> dict:
        """Use Claude to extract structured preferences from free-text query."""
        try:
            response = await self._anthropic.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=256,
                system=_PARSE_SYSTEM,
                messages=[{"role": "user", "content": query}],
            )
            raw = response.content[0].text.strip()
            return json.loads(raw)
        except Exception as e:
            logger.warning("Query parse failed (%s) — using defaults", e)
            return {"cuisine_type": "", "location_hint": "", "dietary": [], "avoid": [], "budget": "any", "time_context": "any"}

    async def _resolve_location(
        self, request: SearchRequest, location_hint: str
    ) -> tuple[float, float, str]:
        """Return (lat, lng, address_label) from request coords, hint, or default."""
        if request.lat is not None and request.lng is not None:
            return request.lat, request.lng, "coordinates provided"

        if location_hint:
            try:
                onemap = OneMapClient()
                lat, lng, address = await onemap.geocode(location_hint)
                return lat, lng, address
            except Exception as e:
                logger.warning("Geocode for %r failed: %s — using default", location_hint, e)

        return _DEFAULT_LAT, _DEFAULT_LNG, "Singapore (default)"
