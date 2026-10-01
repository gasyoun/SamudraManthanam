_Created: 25-08-2026 · Last updated: 05-09-2026_

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

## Architecture Issues — Fixed (Phases 1-5)

### A1 · Morphological search writes to corpus.db
**Fixed:** `morph_cache` has been migrated to `state.db`. `corpus.db` is now strictly read-only.

### A2 · Phase 1 foundation not implemented
**Fixed:** `settings.py` uses `BaseSettings`, `state_db.py` handles persistent state, `/api/health` provides system diagnostics.

### A3 · settings is a mutable plain class
**Fixed:** Converted to `pydantic-settings` `BaseSettings`. Tests now use dependency injection or controlled overrides.

### A4 · SSE stream endpoint is architectural waste
**Partially addressed:** `GET /api/search/stream` remains in `web/app/routers/search.py` — it was retained intentionally to support future progress-bar UX for large corpora. The unified `dispatch_search` is now the canonical search path; the SSE endpoint delegates to it per-source. Whether to keep or remove it should be decided before the next release.

### A5 · No rate limiting on any endpoint
**Fixed:** Implemented `MAX_SCANNED_ROWS` and timeouts for regex searches. Global rate limiting deferred to VPS-level Nginx config as per target architecture.

### A6 · state.db has no backup strategy
**Fixed:** Added administrative `/api/admin/vacuum` and documented the state/corpus split for backup simplicity.

### A7 · Provider-agnostic AI abstraction
**Fixed:** Implemented a clean provider-agnostic `ai_service.py` supporting OpenAI-compatible local providers (Ollama).

---

## Code Quality — Fixed (Phases 1-5)

### Q1 · Dead import `asyncio`
**Fixed:** Removed from routers.

### Q2 · Stale hardcoded version
**Fixed:** Replaced with query to `corpus_meta`.

---

### Q3 · Magic constant 5000 scattered
**Fixed:** Centralized result limit management.

### Q4 · Circular import deferred
**Fixed:** Refactored `dispatch_service.py` to break the circular dependency.

### Q5 · regex search partial results have no signal
**Fixed:** Added `truncated` and `scanned_rows` to `search_metadata`.

### Q6 · Export URL exposes full query
**Fixed:** Export logic now includes metadata context within the generated HTML.

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

_Dr. Mārcis Gasūns_
