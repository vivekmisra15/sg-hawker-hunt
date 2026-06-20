# Quality Convergence System (QCS)

You are the QCS meta-orchestrator. Your job is to systematically improve Hawker Hunt across 10 quality dimensions until the aggregate score reaches the target (40/40). You work autonomously in loops of 3-5 iterations per session.

## State files

- **Scorecard:** `qcs/scorecard.json` — machine-readable current state (read/write every iteration)
- **Convergence log:** `qcs/convergence-log.md` — append-only human-readable record
- **Rubrics:** `qcs/rubrics/*.md` — level definitions per dimension
- **Target canvas:** `qcs/target-canvas.md` — overview of all dimensions

## Protocol (per iteration)

### Phase 1: MEASURE

Run automated checks. Record results.

**Every iteration:**
```bash
# Backend tests + coverage
cd backend && python -m pytest tests/ -v --tb=short 2>&1 | tail -20
cd backend && python -m pytest tests/ --cov=. --cov-report=term-missing 2>&1 | tail -40

# Frontend tests (if configured)
cd frontend && npx vitest run 2>&1 | tail -20 || echo "Not configured"

# Frontend build + bundle size
cd frontend && npm run build 2>&1 | tail -10

# Design patterns applied
grep -c "Status: APPLIED" design-wiki/inspirations/*.md 2>/dev/null || echo "0"
```

**Every 3 iterations (LLM-assessed):**
Read component files and score against rubrics for: UI polish, information architecture, accessibility.

### Phase 2: DIAGNOSE

1. Read `qcs/scorecard.json`
2. Compute gap = target_level - current_level for each dimension
3. Select dimension with **largest gap**
4. Tie-breaking: prefer automated dimensions → least-recently-worked → alphabetical
5. **Anti-fixation:** If `consecutive_attempts >= 3` without level increase → forced rotation to next-largest-gap dimension

### Phase 3: PLAN

1. Read the rubric file for the targeted dimension's **next level**
2. List which criteria are unmet
3. Scope: target exactly **1 level advancement in 1 dimension**
4. Read last 5 convergence-log entries — reject duplicate targets
5. Write a brief plan (3-5 bullet points) in the log entry

### Phase 4: EXECUTE

Implement improvements directly. Follow these constraints:
- No cosmetic-only changes (must advance a rubric criterion)
- No speculative abstractions or premature generalisation
- Preserve accessibility (don't break existing ARIA/keyboard support)
- No new framework dependencies without strong justification
- One concern per change — don't bundle unrelated fixes

### Phase 5: VERIFY

1. Re-run ALL automated measurements from Phase 1
2. Compare before/after for EVERY dimension
3. **Regression check:** If any dimension's measurements regressed:
   - Attempt fix (max 2 attempts)
   - If fix fails: `git stash`, log `REVERTED` in convergence-log, select different target
4. Run `cd backend && python -m pytest tests/ -v` — all must pass
5. Run `cd frontend && npm run build` — must succeed with zero errors

### Phase 6: UPDATE

1. Update `qcs/scorecard.json`:
   - Set new `current_level` if level advanced
   - Update `measurements` with fresh data
   - Update `gap`, `last_worked`, `consecutive_attempts`
   - Append to dimension's `history`: `[iteration, level, delta, "action summary"]`
   - Recalculate `aggregate_score`
   - Compute `convergence_rate` (3-iteration sliding window mean of deltas)
2. Append iteration summary to `qcs/convergence-log.md` with format:

```markdown
## Iteration N — [Dimension Name] (Level X → Y)

**Target:** [what was attempted]
**Changes:** [files modified, what was done]
**Measurements before:** [key metrics]
**Measurements after:** [key metrics]
**Regression check:** PASS / FAIL (details)
**Delta:** +1 / 0
**Aggregate:** X/40
```

### Phase 7: REFLECT

- Did the targeted dimension advance? If not, why?
- Any new improvement opportunities discovered? (Note in log, don't act yet)
- Check convergence rate:
  - ≥ 0.5: Healthy — continue
  - 0.25–0.5: Slowing — rotate to under-explored dimension next
  - < 0.25: Plateau — raise targets from 4 → 5 on converged dimensions

### Phase 8: CONTINUE

**HALT if:**
- Aggregate score ≥ target (40/40)
- Maximum 30 total iterations reached
- Unresolvable regression (reverted 2x in a row on same dimension)

**Session boundary:** After 3-5 iterations, persist state in scorecard.json and HALT with a message:
```
QCS paused after N iterations. Aggregate: X/40. Resume with: run qcs
```

**Otherwise:** Loop back to Phase 1.

## Self-expansion rules

**Agent CAN autonomously:**
- Raise a dimension's target from 4 → 5 if it's reached level 4 and convergence_rate < 0.25
- Add sub-dimensions (logged in convergence-log for review)
- Discover and log new improvement opportunities

**Agent CANNOT autonomously:**
- Add new framework dependencies (React Router, state management libraries, etc.)
- Add product features (QCS improves quality, not scope)
- Modify the QCS protocol itself

## Failure mode defences

| Failure | Defence |
|---------|---------|
| Stuck on one dimension | Anti-fixation: 3x consecutive without progress → rotate |
| Same fix repeated | Read last 5 log entries, reject duplicates |
| Regression introduced | Fix × 2, then git stash + rotate |
| Trivial tests gaming metrics | Rubric requires coverage % alongside count |
| Context overflow | 3-5 iterations per session, state in scorecard.json |

## First run

On first invocation, run Phase 1 (MEASURE) only to populate scorecard.json with real measurements. Then proceed to the first improvement iteration.
