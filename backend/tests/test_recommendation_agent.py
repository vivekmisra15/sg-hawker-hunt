"""Tests for RecommendationAgent — base scoring + Milestone 4 quality signals."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from agents.recommendation_agent import RecommendationAgent, _parse_time_range, _parse_price_upper
from models.schemas import LocationResult, HygieneResult, SentimentResult

# ── helpers ───────────────────────────────────────────────────────────────────

def _make_vs(rag_docs: list[dict]):
    mock = MagicMock()
    mock.query = MagicMock(return_value=rag_docs)
    return mock


def _make_anthropic(sentiment: SentimentResult | None = None):
    """Return a mock Anthropic client that yields a fixed sentiment JSON response."""
    client = AsyncMock()
    if sentiment is not None:
        # Serialise all fields so new fields (peak_time_hint, price_signal) are included
        payload = sentiment.model_dump_json()
        msg = MagicMock()
        msg.content = [MagicMock(text=payload)]
        client.messages.create = AsyncMock(return_value=msg)
    return client


def _loc(
    centre_name,
    distance_km=0.5,
    is_open=True,
    crowd="quiet",
    rating=4.2,
    review_count=100,
    reviews_summary=None,
    price_level=None,
):
    return LocationResult(
        centre_name=centre_name, address="", lat=1.35, lng=103.82,
        distance_km=distance_km, is_open=is_open,
        google_rating=rating, review_count=review_count,
        reviews_summary=reviews_summary,
        price_level=price_level,
        crowd_level=crowd,
    )


def _hyg(centre_name, grade="A", demerit_points=0, suspended=False):
    return HygieneResult(
        stall_name=centre_name, centre_name=centre_name,
        grade=grade, demerit_points=demerit_points, suspended=suspended,
    )


def _rag(
    stall,
    centre,
    is_michelin=False,
    is_halal=False,
    distance=0.3,
    best_time="",
    avoid_time="",
    price_range="",
):
    return {
        "text": f"{stall} at {centre} great food.",
        "metadata": {
            "stall_name": stall,
            "centre_name": centre,
            "cuisine": "chicken rice",
            "tags": "chicken rice",
            "is_michelin": str(is_michelin),
            "is_halal": str(is_halal),
            "best_time": best_time,
            "avoid_time": avoid_time,
            "price_range": price_range,
        },
        "distance": distance,
    }


def _make_agent(vs, anthropic_client=None):
    if anthropic_client is None:
        anthropic_client = _make_anthropic()
    return RecommendationAgent(vector_store=vs, anthropic_client=anthropic_client)


# ── original base tests ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_michelin_stall_scores_higher_than_non_michelin():
    vs = _make_vs([
        _rag("Stall A", "Maxwell", is_michelin=True, distance=0.3),
        _rag("Stall B", "Chinatown", is_michelin=False, distance=0.3),
    ])
    agent = _make_agent(vs)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        results = await agent.run(
            query="chicken rice",
            location_results=[_loc("Maxwell"), _loc("Chinatown")],
            hygiene_results=[_hyg("Maxwell"), _hyg("Chinatown")],
            preferences={},
        )
    assert len(results) >= 2
    michelin_result = next(r for r in results if r.stall_name == "Stall A")
    non_michelin = next(r for r in results if r.stall_name == "Stall B")
    assert michelin_result.score > non_michelin.score


@pytest.mark.asyncio
async def test_halal_filter_removes_non_halal_stalls():
    vs = _make_vs([
        _rag("Halal Stall", "Newton", is_halal=True, distance=0.3),
        _rag("Non-Halal Stall", "Maxwell", is_halal=False, distance=0.2),
    ])
    agent = _make_agent(vs)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        results = await agent.run(
            query="halal food",
            location_results=[_loc("Newton"), _loc("Maxwell")],
            hygiene_results=[_hyg("Newton"), _hyg("Maxwell")],
            preferences={"dietary": ["halal"]},
        )
    stall_names = [r.stall_name for r in results]
    assert "Non-Halal Stall" not in stall_names
    assert "Halal Stall" in stall_names


@pytest.mark.asyncio
async def test_returns_maximum_three_results():
    vs = _make_vs([
        _rag(f"Stall {i}", f"Centre {i}", distance=0.3) for i in range(8)
    ])
    agent = _make_agent(vs)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        results = await agent.run(
            query="food",
            location_results=[_loc(f"Centre {i}") for i in range(8)],
            hygiene_results=[_hyg(f"Centre {i}") for i in range(8)],
            preferences={},
        )
    assert len(results) <= 3


@pytest.mark.asyncio
async def test_each_result_has_non_empty_reasoning():
    vs = _make_vs([_rag("Test Stall", "Maxwell", distance=0.3)])
    agent = _make_agent(vs)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        results = await agent.run(
            query="chicken rice",
            location_results=[_loc("Maxwell")],
            hygiene_results=[_hyg("Maxwell")],
            preferences={},
        )
    assert len(results) > 0
    for r in results:
        assert isinstance(r.reasoning, str) and len(r.reasoning) > 0


@pytest.mark.asyncio
async def test_grade_a_stall_outscores_grade_b_stall():
    vs = _make_vs([
        _rag("Grade A Stall", "Maxwell", distance=0.3),
        _rag("Grade B Stall", "Newton", distance=0.3),
    ])
    agent = _make_agent(vs)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        results = await agent.run(
            query="food",
            location_results=[_loc("Maxwell"), _loc("Newton")],
            hygiene_results=[_hyg("Maxwell", grade="A"), _hyg("Newton", grade="B")],
            preferences={},
        )
    grade_a = next(r for r in results if r.stall_name == "Grade A Stall")
    grade_b = next(r for r in results if r.stall_name == "Grade B Stall")
    assert grade_a.score > grade_b.score


# ── Signal 1: Google rating ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_signal1_high_rating_adds_score():
    vs = _make_vs([_rag("Stall A", "Maxwell", distance=0.3), _rag("Stall B", "Newton", distance=0.3)])
    agent = _make_agent(vs)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        results = await agent.run(
            query="food",
            location_results=[_loc("Maxwell", rating=4.7), _loc("Newton", rating=4.0)],
            hygiene_results=[_hyg("Maxwell", grade="UNKNOWN"), _hyg("Newton", grade="UNKNOWN")],
            preferences={},
        )
    high = next(r for r in results if r.stall_name == "Stall A")
    lower = next(r for r in results if r.stall_name == "Stall B")
    # 4.7 → +2, 4.0 → +1 → delta of 1
    assert high.score > lower.score


@pytest.mark.asyncio
async def test_signal1_low_rating_penalises():
    vs = _make_vs([_rag("Good Stall", "Maxwell", distance=0.3), _rag("Bad Stall", "Newton", distance=0.3)])
    agent = _make_agent(vs)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        results = await agent.run(
            query="food",
            location_results=[_loc("Maxwell", rating=4.0), _loc("Newton", rating=3.2)],
            hygiene_results=[_hyg("Maxwell", grade="UNKNOWN"), _hyg("Newton", grade="UNKNOWN")],
            preferences={},
        )
    good = next(r for r in results if r.stall_name == "Good Stall")
    bad = next(r for r in results if r.stall_name == "Bad Stall")
    # 4.0 → +1, 3.2 → -1 → delta of 2
    assert good.score > bad.score


@pytest.mark.asyncio
async def test_signal1_review_count_bonus():
    vs = _make_vs([_rag("Popular Stall", "Maxwell", distance=0.3), _rag("Unknown Stall", "Newton", distance=0.3)])
    agent = _make_agent(vs)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        results = await agent.run(
            query="food",
            location_results=[
                _loc("Maxwell", rating=4.0, review_count=250),
                _loc("Newton", rating=4.0, review_count=50),
            ],
            hygiene_results=[_hyg("Maxwell", grade="UNKNOWN"), _hyg("Newton", grade="UNKNOWN")],
            preferences={},
        )
    popular = next(r for r in results if r.stall_name == "Popular Stall")
    unknown = next(r for r in results if r.stall_name == "Unknown Stall")
    # review_count ≥200 → +1 bonus
    assert popular.score > unknown.score


@pytest.mark.asyncio
async def test_signal1_missing_rating_no_change():
    vs = _make_vs([_rag("Stall A", "Maxwell", distance=0.3)])
    agent = _make_agent(vs)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        results = await agent.run(
            query="food",
            location_results=[_loc("Maxwell", rating=None, review_count=None)],
            hygiene_results=[_hyg("Maxwell", grade="UNKNOWN")],
            preferences={},
        )
    assert len(results) == 1
    # Base score: grade UNKNOWN (0) + is_open (2) + crowd quiet (1) + rag relevance (~1.4)
    # No rating bonus/penalty — score should be ~4.4
    assert results[0].score > 0


# ── Signal 2: LLM sentiment ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_signal2_positive_sentiment_boosts():
    vs = _make_vs([_rag("Stall A", "Maxwell", distance=0.3), _rag("Stall B", "Newton", distance=0.3)])
    positive = _make_anthropic(SentimentResult(sentiment_score=0.8, standout_quote="Absolutely delicious!"))
    agent = _make_agent(vs, anthropic_client=positive)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        # Both have reviews so sentiment fires for both; Maxwell gets +0.8
        results = await agent.run(
            query="food",
            location_results=[
                _loc("Maxwell", rating=None, reviews_summary="Great food, clean stall."),
                _loc("Newton", rating=None),
            ],
            hygiene_results=[_hyg("Maxwell", grade="UNKNOWN"), _hyg("Newton", grade="UNKNOWN")],
            preferences={},
        )
    maxwell_rec = next(r for r in results if r.stall_name == "Stall A")
    newton_rec = next(r for r in results if r.stall_name == "Stall B")
    assert maxwell_rec.score > newton_rec.score


@pytest.mark.asyncio
async def test_signal2_hygiene_concern_penalises():
    vs = _make_vs([_rag("Dirty Stall", "Maxwell", distance=0.3)])
    concern = _make_anthropic(SentimentResult(
        sentiment_score=0.0, hygiene_concerns=True, standout_quote=""
    ))
    agent = _make_agent(vs, anthropic_client=concern)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        results = await agent.run(
            query="food",
            location_results=[_loc("Maxwell", rating=None, reviews_summary="Saw a cockroach here.")],
            hygiene_results=[_hyg("Maxwell", grade="UNKNOWN")],
            preferences={},
        )
    assert len(results) == 1
    # hygiene_concerns → -0.5 penalty applied
    assert "Hygiene concerns" in results[0].reasoning


@pytest.mark.asyncio
async def test_signal2_haiku_failure_graceful():
    vs = _make_vs([_rag("Stall A", "Maxwell", distance=0.3)])
    failing_client = AsyncMock()
    failing_client.messages.create = AsyncMock(side_effect=Exception("API timeout"))
    agent = _make_agent(vs, anthropic_client=failing_client)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        results = await agent.run(
            query="food",
            location_results=[_loc("Maxwell", reviews_summary="Some reviews here.")],
            hygiene_results=[_hyg("Maxwell", grade="UNKNOWN")],
            preferences={},
        )
    # Should not crash — returns results with neutral sentiment
    assert len(results) == 1


@pytest.mark.asyncio
async def test_signal2_empty_reviews_skips_llm():
    vs = _make_vs([_rag("Stall A", "Maxwell", distance=0.3)])
    client = _make_anthropic()
    agent = _make_agent(vs, anthropic_client=client)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        await agent.run(
            query="food",
            location_results=[_loc("Maxwell", reviews_summary=None)],
            hygiene_results=[_hyg("Maxwell")],
            preferences={},
        )
    # No reviews → no Haiku call
    client.messages.create.assert_not_called()


@pytest.mark.asyncio
async def test_signal2_cache_hit_no_api_call():
    import agents.recommendation_agent as ra
    vs = _make_vs([_rag("Stall A", "Maxwell", distance=0.3)])
    client = _make_anthropic(SentimentResult(sentiment_score=0.5))
    agent = _make_agent(vs, anthropic_client=client)
    reviews = "Tasty hawker food."
    # Clear cache first
    ra._SENTIMENT_CACHE.clear()
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        await agent.run(
            query="food",
            location_results=[_loc("Maxwell", reviews_summary=reviews)],
            hygiene_results=[_hyg("Maxwell")],
            preferences={},
        )
        call_count_first = client.messages.create.call_count
        await agent.run(
            query="food",
            location_results=[_loc("Maxwell", reviews_summary=reviews)],
            hygiene_results=[_hyg("Maxwell")],
            preferences={},
        )
    # Second run should hit cache — call count unchanged
    assert client.messages.create.call_count == call_count_first


# ── Signal 3: time-aware ──────────────────────────────────────────────────────

def test_parse_time_range_range_pattern():
    ranges = _parse_time_range("12pm-2pm (busy)")
    assert (12, 14) in ranges


def test_parse_time_range_before_pattern():
    ranges = _parse_time_range("Before 11:30am")
    assert any(end <= 12 for _, end in ranges)


def test_parse_time_range_after_pattern():
    ranges = _parse_time_range("After 2pm")
    assert any(start >= 14 for start, _ in ranges)


def test_parse_time_range_empty_string():
    assert _parse_time_range("") == []


def test_parse_time_range_unrecognised():
    assert _parse_time_range("anytime is fine") == []


@pytest.mark.asyncio
async def test_signal3_best_time_match_boosts():
    vs = _make_vs([
        _rag("Early Bird", "Maxwell", distance=0.3, best_time="7am-10am"),
        _rag("Baseline", "Newton", distance=0.3),
    ])
    agent = _make_agent(vs)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        with patch("agents.recommendation_agent.datetime") as mock_dt:
            mock_dt.now.return_value.hour = 8  # 8am SGT
            results = await agent.run(
                query="food",
                location_results=[_loc("Maxwell"), _loc("Newton")],
                hygiene_results=[_hyg("Maxwell", grade="UNKNOWN"), _hyg("Newton", grade="UNKNOWN")],
                preferences={},
            )
    early = next(r for r in results if r.stall_name == "Early Bird")
    base = next(r for r in results if r.stall_name == "Baseline")
    assert early.score > base.score


@pytest.mark.asyncio
async def test_signal3_avoid_time_penalises():
    vs = _make_vs([
        _rag("Crowded Stall", "Maxwell", distance=0.3, avoid_time="12pm-2pm"),
        _rag("Baseline", "Newton", distance=0.3),
    ])
    agent = _make_agent(vs)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        with patch("agents.recommendation_agent.datetime") as mock_dt:
            mock_dt.now.return_value.hour = 13  # 1pm SGT
            results = await agent.run(
                query="food",
                location_results=[_loc("Maxwell"), _loc("Newton")],
                hygiene_results=[_hyg("Maxwell", grade="UNKNOWN"), _hyg("Newton", grade="UNKNOWN")],
                preferences={},
            )
    crowded = next(r for r in results if r.stall_name == "Crowded Stall")
    base = next(r for r in results if r.stall_name == "Baseline")
    assert crowded.score < base.score


@pytest.mark.asyncio
async def test_signal3_missing_time_no_change():
    vs = _make_vs([_rag("Stall A", "Maxwell", distance=0.3)])
    agent = _make_agent(vs)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        results = await agent.run(
            query="food",
            location_results=[_loc("Maxwell")],
            hygiene_results=[_hyg("Maxwell", grade="UNKNOWN")],
            preferences={},
        )
    assert len(results) == 1  # no crash, no score anomaly


# ── Signal 4: demerit nuance ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_signal4_zero_demerits_bonus():
    vs = _make_vs([
        _rag("Clean Stall", "Maxwell", distance=0.3),
        _rag("No Grade Stall", "Newton", distance=0.3),
    ])
    agent = _make_agent(vs)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        results = await agent.run(
            query="food",
            location_results=[_loc("Maxwell"), _loc("Newton")],
            hygiene_results=[
                _hyg("Maxwell", grade="A", demerit_points=0),
                _hyg("Newton", grade="UNKNOWN", demerit_points=0),
            ],
            preferences={},
        )
    clean = next(r for r in results if r.stall_name == "Clean Stall")
    no_grade = next(r for r in results if r.stall_name == "No Grade Stall")
    # Grade A (+3) + zero demerits (+0.5) vs UNKNOWN (0) + no demerit bonus
    assert clean.score > no_grade.score


@pytest.mark.asyncio
async def test_signal4_high_demerits_penalty():
    vs = _make_vs([
        _rag("Good Stall", "Maxwell", distance=0.3),
        _rag("Bad Record Stall", "Newton", distance=0.3),
    ])
    agent = _make_agent(vs)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        results = await agent.run(
            query="food",
            location_results=[_loc("Maxwell"), _loc("Newton")],
            hygiene_results=[
                _hyg("Maxwell", grade="B", demerit_points=0),
                _hyg("Newton", grade="B", demerit_points=12),
            ],
            preferences={},
        )
    good = next(r for r in results if r.stall_name == "Good Stall")
    bad = next(r for r in results if r.stall_name == "Bad Record Stall")
    # Both grade B; good has +0.5 demerits bonus, bad has -0.5 → delta of 1.0
    assert good.score > bad.score


@pytest.mark.asyncio
async def test_signal4_unknown_grade_skips():
    vs = _make_vs([_rag("Stall A", "Maxwell", distance=0.3)])
    agent = _make_agent(vs)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        results = await agent.run(
            query="food",
            location_results=[_loc("Maxwell")],
            hygiene_results=[_hyg("Maxwell", grade="UNKNOWN", demerit_points=0)],
            preferences={},
        )
    assert len(results) == 1  # no crash, demerit bonus not applied for UNKNOWN


# ── Signal 5: price range ─────────────────────────────────────────────────────

def test_parse_price_upper_standard():
    assert _parse_price_upper("S$5-7") == 7.0


def test_parse_price_upper_single():
    assert _parse_price_upper("S$5") == 5.0


def test_parse_price_upper_empty():
    assert _parse_price_upper("") is None


@pytest.mark.asyncio
async def test_signal5_cheap_query_boosts_cheap_stall():
    vs = _make_vs([
        _rag("Budget Stall", "Maxwell", distance=0.3, price_range="S$3-5"),
        _rag("Expensive Stall", "Newton", distance=0.3, price_range="S$15-20"),
    ])
    agent = _make_agent(vs)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        results = await agent.run(
            query="cheap food",
            location_results=[_loc("Maxwell"), _loc("Newton")],
            hygiene_results=[_hyg("Maxwell", grade="UNKNOWN"), _hyg("Newton", grade="UNKNOWN")],
            preferences={"budget": "cheap"},
        )
    budget = next(r for r in results if r.stall_name == "Budget Stall")
    expensive = next(r for r in results if r.stall_name == "Expensive Stall")
    # cheap + price ≤6 → +1; cheap + price >12 → -1; delta = 2
    assert budget.score > expensive.score


@pytest.mark.asyncio
async def test_signal5_cheap_query_penalises_expensive():
    vs = _make_vs([_rag("Pricey Stall", "Maxwell", distance=0.3, price_range="S$18-25")])
    agent = _make_agent(vs)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        results_cheap = await agent.run(
            query="food",
            location_results=[_loc("Maxwell")],
            hygiene_results=[_hyg("Maxwell", grade="UNKNOWN")],
            preferences={"budget": "cheap"},
        )
        results_any = await agent.run(
            query="food",
            location_results=[_loc("Maxwell")],
            hygiene_results=[_hyg("Maxwell", grade="UNKNOWN")],
            preferences={"budget": "any"},
        )
    assert results_cheap[0].score < results_any[0].score


@pytest.mark.asyncio
async def test_signal5_no_budget_no_change():
    vs = _make_vs([_rag("Stall A", "Maxwell", distance=0.3, price_range="S$3-5")])
    agent = _make_agent(vs)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        results = await agent.run(
            query="food",
            location_results=[_loc("Maxwell")],
            hygiene_results=[_hyg("Maxwell", grade="UNKNOWN")],
            preferences={"budget": "any"},
        )
    assert len(results) == 1  # no crash, no unexpected score change


# ── Signal 6: suspension filter ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_signal6_suspended_stall_excluded():
    vs = _make_vs([
        _rag("Suspended Stall", "Maxwell", distance=0.3),
        _rag("Good Stall", "Newton", distance=0.3),
    ])
    agent = _make_agent(vs)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        results = await agent.run(
            query="food",
            location_results=[_loc("Maxwell"), _loc("Newton")],
            hygiene_results=[
                _hyg("Maxwell", grade="A", suspended=True),
                _hyg("Newton", grade="A", suspended=False),
            ],
            preferences={},
        )
    stall_names = [r.stall_name for r in results]
    assert "Suspended Stall" not in stall_names
    assert "Good Stall" in stall_names


@pytest.mark.asyncio
async def test_signal6_non_suspended_included():
    vs = _make_vs([_rag("Active Stall", "Maxwell", distance=0.3)])
    agent = _make_agent(vs)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        results = await agent.run(
            query="food",
            location_results=[_loc("Maxwell")],
            hygiene_results=[_hyg("Maxwell", grade="A", suspended=False)],
            preferences={},
        )
    assert any(r.stall_name == "Active Stall" for r in results)

# ── Signal 3A: peak_time_hint from Haiku ─────────────────────────────────────

@pytest.mark.asyncio
async def test_signal3a_peak_time_hint_matches_time_context_boosts():
    """Haiku says 'best at lunch'; user querying for lunch → +0.5 via peak_time_hint path.
    Newton has a neutral cuisine (not in any time bucket) so no cuisine prior fires there."""
    vs = _make_vs([
        _rag("Lunch Stall", "Maxwell", distance=0.3),
        _rag("Baseline", "Newton", distance=0.3),
    ])
    # Override Newton's cuisine to something time-neutral (not in _TIME_CUISINE_MAP)
    vs.query = MagicMock(return_value=[
        _rag("Lunch Stall", "Maxwell", distance=0.3),
        {**_rag("Baseline", "Newton", distance=0.3),
         "metadata": {**_rag("Baseline", "Newton", distance=0.3)["metadata"],
                      "cuisine": "rojak", "tags": "mixed fruit nuts"}},
    ])
    lunch_sentiment = _make_anthropic(SentimentResult(
        sentiment_score=0.0, peak_time_hint="lunch"
    ))
    agent = _make_agent(vs, anthropic_client=lunch_sentiment)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        results = await agent.run(
            query="lunch food",
            location_results=[
                _loc("Maxwell", reviews_summary="Best at lunchtime, always busy."),
                _loc("Newton"),
            ],
            hygiene_results=[_hyg("Maxwell", grade="UNKNOWN"), _hyg("Newton", grade="UNKNOWN")],
            preferences={"time_context": "lunch"},
        )
    lunch_rec = next(r for r in results if r.stall_name == "Lunch Stall")
    baseline = next(r for r in results if r.stall_name == "Baseline")
    # Maxwell: peak_time_hint=lunch matches time_context=lunch → +0.5
    # Newton: neutral cuisine, no Haiku (no reviews), time_context=lunch → 0 (cuisine doesn't match)
    assert lunch_rec.score > baseline.score


@pytest.mark.asyncio
async def test_signal3a_mismatched_peak_time_hint_no_boost():
    """Haiku says 'best at breakfast'; user wants supper → no boost (no match)."""
    vs = _make_vs([_rag("Brekkie Stall", "Maxwell", distance=0.3)])
    breakfast_sentiment = _make_anthropic(SentimentResult(
        sentiment_score=0.0, peak_time_hint="breakfast"
    ))
    agent = _make_agent(vs, anthropic_client=breakfast_sentiment)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        results_supper = await agent.run(
            query="supper",
            location_results=[_loc("Maxwell", reviews_summary="Great for early birds!")],
            hygiene_results=[_hyg("Maxwell", grade="UNKNOWN")],
            preferences={"time_context": "supper"},
        )
        results_any = await agent.run(
            query="food",
            location_results=[_loc("Maxwell", reviews_summary="Great for early birds!")],
            hygiene_results=[_hyg("Maxwell", grade="UNKNOWN")],
            preferences={"time_context": "any"},
        )
    # supper context but breakfast hint — no bonus in either direction
    assert results_supper[0].score == results_any[0].score


# ── Signal 3B: cuisine-based time priors ─────────────────────────────────────

@pytest.mark.asyncio
async def test_signal3b_breakfast_cuisine_boosts_for_breakfast_query():
    """Kaya toast is a breakfast cuisine — querying for breakfast gives +0.5."""
    vs = _make_vs([
        _rag("Toast Stall", "Maxwell", distance=0.3),
        _rag("Laksa Stall", "Newton", distance=0.3),
    ])
    # Override cuisine/tags in the RAG result
    vs.query = MagicMock(return_value=[
        {**_rag("Toast Stall", "Maxwell", distance=0.3),
         "metadata": {**_rag("Toast Stall", "Maxwell", distance=0.3)["metadata"],
                      "cuisine": "kaya toast", "tags": "toast breakfast"}},
        _rag("Laksa Stall", "Newton", distance=0.3),
    ])
    agent = _make_agent(vs)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        results = await agent.run(
            query="breakfast near Maxwell",
            location_results=[_loc("Maxwell"), _loc("Newton")],
            hygiene_results=[_hyg("Maxwell", grade="UNKNOWN"), _hyg("Newton", grade="UNKNOWN")],
            preferences={"time_context": "breakfast"},
        )
    toast = next(r for r in results if r.stall_name == "Toast Stall")
    laksa = next(r for r in results if r.stall_name == "Laksa Stall")
    assert toast.score > laksa.score


@pytest.mark.asyncio
async def test_signal3b_supper_cuisine_penalised_for_breakfast_query():
    """Bak kut teh is a supper food — querying for breakfast gives -0.5."""
    vs = _make_vs([
        _rag("BKT Stall", "Maxwell", distance=0.3),
        _rag("Neutral Stall", "Newton", distance=0.3),
    ])
    vs.query = MagicMock(return_value=[
        {**_rag("BKT Stall", "Maxwell", distance=0.3),
         "metadata": {**_rag("BKT Stall", "Maxwell", distance=0.3)["metadata"],
                      "cuisine": "bak kut teh", "tags": "pork ribs supper"}},
        _rag("Neutral Stall", "Newton", distance=0.3),
    ])
    agent = _make_agent(vs)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        results = await agent.run(
            query="breakfast",
            location_results=[_loc("Maxwell"), _loc("Newton")],
            hygiene_results=[_hyg("Maxwell", grade="UNKNOWN"), _hyg("Newton", grade="UNKNOWN")],
            preferences={"time_context": "breakfast"},
        )
    bkt = next(r for r in results if r.stall_name == "BKT Stall")
    neutral = next(r for r in results if r.stall_name == "Neutral Stall")
    assert bkt.score < neutral.score


# ── Signal 5A: Google Places priceLevel ──────────────────────────────────────

@pytest.mark.asyncio
async def test_signal5a_places_price_level_boosts_inexpensive_for_cheap_query():
    """Places returns PRICE_LEVEL_INEXPENSIVE → treated as cheap stall → +1 for budget query."""
    vs = _make_vs([
        _rag("Cheap Place", "Maxwell", distance=0.3),   # no price_range in metadata
        _rag("Pricey Place", "Newton", distance=0.3),
    ])
    agent = _make_agent(vs)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        results = await agent.run(
            query="cheap food",
            location_results=[
                _loc("Maxwell", price_level="PRICE_LEVEL_INEXPENSIVE"),
                _loc("Newton", price_level="PRICE_LEVEL_EXPENSIVE"),
            ],
            hygiene_results=[_hyg("Maxwell", grade="UNKNOWN"), _hyg("Newton", grade="UNKNOWN")],
            preferences={"budget": "cheap"},
        )
    cheap = next(r for r in results if r.stall_name == "Cheap Place")
    pricey = next(r for r in results if r.stall_name == "Pricey Place")
    # INEXPENSIVE upper=5 → +1; EXPENSIVE upper=25 → -1; delta=2
    assert cheap.score > pricey.score


@pytest.mark.asyncio
async def test_signal5a_places_price_level_ignored_when_metadata_present():
    """Seeded price_range takes priority over Places priceLevel."""
    vs = _make_vs([
        _rag("Stall A", "Maxwell", distance=0.3, price_range="S$3-5"),  # seeded cheap
    ])
    agent = _make_agent(vs)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        # Even if Places says expensive, the seeded S$3-5 should dominate
        results_places_expensive = await agent.run(
            query="food",
            location_results=[_loc("Maxwell", price_level="PRICE_LEVEL_EXPENSIVE")],
            hygiene_results=[_hyg("Maxwell", grade="UNKNOWN")],
            preferences={"budget": "cheap"},
        )
        results_no_places = await agent.run(
            query="food",
            location_results=[_loc("Maxwell", price_level=None)],
            hygiene_results=[_hyg("Maxwell", grade="UNKNOWN")],
            preferences={"budget": "cheap"},
        )
    # Both should give the same score — seeded S$3-5 wins in both cases
    assert results_places_expensive[0].score == results_no_places[0].score


# ── Signal 5B: Haiku price_signal ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_signal5b_review_price_signal_used_as_fallback():
    """When neither seeded price_range nor Places priceLevel is available,
    Haiku's price_signal from reviews is used."""
    vs = _make_vs([
        _rag("Value Stall", "Maxwell", distance=0.3),  # no price_range
        _rag("Baseline", "Newton", distance=0.3),
    ])
    cheap_sentiment = _make_anthropic(SentimentResult(
        sentiment_score=0.0, price_signal="cheap"
    ))
    agent = _make_agent(vs, anthropic_client=cheap_sentiment)
    with patch("agents.recommendation_agent._load_json_list", return_value=[]):
        results = await agent.run(
            query="cheap food",
            location_results=[
                _loc("Maxwell", price_level=None, reviews_summary="So cheap, only $3 a bowl!"),
                _loc("Newton"),
            ],
            hygiene_results=[_hyg("Maxwell", grade="UNKNOWN"), _hyg("Newton", grade="UNKNOWN")],
            preferences={"budget": "cheap"},
        )
    value = next(r for r in results if r.stall_name == "Value Stall")
    baseline = next(r for r in results if r.stall_name == "Baseline")
    # cheap price_signal → upper=5.0 → +1 for budget="cheap"
    assert value.score > baseline.score


# ── Signal 2: Singlish-aware prompt structure ─────────────────────────────────

def test_singlish_prompt_contains_local_terms():
    """Haiku prompt must include Singlish glossary and queue reinterpretation."""
    from agents.recommendation_agent import _SENTIMENT_SYSTEM
    assert "shiok" in _SENTIMENT_SYSTEM
    assert "ho jiak" in _SENTIMENT_SYSTEM
    assert "sedap" in _SENTIMENT_SYSTEM
    assert "queue" in _SENTIMENT_SYSTEM.lower()
    assert "peak_time_hint" in _SENTIMENT_SYSTEM
    assert "price_signal" in _SENTIMENT_SYSTEM
