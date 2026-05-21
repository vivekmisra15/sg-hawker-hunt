---
source: Zillow
category: map-interaction
status: partial
last_applied: 2026-05-21
patterns_total: 6
patterns_applied: 2
---

## What they do well

Zillow's map search is the gold standard for spatial browsing. The screen is split 50/50 between map and results — neither is hidden or secondary. Every map pin shows the key metric (price) colour-coded, so you can scan the map without clicking anything. The result grid uses a compact 2-column layout that maximises density. A floating control bar provides sort/filter without leaving the view. A "results in this area" counter updates as you pan the map.

## Patterns — extracted for Hawker Hunt

### zillow-01: Persistent 50/50 split pane
- Status: [ ] pending
- Description: Map and results list are always visible together after a search — no toggling, no hiding. Desktop: side-by-side. Mobile: stacked with a toggle.
- Hawker Hunt translation: After search completes, restructure `App.tsx` to show results and map in a persistent split layout on desktop. The agent panel becomes a collapsible sidebar or top bar. On mobile, keep the current stacked layout with the map below.

### zillow-02: Key stat labels on ALL map pins
- Status: [x] applied
- Description: Every Zillow pin shows the price in a colour-coded label. You can scan the entire map and understand the data without clicking.
- Hawker Hunt translation: Every map marker shows the hygiene grade letter (A/B/C/D) inside a circle colour-coded by grade: green for A, amber for B, red for C/D. This replaces the current rank-number markers. UNKNOWN grades show a grey dash.

### zillow-03: 2-column result card grid
- Status: [ ] pending
- Description: Results are displayed in a dense 2-column grid rather than a single-column list. Each card is compact but information-rich.
- Hawker Hunt translation: On desktop, show result cards in a 2-column grid layout. Each card is slightly more compact than the current full-width design. On mobile, fall back to single-column.

### zillow-04: Viewport-aware result counter
- Status: [ ] pending
- Description: "Showing 8 of 42 results in map view" updates as you pan/zoom. Tells the user there's more to explore.
- Hawker Hunt translation: Show "Showing X of Y results" counter that updates based on which results have map coordinates visible in the current viewport. This builds on the existing counter in ResultsList.

### zillow-05: Floating map controls
- Status: [ ] pending
- Description: "Re-centre" button and "Map/List" toggle float over the map as semi-transparent pills. They don't take up layout space.
- Hawker Hunt translation: Add a floating "Re-centre" button on the map that fits all markers back into view. On mobile, add a "Map/List" toggle pill.

### zillow-06: Filter bar with dropdowns
- Status: [x] applied
- Description: A horizontal filter bar sits between the search box and results. Dropdowns for Price, Type, Sort. Active filters show as filled pills with an X to remove.
- Hawker Hunt translation: Add a `FilterStrip` component between search and results with toggle pills: "Michelin only", "Halal", "Open now", "Grade A", "Under $5". Active: filled amber. Inactive: outlined. Client-side filtering over the existing results array.

## What NOT to copy

- Saved searches / alerts: Out of scope.
- Agent-based property tours: Different domain.
- Mortgage calculator: Not applicable.
- Street view integration: No stall-level street view data.
