# Performance — Rubric

## Level 1
- No build optimisation
- Single monolithic bundle

## Level 2
- Vite production build configured
- Bundle < 1MB

## Level 3 (Current)
- Bundle ~478KB JS (excluding Leaflet CSS)
- No lazy loading or code splitting
- No image optimisation pipeline

## Level 4 (Target)
- Code splitting: map component lazy-loaded
- Route-based splitting if applicable
- Bundle < 350KB for initial load (excluding lazy chunks)
- Images: WebP with fallbacks, lazy loading
- Font subsetting (only used characters)

## Level 5
- Lighthouse Performance score > 90
- Service worker for offline shell
- Prefetching: preload likely next queries
- Bundle analysis in CI (size budget alerts)
- Critical CSS inlined, non-critical deferred
