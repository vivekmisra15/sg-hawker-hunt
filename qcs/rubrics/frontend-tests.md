# Frontend Test Coverage — Rubric

## Level 1 (Current)
- No test framework configured
- Zero component or hook tests

## Level 2
- Vitest + React Testing Library configured and working
- At least 5 component/hook tests passing
- Test script in `package.json`

## Level 3
- 15+ tests covering all major components and hooks
- Coverage measurement configured (c8 or istanbul via Vitest)
- Coverage > 40%

## Level 4 (Target)
- 30+ tests covering components, hooks, and integration scenarios
- Coverage > 65%
- Edge cases tested: error states, loading states, empty states
- SSE streaming hook tested with mock EventSource

## Level 5
- Coverage > 85%
- Snapshot tests for visual regression
- Accessibility assertions (axe-core integration)
- Performance assertions (render time budgets)
