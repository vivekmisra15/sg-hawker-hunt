"""
RecommendationAgent — RAG-based stall ranking with hygiene, Michelin, and halal signals.
Single responsibility: query + location + hygiene → list[RankedRecommendation] (top 3).

Scoring weights:
  Hygiene Grade A: +3  |  B: +2  |  C: +1  |  UNKNOWN/D: 0
  Michelin flag:   +3
  is_open:         +2
  Crowd quiet:     +1
  RAG relevance:   up to +2  (2 * (1 - cosine_distance), capped 0–2)
  Google rating:   +2 (≥4.5) | +1 (≥4.0) | -1 (<3.5)
  Review count:    +1 (≥200 reviews)
  LLM sentiment:   -1.0 to +1.0 (claude-haiku-4-5)
  Hygiene concern: -0.5 (review-flagged)
  Time-aware:      ±1 (best_time / avoid_time vs current SGT hour)
  Demerit nuance:  +0.5 (0 demerits) | -0.5 (≥12 demerits), when grade known
  Price match:     ±1 (budget preference vs stall price_range)
"""
import asyncio
import hashlib
import json
import logging
import os
import re
import time
from datetime import datetime
from typing import Optional

import anthropic
import pytz

from models.schemas import LocationResult, HygieneResult, RankedRecommendation, SentimentResult
from rag.vector_store import VectorStore

logger = logging.getLogger(__name__)

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

_GRADE_SCORES = {"A": 3, "B": 2, "C": 1, "D": 0, "UNKNOWN": 0, "": 0}
_DIETARY_REQUIRES_HALAL = {"halal", "muslim"}
_DIETARY_REQUIRES_VEGETARIAN = {"vegetarian", "vegan", "veggie"}

_SENTIMENT_CACHE: dict[str, tuple[SentimentResult, float]] = {}
_SENTIMENT_CACHE_TTL = 86400  # 24 hours

_SENTIMENT_SYSTEM = """You are a food review analyst for Singapore hawker stalls.
Analyse the provided reviews and return ONLY valid JSON with these keys:
  sentiment_score: float from -1.0 (very negative) to 1.0 (very positive)
  hygiene_concerns: true if reviews mention dirty, unclean, cockroach, pest, or similar, else false
  queue_signal: "short" if queues mentioned as quick or short waits, "long" if long waits or crowds, else "unknown"
  standout_quote: the single most useful sentence for a potential customer, or ""
No markdown, no explanation — just the JSON object."""

_SGT = pytz.timezone("Asia/Singapore")


def _load_json_list(path: str) -> list[str]:
    try:
        with open(path) as f:
            return [s.upper() for s in json.load(f)]
    except Exception:
        return []


def _parse_time_range(s: str) -> list[tuple[int, int]]:
    """Parse a free-text time string into a list of (start_hour_24, end_hour_24) tuples."""
    if not s:
        return []
    s_lower = s.lower()

    # Normalise am/pm tokens to 24h integers
    def to_24h(hour: int, meridiem: str) -> int:
        if meridiem == "pm" and hour != 12:
            return hour + 12
        if meridiem == "am" and hour == 12:
            return 0
        return hour

    # Named periods
    if "early morning" in s_lower:
        return [(6, 10)]
    if "late night" in s_lower or "after midnight" in s_lower:
        return [(22, 24)]

    results: list[tuple[int, int]] = []

    # Pattern: "12pm-2pm", "11:30am-1pm", "6pm-8pm"
    range_re = re.compile(
        r"(\d{1,2})(?::\d{2})?\s*(am|pm)\s*[-–to]+\s*(\d{1,2})(?::\d{2})?\s*(am|pm)",
        re.IGNORECASE,
    )
    for m in range_re.finditer(s_lower):
        start = to_24h(int(m.group(1)), m.group(2))
        end = to_24h(int(m.group(3)), m.group(4))
        if end > start:
            results.append((start, end))

    # Pattern: "before 11:30am" → (0, 11), "after 2pm" → (14, 24)
    before_re = re.compile(r"before\s+(\d{1,2})(?::\d{2})?\s*(am|pm)", re.IGNORECASE)
    after_re = re.compile(r"after\s+(\d{1,2})(?::\d{2})?\s*(am|pm)", re.IGNORECASE)
    for m in before_re.finditer(s_lower):
        end = to_24h(int(m.group(1)), m.group(2))
        results.append((0, end))
    for m in after_re.finditer(s_lower):
        start = to_24h(int(m.group(1)), m.group(2))
        results.append((start, 24))

    return results


def _parse_price_upper(price_range_str: str) -> Optional[float]:
    """Extract the upper price bound from a string like 'S$5-7' or '$3-5'."""
    m = re.search(r"[\$S]+\d+[-–](\d+)", price_range_str)
    if m:
        return float(m.group(1))
    # Single price like "S$5"
    m2 = re.search(r"[\$S]+(\d+)", price_range_str)
    if m2:
        return float(m2.group(1))
    return None


_NEUTRAL_SENTIMENT = SentimentResult()


class RecommendationAgent:
    def __init__(
        self,
        vector_store: VectorStore | None = None,
        anthropic_client: anthropic.AsyncAnthropic | None = None,
    ):
        self._vs = vector_store or VectorStore()
        self._anthropic = anthropic_client or anthropic.AsyncAnthropic()

    async def run(
        self,
        query: str,
        location_results: list[LocationResult],
        hygiene_results: list[HygieneResult],
        preferences: dict,
    ) -> list[RankedRecommendation]:
        """
        Return up to 3 ranked recommendations.
        preferences keys: cuisine_type, dietary (list[str]), avoid (list[str]), budget (str)
        """
        michelin_names = _load_json_list(os.path.join(_DATA_DIR, "michelin_2025.json"))
        halal_names = _load_json_list(os.path.join(_DATA_DIR, "halal_stalls.json"))

        rag_results = self._vs.query(query, n_results=10)

        # Build lookup maps
        loc_map: dict[str, LocationResult] = {r.centre_name.upper(): r for r in location_results}
        hygiene_map: dict[str, HygieneResult] = {r.centre_name.upper(): r for r in hygiene_results}

        # Signal 2: run sentiment analysis in parallel for all centres with reviews
        sentiment_map = await self._build_sentiment_map(location_results)

        dietary = [d.lower() for d in preferences.get("dietary", [])]
        requires_halal = any(d in _DIETARY_REQUIRES_HALAL for d in dietary)
        requires_vegetarian = any(d in _DIETARY_REQUIRES_VEGETARIAN for d in dietary)
        budget = preferences.get("budget", "any")

        current_hour = datetime.now(_SGT).hour

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

            # Signal 6: hard filter — exclude suspended stalls
            if hygiene and hygiene.suspended:
                continue

            is_open = loc.is_open if loc else True
            distance_km = loc.distance_km if loc else 99.0
            crowd_level = loc.crowd_level if loc else "unknown"
            google_rating = loc.google_rating if loc else None
            review_count = loc.review_count if loc else None
            grade = hygiene.grade if hygiene else "UNKNOWN"
            demerit_points = hygiene.demerit_points if hygiene else 0

            # ── Scoring ───────────────────────────────────────────────────────
            score = 0.0

            # Base signals (pre-M4)
            score += _GRADE_SCORES.get(grade.upper(), 0)
            if is_michelin:
                score += 3
            if is_open:
                score += 2
            if crowd_level == "quiet":
                score += 1
            rag_relevance = max(0.0, min(2.0, 2.0 * (1.0 - rag["distance"])))
            score += rag_relevance

            # Signal 1: Google rating
            if google_rating is not None:
                if google_rating >= 4.5:
                    score += 2
                elif google_rating >= 4.0:
                    score += 1
                elif google_rating < 3.5:
                    score -= 1
            if review_count is not None and review_count >= 200:
                score += 1  # high-confidence signal

            # Signal 2: LLM sentiment
            sentiment = sentiment_map.get(centre_name.upper(), _NEUTRAL_SENTIMENT)
            score += max(-1.0, min(1.0, sentiment.sentiment_score))
            if sentiment.hygiene_concerns:
                score -= 0.5

            # Signal 3: time-aware
            best_ranges = _parse_time_range(meta.get("best_time", ""))
            avoid_ranges = _parse_time_range(meta.get("avoid_time", ""))
            if any(s <= current_hour < e for s, e in best_ranges):
                score += 1
            elif any(s <= current_hour < e for s, e in avoid_ranges):
                score -= 1

            # Signal 4: demerit nuance (only when grade is known)
            if grade not in ("UNKNOWN", ""):
                if demerit_points == 0:
                    score += 0.5
                elif demerit_points >= 12:
                    score -= 0.5

            # Signal 5: price range preference
            price_upper = _parse_price_upper(meta.get("price_range", ""))
            if budget == "cheap" and price_upper is not None:
                if price_upper <= 6:
                    score += 1
                elif price_upper > 12:
                    score -= 1
            elif budget == "moderate" and price_upper is not None:
                if 6 < price_upper <= 12:
                    score += 0.5

            # ── Reasoning string ──────────────────────────────────────────────
            michelin_note = " Michelin Bib Gourmand 2025." if is_michelin else ""
            halal_note = " Halal certified." if is_halal else ""
            open_note = "Currently open." if is_open else "Currently closed."
            crowd_note = (
                f"{'Busy' if crowd_level == 'busy' else 'Quiet'} period — "
                f"{'expect queues' if crowd_level == 'busy' else 'good time to visit'}."
            )
            dist_note = f"{distance_km:.1f}km from you." if distance_km < 99 else ""

            rating_note = ""
            if google_rating is not None:
                count_part = f" ({review_count} reviews)" if review_count else ""
                rating_note = f" Rated {google_rating}/5{count_part}."

            hygiene_concern_note = " ⚠️ Hygiene concerns mentioned in reviews." if sentiment.hygiene_concerns else ""

            quote_note = f' "{sentiment.standout_quote}"' if sentiment.standout_quote else ""

            reasoning = (
                f"{stall_name} at {centre_name}."
                f" Grade {grade} hygiene.{michelin_note}{halal_note}"
                f"{rating_note}"
                f" {open_note} {dist_note} {crowd_note}"
                f"{hygiene_concern_note}{quote_note}"
            ).strip()

            candidates.append(
                RankedRecommendation(
                    stall_name=stall_name,
                    centre_name=centre_name,
                    rank=0,
                    reasoning=reasoning,
                    hygiene_grade=grade,
                    is_michelin=is_michelin,
                    is_halal=is_halal,
                    is_open=is_open,
                    distance_km=distance_km,
                    google_rating=google_rating,
                    standout_quote=sentiment.standout_quote or None,
                    score=round(score, 3),
                )
            )

        candidates.sort(key=lambda c: c.score, reverse=True)
        top3 = candidates[:3]
        for i, rec in enumerate(top3, start=1):
            rec.rank = i
        return top3

    async def _build_sentiment_map(
        self, location_results: list[LocationResult]
    ) -> dict[str, SentimentResult]:
        """Run sentiment analysis in parallel for all centres with non-empty reviews."""
        tasks = {}
        for loc in location_results:
            if loc.reviews_summary and loc.reviews_summary.strip():
                tasks[loc.centre_name.upper()] = asyncio.create_task(
                    self._analyse_sentiment(loc.reviews_summary)
                )
        if not tasks:
            return {}
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        sentiment_map: dict[str, SentimentResult] = {}
        for centre_key, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                logger.warning("Sentiment analysis failed for %s: %s", centre_key, result)
                sentiment_map[centre_key] = _NEUTRAL_SENTIMENT
            else:
                sentiment_map[centre_key] = result
        return sentiment_map

    async def _analyse_sentiment(self, reviews_summary: str) -> SentimentResult:
        """Call claude-haiku-4-5 to extract sentiment from review text. Cached 24h."""
        cache_key = hashlib.sha256(reviews_summary[:500].encode()).hexdigest()
        cached = _SENTIMENT_CACHE.get(cache_key)
        if cached is not None:
            result, ts = cached
            if time.time() - ts < _SENTIMENT_CACHE_TTL:
                return result

        try:
            response = await self._anthropic.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=200,
                system=_SENTIMENT_SYSTEM,
                messages=[{"role": "user", "content": reviews_summary[:2000]}],
            )
            raw = response.content[0].text.strip()
            if not raw:
                logger.debug("Empty Haiku response for sentiment — using neutral")
                result = _NEUTRAL_SENTIMENT
            else:
                data = json.loads(raw)
                result = SentimentResult(
                    sentiment_score=float(data.get("sentiment_score", 0.0)),
                    hygiene_concerns=bool(data.get("hygiene_concerns", False)),
                    queue_signal=str(data.get("queue_signal", "unknown")),
                    standout_quote=str(data.get("standout_quote", "")),
                )
        except json.JSONDecodeError as e:
            logger.debug("Sentiment JSON parse failed (%s) — using neutral", e)
            result = _NEUTRAL_SENTIMENT
        except Exception as e:
            logger.warning("Sentiment analysis error: %s", e)
            result = _NEUTRAL_SENTIMENT

        _SENTIMENT_CACHE[cache_key] = (result, time.time())
        return result
