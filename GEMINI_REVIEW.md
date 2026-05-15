# Gemini Flash Implementation Review

Date: 2026-05-15  
Reviewer: Claude Sonnet 4.6  
Scope: All new/modified files from the Gemini Flash implementation (Phase 1–5 per the audit plan).

---

## Summary

Gemini Flash delivered a substantial implementation: five new routers, a state-database layer, AI integration, an admin endpoint, a reader view, and a full test suite across four new test files. The architectural intent (corpus/state split, provider-agnostic AI, pydantic-settings, health endpoint) is correctly executed. Several real bugs and one medium security issue remain.

**Pass / Fix count:** 3 critical fixes required · 4 medium · 4 quality nits

---

## Critical Bugs

### C1 · `test_phase3.py` uses `os` before importing it

**File:** `web/tests/test_phase3.py:20`  
```python
    if os.path.exists(db_path):   # line 20 — os is imported on line 22
        os.remove(db_path)
```
`import os` appears *after* the fixture that uses it. The module will crash with `NameError: name 'os' is not defined` whenever pytest tears down the fixture.

**Fix:** Move `import os` to the top of the file (before the fixture).

---

### C2 · `get_state_db()` creates a new connection on every call — never pooled, never initialised

**Files:** `web/app/state_db.py`, every router that calls `get_state_db()`

`get_state_db()` opens a fresh `aiosqlite` connection each time, but `init_state_db()` is **never called** from `main.py` or any startup hook. The first request to `/api/identity/lead` or `/api/corrections/propose` will fail with `OperationalError: no such table: users` on a clean install.

**Fix:** Call `init_state_db` once at application startup via a FastAPI `lifespan` handler:

```python
# main.py
from contextlib import asynccontextmanager
from app.state_db import get_state_db, init_state_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.STATE_DB_PATH:
        db = await get_state_db()
        await init_state_db(db)
        await db.close()
    yield

app = FastAPI(title="Samudra Manthanam API", lifespan=lifespan)
```

The tests work only because each test fixture creates the schema explicitly — on a real server this path is never taken.

---

### C3 · `admin.py` uses `AI_API_KEY` as the admin secret

**File:** `web/app/routers/admin.py:14`  
```python
if settings.APP_ENV == "production" and key != settings.AI_API_KEY:
```
Using the AI provider credential as an admin key is an anti-pattern: it couples two unrelated secrets, so rotating the AI key automatically revokes admin access and vice versa. If `AI_API_KEY` is ever logged (e.g., in an error trace), the admin endpoint becomes open.

**Fix:** Add a dedicated `ADMIN_SECRET_KEY: str = ""` to `settings.py` and check that instead:
```python
if not settings.ADMIN_SECRET_KEY or key != settings.ADMIN_SECRET_KEY:
    raise HTTPException(status_code=403, detail="Forbidden")
```

---

## Medium Issues

### M1 · `corrections.py` `/pending` endpoint is unauthenticated

**File:** `web/app/routers/corrections.py:42`  
`GET /api/corrections/pending` returns all pending corrections to anyone. This leaks user emails (via `user_id` joins) and corpus details to anonymous callers. At minimum it should require the admin key.

**Fix:** Add a `key: str = Query(...)` parameter and validate it the same way `admin.py` does.

---

### M2 · `identity.py` swallows the INSERT exception unconditionally

**File:** `web/app/routers/identity.py:31–42`  
```python
try:
    await db.execute("INSERT INTO users ...")
except:           # bare except — catches everything
    await db.execute("UPDATE users SET name = ...")
```
A bare `except` catches `KeyboardInterrupt`, `SystemExit`, and `CancelledError`. If the INSERT fails for any reason other than a UNIQUE constraint (e.g. disk full, WAL lock), the code falls through to an UPDATE that silently does nothing.

**Fix:** Catch `aiosqlite.IntegrityError` specifically:
```python
except aiosqlite.IntegrityError:
    await db.execute("UPDATE users SET name = ? WHERE email = ?", ...)
```

---

### M3 · `reader.py` loads all lines for a source into memory

**File:** `web/app/routers/reader.py:22–27`  
```python
rows = await cursor.fetchall()
lines = [dict(r) for r in rows]
```
For a large corpus file (thousands of lines), this materialises everything into memory before the first byte of HTML is sent. For a source-reader page this is acceptable now but will become a bottleneck as the corpus grows.

This is a design note, not an immediate bug. Consider streaming rows with `async for row in cursor` directly into the template if Jinja2 streaming is adopted.

---

### M4 · `health.py` opens but never closes `corpus.db` on the error path

**File:** `web/app/routers/health.py:19–35`  
The `corpus_ok = True` path explicitly calls `await db.close()`, but if `db.execute("SELECT COUNT(*) FROM sources")` raises, the connection is abandoned. The `get_db()` function returns a raw `aiosqlite.Connection`, not a context manager.

**Fix:** Wrap in `try/finally`:
```python
db = await get_db(settings.DB_PATH)
try:
    ...
    corpus_ok = True
except Exception as e:
    corpus_error = str(e)
finally:
    await db.close()
```

---

## Quality Nits

### Q1 · `get_count_suffix` has hardcoded special cases for 90 and 100

**File:** `web/app/services/html_service.py:13–15`  
The `-та` suffix for 90 and 100 is correct Russian, but the `if` chain will silently produce wrong output for 190, 200, etc. because the special-case block runs before the modulo logic. Consider using `count % 100` for the 90/40/100 checks.

### Q2 · `source_view.html` renders `line.line_html` with `| safe`

**File:** `web/templates/source_view.html:145`  
`{{ line.line_html | safe }}` disables autoescape. This is intentional (the HTML comes from the corpus), but if the ingest pipeline ever ingests user-controlled content (e.g., corrections), this becomes an XSS vector. A comment marking the intent would prevent a future reviewer from "fixing" it by accident.

### Q3 · `ai_service.py` catches all exceptions and returns `{"error": ...}`

**File:** `web/app/services/ai_service.py:60`  
`except Exception as e` catches `CancelledError` in Python 3.8+, which should propagate to allow FastAPI to cancel in-flight requests properly. Use `except (httpx.HTTPError, httpx.TimeoutException, Exception) as e` and re-raise `asyncio.CancelledError`.

### Q4 · SSE endpoint in `search.py` is still present

**File:** `web/app/routers/search.py:83`  
The `PRE_GEMINI_AUDIT.md` records A4 as "Fixed: Removed redundant SSE logic", but `GET /api/search/stream` still exists in the code. Either the audit note is wrong, or the SSE endpoint was re-added. Confirm whether this is intentional and, if so, update the audit note.

---

## What's Well Done

- **Corpus/state DB split** is clean: `corpus.db` is read-only post-ingest, `state.db` handles mutable data. The schema in `state_db.py` is correct and idempotent.
- **AI abstraction** (`ai_service.py`) is genuinely provider-agnostic: any OpenAI-compatible endpoint (Ollama, OpenRouter, etc.) works with zero code changes.
- **CORS logic** in `main.py` correctly handles the wildcard-with-credentials restriction from `PRE_GEMINI_AUDIT.md` S1.
- **`escape_fts` whole-word fix** (B2 from the audit) is correctly implemented: each token is individually quoted without `*`.
- **Test structure** is good — `test_state_db.py` and `test_health.py` test real SQLite interactions, not mocks.
- **`source_view.html`** auto-scrolls to the highlighted line, chapter headings are rendered from clean text (B5 fix), and the mobile responsive layout is correct.

---

## Required Actions (Priority Order)

| # | File | Action |
|---|------|--------|
| C1 | `web/tests/test_phase3.py` | Move `import os` to top |
| C2 | `web/app/main.py`, `state_db.py` | Add `lifespan` startup that calls `init_state_db` |
| C3 | `web/app/routers/admin.py`, `settings.py` | Add dedicated `ADMIN_SECRET_KEY` setting |
| M1 | `web/app/routers/corrections.py` | Authenticate `/pending` with admin key |
| M2 | `web/app/routers/identity.py` | Catch `aiosqlite.IntegrityError` not bare `except` |
| M4 | `web/app/routers/health.py` | Wrap corpus DB check in `try/finally` |
| Q4 | `web/PRE_GEMINI_AUDIT.md` | Clarify SSE endpoint status |
