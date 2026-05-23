# Session 15 — OpenRouter Integration (2026-05-23)

## Goal
Reduce inference costs by adding OpenRouter as the primary LLM provider with free-tier Nemotron models, keeping Anthropic as a silent fallback.

## What changed

### New: `backend/tools/inference_client.py`
Central inference abstraction. All agents call LLM through this module — never Anthropic or OpenRouter directly.

- `InferenceClient` class with `complete(call_type, system, user_content, max_tokens)` method
- `InferenceError` exception raised when both providers fail
- `_clean_response()` strips `<think>...</think>` reasoning tokens from Nemotron responses
- JSON extraction fallback: regex `{...}` match when Nemotron wraps JSON in prose
- Properties: `active_provider`, `openrouter_configured`, `anthropic_configured`

### Model routing

| Call type | OpenRouter (primary, free) | Anthropic (fallback) |
|-----------|---------------------------|---------------------|
| orchestrator | nvidia/nemotron-3-super-120b-a12b:free | claude-sonnet-4-6 |
| sentiment | nvidia/llama-3.3-nemotron-super-49b-v1:free | claude-haiku-4-5-20251001 |

### OpenRouter integration details
- Uses `openai` Python SDK with `base_url="https://openrouter.ai/api/v1"`
- Required headers on every request: `HTTP-Referer` (from FRONTEND_URL), `X-Title: Hawker Hunt`
- Fallback triggers: missing key, HTTP 429, HTTP 5xx, timeout, any exception
- All fallbacks log WARNING then proceed silently to Anthropic

### Agent changes
- `orchestrator.py`: `anthropic_client` param → `inference_client`, `_parse_query()` calls `self._inference.complete("orchestrator", ...)`
- `recommendation_agent.py`: same pattern, `_analyse_sentiment()` calls `self._inference.complete("sentiment", ...)`
- Cache, eviction, and error handling in recommendation agent unchanged

### Health endpoint
`/api/health` now returns `llm_provider`, `openrouter_configured`, `anthropic_configured` fields.

### Dependencies
- `openai>=1.40.0` added to `requirements.txt`
- `OPENROUTER_API_KEY` added to `.env.example`

### Not changed
- `data_pipeline.py` (CLI batch tool) still uses Anthropic directly — not on the runtime path

## Test results
- **122/122 passing** (+16 new, 0 regressions)
- New `test_inference_client.py`: 16 tests covering success path, think tag stripping, JSON extraction, all fallback triggers (missing key, 429, 5xx, generic exception), both-fail error, correct model routing for orchestrator vs sentiment, provider properties
- All existing agent tests updated: `anthropic_client=` → `inference_client=`, mock pattern simplified to `complete = AsyncMock(return_value=json_string)`

## Files changed

| File | Action |
|------|--------|
| `backend/tools/inference_client.py` | NEW |
| `backend/tests/test_inference_client.py` | NEW |
| `backend/agents/orchestrator.py` | Modified |
| `backend/agents/recommendation_agent.py` | Modified |
| `backend/main.py` | Modified |
| `backend/tests/test_orchestrator.py` | Modified |
| `backend/tests/test_recommendation_agent.py` | Modified |
| `backend/tests/test_sse_endpoint.py` | Modified |
| `backend/requirements.txt` | Modified |
| `.env.example` | Modified |
| `CLAUDE.md` | Updated session notes |
