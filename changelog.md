# Changelog - Samudra Manthanam

All notable changes to this project will be documented in this file.

## [1.7.0] - 2026-05-15 (Hardening & Operational Readiness)
### Added
- **Hermetic Test Suite**: Implementation of a tiny SQLite fixture database for fast, isolated CI/CD testing.
- **Search Contract**: Formalized search engine semantics in `SEARCH_CONTRACT.md`.
- **Prefix Matching**: Enabled `arjun*` matching by default for scholarly search.
- **Unified Dispatch**: Created `dispatch_service.py` to consolidate all search mode logic.
- **Resource Safety**: Added a 5-second timeout to regex table scans.

### Fixed
- **Python 3.11 Compatibility**: Resolved nested f-string syntax errors and missing typing imports.
- **Morphological SSE Bug**: Fixed progress tracking typo for morphological searches.
- **Architecture Cleanup**: Moved ad-hoc scripts to `web/scripts/` and centralized configuration in `settings.py`.

## [Unreleased]

### Added
- **User Documentation**: Created `use_cases.md` detailing scholarly and technical scenarios for the platform.
- **Production Automation**: Created `reindex.sh` to facilitate daily automated re-indexing via Docker.
- **Deployment Infrastructure**: Added `Dockerfile` and `docker-compose.yml` for containerized deployment.
- **Testing Suite**: Created `test_services.py` for automated backend validation.
- **Corpus Sync API**: Integrated `corpus_sync` router for legacy desktop app updates.
- **SSE Support**: Finalized server-sent events for search progress tracking.

### Fixed
- **Security**: Hardened XSS protection by refactoring search result header rendering into Jinja2 templates.
- **Regex Safety**: Added robust validation for regex patterns across all search endpoints.
- **Architecture**: Corrected Pydantic model field ordering and migrated to V2-native validators.
- **Search Logic**: Improved FTS5 tokenization to support intelligent diacritic-tolerant matching for Sanskrit.

## [1.6.0] - 2026-05-12 (Web Stabilization & Gemini Implementation)
### Added
- **Golden Query Suite**: Implemented `test_golden_queries.py` to ensure scholarly search quality.
- **Stem/Root Lookup Polish**: Enhanced morphological search with searched-stem transparency and variant highlighting.
- **UX Improvements**: Added "Selected Sources" count, refined zero-result messaging, and polished the search summary header.
- **Enhanced Observability**: Added plain-text (`line_text`) field to search results for automated quality verification.
- **Documentation**: Synchronized `ai_status.md` and `use_cases.md` with the new production-ready state.

### Changed
- Reorganized repository to include both legacy Pascal code and new Python web components.

---

## [1.5.1] - 2024-05-10 (Legacy Desktop)
### Added
- Parallel search optimization using `TAbstractThread`.
- Multi-word search dialog (`u_words.pas`).
- Automatic update mechanism via `UpdateChecker.pas` and `POUpdater.exe`.

### Fixed
- UTF-8 handling in source file previews.
- Highlight logic in exported HTML files.
