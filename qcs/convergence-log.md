# QCS Convergence Log

Append-only log of each QCS iteration.

---

## Iteration 0 — Baseline Measurement (2026-06-20)

**Purpose:** Populate scorecard with real measurements.

**Backend:** 123 tests passing, 79% coverage (pytest-cov)
**Frontend:** Vitest installed, 0 test files, build succeeds (442KB total, map chunk lazy-loaded)
**Design patterns:** 5/19 applied from Design Wiki Run 01

| Dimension | Level | Key metric |
|-----------|:---:|------------|
| Frontend test coverage | 1 | 0 tests, 0% coverage |
| Design pattern coverage | 2 | 5/19 patterns |
| Information architecture | 2 | No collapsible sections or citations |
| API robustness | 2 | No rate-limit/concurrent tests |
| Backend test coverage | 3 | 123 tests, 79% coverage |
| Accessibility | 3 | ARIA/keyboard/reduced-motion done |
| UI polish | 3 | Theme, animations, glass morphism |
| Performance | 3 | 292KB initial + 150KB lazy map |
| Data quality | 3 | 2,511 stalls, 122 centres |
| Error resilience | 3 | Error boundary, SSE timeout, inference fallback |

**Aggregate: 24/40 (target: 40/40)**

**Next:** Iteration 1 targets Frontend Test Coverage (gap: 3, largest).

---

## Iteration 1 -- Frontend Test Coverage (Level 1 -> 2)

**Target:** Configure Vitest + React Testing Library and write 5+ component/hook tests.

**Changes:**
- Installed `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `jsdom`, `@testing-library/user-event`
- Created `frontend/vitest.config.ts` with jsdom environment and setup file
- Created `frontend/src/test-setup.ts` for jest-dom matchers
- Added `"test"` and `"test:watch"` scripts to `package.json`
- Excluded test files from `tsconfig.app.json` to prevent build errors
- Created 4 test files with 28 tests:
  - `StatusBadge.test.tsx` (14 tests): all badge types, grade variants, price categories
  - `FilterStrip.test.tsx` (5 tests): rendering, toggle callback, aria-pressed, count indicator
  - `ErrorBoundary.test.tsx` (3 tests): normal render, error catch, retry button
  - `useGeolocation.test.ts` (6 tests): initial state, loading, success, failure, unsupported, clear

**Measurements before:** 0 tests, 0% coverage, Vitest not a project dependency
**Measurements after:** 28 tests passing across 4 files, Vitest configured as project dependency

**Regression check:** PASS (frontend build 443 KB, zero TS errors; backend 137/137 tests passing)
**Delta:** +1 (level 1 -> 2)
**Aggregate:** 26/40

---

## Iteration 2 -- Frontend Test Coverage (Level 2 -> 3)

**Target:** Reach 15+ tests covering all major components/hooks, configure coverage > 40%.

**Changes:**
- Installed `@vitest/coverage-v8` for coverage reporting
- Added v8 coverage config to `vitest.config.ts`
- Added `matchMedia` stub to `test-setup.ts` (jsdom does not implement it)
- Created 5 new test files:
  - `SearchBar.test.tsx` (10 tests): input rendering, chip interaction, submit, disable states
  - `useSSE.test.ts` (11 tests): state machine transitions, event handling, cancel, reset
  - `ResultsList.test.tsx` (8 tests): empty/loading states, rendering, IntersectionObserver, selection
  - `AgentPanel.test.tsx` (9 tests): idle, traces, block headers, cursor, complete/error indicators
  - `ThemeContext.test.tsx` (5 tests): default theme, localStorage, toggle, system preference

**Measurements before:** 28 tests, 4 files, 0% coverage (not configured)
**Measurements after:** 71 tests across 9 files, 42% statement coverage, 43% line coverage

**Regression check:** PASS (frontend build 443 KB, zero TS errors; backend 137/137 tests passing)
**Delta:** +1 (level 2 -> 3)
**Aggregate:** 27/40

---

## Iteration 3 -- API Robustness (Level 2 -> 3)

**Target:** Add retry logic with backoff, request deduplication, rate-limit tests, concurrent request tests.

**Changes:**
- `backend/tools/nea_client.py`: Added retry with exponential backoff on transient failures (429, 5xx, timeouts). Max 3 retries with 1s/2s/4s delays. Non-retriable 4xx errors fail immediately.
- `backend/tools/inference_client.py`: Added request deduplication via `_in_flight` dict mapping SHA-256 hash of (call_type, system, user_content) to asyncio Future. Concurrent identical calls share one LLM request. Errors propagate to all waiters. Cleanup guaranteed via `finally`.
- `backend/tests/test_api_robustness.py` (NEW): 12 tests in 3 classes:
  - `TestNEARetry` (6 tests): 429 retry, 500 retry, exhaust retries, no retry on 4xx, timeout retry, backoff delay verification
  - `TestInferenceDedup` (4 tests): concurrent dedup, different calls not deduped, error propagation, cleanup
  - `TestRateLimitHandling` (2 tests): 429 error message, cache prevents repeated calls

**Measurements before:** No retry logic, no dedup, 0 rate-limit/concurrent tests, 137 backend tests
**Measurements after:** Retry with backoff, request dedup, 12 robustness tests, 149 backend tests

**Regression check:** PASS (149/149 backend tests; 71/71 frontend tests; build 443 KB)
**Delta:** +1 (level 2 -> 3)
**Aggregate:** 28/40

---

