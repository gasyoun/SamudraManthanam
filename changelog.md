# Changelog - Samudra Manthanam

All notable changes to this project will be documented in this file.

## [1.12.0] - 2026-05-15 (Funnel foundations — Systema Sanscriticum cross-link, OG, SEO)
### Added
- **`SYSTEMA_SANSCRITICUM_URL` setting + cross-link banner**: When set, a "Курс грамматики →" CTA appears in the navbar (index) and source view header. Distinct `utm_medium` per placement (`navbar` vs `source_view`) so analytics can attribute conversions by surface. Hidden cleanly when the env var is empty.
- **Open Graph / Twitter / VK link-preview meta tags** on `/` and `/sources/{id}` — `og:title`, `og:description`, `og:url`, `og:type`, `og:locale=ru_RU`, plus Twitter Card. Telegram and VK link shares now render as proper preview cards instead of bare URLs.
- **Sitemap expansion**: `/sitemap.xml` now lists every source page (`/sources/{id}`) so search engines can index the corpus. Uses `PUBLIC_BASE_URL` for absolute URLs when set. `robots.txt` points at the absolute sitemap URL.
- **Site-wide description setting** (`SITE_DESCRIPTION`) drives meta description + OG description with a single source of truth.
- **Telegram username on lead capture**: optional `@username` field added to the form and `users.telegram_username` column. Migration is idempotent — existing deploys gain the column on next startup.
- **UTM attribution capture**: `utm_source` / `utm_medium` / `utm_campaign` captured from URL on page load, persisted in `sessionStorage`, attached to lead submissions, and stored in `users` columns. First-touch attribution (UTM only writes on INSERT; updates preserve original values).
- **Social share buttons** (Telegram, VK, WhatsApp) on every citation result — pre-fill text + permalink, open in popup. Brand-coloured letters (TG / VK / WA) for unambiguous identification.
- **`test_funnel.py`**: 8 new tests covering sitemap contents, OG tag presence on both routes, cross-link banner visibility under different `SYSTEMA_SANSCRITICUM_URL` states, UTM tagging.
- **`test_phase3.py`**: 2 new tests verifying lead capture persists telegram_username + UTM, and that legacy clients omitting the new fields still succeed.

### Fixed
- **`TemplateResponse` signature**: Migrated `/` route to the FastAPI keyword-arg form (`request=`, `name=`, `context=`) matching the rest of the codebase. The old positional form was triggering a Jinja2 cache-key error on dict contexts.

## [1.11.1] - 2026-05-15 (Search URL popstate)
### Fixed
- **Browser back/forward now re-runs the search**: `window.addEventListener('popstate', restoreFromUrl)` wires the existing permalink restore logic to browser history navigation. Previously, back/forward changed the URL but left stale results on screen.

## [1.11.0] - 2026-05-15 (Track C — No-Docker VPS Deployment)
### Added
- **`DEPLOYMENT.md`**: Step-by-step VPS setup guide covering prerequisites, directory layout, venv creation, `.env` configuration, initial corpus build, systemd service install, nginx reverse proxy, HTTPS via certbot, cron-based publish automation, rollback procedure.
- **`deploy/samudra.service`**: Ready-to-install systemd unit file — uvicorn on `127.0.0.1:8000`, `EnvironmentFile` for secrets, `PrivateTmp`, 2-worker default.
- **`deploy/samudra.nginx`**: nginx site config — static files served directly with `expires 7d`, proxy pass to uvicorn with SSE-safe `proxy_buffering off` and 120 s read timeout.
- **`web/scripts/smoke_check.py`**: Standalone post-publish health check — verifies DB exists, queries source/line counts and corpus version, exits 1 if below `--min-sources`. Safe for cron or monitoring scripts.

## [1.10.0] - 2026-05-15 (Track A — Corpus Publication Workflow)
### Added
- **`web/ingest/validate.py`**: `ValidationReport` dataclass + `validate_corpus()` — checks manifest existence, duplicate entries, missing files, and malformed/absent title comments. Errors block publish; missing titles are warnings only.
- **`web/ingest/publish.py`**: Atomic publish pipeline with six guarded steps: validate → ingest into temp DB → `PRAGMA integrity_check` → smoke-check row counts → timestamped backup → `Path.replace()` atomic swap. Also exposes individual helpers (`integrity_check`, `smoke_check`, `do_backup`, `atomic_swap`) for scripting. CLI via `python ingest/publish.py --help`.
- **`reindex.sh` (rewritten)**: No-Docker VPS-friendly shell script; drives `publish.py` via env vars (`CORPUS_PATH`, `DB_PATH`, `NEXT_DB_PATH`, `BACKUP_DIR`, `VENV`, `MIN_SOURCES`). Activates virtualenv if `VENV` is set.
- **`web/tests/test_publish.py`**: 12 hermetic tests covering validate_corpus (ok / no-manifest / missing-file / duplicate / no-title), integrity_check (ok / corrupt), smoke_check, do_backup (creates file / missing source), and atomic_swap (replace / fresh install).

## [1.9.1] - 2026-05-15 (Scholarly Workbench — Track B, continued)
### Added
- **Export result count**: Standalone HTML export now shows "Найдено: N записей" in the metadata header.
- **Export live search link**: "← Открыть в поиске" link in the export header reconstructs the full permalink and links back to the live app with all original query parameters pre-filled.

### Fixed
- **Morph cache migrated to state.db**: `morph_cache` moved from `corpus.db` to `state.db` — corpus DB is now strictly read-only post-ingest as intended. `expand_word` no longer writes to the corpus connection.
- **Morph logging**: `print()` error output replaced with `logging.warning()` throughout `morph_service.py`.
- **Morph graceful degradation**: Network failure always returns at least the input word with no crash; unset `STATE_DB_PATH` skips cache silently without error.

## [1.9.0] - 2026-05-15 (Scholarly Workbench — Track B)
### Added
- **Search permalink URLs**: URL bar now reflects every search (`?q=...&mode=...&cs=&ww=&src=`). Loading such a URL restores form state and re-runs the search automatically — searches are bookmarkable and shareable.
- **Context window** (`GET /api/search/context`): Returns up to 20 corpus lines surrounding any source/line pair. Each search result now has an expand toggle (≡/▲) that lazy-fetches ±5 lines on first open and shows them inline without leaving the page. Validated: `window` clamped 1–20 by FastAPI.
- **Citation copy button** (⎘): One-click clipboard copy of the stable anchor permalink for each result line. Falls back to `prompt()` when the Clipboard API is unavailable.
- **Anchor permalink route** (`GET /sources/{source_id}/anchor/{link_id}`): Stable URL for a corpus line identified by its `link_id` attribute (e.g. `/sources/1/anchor/1.10`). Redirects 302 to the reader with the highlight parameter set.

## [1.8.1] - 2026-05-15 (Post-Review Hardening)
### Fixed
- **Startup schema init**: `init_state_db` is now called via a FastAPI `lifespan` handler — on a clean install the first request to `/api/identity/lead` or `/api/corrections/propose` no longer fails with `OperationalError: no such table`.
- **Admin key decoupled from AI key**: `ADMIN_SECRET_KEY` is now a separate setting; `admin.py` no longer uses `AI_API_KEY` as a proxy secret.
- **Corrections `/pending` authenticated**: `GET /api/corrections/pending` now requires the admin key, preventing anonymous access to pending correction data.
- **Bare `except` narrowed in identity router**: `except:` replaced with `except aiosqlite.IntegrityError:` so disk-full and WAL-lock errors propagate correctly instead of being silently swallowed.
- **Health endpoint connection leak**: Corpus DB connection is now always closed in a `finally` block on both success and error paths.
- **`get_count_suffix` modulo fix**: Special cases for 90 and 40 now use `count % 100` so 190, 290, 140, 240, etc. produce correct Russian suffixes.
- **`CancelledError` propagation in AI service**: `asyncio.CancelledError` is re-raised before the general `except Exception` handler so FastAPI can cleanly cancel in-flight AI requests on client disconnect.
- **`test_phase3.py` import order**: `import os` was referenced before being imported, causing `NameError` on fixture teardown.
- **Audit doc corrected**: `PRE_GEMINI_AUDIT.md` A4 now accurately states that the SSE endpoint was retained intentionally rather than removed.

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
