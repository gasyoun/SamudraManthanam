# Changelog - Samudra Manthanam

All notable changes to this project will be documented in this file.

## [Unreleased] - Web Migration Phase

### Added
- **User Documentation**: Created `use_cases.md` detailing scholarly and technical scenarios for the platform.
- **Production Automation**: Created `reindex.sh` to facilitate daily automated re-indexing via Docker.
- **Deployment Infrastructure**: Added `Dockerfile` and `docker-compose.yml` for containerized deployment.
- **Testing Suite**: Created `test_services.py` for automated backend validation.
- **Corpus Sync API**: Integrated `corpus_sync` router for legacy desktop app updates.
- **SSE Support**: Finalized server-sent events for search progress tracking.

### Fixed
- **Data Ingestion**: Optimized `parse_html.py` to handle diverse HTML comment styles in source titles.
- **Frontend Logic**: Fixed `source_ids.append` bug in `search.js` and improved SSE error handling.
- **UI/UX**: Added smooth scrolling to search results and improved HTML injection.
- **Highlighting**: Optimized result highlighting regex to avoid matching inside HTML tags.
- **Backend Plumbing**: Fixed missing imports and router registration in `main.py`.

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
