# API Robustness — Rubric

## Level 1
- No error handling on API calls
- No timeout protection

## Level 2 (Current)
- Error handling on all external API calls
- Graceful degradation (UNKNOWN grades, missing data)
- No rate-limiting tests
- No concurrent request protection tests

## Level 3
- Rate-limiting tests for external APIs
- Concurrent request handling tested
- Retry logic with backoff on transient failures
- Request deduplication for identical queries

## Level 4 (Target)
- Circuit breaker pattern for external APIs
- Request queuing under load
- Health check endpoint validates all dependencies
- Timeout budget: total request < 30s, per-API < 10s
- All failure modes have dedicated tests

## Level 5
- Chaos testing: random API failure injection
- Latency percentile tracking (p50, p95, p99)
- Adaptive timeout based on historical response times
- Graceful degradation matrix documented and tested
