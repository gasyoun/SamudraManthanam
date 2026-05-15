# Changelog - Samudra Manthanam

All notable changes to this project will be documented in this file.

## [1.8.0] - 2026-05-15 (Samudra Manthanam Web Phase 1-5 Complete)
### Added
- **Centralized Settings**: Migrated to Pydantic-Settings with `APP_ENV` and CORS management.
- **State Database**: Decoupled mutable data (`state.db`) from the read-only corpus.
- **Scholarly Reader**: Implemented full-text viewing with chapter navigation and line highlighting.
- **AI Explanation Engine**: Context-aware AI analysis with scholarly system prompts and provider abstraction.
- **Identity & Corrections**: Lead capture system with consent tracking and correction proposal API.
- **Corpus Integrity**: Added `corpus_meta` for versioning and health endpoints for system diagnostics.
- **SEO & Operations**: Added `robots.txt`, `sitemap.xml`, and administrative `VACUUM` support.

### Fixed
- **Regex Safety**: Implemented row-scanning limits and metadata reporting to prevent CPU exhaustion.
- **CORS Hardening**: Enforced `ALLOWED_ORIGINS` filtering in production.
- **Export Metadata**: Added query, mode, and corpus version to standalone result pages.

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
- **Architecture Critique**: Added `ARCHITECTURE_CRITIQUE_AND_OPEN_QUESTIONS.md` to challenge proposed solutions, compare alternatives, and collect decision questions.
- **Documentation Index**: Added `DOCUMENTATION_INDEX.md` to separate current, supporting, and historical Markdown guidance for humans and Gemini Flash.
- **Target Architecture**: Added `TARGET_ARCHITECTURE.md` describing the VPS/no-Docker target architecture, `corpus.db`/`state.db` split, AI provider abstraction, identity, correction proposals, and corpus publication flow.
- **6-Month Roadmap**: Added `ARCHITECTURE_REVIEW_6_MONTH_ROADMAP.md` with phased plans for corpus/search engine, scholarly workbench, and research platform development.
- **Gemini Flash Phase Plans**: Split the implementation plan into short under-100-line phase files for foundation, search/reader, identity/corrections, AI, and deployment/operations.
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
