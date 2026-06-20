# Accessibility (WCAG 2.1) — Rubric

## Level 1
- No ARIA attributes
- No keyboard navigation
- No reduced-motion support

## Level 2
- Basic ARIA labels on interactive elements
- Some keyboard navigation

## Level 3 (Current)
- ARIA labels on all interactive elements (search, cards, map, filters)
- Keyboard navigation (Tab, Enter, Space, Escape)
- `prefers-reduced-motion` respected globally + in TypewriterText
- Focus-visible rings on interactive elements
- `aria-live="polite"` on agent panel
- Detail panel is ARIA dialog with modal

## Level 4 (Target)
- WCAG 2.1 AA compliance (contrast ratios, target sizes)
- Skip-to-content link
- Landmark regions (`<main>`, `<nav>`, `<aside>`)
- Screen reader tested (VoiceOver audit with zero blockers)
- Colour not sole indicator of state (icons + text accompany colour)

## Level 5
- WCAG 2.1 AAA compliance where feasible
- axe-core automated audit in CI with zero violations
- High contrast mode support
- Text scaling up to 200% without layout break
