# Pre-Gemini Flash Audit

Date: 2026-05-15
Reviewer: Claude Sonnet 4.6

This document records every finding from the red-team review of all code and planning
documents produced before Gemini Flash begins Phase 1.

Each finding lists: location, description, severity, and fix status.

---

## Critical Bugs — Fixed

### B1 · Limit applied before Python-side filtering
**File:** `web/app/services/search_service.py`
**Problem:** SQL `LIMIT ?` ran before the Python whole-word / case-sensitive pass. If FTS5
returned 5000 candidates and 4900 failed the filter, the user received 100 results instead of
up to 5000. The contract promises limit applies to final results.
**Fix:** When Python filtering is needed, SQL now uses `min(limit*10, 50000)` to over-fetch,
and the limit is enforced after Python filtering with an early `break`.

### B2 · Whole-word filter broken for multi-token queries
**File:** `web/app/services/search_service.py`
**Problem (FTS5 side):** `escape_fts` with `whole_word=True` wrapped the entire term in one
FTS5 phrase query (`"svasti arjuna"`), which demanded adjacent tokens — phrase search, not
whole-word. Fix: each token is now individually quoted without `*` (`"svasti" AND "arjuna"`).
**Problem (Python side):** `\b{re.escape(q)}\b` applied to the full multi-word string `q`.
Word boundaries around the space character are not meaningful boundaries. Fix: each token in
`q` is now checked independently with `\b...\b`.

### B3 · render_fragment sorts groups by source_id instead of sort_order
**File:** `web/app/services/html_service.py`
**Problem:** After grouping results by source, the code did `sorted(grouped.keys())` which
sorted by the auto-increment primary key. If any source is re-ingested its id increases while
its sort_order stays the same, causing the displayed corpus order to diverge silently.
**Fix:** Groups are now taken from `grouped.values()` directly; Python 3.7+ dict preserves
insertion order, which mirrors the SQL `ORDER BY s.sort_order, cl.line_num`.

### B4 · `<head>` filter too broad in parse_html
**File:** `web/ingest/parse_html.py`
**Problem:** `if '<head>' in line.lower(): continue` dropped any corpus line containing the
substring `<head>` — including natural language like "the head of the monastery."
**Fix:** The filter now matches lines whose entire content is a structural HTML element
(`<html>`, `<head>`, `<body>` and their closing forms) using a regex anchored to the full line.

### B5 · Chapter heading stored with raw HTML markup
**File:** `web/ingest/parse_html.py`
**Problem:** `current_chapter = chapter_match.group(1)` stored the raw HTML content between
`<H1>` tags. A heading `<H1><b>Глава 1</b></H1>` stored `<b>Глава 1</b>` as the chapter name.
**Fix:** `remove_html_tags(chapter_match.group(1))` strips markup before storing.

---

## Security Issues — Fixed

### S1 · CORS wildcard origin with credentials=True
**File:** `web/app/main.py`
**Problem:** `allow_origins=["*"]` combined with `allow_credentials=True` is forbidden by the
CORS spec. Starlette raises `ValueError` in recent versions; older versions silently produce
invalid headers that browsers reject. Would have caused every authenticated request to fail the
moment cookies or magic-link sessions were added.
**Fix:** Changed to `allow_credentials=False`. Phase 1 must replace `allow_origins=["*"]` with
`ALLOWED_ORIGINS` from settings and set `allow_credentials=True` once specific domains are known.

### S2 · No max_length on query field
**File:** `web/app/models.py`
**Problem:** `query: str = Field(..., min_length=1)` had no upper bound. A 100 MB regex query
was accepted and compiled.
**Fix:** Added `max_length=1000`.

### S3 · Bare `except:` swallowing all exceptions in render_standalone
**File:** `web/app/services/html_service.py`
**Problem:** `except:` caught `SystemExit`, `KeyboardInterrupt`, `MemoryError`, and everything
else. A disk-full condition would silently produce an unstyled export with no log entry.
**Fix:** Changed to `except OSError:` for both the CSS and JS reads.

### S4 · CORPUS_PATH hard-coded to Windows-relative path, bypassing settings
**File:** `web/app/routers/corpus_sync.py`
**Problem:** `CORPUS_PATH = os.environ.get("CORPUS_PATH", "../Index/lib/x86_64-win64")` was a
module-level constant with a Windows-specific default that fails on any Linux VPS. It also
bypassed `settings`, so it could not be overridden in tests.
**Fix:** Moved to `settings.CORPUS_PATH` (default `""`). The `/file/` endpoint now returns 503
if `CORPUS_PATH` is not configured, and path traversal sanitisation still runs first (400).

---

## Architecture Issues — Not Code-Fixed (Gemini Phase 1+)

### A1 · Morphological search writes to corpus.db
**File:** `web/app/services/morph_service.py`
**Problem:** `morph_cache` writes and commits to `corpus.db` during live search requests.
`corpus.db` is intended to be a generated, read-mostly artifact replaceable by atomic publish.
Writing to it: (a) requires a read-write file handle at all times; (b) loses the accumulated
cache when `corpus.db` is swapped; (c) risks write contention with multiple uvicorn workers.
**Partial fix applied:** Cache write is now wrapped in `try/except` so a read-only `corpus.db`
or concurrency failure never breaks a search response.
**Gemini Phase 1 task:** Move `morph_cache` to `state.db`. The `morph_cache` schema in
`corpus.db` and in `TARGET_ARCHITECTURE.md` (state.db version with `created_at`, `refreshed_at`)
are already inconsistent and must be reconciled when `state_db.py` is created.

### A2 · Phase 1 foundation not implemented
The `GEMINI_FLASH_PHASE_01_FOUNDATION.md` tasks are not done:
- `settings.py` has only `DB_PATH` (now also `CORPUS_PATH`); missing `APP_ENV`,
  `STATE_DB_PATH`, `PUBLIC_BASE_URL`, `ALLOWED_ORIGINS`.
- `state_db.py` does not exist.
- `/api/health` endpoint does not exist.
- VPS deploy docs do not exist.
Gemini Flash starts with Phase 1.

### A3 · settings is a mutable plain class, not a validated config object
**File:** `web/app/settings.py`
The class has no type validation, no required-field enforcement, and is mutated directly by
tests (`settings.DB_PATH = db_path`). Phase 1 should convert to `pydantic-settings`
`BaseSettings` and use FastAPI `Depends` for DB injection so tests do not mutate globals.

### A4 · SSE stream endpoint is architectural waste
**File:** `web/app/routers/search.py`
`/api/search/stream` runs `dispatch_search` once per source (discarding results), reports counts
only, and is never called by the frontend (`search.js` uses only the POST endpoint). It should
be removed in Phase 2 unless rebuilt as the sole owner of background search jobs.

### A5 · No rate limiting on any endpoint
A single client can sustain 12 parallel regex requests, consuming all CPU. Add per-IP rate
limits (e.g., `slowapi`) at minimum on `/api/search` before any public deployment.

### A6 · state.db has no backup strategy
`state.db` will contain user accounts, consent records (legally required to retain), and
correction proposals. The corpus publish flow has backup logic; `state.db` has none. Design
backup/restore before any identity feature goes live.

### A7 · Provider-agnostic AI abstraction is premature (Phase 4)
The architecture plans a full provider framework before any AI feature exists. Ship one AI task
with one hardcoded provider first; extract the abstraction when a second provider is needed.

---

## Code Quality — Fixed

### Q1 · Dead import `asyncio` in search.py
**File:** `web/app/routers/search.py`
The only usage (`await asyncio.sleep(0.01)`) was commented out. Removed.

### Q2 · Stale hardcoded version `"2026.05"` in corpus_sync manifest
**File:** `web/app/routers/corpus_sync.py`
Replaced with a query to `corpus_meta` (returns `None` if the table does not exist yet).
The manifest now omits `version` unless `corpus_meta` has a `corpus_version` row.

---

## Code Quality — Not Fixed (Gemini Phase 2+)

### Q3 · Magic constant 5000 scattered in multiple files
Appears in `models.py`, `search.py` SSE handler, `search.js`, and `SEARCH_CONTRACT.md`.
Define a shared constant in Phase 2.

### Q4 · Circular import deferred with in-function import
**File:** `web/app/services/morph_service.py:91`
`from app.services.search_service import search_plain` is inside the function body to avoid
a circular dependency. The structural problem (`morph_service` calling `search_service` which
imports from `morph_service`) needs a clean separation in Phase 2.

### Q5 · regex search partial results have no signal
**File:** `web/app/services/search_service.py`
When the 5-second timeout fires, `search_regex` returns partial results with no indication of
truncation. Add a `truncated` flag to `search_metadata` (Phase 2 Task 2.2).

### Q6 · Export URL exposes full query in browser history and server logs
**File:** `web/static/search.js`
GET parameters appear in proxy access logs and browser history. Use a POST form or short-lived
token before any privacy-sensitive deployment.

---

## Documentation Risk — Addressed

The DOCUMENTATION_INDEX.md already marks old planning files as historical. The remaining risk
is that Gemini Flash reads `WEB_PLAN.md`, `roadmap.md`, or `gemini-implementation-plan.md` and
treats them as current instructions. A `STATUS: SUPERSEDED` header has been added to each of
those three files (see separate edits).

---

## Gemini Flash Starting State

After this audit:
- All B* and S* findings are fixed.
- Tests: 19/19 pass (hermetic).
- Phase 1 foundation tasks remain fully open for Gemini Flash.
- The most important Phase 1 items: `settings.py` → `BaseSettings`, `state_db.py`,
  `/api/health`, CORS tightening, `morph_cache` migration.
