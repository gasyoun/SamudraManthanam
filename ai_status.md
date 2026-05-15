# Samudra Manthanam — AI Status

## Current Sprint: Hardening & Operational Readiness
**Status:** 🏗️ IN PROGRESS

### Phase 1: Reliable Boot & Basic Safety (P0)
- [x] **Task 1.1: Python 3.11 Compatibility**: Fixed nested f-strings and missing typing imports. Verified with `compileall`.
- [x] **Task 1.2: Morphological SSE Typo**: Fixed `request.mode` bug in search router. Added regression test.

### Phase 2: Hermetic Testing (P1)
- [x] **Task 2.1: Remove Ad Hoc Scripts**: Moved `test_search.py` and `test_services.py` to `web/scripts/` to avoid pytest collection.
- [x] **Task 2.2: Tiny SQLite Fixture DB**: Created `conftest.py` with a temporary DB fixture. Centralized settings in `settings.py` for easy overriding. Tests are now hermetic.
- [ ] **Task 2.3: Split Full-Corpus Tests**: Mark tests that can run against the full corpus with a `corpus` marker.
### Production Stabilization & Gemini Flash Implementation
**Status:** ✅ COMPLETED

- **Phase 1: Search Quality Baseline**: Created `test_golden_queries.py`, codified search semantics.
- **Phase 2: Web Result UX Improvements**: Improved header summary, zero-result handling, and source selection UI.
- **Phase 3: Stem/Root Lookup Polish**: Transparency in headers, highlighting variants, script consistency.
- **Phase 4: Cleanup & Final Handoff**: Pydantic V2 migration, orphan removal, final verification.

## Technical Debt / Known Issues
- **Optimization**: Regex search remains a full-table scan in Python.
- **Tests**: Default tests still require a 521MB local DB (planned fix in Phase 2).

