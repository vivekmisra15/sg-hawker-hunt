"""
RecommendationAgent — RAG-based stall ranking with hygiene, Michelin, and halal signals.
Single responsibility: query + location + hygiene → list[RankedRecommendation] (top 3).

Scoring weights:
  Hygiene Grade A: +3  |  B: +2  |  C: +1  |  UNKNOWN/D: 0
  Michelin flag:   +3
  is_open:         +2
  Crowd quiet:     +1
  RAG relevance:   up to +2  (2 * (1 - cosine_distance), capped 0–2)
"""
import json
import logging
import os

from models.schemas import LocationResult, HygieneResult, RankedRecommendation
from rag.vector_store import VectorStore

logger = logging.getLogger(__name__)

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

_GRADE_SCORES = {"A": 3, "B": 2, "C": 1, "D": 0, "UNKNOWN": 0, "": 0}
_DIETARY_REQUIRES_HALAL = {"halal", "muslim"}
_DIETARY_REQUIRES_VEGETARIAN = {"vegetarian", "vegan", "veggie"}


def _load_json_list(path: str) -> list[str]:
    try:
        with open(path) as f:
            return [s.upper() for s in json.load(f)]
    except Exception:
        return []


class RecommendationAgent:
    def __init__(self, vector_store: VectorStore | None = None):
        self._vs = vector_store or VectorStore()

    async def run(
        self,
        query: str,
        location_results: list[LocationResult],
        hygiene_results: list[HygieneResult],
        preferences: dict,
    ) -> list[RankedRecommendation]:
        """
        Return up to 3 ranked recommendations.
        preferences keys: cuisine, dietary (list[str]), avoid (list[str])
        """
        michelin_names = _load_json_list(
            os.path.join(_DATA_DIR, "michelin_2025.json")
        )
        halal_names = _load_json_list(
            os.path.join(_DATA_DIR, "halal_stalls.json")
        )

        rag_results = self._vs.query(query, n_results=10)

        # Build lookup maps for quick cross-referencing
        loc_map: dict[str, LocationResult] = {
            r.centre_name.upper(): r for r in location_results
        }
        hygiene_map: dict[str, HygieneResult] = {
            r.centre_name.upper(): r for r in hygiene_results
        }

        dietary = [d.lower() for d in preferences.get("dietary", [])]
        requires_halal = any(d in _DIETARY_REQUIRES_HALAL for d in dietary)
        requires_vegetarian = any(d in _DIETARY_REQUIRES_VEGETARIAN for d in dietary)

        candidates = []
        for rag in rag_results:
            meta = rag.get("metadata", {})
            stall_name = meta.get("stall_name", "Unknown Stall")
            centre_name = meta.get("centre_name", "Unknown Centre")
            is_michelin = str(meta.get("is_michelin", "False")).lower() == "true"
            is_halal = str(meta.get("is_halal", "False")).lower() == "true"

            # Dietary filter
            if requires_halal and not is_halal:
                continue
            if requires_vegetarian:
                cuisine = meta.get("cuisine", "").lower()
                tags = meta.get("tags", "").lower()
                if not any(v in cuisine + tags for v in ("vegetarian", "vegan", "carrot cake", "rojak")):
                    continue

            # Cross-reference location and hygiene
            loc = loc_map.get(centre_name.upper())
            hygiene = hygiene_map.get(centre_name.upper())

            is_open = loc.is_open if loc else True
            distance_km = loc.distance_km if loc else 99.0
            crowd_level = loc.crowd_level if loc else "unknown"
            google_rating = loc.google_rating if loc else None
            grade = hygiene.grade if hygiene else "UNKNOWN"

            # Scoring
            score = 0.0
            score += _GRADE_SCORES.get(grade.upper(), 0)
            if is_michelin:
                score += 3
            if is_open:
                score += 2
            if crowd_level == "quiet":
                score += 1
            rag_relevance = max(0.0, min(2.0, 2.0 * (1.0 - rag["distance"])))
            score += rag_relevance

            # Build reasoning string
            michelin_note = " Michelin Bib Gourmand 2025." if is_michelin else ""
            halal_note = " Halal certified." if is_halal else ""
            open_note = "Currently open." if is_open else "Currently closed."
            crowd_note = f"{'Busy' if crowd_level == 'busy' else 'Quiet'} period — {'expect queues' if crowd_level == 'busy' else 'good time to visit'}."
            dist_note = f"{distance_km:.1f}km from you." if distance_km < 99 else ""
            reasoning = (
                f"{stall_name} at {centre_name}."
                f" Grade {grade} hygiene.{michelin_note}{halal_note}"
                f" {open_note} {dist_note} {crowd_note}"
            ).strip()

            candidates.append(
                RankedRecommendation(
                    stall_name=stall_name,
                    centre_name=centre_name,
                    rank=0,  # assigned after sort
                    reasoning=reasoning,
                    hygiene_grade=grade,
                    is_michelin=is_michelin,
                    is_halal=is_halal,
                    is_open=is_open,
                    distance_km=distance_km,
                    google_rating=google_rating,
                    score=round(score, 3),
                )
            )

        candidates.sort(key=lambda c: c.score, reverse=True)
        top3 = candidates[:3]
        for i, rec in enumerate(top3, start=1):
            rec.rank = i
        return top3
