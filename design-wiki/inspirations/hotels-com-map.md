---
source: Hotels.com
category: map-interaction
status: partial
last_applied: 2026-05-21
patterns_total: 5
patterns_applied: 3
---

## What they do well

Hotels.com's map search view is a masterclass in spatial browsing. The map and listing cards are always visible side-by-side. Clicking a card highlights the corresponding map pin (and vice versa) — the user never loses spatial context. Detail panels slide in from the side instead of navigating to a new page, keeping the map visible. Distance context ("X km from city centre") and contextual callouts ("Popular area") give the user confidence in their choice.

## Patterns — extracted for Hawker Hunt

### hotels-01: Slide-in detail panel on card/pin click
- Status: [x] applied
- Description: Clicking a listing opens a rich detail panel that slides in from the right (desktop) or bottom (mobile), without navigating away from the results view. The map stays visible behind it.
- Hawker Hunt translation: Clicking a result card or map pin opens a `StallDetailPanel` with stall name, centre, all badges, full reasoning, standout quote, price range, best time to visit, and a Google Maps link. Framer Motion slide from right on desktop, sheet from bottom on mobile.

### hotels-02: Bidirectional card-to-pin selection sync
- Status: [x] applied
- Description: Hovering or clicking a listing card highlights the corresponding map pin with a scale-up animation. Clicking a map pin scrolls the list to the matching card and highlights it. The two views are always in sync.
- Hawker Hunt translation: `App.tsx` maintains a `selectedKey` state. `ResultCard` emits `onSelect(key)` on click. `HawkerMap` accepts `selectedKey` prop — the matching marker scales up and opens its popup. Clicking a map marker calls `onMarkerClick(key)` which scrolls the results list to the matching card.

### hotels-03: Distance context labels
- Status: [ ] pending
- Description: Each listing shows "X km away" with a small map icon, plus contextual nearby landmarks ("Top attractions nearby"). This grounds the user spatially without requiring them to check the map.
- Hawker Hunt translation: Show "X.X km away" prominently on each ResultCard (already partially done). Add "Near [landmark]" when location data is available. Could use the centre name as the landmark reference.

### hotels-04: Contextual callout banner
- Status: [x] applied
- Description: A banner at the top of results provides time-aware context ("Most popular time to visit", "Peak season — book early"). This primes user expectations.
- Hawker Hunt translation: When `time_context` from the orchestrator is not "any", show a banner: "It's lunchtime — lunch stalls ranked first" or "Dinner hour — evening favourites highlighted". Uses the existing time_context data from the backend.

### hotels-05: Rich amenity highlights as inline chips
- Status: [ ] pending
- Description: Key amenities are shown as small inline chips (wifi, pool, parking) rather than buried in a details page. Scannable at a glance.
- Hawker Hunt translation: Show key attributes as inline chips on ResultCard: cuisine type, price range, "Queue: short/long", best time. These complement the existing status badges.

## What NOT to copy

- Photo carousels: We don't have stall photos (no image data source).
- Save/wishlist functionality: Out of scope for V1.
- Price comparison across dates: Not applicable to hawker food.
