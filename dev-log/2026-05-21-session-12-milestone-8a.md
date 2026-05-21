# Milestone 8A -- ChromaDB Production Fix

**Date:** 2026-05-21
**Type:** Production deployment fix
**Branch:** main
**Tests:** 96/96 (no change)
**Build:** Zero TS errors, 478 KB JS bundle
**Regressions:** 0

---

## Starting State

| Metric | Value |
|--------|-------|
| Tests | 96/96 |
| Bundle | 434 KB |
| Production | Backend deployed on Render, frontend on Vercel |
| Problem | First search request on Render times out — ONNX embedding model (~80MB) downloaded at query time, not cached |

### Root cause

`DefaultEmbeddingFunction` (chromadb built-in, all-MiniLM-L6-v2 via ONNX runtime) downloads
the model on first use. On Render's ephemeral filesystem, this happens on every fresh deploy.
The `chroma_db/` vector data was committed to git as a workaround, but the model binary was not.

---

## Fix: Pre-download ONNX model during Render build phase

### Step 1 -- `backend/nixpacks.toml`

Added `[phases.build]` section with two commands:
1. `pip install -r requirements.txt`
2. Python one-liner that imports `DefaultEmbeddingFunction`, calls `ef(['warmup'])`, forcing
   the 80MB model download during the BUILD phase (cached in deployment image).

### Step 2 -- `backend/rag/vector_store.py`

Added `warmup()` method:
```python
def warmup(self) -> None:
    self._ef(["warmup"])
```
Triggers model load at startup. Instant if model already cached from build phase.

### Step 3 -- `backend/main.py`

Modified `lifespan()` to call `vs.warmup()` immediately after `VectorStore()` instantiation.
Production seeding remains disabled (`ENVIRONMENT=production` guard) to prevent startup timeout.

---

## Verification

```
curl https://sg-hawker-hunt.onrender.com/api/health
→ {"status":"ok","orchestrator":"ready",...}

POST /api/search {"query":"laksa"}
→ 5 agent_update events + 1 result event with 10 ranked stalls
→ No timeout, SSE streaming works immediately
```

---

## Files changed

| File | Change |
|------|--------|
| `backend/nixpacks.toml` | Added `[phases.build]` with model pre-download command |
| `backend/rag/vector_store.py` | Added `warmup()` method |
| `backend/main.py` | Call `warmup()` in lifespan startup |
