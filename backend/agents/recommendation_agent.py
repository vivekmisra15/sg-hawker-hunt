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
  LLM sentiment:   -1.0 to +1.0 (claude-haiku-4-5, Singlish-aware)
  Hygiene concern: -0.5 (review-flagged)
  Time-aware:      ±1 seeded metadata | ±0.5 peak_time_hint/time_context | ±0.5 cuisine priors
  Demerit nuance:  +0.5 (0 demerits) | -0.5 (≥12 demerits), when grade known
  Price match:     ±1 seeded metadata | ±0.5 Places priceLevel | ±0.5 review price_signal
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

# Google Places priceLevel → proxy upper price bound (SGD)
_PRICE_LEVEL_MAP: dict[str, float] = {
    "PRICE_LEVEL_FREE": 2.0,
    "PRICE_LEVEL_INEXPENSIVE": 5.0,
    "PRICE_LEVEL_MODERATE": 12.0,
    "PRICE_LEVEL_EXPENSIVE": 25.0,
    "PRICE_LEVEL_VERY_EXPENSIVE": 50.0,
}

# Haiku price_signal → proxy upper price bound (SGD)
_PRICE_SIGNAL_MAP: dict[str, float] = {
    "cheap": 5.0,
    "moderate": 12.0,
    "expensive": 25.0,
}

# Cuisine keywords that strongly indicate a meal-time slot
_TIME_CUISINE_MAP: dict[str, set[str]] = {
    "breakfast": {"kaya toast", "toast", "congee", "porridge", "dim sum", "you tiao",
                  "teh tarik", "kopi", "nasi lemak", "roti prata", "bak chor mee"},
    "supper": {"bak kut teh", "frog porridge", "bbq stingray", "oyster omelette",
               "wonton soup", "bak chor mee", "satay"},
    "lunch": {"chicken rice", "char kway teow", "laksa", "duck rice", "wonton mee",
              "nasi padang", "economy rice", "mixed rice"},
    "dinner": {"char kway teow", "bbq", "satay", "steamboat", "seafood",
               "fish head curry", "crab"},
}

_SENTIMENT_SYSTEM = """You are a food review analyst specialising in Singapore hawker stalls.
Reviews may be written in English, Singlish, Malay, or a mix. Interpret local expressions correctly:

Positive signals: "shiok", "ho jiak" (Hokkien: delicious), "sedap" (Malay: delicious),
  "confirm plus chop" (definitely good), "die die must try" (must-try), "power", "steady",
  "solid", "not bad leh", "damn good", "wah so nice", "best in Singapore", "legit".

Negative signals: "jialat" (terrible), "lousy", "not worth it", "stale", "terrible",
  "horrible", "overrated", "disappointing", "yucks".

Queue interpretation: A long queue at a Singapore hawker stall is a POSITIVE quality signal —
  it means the food is well-regarded. Do NOT treat "queue very long" or "always packed" as
  a negative sentiment. Set queue_signal to "long" and keep sentiment_score positive.

Terse reviews: Short reviews like "good", "nice", "ok lah", "steady", "not bad" are
  genuinely positive in Singapore review culture — score them at least +0.3.

Sentence-final particles "lah", "lor", "leh", "sia", "meh", "wah", "boh" carry tone,
  not literal negative meaning. "Not bad lah" = positive. "Ok lor" = mildly positive.

Return ONLY valid JSON with these keys:
  sentiment_score: float from -1.0 (very negative) to 1.0 (very positive)
  hygiene_concerns: true if reviews mention dirty, unclean, cockroach, pest, or "not clean", else false
  queue_signal: "short" if queues quick/short, "long" if long waits or packed, else "unknown"
  standout_quote: the single most useful sentence for a potential customer (preserve original language), or ""
  peak_time_hint: "breakfast" | "lunch" | "dinner" | "supper" if reviews suggest a best time to visit, else "unknown"
  price_signal: "cheap" if reviews mention low prices/value/affordable, "expensive" if pricey/overpriced, "moderate" if mid-range, else "unknown"
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

    def to_24h(hour: int, meridiem: str) -> int:
        if meridiem == "pm" and hour != 12:
            return hour + 12
        if meridiem == "am" and hour == 12:
            return 0
        return hour

    if "early morning" in s_lower:
        return [(6, 10)]
    if "late night" in s_lower or "after midnight" in s_lower:
        return [(22, 24)]

    results: list[tuple[int, int]] = []

    range_re = re.compile(
        r"(\d{1,2})(?::\d{2})?\s*(am|pm)\s*[-–to]+\s*(\d{1,2})(?::\d{2})?\s*(am|pm)",
        re.IGNORECASE,
    )
    for m in range_re.finditer(s_lower):
        start = to_24h(int(m.group(1)), m.group(2))
        end = to_24h(int(m.group(3)), m.group(4))
        if end > start:
            results.append((start, end))

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
    m2 = re.search(r"[\$S]+(\d+)", price_range_str)
    if m2:
        return float(m2.group(1))
    return None


def _price_upper_from_level(price_level: Optional[str]) -> Optional[float]:
    """Convert a Google Places priceLevel enum string to an upper price bound."""
    if not price_level:
        return None
    return _PRICE_LEVEL_MAP.get(price_level)


def _cuisine_time_score(cuisine_combined: str, time_context: str) -> float:
    """Score ±0.5 based on whether the stall's cuisine fits the user's time intent."""
    if time_context == "any":
        return 0.0
    match_cuisines = _TIME_CUISINE_MAP.get(time_context, set())
    # Opposite meal slots (breakfast vs supper are inversely correlated)
    opposite = {"breakfast": "supper", "supper": "breakfast", "lunch": "", "dinner": ""}.get(time_context, "")
    opposite_cuisines = _TIME_CUISINE_MAP.get(opposite, set()) if opposite else set()
    if any(c in cuisine_combined for c in match_cuisines):
        return 0.5
    if any(c in cuisine_combined for c in opposite_cuisines):
        return -0.5
    return 0.0


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
        preferences keys: cuisine_type, dietary (list[str]), avoid (list[str]),
                          budget (str), time_context (str)
        """
        michelin_names = _load_json_list(os.path.join(_DATA_DIR, "michelin_2025.json"))
        halal_names = _load_json_list(os.path.join(_DATA_DIR, "halal_stalls.json"))

        rag_results = self._vs.query(query, n_results=15)

        loc_map: dict[str, LocationResult] = {r.centre_name.upper(): r for r in location_results}
        hygiene_map: dict[str, HygieneResult] = {r.centre_name.upper(): r for r in hygiene_results}

        # Signal 2: run sentiment analysis in parallel for all centres with reviews
        sentiment_map = await self._build_sentiment_map(location_results)

        dietary = [d.lower() for d in preferences.get("dietary", [])]
        requires_halal = any(d in _DIETARY_REQUIRES_HALAL for d in dietary)
        requires_vegetarian = any(d in _DIETARY_REQUIRES_VEGETARIAN for d in dietary)
        budget = preferences.get("budget", "any")
        time_context = preferences.get("time_context", "any")

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
            price_level = loc.price_level if loc else None
            grade = hygiene.grade if hygiene else "UNKNOWN"
            demerit_points = hygiene.demerit_points if hygiene else 0

            sentiment = sentiment_map.get(centre_name.upper(), _NEUTRAL_SENTIMENT)

            cuisine_combined = (meta.get("cuisine", "") + " " + meta.get("tags", "")).lower()

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
                score += 1

            # Signal 2: LLM sentiment
            score += max(-1.0, min(1.0, sentiment.sentiment_score))
            if sentiment.hygiene_concerns:
                score -= 0.5

            # Signal 3: time-aware (tiered — seeded metadata → Haiku hint → cuisine prior)
            best_ranges = _parse_time_range(meta.get("best_time", ""))
            avoid_ranges = _parse_time_range(meta.get("avoid_time", ""))
            if any(s <= current_hour < e for s, e in best_ranges):
                score += 1   # seeded metadata — high confidence
            elif any(s <= current_hour < e for s, e in avoid_ranges):
                score -= 1
            elif sentiment.peak_time_hint != "unknown" and time_context != "any":
                # Haiku-extracted hint vs user's stated time intent
                if sentiment.peak_time_hint == time_context:
                    score += 0.5  # e.g. user wants lunch, reviews say "best at lunch"
            elif time_context != "any":
                # Cuisine-based prior as final fallback (Signal 3B)
                score += _cuisine_time_score(cuisine_combined, time_context)

            # Signal 4: demerit nuance (only when grade is known)
            if grade not in ("UNKNOWN", ""):
                if demerit_points == 0:
                    score += 0.5
                elif demerit_points >= 12:
                    score -= 0.5

            # Signal 5: price range preference (tiered — seeded → Places level → review signal)
            price_upper = _parse_price_upper(meta.get("price_range", ""))
            if price_upper is None:
                price_upper = _price_upper_from_level(price_level)        # Signal 5A
            if price_upper is None and sentiment.price_signal != "unknown":
                price_upper = _PRICE_SIGNAL_MAP.get(sentiment.price_signal)  # Signal 5B

            if price_upper is not None:
                if budget == "cheap":
                    if price_upper <= 6:
                        score += 1
                    elif price_upper > 12:
                        score -= 1
                elif budget == "moderate":
                    if 6 < price_upper <= 12:
                        score += 0.5

            # ── Reasoning string ──────────────────────────────────────────────
            michelin_note = " Michelin Bib Gourmand 2025." if is_michelin else ""
            halal_note = " Halal certified." if is_halal else ""
            open_note = "Currently open." if is_open else "Currently closed."
            if not is_open:
                crowd_note = ""
            elif crowd_level == "busy":
                crowd_note = "Busy period — expect queues."
            elif crowd_level == "quiet":
                crowd_note = "Quiet period — good time to visit."
            else:
                crowd_note = ""
            dist_note = f"{distance_km:.1f}km from you." if distance_km < 99 else ""

            rating_note = ""
            if google_rating is not None:
                count_part = f" ({review_count} reviews)" if review_count else ""
                rating_note = f" Rated {google_rating}/5{count_part}."

            hygiene_concern_note = " ⚠️ Hygiene concerns mentioned in reviews." if sentiment.hygiene_concerns else ""
            quote_note = f' "{sentiment.standout_quote}"' if sentiment.standout_quote else ""

            timing_note = f" {crowd_note}" if crowd_note else ""
            reasoning = (
                f"{stall_name} at {centre_name}."
                f" Grade {grade} hygiene.{michelin_note}{halal_note}"
                f"{rating_note}"
                f" {open_note} {dist_note}{timing_note}"
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
                    review_count=review_count,
                    crowd_level=crowd_level,
                    standout_quote=sentiment.standout_quote or None,
                    score=round(score, 3),
                    lat=loc.lat if loc else None,
                    lng=loc.lng if loc else None,
                )
            )

        candidates.sort(key=lambda c: c.score, reverse=True)
        top_n = candidates[:10]
        for i, rec in enumerate(top_n, start=1):
            rec.rank = i
        return top_n

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
                max_tokens=256,
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
                    peak_time_hint=str(data.get("peak_time_hint", "unknown")),
                    price_signal=str(data.get("price_signal", "unknown")),
                )
        except json.JSONDecodeError as e:
            logger.debug("Sentiment JSON parse failed (%s) — using neutral", e)
            result = _NEUTRAL_SENTIMENT
        except Exception as e:
            logger.warning("Sentiment analysis error: %s", e)
            result = _NEUTRAL_SENTIMENT

        _SENTIMENT_CACHE[cache_key] = (result, time.time())
        return result
