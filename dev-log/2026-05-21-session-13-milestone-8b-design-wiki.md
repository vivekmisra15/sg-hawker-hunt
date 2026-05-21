# Milestone 8B -- Design Wiki (Recursive UX Improvement Loop)

**Date:** 2026-05-21
**Type:** Feature + Design Wiki Run 01
**Branch:** main
**Tests:** 96/96 (no change -- frontend-only changes)
**Build:** Zero TS errors, 478 KB JS bundle
**Regressions:** 0

---

## Starting State

| Metric | Value |
|--------|-------|
| Tests | 96/96 |
| Bundle | 434 KB |
| Prior work | 3 RQA runs shipped 27 incremental improvements (a11y, caching, tests, perf). User wanted transformative UX changes, not just code quality. |

### Motivation

RQA improves code quality recursively but starts from the codebase — it only finds defects.
Design Wiki starts from **external inspiration** and finds gaps between what we have and what's
possible. The loop is recursive because each run discovers sub-patterns from what was just built.

---

## Part 1: Infrastructure

### Agent definition: `.claude/agents/design-wiki.md`

Protocol: 3 cycles per run, each cycle SCAN -> SCORE -> EXECUTE -> EXPAND -> DOCUMENT.
Scoring: User Delight x Feasibility x Differentiation (1-5 each).
Self-expanding: EXPAND phase discovers sub-patterns that feed back into the next run's backlog.

### Seed entries: `design-wiki/inspirations/`

| Entry | Patterns | Category |
|-------|----------|----------|
| `hotels-com-map.md` | 5 | map-interaction |
| `zillow-map-grid.md` | 6 | map-interaction |
| `linear-density.md` | 5 | information-density |
| `perplexity-sources.md` | 3 | agent-ux |
| **Total** | **19** | |

---

## Part 2: Design Wiki Run 01 -- 5 patterns implemented

### Cycle 1 -- Map interaction (highest delight)

**hotels-02: Bidirectional card-to-pin selection sync (Score: 14)**

Problem: Cards and map pins had no interaction. Clicking a card opened Google Maps in a new tab.

Fix:
- `App.tsx`: Added `selectedKey` state, `handleSelect` and `handleMarkerClick` callbacks
- `ResultCard.tsx`: `onSelect` prop replaces direct Google Maps open. `isSelected` adds accent
  border + ring. `data-key` attribute enables scroll targeting. `role` changed from `"link"` to `"button"`
- `HawkerMap.tsx`: `selectedKey` prop highlights matching marker (scale 34->42px, glow ring).
  `onMarkerClick` callback fires when pin clicked. Selected marker opens popup and map pans to it.
- `ResultsList.tsx`: When `selectedKey` changes (from map click), scrolls to matching card via
  `CSS.escape(selectedKey)` + `scrollIntoView({ behavior: 'smooth', block: 'center' })`

**zillow-02: Grade-coloured labels on ALL map pins (Score: 14)**

Problem: Map markers showed rank numbers (1, 2, 3...) in amber circles. No hygiene data visible
on the map without clicking.

Fix:
- `HawkerMap.tsx`: `makeMarkerIcon()` rewritten. Markers now show hygiene grade letter (A/B/C/D)
  inside a colour-coded circle: green (#16a34a) for A, amber (#d97706) for B, red (#dc2626) for
  C/D, grey (#737373) for UNKNOWN (shows dash). White text on coloured background.
- Selected marker: scales to 42px, adds 4px glow ring in grade colour at 25% opacity,
  border widens to 3px, z-index elevated.
- `markerKey()` function exported for use by other components.

### Cycle 2 -- Information richness

**hotels-01: Slide-in detail panel (Score: 13)**

Problem: No way to see full stall details without leaving the app (Google Maps link).

Fix: New `StallDetailPanel.tsx`:
- Desktop: slides from right edge, full height, max-w-md, border-left
- Mobile: sheet from bottom, 75vh, rounded-t-2xl, drag handle bar
- Content: rank badge circle, stall name/centre, all status badges, stats grid
  (distance/rating/score in `bg-background-subtle` cards), standout quote blockquote,
  full reasoning text, Google Maps CTA button (amber, full-width)
- Closes on: Escape key, outside click (50ms delay to avoid catching opening click), X button
- ARIA: `role="dialog"`, `aria-modal="true"`, `aria-label` with stall name
- Mobile backdrop: `bg-black/40` overlay behind panel

### Cycle 3 -- Filters + context

**zillow-06: Filter strip (Score: 12)**

Problem: No way to narrow down results without rephrasing the query.

Fix: New `FilterStrip.tsx`:
- 5 toggle pills: Michelin (star), Halal (crescent), Open now (dot), Grade A, Under $5
- Active: `bg-accent text-accent-foreground` with accent shadow
- Inactive: `bg-transparent border border-border text-muted`
- `aria-pressed` for accessibility
- Count indicator: "X of Y" shown when filters active
- `App.tsx`: `applyFilters()` function filters results client-side. Filtered array passed
  to both `ResultsList` and `HawkerMap` so map markers also update.

**hotels-04: Contextual time banner (Score: 12)**

Problem: Time-aware scoring happens in the backend but the user has no visibility into it.

Fix:
- `App.tsx`: `getTimeContext()` computes Singapore time (UTC+8) and returns a label:
  - Breakfast (6-11): "Breakfast time -- morning favourites ranked first"
  - Lunch (11-15): "It's lunchtime -- lunch stalls ranked first"
  - Dinner (17-21): "Dinner hour -- evening favourites highlighted"
  - Supper (21-3): "Supper time -- late-night spots ranked first"
- Rendered as an amber-tinted banner (`bg-accent/10 border-accent/20`) with clock emoji
- Animates in with Framer Motion height transition
- Only shown when results are present

---

## EXPAND phase -- 12 sub-patterns discovered

These feed into Design Wiki Run 02's backlog:

| Source | Sub-patterns |
|--------|-------------|
| hotels-01 (detail panel) | Swipe between stalls, share stall link, panel scroll memory |
| hotels-02 (card-pin sync) | Hover preview, smooth animated pan between distant markers |
| zillow-02 (grade pins) | Cluster overlapping markers at low zoom, cuisine label on hover |
| zillow-06 (filter strip) | Count badges per filter, animate transitions, persist to URL |
| hotels-04 (time banner) | Dismiss for session, click-to-filter action |

---

## Other changes

- `ResultCard.tsx`: reasoning text truncated to 2 lines (`line-clamp-2`) on card; full text
  available in detail panel. Previously showed all text on the card.
- `ResultsList.tsx`: empty state icon changed from emoji to SVG search icon (resolves
  RQA Run 03 carry-forward item).

---

## Files changed

| File | Change |
|------|--------|
| `.claude/agents/design-wiki.md` | **New** -- agent definition |
| `design-wiki/README.md` | **New** -- contributor instructions |
| `design-wiki/inspirations/hotels-com-map.md` | **New** -- 5 patterns (3 applied) |
| `design-wiki/inspirations/zillow-map-grid.md` | **New** -- 6 patterns (2 applied) |
| `design-wiki/inspirations/linear-density.md` | **New** -- 5 patterns |
| `design-wiki/inspirations/perplexity-sources.md` | **New** -- 3 patterns |
| `design-wiki/run-log/2026-05-21-run-01.md` | **New** -- run log |
| `frontend/src/App.tsx` | Rewritten -- selectedKey, filters, time banner, detail panel |
| `frontend/src/components/HawkerMap.tsx` | Rewritten -- grade pins, selectedKey, onMarkerClick |
| `frontend/src/components/ResultCard.tsx` | Modified -- onSelect, isSelected, line-clamp |
| `frontend/src/components/ResultsList.tsx` | Modified -- selectedKey, onSelect, scroll-to-card |
| `frontend/src/components/StallDetailPanel.tsx` | **New** -- slide-in detail panel |
| `frontend/src/components/FilterStrip.tsx` | **New** -- filter toggle pills |

---

## Carry-forward to Design Wiki Run 02

- zillow-01 (persistent 50/50 split pane) -- partially done, not true 50/50
- zillow-03 (2-column card grid) -- high feasibility
- zillow-05 (floating map controls) -- quick win
- perplexity-02 (collapsible reasoning with expand toggle)
- linear-04 (keyboard navigation j/k/Enter/Escape)
- 12 sub-patterns from Run 01 EXPAND phase
