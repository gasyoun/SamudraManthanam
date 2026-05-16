# Changelog - Samudra Manthanam

All notable changes to this project will be documented in this file.

## [1.12.10] - 2026-05-16 (Bug sweep #10)
### Fixed
- **Ingest extracted useless page-style `link_id` for Mahābhārata Bhīṣma-parvan and Gītagovinda**: the original regex `re.search(r'id=...')` matched the *first* `id=` on the line, which for these older corpus files is the `<div class="range">` bibliographic-page identifier ("Махабхарата 2009 (VI): 9"), not a URL-routable verse anchor. As a result `corpus_lines.link_id` for ~1,337 Bhīṣma-parvan verses and all 289 Gītagovinda verses pointed at non-routable strings, preventing deep linking from search results into source view.
- New `_extract_link_id(line)` helper in `parse_html.py` with three priorities: (1) `id="..."` on a `class="citation_block"` div, (2) parse the trailing `CHAPTER. VERSE` (or `CHAPTER. VERSE_RANGE` for merged stanzas) from a `class="range" title="..."` element, (3) any `id="..."` on the line. Range-only lines whose title isn't parseable now return empty rather than leak the bibliographic page id.

### Added
- **`web/tests/test_parse_html.py`**: 10 unit tests covering Smirnov-style clean ids (regression), Bhīṣma-parvan + Gītagovinda fallbacks, range-merged stanzas (`1.3-6`), MBh-internal numbering for chapter 23+ (Gītā in Bhīṣma-parvan), chapter-title fallthrough, and the page-id-leak regression case.
- Smoke-verified on real corpus: Bhīṣma-parvan now yields 750 clean `X.Y` + 587 range-merged `X.Y-Z` anchors; Gītagovinda all 289 verses; Smirnov BhG unchanged at 701 anchors. 90/90 hermetic tests pass.

### Operator action required
- A re-ingest (`python -m ingest.ingest --corpus-path ... --db-path corpus.db`) is needed to repopulate `corpus_lines.link_id` with the new values. Existing search/source routes will then deep-link MBh and Gītagovinda verses correctly.

## [1.12.9] - 2026-05-16 (Bug sweep #8)
### Fixed
- **GET `/api/search/export` and `/api/search/stream` accepted unbounded `query`** while POST `/api/search` was capped at 1000 chars by Pydantic — inconsistent validation across the same logical input. A 60KB regex pattern through GET would slip past, eating CPU on `re.compile`. Both GET endpoints now use `Query(..., min_length=1, max_length=1000)`.

### Added
- **`test_api.py`**: 3 new regression tests — export rejects oversized + empty queries, stream rejects oversized query. 92/92 hermetic tests pass.

## [1.12.8] - 2026-05-16 (Bug sweep #7)
### Fixed
- **`test_health_ok` was a `pass` placeholder**: looked like a real test in the suite count but exercised nothing — gave false coverage for the `/api/health` happy path. Replaced with a real assertion that both DBs are reachable, `status=="ok"`, and `source_count >= 1`.
- **Lifespan never warned about missing or empty corpus DB**: `aiosqlite.connect` silently creates an empty SQLite file at `DB_PATH` if none exists, so a misconfigured deploy showed up as "search returns no results" with no clear diagnostic. Lifespan now probes `corpus.db` at startup and logs a clear warning if the file is missing, the `sources` table is empty, or the probe raises. The app still starts (corpus might be intentionally swapped in later), so this is a log-only signal — but the operator now sees the misconfig immediately.

## [1.12.7] - 2026-05-15 (Bug sweep #6 — operational hardening)
### Fixed
- **`lifespan` crashed the whole app if `init_state_db` failed**: a misconfigured `STATE_DB_PATH` (pointing at a directory, wrong permissions) used to abort startup, leaving uvicorn in a restart loop with no useful log. Now the handler catches, logs once with `logger.exception`, and continues — corpus search keeps working while operators fix the state DB; state-dependent endpoints surface clean 503s.
- **`lifespan` leaked the state-DB connection on init failure**: the open `db.close()` was after `init_state_db(db)` and never ran if init raised. Now `finally`-guarded.

### Added
- **`deploy/samudra.service` hardening directives**: `ProtectSystem=strict` with explicit `ReadWritePaths=/opt/samudra`, `ProtectHome=yes`, `ProtectKernel*=yes`, `NoNewPrivileges=yes`, `CapabilityBoundingSet=`, `RestrictNamespaces=yes`, `RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX`, `LockPersonality=yes`, `SystemCallFilter=@system-service`. Defense in depth if the FastAPI process is compromised.
- **`deploy/samudra.nginx` rewritten for safe certbot bootstrap**: explicit `/.well-known/acme-challenge/` location so certbot renewals work even after HTTPS redirect is added; documented `certbot --redirect` flag so operators don't miss the interactive prompt; security-header snippet (HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy) ready to paste into the HTTPS server block certbot creates.
- **`test_funnel.test_lifespan_survives_state_db_init_failure`**: regression — confirms the app boots cleanly with a broken `STATE_DB_PATH`, corpus search keeps working, identity endpoint gives a clean 503. 89/89 hermetic tests pass.

### Known issue (not fixed)
- **`web/static/scripts/wrapLatinInBlue_history.js/` is a directory containing `wrapLatinInBlue.js`** — legacy desktop-app filesystem layout. Corpus HTML referencing the script as a JS path silently 404s in the web context. The "wrap Latin in blue" decorative effect is broken in the web app but was working in the legacy desktop. Investigation needed before fixing (need to know the exact `<script src>` corpus HTML uses).

## [1.12.6] - 2026-05-15 (Bug sweep #5)
### Fixed
- **`ingest.py` recorded `source_count` from `len(filenames)`**, which overstated reality when the ingest skipped a missing file. The recorded count now comes from `SELECT COUNT(*) FROM sources` after all inserts so `corpus_meta.source_count` matches the actual rows in the DB.
- **`/api/morph/{word}` accepted unbounded path length**: a megabyte word would still go through `to_slp1` and an HTTPS lookup to Sanskrit Heritage. Now `Path(..., min_length=1, max_length=200)`.
- **`get_state_db()` called outside try in three handlers** (`corrections.propose`, `corrections.pending`, `admin.vacuum`): a config or connection failure leaked tracebacks via FastAPI's default 500 handler. All three now follow the identity.py pattern — wrapped, logged, and returned as a clean 503 (or empty list, for `/pending`).

### Removed
- **`web/static/scripts/selection0.js`**: dead — referenced nowhere, had drifted from `selection.js`.

### Added
- **`test_phase4.py`**: 2 new regression tests — morph route length cap, and `source_count` reflecting actual rows after a skipped file (the ingest fix). 88/88 hermetic tests pass.

## [1.12.5] - 2026-05-15 (Bug sweep #4)
### Fixed
- **Dead prev / next / nearest navigation buttons on the main `/` page**: `selection.js` (which binds those buttons and the `a` / `s` / `d` keyboard shortcuts) was only inlined into the standalone HTML export. On the live site the buttons appeared in the result fragment but had no effect. Now loaded as a static script alongside `search.js`; `selection.js` also looks for either `#results` (standalone) or `#results-area` (live) for its index-reset observer.
- **`/api/ai/explain` accepted unbounded `context_lines`**: an abuser could POST 10,000 lines × 100KB and burn the AI-provider budget. `AIRequest` now caps the list at 50 items, each ≤ 2000 chars, plus `query` length ≤ 1000.
- **`/api/corrections/propose` accepted unbounded `old_text` / `new_text`**: state.db could be filled with multi-megabyte spam. `CorrectionProposal` now requires `1–10000` chars for both fields, `email` ≤ 320 (RFC 5321), and `source_id` / `line_num` ≥ 1.
- **`test_phase3.test_correction_proposal` mutated `settings.APP_ENV` without restoring**: dev mode could leak into later tests. Now `try/finally`-restored. Similar fix in `test_phase4.test_ai_explain_unconfigured` which previously relied on whatever `APP_ENV` an earlier test had left behind.

### Added
- **`test_phase4.py`**: 4 new tests covering AI context_lines cap (count + per-line) and corrections payload bounds (size + empty). 86/86 hermetic tests pass.

## [1.12.4] - 2026-05-15 (Bug sweep #3)
### Security
- **CORS fail-open in production with unset `ALLOWED_ORIGINS`** (HIGH): `if not origins or settings.APP_ENV == "development"` — the `or` meant an operator who forgot to set `ALLOWED_ORIGINS` in production shipped `allow_origins=["*"]`. Replaced `or` with `and` so wildcard is reserved for *development with no allowlist*. Production with unset origins now fails closed (`allow_origins=[]`).

### Fixed
- **`publish.py smoke_check` connection leak**: if either `SELECT COUNT(*)` raised, the SQLite connection was never closed. Now `try/finally`-guarded.
- **`publish.py integrity_check` connection leak**: same pattern — exception inside the try meant the connection wasn't closed before returning. Now finally-guarded.
- **Search submitted before `/api/sources` loaded sent `source_ids=[]`**: the user got an empty result with no indication that sources hadn't loaded yet. Find + HTML buttons now disabled until sources resolve. On fetch failure, a clear Russian-language error appears in place of the source counter.

### Added
- **`test_cors.py`**: 2 new tests — the regression for production-with-unset (the bug fixed here), and a verification that explicit dev origins are respected (the test previously expected the buggy behavior of forced-wildcard in dev). 82/82 hermetic tests pass.

## [1.12.3] - 2026-05-15 (Bug sweep #2)
### Fixed
- **Query-string injection on Sanskrit Heritage lookup**: `morph_service.expand_word` built the URL with `f"…?lex=SH&q={slp1_word}"`, so a token containing `&` or `=` would inject additional query parameters into the third-party API call. Now uses `httpx.get(url, params={...})` so all characters are correctly percent-encoded.
- **`/sources/{id}/anchor/{link_id}` redirect broke for special characters**: a link_id containing `&`, `?`, `#`, `=` was inserted raw into the redirect URL, causing the target page to lose the anchor. Now `urllib.parse.quote(link_id, safe="")`'d before insertion.
- **`/api/health` leaked DB paths and stack-trace fragments**: `corpus_error` / `state_error` previously echoed `str(e)` to anonymous callers. In production they now expose only the exception class name (e.g. `OperationalError`); the full message is `logger.exception`-logged for operators. Development mode still surfaces the full text for fast debugging.
- **`/api/ai/explain` propagated provider error text verbatim**: AI provider errors potentially containing URLs, model names, or transport details were forwarded to the client. Production now returns a stable "AI service unavailable" message; full text is logged. Development keeps verbose output.
- **State-DB connection leaked from `/api/health`**: if `SELECT 1` raised, the connection was never closed. Now opened with a `finally`-guarded close.

### Added
- **`test_funnel.py`**: 3 new regression tests — anchor redirect URL-encoding (both special and safe link_ids), and production-mode health endpoint redaction. 80/80 hermetic tests pass.

## [1.12.2] - 2026-05-15 (Bug sweep)
### Fixed
- **URL concat bug with query-bearing `SYSTEMA_SANSCRITICUM_URL`**: Setting the env var to `https://x.ru/?ref=launch` previously produced malformed `…?ref=launch?utm_source=…` links. UTM URLs are now built server-side with `urllib.parse.urlencode` and a sensible `?`/`&` separator. New `_ss_link(medium)` helper in `main.py`; reader and templates take the precomputed `ss_link` / `engaged_ss_link`.
- **`restoreFromUrl` left stale state on back-to-empty navigation**: clicking back from `?q=X` to `/` left the form populated and old results visible. Now clears query/mode/filters/results on a no-query URL.
- **`state.db` migration race**: two workers starting concurrently could both attempt the same `ALTER TABLE ADD COLUMN`, crashing the loser with "duplicate column name". Each ALTER is now wrapped in `try/except aiosqlite.OperationalError`.
- **Sitemap XML breakage with `&` in `PUBLIC_BASE_URL`**: an operator-set base URL containing `&` produced invalid XML. Now `xml_escape`d before insertion.
- **Internal exception text leaked to clients**: `identity.lead` and `admin.vacuum` raised `HTTPException(500, detail=str(e))`, exposing tracebacks/paths. Replaced with generic "Internal server error" message + `logger.exception(...)` for operators.
- **DB-open failure in `identity.lead` returned 500 instead of 503**: `await get_state_db()` was outside the try block, so an open failure bypassed the handler. Now wrapped — yields a clean 503 with no leak.
- **Engaged CTA re-animated when already visible**: clicking search after the banner appeared briefly re-played the slide-in animation. Now skips re-animation if `display === 'flex'`.

### Added
- **`test_funnel.py`**: 4 new regression tests — UTM URL building with both `?`-bearing and plain base URLs, sitemap validity with `&` in base URL (parses with `xml.etree.ElementTree`), and identity lead 503 cleanliness on state DB failure. 77/77 hermetic tests pass.

## [1.12.1] - 2026-05-15 (Engaged-user CTA)
### Added
- **Search-count engagement signal**: localStorage tracks searches per browser; after 3 searches a sliding bottom-of-page banner surfaces a stronger course CTA — *"Похоже, вы серьёзно изучаете санскрит. Курс грамматики поможет читать тексты системно."* Distinct `utm_medium=engaged_banner` for conversion attribution. Dismissal is sticky across sessions. Hidden entirely when `SYSTEMA_SANSCRITICUM_URL` is unset.
- **`test_funnel.py`**: 2 new tests verifying the banner element + UTM are rendered when `SS_URL` is set and absent when unset.

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
