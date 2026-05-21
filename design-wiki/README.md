# Design Wiki — Recursive UX Improvement Loop

This wiki drives product experience improvements through external design inspiration, not code quality heuristics.

## How it works

1. **Inspiration entries** live in `inspirations/`. Each entry describes a reference product and extracts specific patterns for Hawker Hunt.
2. The **design-wiki agent** (`.claude/agents/design-wiki.md`) reads all entries, scores patterns, implements the highest-impact ones, and documents results.
3. Each run **expands** the wiki by discovering sub-patterns from what was just built.
4. Run logs in `run-log/` track what was done and inform the next run's baseline.

## Adding a new inspiration

Create a markdown file in `inspirations/` with this format:

```markdown
---
source: ProductName
category: map-interaction | information-density | filtering | agent-ux
status: pending
last_applied: ~
patterns_total: N
patterns_applied: 0
---

## What they do well
[Description of the reference product's UX]

## Patterns — extracted for Hawker Hunt
### productname-01: Pattern title
- Status: [ ] pending
- Description: What the reference product does
- Hawker Hunt translation: How this applies to our app

## What NOT to copy
[Patterns that don't translate to our context]
```

## Running the agent

```
run design-wiki
```

The agent executes 3 cycles per run. Each cycle: SCAN → SCORE → EXECUTE → EXPAND → DOCUMENT.

## Pattern statuses

- `pending` — not yet implemented
- `partial` — started but incomplete
- `applied` — fully implemented and verified
