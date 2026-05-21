---
source: Linear
category: information-density
status: pending
last_applied: ~
patterns_total: 5
patterns_applied: 0
---

## What they do well

Linear achieves extraordinary information density without feeling cluttered. The secret is a strict opacity hierarchy: primary content at 100%, secondary at 60%, tertiary at 40%. Borders are 1px at 10-15% opacity — present but nearly invisible. Numbers use tabular alignment so columns of data feel structured. Keyboard shortcuts are first-class. Activity indicators (pulsing dots, subtle progress bars) communicate system state without demanding attention.

## Patterns — extracted for Hawker Hunt

### linear-01: Tabular number alignment
- Status: [ ] pending
- Description: All numeric data (distances, ratings, scores) is rendered with `font-variant-numeric: tabular-nums`. Columns of numbers align perfectly without manual spacing.
- Hawker Hunt translation: Apply `.tabular` class to all numeric displays: distances, ratings, review counts, scores. Already partially done in ResultCard — extend to map popups and detail panel.

### linear-02: Opacity-based text hierarchy
- Status: [ ] pending
- Description: Three tiers of text opacity: primary (100%), secondary (60%), tertiary (40%). No colour changes needed — just opacity creates a clear visual hierarchy.
- Hawker Hunt translation: Audit all text in ResultCard and detail panel. Stall name = 100% (foreground). Centre name, reasoning = 60% (muted). Metadata labels, timestamps = 40% (subtle). The existing token system supports this — ensure consistent application.

### linear-03: Ultra-subtle borders
- Status: [ ] pending
- Description: Borders are 1px at 10-15% opacity. Never thick, never coloured. They separate content zones without drawing attention.
- Hawker Hunt translation: Audit all card and panel borders. Ensure they use `border-border` (which maps to the 10-15% opacity tokens). Remove any thick or coloured borders. The existing dark theme tokens already support this.

### linear-04: Keyboard-first navigation
- Status: [ ] pending
- Description: j/k keys navigate between items. Enter opens the selected item. Escape closes panels. Arrow keys move through lists. All without touching the mouse.
- Hawker Hunt translation: Add keyboard navigation to result cards: j/k to move selection up/down, Enter to open detail panel, Escape to close panel. Visual focus indicator follows keyboard selection.

### linear-05: Activity indicators
- Status: [ ] pending
- Description: Subtle pulsing dots indicate live activity. Progress is shown as a thin bar, not a spinner. State changes are communicated through micro-animations, not text.
- Hawker Hunt translation: Replace the blinking cursor in AgentPanel with a thin progress bar or pulsing dot that's more Linear-like. Add a subtle "live" indicator when agents are streaming. The existing `animate-pulse` on the open/closed badge is a good start.

## What NOT to copy

- Dense table views: Our data is too varied for rigid tables.
- Keyboard shortcut overlay (Cmd+K): Overkill for a food search app.
- Multi-select and bulk actions: Not applicable.
