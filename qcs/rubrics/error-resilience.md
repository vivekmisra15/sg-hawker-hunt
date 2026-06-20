# Error Resilience — Rubric

## Level 1
- Unhandled exceptions crash the app
- No error boundaries

## Level 2
- Basic try/catch around API calls
- Error messages shown to user

## Level 3 (Current)
- React ErrorBoundary catches render crashes
- SSE errors yield error events to client
- HygieneAgent returns UNKNOWN on failure
- WeatherClient returns default on missing key
- InferenceClient falls back from OpenRouter to Anthropic
- SSE timeout (120s) with auto-abort

## Level 4 (Target)
- Fault injection tests for each external dependency
- Degradation audit: app works with each API individually failing
- Partial results: show what's available even if one agent fails
- User-visible status per agent (succeeded/failed/skipped)
- Retry with exponential backoff on transient failures

## Level 5
- Chaos engineering: random failure injection in staging
- Recovery time objective (RTO) measured and documented
- Bulkhead pattern: one failing agent doesn't block others
- Error budget tracking
