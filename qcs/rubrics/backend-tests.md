# Backend Test Coverage — Rubric

## Level 1
- No tests
- No test framework configured

## Level 2
- pytest configured
- At least 20 tests passing
- Coverage < 50%

## Level 3 (Current)
- 100+ tests passing
- Coverage 70-84%
- All agents and tool clients tested
- Async tests working with pytest-asyncio

## Level 4 (Target)
- Coverage > 85%
- All error paths tested
- Integration tests for SSE endpoint
- Edge cases: empty results, malformed API responses, timeout handling

## Level 5
- Coverage > 95%
- Mutation testing configured (mutmut)
- Property-based tests for scoring logic (hypothesis)
- Load/stress tests for concurrent requests
