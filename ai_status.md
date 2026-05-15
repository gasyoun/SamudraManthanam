# Samudra Manthanam — AI Status

## Current Sprint: Hardening & Operational Readiness
**Status:** ✅ COMPLETED

### Phase 1: Reliable Boot & Basic Safety (P0)
- [x] **Task 1.1: Python 3.11 Compatibility**: Fixed nested f-strings and missing typing imports. Verified with `compileall`.
- [x] **Task 1.2: Morphological SSE Typo**: Fixed `request.mode` bug in search router. Added regression test.

### Phase 2: Hermetic Testing (P1)
- [x] **Task 2.1: Remove Ad Hoc Scripts**: Moved `test_search.py` and `test_services.py` to `web/scripts/` to avoid pytest collection.
- [x] **Task 2.2: Tiny SQLite Fixture DB**: Created `conftest.py` with a temporary DB fixture. Centralized settings in `settings.py` for easy overriding. Tests are now hermetic.
- [x] **Task 2.3: Split Full-Corpus Tests**: Marked golden queries with `corpus` marker. Added `pytest.ini` and environment toggle (`USE_REAL_CORPUS`) for running against the production DB.
### Phase 3: Stabilize Search Semantics (P1)
- [x] **Task 3.1: Document Search Contract**: Created `SEARCH_CONTRACT.md` defining token AND-logic and prefix matching.
- [x] **Task 3.2: Contract Regression Tests**: Added `tests/test_contract.py` verifying prefix matching and AND logic.
- [x] **Task 3.3: Implement Contracted Plain Search**: Updated `search_service.py` with prefix matching (`*`) in `escape_fts`.

### Phase 4: Optimization & Refactoring (P1)
- [x] **Task 4.1: Unified SSE Generator**: Refactored `search.py` to use a central `dispatch_service.py`.
- [x] **Task 4.2: Resource Limits for Regex**: Added a 5-second safety timeout to regex table scans.

### Phase 5: Cleanup & Validation (P0)
- [x] **Task 5.1: Final Acceptance Check**: Verified all 23 tests pass in hermetic environment.
- [x] **Task 5.2: Update Deployment Docs**: Updated `README.md` and `CLAUDE.md` with configuration and search contract details.

## Past Sprints
### Hardening & Operational Readiness
**Status:** ✅ COMPLETED
### Production Stabilization & Gemini Flash Implementation
**Status:** ✅ COMPLETED

- **Phase 1: Search Quality Baseline**: Created `test_golden_queries.py`, codified search semantics.
- **Phase 2: Web Result UX Improvements**: Improved header summary, zero-result handling, and source selection UI.
- **Phase 3: Stem/Root Lookup Polish**: Transparency in headers, highlighting variants, script consistency.
- **Phase 4: Cleanup & Final Handoff**: Pydantic V2 migration, orphan removal, final verification.

## Technical Debt / Known Issues
- **Optimization**: Regex search remains a full-table scan but is now protected by a 5-second timeout (Task 4.2).
- **Tests**: Hermetic tests are implemented (Phase 2); `corpus.db` is only used when `USE_REAL_CORPUS=1` is set.

---

## Pre-Gemini Flash Audit (2026-05-15)
**Status:** ✅ All critical bugs and security issues fixed. See `PRE_GEMINI_AUDIT.md` for full findings.

### Bugs Fixed
- [x] **B1 – Limit before Python filter**: SQL LIMIT now over-fetches when Python whole-word/case filter is active; final limit applied after filter.
- [x] **B2 – Whole-word multi-token broken**: `escape_fts` now quotes each token individually (no phrase wrapping); Python filter checks each word with `\b` independently.
- [x] **B3 – Groups sorted by source_id not sort_order**: `render_fragment` now preserves SQL insertion order via `dict.values()`.
- [x] **B4 – `<head>` filter dropped content lines**: Filter now matches only structural HTML-only lines via anchored regex.
- [x] **B5 – Chapter stored with raw HTML markup**: `remove_html_tags()` applied to H1 capture group before storing.

### Security Fixes
- [x] **S1 – CORS wildcard + credentials=True**: Changed to `allow_credentials=False`; comment marks Phase 1 ALLOWED_ORIGINS task.
- [x] **S2 – No max_length on query**: Added `max_length=1000` to `SearchRequest.query`.
- [x] **S3 – Bare except in render_standalone**: Changed to `except OSError`.
- [x] **S4 – CORPUS_PATH hard-coded Windows path**: Moved to `settings.CORPUS_PATH`; endpoint returns 503 when unconfigured, 400 for traversal (sanitisation runs first).

### Quality Fixes
- [x] **Q1 – Dead import `asyncio`**: Removed from `search.py`.
- [x] **Q2 – Stale hardcoded version "2026.05"**: Manifest now reads `corpus_meta` for version; omits field if table absent.

### Documentation
- [x] Added `PRE_GEMINI_AUDIT.md` with all 26 findings and fix status.
- [x] Added `STATUS: SUPERSEDED` banners to `WEB_PLAN.md`, `roadmap.md`, `gemini-implementation-plan.md`.
- [x] Added `PRE_GEMINI_AUDIT.md` and updated reading order in `DOCUMENTATION_INDEX.md`.

### Open for Gemini Flash Phase 1
- `settings.py` → convert to `pydantic-settings` `BaseSettings` with all env vars.
- Create `state_db.py` and schema.
- Create `/api/health` endpoint.
- CORS tightening with `ALLOWED_ORIGINS`.
- Move `morph_cache` to `state.db`.
- VPS deployment docs.

