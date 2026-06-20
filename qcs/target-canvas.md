# QCS Target State Canvas

Ten quality dimensions, each scored 1–5. Current baseline: 24/40, target: 40/40.

| # | Dimension | Current | Target | Gap | Rubric |
|---|-----------|:---:|:---:|:---:|--------|
| 1 | Frontend test coverage | 1 | 4 | 3 | [rubrics/frontend-tests.md](rubrics/frontend-tests.md) |
| 2 | Design pattern coverage | 2 | 4 | 2 | [rubrics/design-patterns.md](rubrics/design-patterns.md) |
| 3 | Information architecture | 2 | 4 | 2 | [rubrics/information-architecture.md](rubrics/information-architecture.md) |
| 4 | API robustness | 2 | 4 | 2 | [rubrics/api-robustness.md](rubrics/api-robustness.md) |
| 5 | Backend test coverage | 3 | 4 | 1 | [rubrics/backend-tests.md](rubrics/backend-tests.md) |
| 6 | Accessibility (WCAG 2.1) | 3 | 4 | 1 | [rubrics/accessibility.md](rubrics/accessibility.md) |
| 7 | UI polish & delight | 3 | 4 | 1 | [rubrics/ui-polish.md](rubrics/ui-polish.md) |
| 8 | Performance | 3 | 4 | 1 | [rubrics/performance.md](rubrics/performance.md) |
| 9 | Data quality | 3 | 4 | 1 | [rubrics/data-quality.md](rubrics/data-quality.md) |
| 10 | Error resilience | 3 | 4 | 1 | [rubrics/error-resilience.md](rubrics/error-resilience.md) |

## Scoring rules

- Each level has concrete, verifiable criteria in the rubric file
- A dimension is at level N only when ALL criteria for level N are met
- Levels are cumulative: level 3 requires all of level 2 criteria plus level 3 criteria
- Automated measurements are preferred; LLM-assessed dimensions scored every 3 iterations
