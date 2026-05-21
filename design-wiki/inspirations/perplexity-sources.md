---
source: Perplexity
category: agent-ux
status: pending
last_applied: ~
patterns_total: 3
patterns_applied: 0
---

## What they do well

Perplexity makes AI reasoning transparent and trustworthy. Source citations appear inline while you read the answer — not buried in footnotes. The full reasoning chain is available but collapsed by default, so casual users get a clean answer while power users can drill into the thinking. The agent trace is structured into named blocks with clear visual separation, not a wall of text.

## Patterns — extracted for Hawker Hunt

### perplexity-01: Inline source citations
- Status: [ ] pending
- Description: While reading the AI's answer, source references appear as small superscript numbers (NEA data^1, Google Reviews^2). Clicking a citation highlights the source. This builds trust by showing where each claim comes from.
- Hawker Hunt translation: In the reasoning text on ResultCard, add inline markers for data sources: "Grade A (NEA)", "4.5 stars (Google)", "Michelin 2025". These are already partially present in some reasoning strings from the backend — make them visually distinct with a subtle background highlight or superscript style.

### perplexity-02: Collapsible reasoning
- Status: [ ] pending
- Description: The default view shows a concise 2-3 sentence summary. "Show full reasoning" expands to reveal the complete chain. This serves both casual users (quick answer) and power users (full transparency).
- Hawker Hunt translation: On ResultCard, show only the first sentence of `reasoning` by default. Add a "Show reasoning" toggle that expands to the full text with a smooth height animation. The current italic block-quote style works well for the expanded state.

### perplexity-03: Structured agent trace blocks
- Status: [ ] pending
- Description: The reasoning trace is displayed as named, visually distinct blocks: "Searching", "Reading sources", "Synthesising". Each block has a header, content, and completion indicator. Not a flat log.
- Hawker Hunt translation: The current AgentPanel already groups traces by agent name with headers. Enhance by adding completion checkmarks per block (not just at the end), and a subtle progress indication within each block. The Warp-terminal aesthetic is already strong — just add block-level status.

## What NOT to copy

- Chat interface / follow-up questions: We're a single-query search, not a conversation.
- Web search integration: We have specific data sources, not general web search.
- Copy-to-clipboard for answers: Not useful for food recommendations.
