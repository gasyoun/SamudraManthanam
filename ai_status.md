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

