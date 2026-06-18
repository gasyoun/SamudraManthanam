# Changelog - Samudra Manthanam

All notable changes to this project will be documented in this file.

## [wisdomlib-0.0.1] - 2026-06-18

First tagged release of the wisdomlib catalog crawler (a standalone
corpus-acquisition tool under `web/corpus_builder/wisdomlib/`; versioned
independently of the main platform, which is at 1.x). Tag: `wisdomlib-v0.0.1`.

### Added
- **wisdomlib catalog crawler** (`web/corpus_builder/wisdomlib/`, branch
  `offline-search`) — async indexer of wisdomlib.org as a candidate corpus
  source. `crawl.py stageA` enumerates 848 non-Marathi entries
  (`entries_index.jsonl`); `stageB` enriches each landing page into
  `books_full.jsonl` (source language, English-translation flag, chapter
  count); `report` writes `CATALOG.md` (848 entries, 122.7M words, 97,263
  chapters, with breakdowns, top-25, and a fetch-failures table). `stageC`
  downloads selected books' chapter pages (`/d/docN.html`) into
  `content/<slug>/` (gitignored), resumable per page and per book.
- **Shared selection filters** for `stageB`/`stageC`:
  `--section/--ctype/--lang/--slug/--english/--pali/--min-words/--limit`.
- **`watch.py`** — Stage C progress watcher (live bar, pages/books done, rate,
  ETA, stall warning, `--once`, `--supervise`), driven by a run manifest;
  mirrors the NWS scraper's watcher.
- **Politeness controls** — `--delay` (jittered, held inside the worker slot),
  browser-like UA + headers, HTTP/2 (graceful HTTP/1.1 fallback when `h2`
  is absent), and `Retry-After` handling on 429/503.

### Fixed
- **Block-page guard** — `is_block_page()` rejects soft-200 Cloudflare/
  challenge pages so a block is never cached as chapter content nor
  permanently skipped by the per-page resume check.
- **Byte-faithful archive** — chapter HTML written with `newline=""` so Windows
  newline translation no longer rewrites source CRLF.

### Notes
- wisdomlib has no stated bulk-reuse licence; scraped content is gitignored and
  provisional. Stage C is currently blocked by a Cloudflare IP block (the
  catalog build completed before the block); see `.ai_state.md` Dev Notes
  2026-06-18.

## [1.0.0] - 2026-06-13

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

## [1.21.0] - 2026-06-12 (Phase 0: DH-standards foundation)

Start of the H2 2026 roadmap (`ROADMAP_2026_H2_DH_MOBILE.md`): stable
identity, FAIR metadata, and rights clarity ahead of the canonical-JSONL
data layer and offline-search phases.

### Added
- **`ROADMAP_2026_H2_DH_MOBILE.md`** — six-month roadmap: DH-standards gap
  analysis, canonical JSONL layer, PWA + sqlite-wasm offline search, citation
  and export work. Decisions of 2026-06-12 recorded (rights stay grey, JSONL
  not TEI, browser PWA not native ports).
- **`CITATION.cff`** — software citation metadata; explicitly scoped to code.
- **README "License and corpus rights"** — Apache 2.0 covers code only; the
  Russian translations carry their own rights and are not redistributable.
- **Per-source metadata skeletons** — `web/ingest/extract_source_meta.py`
  generated `Data/<name>.meta.json` for all 148 sources (title, credit,
  imprint, publisher, year, scripts present, slug). `title_en`, `provenance`,
  `rights` left empty with `needs_review: true` for an editing pass; 8 sources
  flagged for missing year. Hand edits win — extraction never overwrites
  without `--force`.
- **Corpus version in the footer** — `app/corpus_info.py` snapshots
  `corpus_meta` at lifespan; `_base.html` gains a footer showing
  "Корпус: версия N от YYYY-MM-DD" (hidden when corpus.db predates
  `corpus_meta`). Registered as a Jinja global on all five template envs.
- 9 new tests (footer rendering ×3, slug filter resolution ×3, canonical
  slug URL, legacy-id fallback, unknown-token fallback).

### Changed
- **Search permalinks are now re-ingest-stable.** `/api/sources` returns
  `slug`; `search.js` writes slugs (not ids) into the `?src=` permalink and
  accepts both on restore. `GET /search` resolves `src=` slug-first with a
  legacy numeric-id fallback (`_resolve_source_filter` replaces
  `_parse_source_ids`); canonical URLs emit sorted slugs. Old numeric
  bookmarks keep working and canonicalise to slug form.
- Documentation root decluttered: 14 superseded planning docs moved to
  `docs/archive/`; `DOCUMENTATION_INDEX.md` rewritten with the new reading
  order.
- `.gitignore`: corpus.db backups (`web/corpus.db*`) and `reingest.log`.

### Tests
- 383 hermetic tests pass (380 before; 3 `_parse_source_ids` unit tests
  replaced by 6 HTTP-level resolution tests, plus footer coverage).

## [1.20.1] - 2026-05-18 (Feature: AI response cache)

### Added
- **`ai_cache` table on `state.db`** — `(request_hash PRIMARY KEY, task, response, model, created_at, latency_ms)` plus indexes on `created_at` and `task`. Idempotent migration via `init_state_db`.
- **`web/app/services/ai_cache.py`** with three public helpers:
  - `hash_request(system, user, model)` — SHA-256 of canonical JSON. Includes both prompts AND the model so a prompt-template tweak in `ai_service.py` automatically invalidates affected entries, and different models cache separately.
  - `cache_get(request_hash)` — returns the cached `response` dict or None on miss/stale/error.
  - `cache_put(request_hash=, task=, response=, model=, latency_ms=)` — INSERT OR REPLACE, refreshes TTL on rewrite.
  - `cache_stats()` — `{total, task_<name>: count, ...}` for admin diagnostics.
- **`AI_CACHE_ENABLED` (default True) and `AI_CACHE_TTL_DAYS` (default 30)** settings. TTL is checked on read; no background sweeper needed at current scale.
- **Cache hit/miss visible to callers**: successful responses include `cached: True` when served from the cache, `False` (or absent) otherwise. Operators can grep logs for `cached` to track hit rate without extra instrumentation.

### Changed
- `_openai_chat` in `ai_service.py` now consults the cache before calling the provider, writes successful responses back, and propagates the `cached` flag. Cache failures are swallowed — a broken `state.db` never blocks AI requests, just degrades to live-call-every-time.
- `explain_with_ai` and `compare_translations` thread a `task` label into the cache (`"explain"`, `"compare_translations"`) so `cache_stats` can categorise hits.

### Fail-soft contract
- `STATE_DB_PATH` unset → cache is a no-op (every call goes live).
- `AI_CACHE_ENABLED=False` → same.
- DB row corrupted or schema missing → exception swallowed, miss returned, live call proceeds.
- Provider 5xx → error result is NEVER cached (would poison the cache with transient failures).

### Tests
- 17 new tests in `test_ai_cache.py`:
  - Hash determinism + sensitivity to each of system/user/model.
  - Unicode + empty-input handling.
  - Round-trip put/get, REPLACE semantics, TTL expiry.
  - Disabled-by-flag fail-soft path.
  - `STATE_DB_PATH=""` fail-soft path (cache silently skipped).
  - `cache_stats` task tallies.
  - End-to-end through `_openai_chat`: provider hit on first call, cache hit on second (verified by `mock_post.call_count == 1`), prompts cache separately, error responses are NOT cached.
- 368/368 hermetic tests pass.

### Cost impact
- For the AI compare feature (v1.20.0), each unique BhG verse comparison goes to the provider ONCE per 30-day window. Repeated visitors hit cache. Operators get the `cached` flag in responses + per-task counts via `cache_stats` for monitoring.

## [1.20.0] - 2026-05-18 (Feature: AI translation-comparison synthesis)

### Added
- **`POST /api/ai/compare-translations`** — sends one verse's full payload (work title, chapter/verse, IAST, all translations + commentaries with their roles) to the configured LLM provider and returns a scholarly synthesis identifying key Sanskrit terms, translator divergences, and commentary readings.
- **"✨ Сравнить переводы (AI)" button** on every `/compare/{work}/{ch}.{v}` page with ≥2 hits. Clicking expands a slide-in synthesis panel; result panel is hidden by default to avoid visual clutter. Per-pageview cache prevents re-calling the provider on repeated clicks; transient failures clear the cache so the user can retry.
- **`build_compare_prompt`** in `ai_service.py` — pure prompt assembler with HTML-tag stripping for embedded commentary markup, role markers (`[commentary]`, `[anthology]`, `[context]`) so the model treats medieval ācāryas differently from modern translators, optional IAST line, numbered translation list. Extracted as a pure function so tests can validate the prompt shape independently of any AI call.
- **Shared `_openai_chat` helper** consolidates the two AI service functions (`explain_with_ai` and the new `compare_translations`) onto one transport path. Provider-agnostic OpenAI-compatible — works with OpenAI, Ollama-with-openai-shim, vLLM, LM Studio.

### Frontend
- `compare_view.html` emits the AI payload as `<script id="aiComparePayload" type="application/json">` — embedded server-side so the JS handler doesn't need a second DB roundtrip. Spinner + content + error + footer states; model attribution in the footer.

### Bounds
- `MAX_COMPARE_TRANSLATIONS = 20` (live max is 14 for BhG; cap gives headroom without trivial denial-of-wallet)
- `MAX_COMPARE_TEXT_LEN = 4000` per translation
- `MAX_COMPARE_LABEL_LEN = 200` per label
- Chapter 1-999, verse 1-9999

### Tests
- 16 new tests in `test_ai_compare.py`: prompt builder (verse coord, HTML stripping, role markers, IAST handling, numbering), route validation (min 2 translations, oversized text/label, too many translations, chapter bounds), 503 mapping on missing AI_BASE_URL, mocked-provider happy path, template integration (button + payload script + hidden panel). 351/351 hermetic tests pass.

### Live verification
- `GET /compare/bhagavadgita/2.47` renders the AI button + 14-source payload (10 translations + 1 anthology + 2 commentaries + MBh-Bhīṣma context bridge) with the 141-char IAST string.
- 503 path verified by clearing `AI_BASE_URL` in test.
- Compare pages with 0-1 hits (rare, dictionary-only sources) correctly suppress both the button and the payload script.

## [1.19.0] - 2026-05-18 (Feature: result-page visualisations — bar chart + KWIC)

### Added
- **Per-source hits bar chart** at the top of every multi-source result fragment. Inline SVG, no JS library, sorted by hit count descending, each bar wrapped in an `<a href="#chapter_N">` so clicking jumps to that source's group. SVG `<title>` provides on-hover tooltip with full source name + count. Live coverage: `q=дхарма` → 78 bars; `Кришна` → 75; `yoga` → 87. Suppressed entirely when 0–1 sources are hit (chart adds no info).
- **KWIC (keyword-in-context) excerpts** per result row — `{before} <mark>{match}</mark> {after}` with 40-char windows on each side and `…` elisions for truncation. Multi-line queries pick the first matching term. Fallback to a leading-window slice when no term matches.
- **"Компактный вид" toggle button** in the results header (when total > 1). Sets `body.compact-mode` which swaps the per-result display from full `line_html` to just the KWIC preview — turns the page into a corpus-linguistics-style overview for fast scanning. Toggle text flips to "Полный вид" when active.

### Files
- `web/app/services/html_service.py` — `kwic_excerpt(text, query, window)`, `build_source_chart_data(results)`, plus enrichment of each `r["kwic"]` in `render_fragment`.
- `web/templates/result_fragment.html` — SVG bar chart block, KWIC preview div per result, compact-toggle button + script + scoped CSS.
- `web/tests/test_visualisations.py` — 21 tests: KWIC helper (centered/edge/multiline/no-match/empty), chart aggregator (zero/single-source/sort/anchor mapping), rendering integration (chart presence, KWIC blocks, compact toggle).

### Notes
- All 335 hermetic tests pass.
- Bar chart is pure server-rendered SVG — works without JS, no Chart.js dep added.
- KWIC search is case-insensitive substring (`line_text.lower().find`). Regex-mode hits with no literal substring fall through to the no-match fallback path; could be improved by re-matching with the regex but adds complexity.
- Compact mode is per-pageview, not persisted. Re-toggle per session. Future enhancement: localStorage like the reader's font-size preference.

## [1.18.0] - 2026-05-18 (Feature: scholarly reader)

### Added
- **Sticky chapter sidebar** on `/sources/{slug}` — auto-populated TOC with anchor links to each chapter's first line. Two-track detection: uses the `chapter` DB column when populated (sources with `<H1>` markers), falls back to scanning `line_html` for `<div class="chapter_title">` (the majority of corpus sources). Live coverage: Bhīṣma-parvan 121 entries, Ṛgveda I 191, BhG-Smirnov 18, Kāmasūtra 79. Sources with no chapters (Īśa Upaniṣad etc.) cleanly hide the sidebar and switch to a single-column layout.
- **Sticky reader toolbar** below the header: `A− / A+` font-size buttons (persisted in `localStorage`), `Оба / Рус / Санскрит` language toggle for parallel sources only, `?` help button.
- **Per-line copy-citation button** — appears on row hover, copies a markdown-style deep link (`[Source title 1.1](https://samskrtam.ru/sources/slug?highlight=1.1)`) via the Clipboard API with a fallback for non-HTTPS contexts. Flashes `✓` on success.
- **Keyboard navigation** (`reader.js`, vanilla JS, no jQuery):
  - `j` / `k` — step through verses with smooth-scroll and visual `.focused` highlight.
  - `]` / `[` — jump to next / previous chapter heading.
  - `g g` — top of page (gmail-style double-tap, 500ms window).
  - `G` — bottom of page.
  - `?` — toggle a help overlay with all shortcuts.
- **Mobile sidebar drawer** — at ≤900 px the sidebar collapses to an off-canvas drawer; a `≡ Главы` button in the toolbar slides it in. Tapping a chapter link auto-closes the drawer.

### Files
- `web/static/scripts/reader.js` — new, vanilla JS, ~210 lines.
- `web/templates/source_view.html` — sidebar/toolbar markup + new line-row schema (`data-line-num` + `data-link-id` for the copy-citation handler).
- `web/app/routers/reader.py` — chapter extraction with html-fallback regex, `chapters`/`is_parallel`/`slug` added to template context.
- `web/tests/test_reader.py` — 15 tests covering chapter sidebar (with and without chapters, fallback detection), toolbar markup (font, lang toggle on parallel only, help button), per-line copy buttons + data attrs, reader.js loaded on `/sources/{slug}` and absent elsewhere.

### Notes
- 314/314 hermetic tests pass.
- Font-size and (future) other preferences live in `localStorage` keyed `sm_reader_*` — no server-side state. Works incognito; resets across browsers, fine for scholarly reading.
- The chapter-extraction fallback is render-time only; `parse_html.py` still only picks up `<H1>` at ingest time. A future ingest improvement could backfill the `chapter` column for chapter_title-style sources, but it isn't required — render-time detection is fast (regex on already-loaded `line_html`).

## [1.17.0] - 2026-05-18 (Feature: design system refactor — Jinja base + site.css)

### Added
- **`web/static/site.css`** — shared design system: CSS variables (`--primary`, `--accent`, `--bg`, `--text-muted`, etc.), navbar/`site-container`/`site-hero`/`site-breadcrumb`/`site-empty`/`site-stats` components, `.btn`/`.btn-primary`/`.btn-secondary`/`.btn-ghost` button system, responsive breakpoints. Loaded AFTER `style.css` so it overrides the legacy corpus-content stylesheet's body styling without affecting the desktop-exported standalone HTML (which only loads `style.css`).
- **`web/templates/_base.html`** — Jinja base with parameterised blocks: `title`, `meta` (default OG/Twitter card with canonical and hreflang plumbing), `extra_head` (per-page CSS), `navbar` (overridable for reader pages with their own sticky header), `navlinks` (per-page nav button set), `content`, `extra_body` (JSON-LD scripts).

### Changed
- **All 5 page templates now `{% extends "_base.html" %}`** and own only their unique CSS:
  - `index.html`: 439 → 281 lines (search card / modal / AI panel kept locally; navbar + meta come from base).
  - `popular_term_page.html`: 247 → 135 lines.
  - `compare_index.html`: 207 → 129 lines.
  - `search_page.html`: 226 → 136 lines.
  - `source_view.html`: 188 → 153 lines (overrides `navbar` block to use its sticky reader-header instead).
  - `compare_view.html`: rewrites the navbar via override since it uses the light-variant chrome.
- **`_base.html` emits hreflang alternates** from a context-supplied `hreflang_alternates` list, replacing the inline `{% for %}` loop that previously lived in `source_view.html`. The reader route's context shape already matches.
- **`/sources/{slug}` route adds `og_type="article"`** to the template context so the base template's OG block emits `article` instead of the default `website`.
- **CSS tokens unified** across pages: every template references the same `--accent: #e67e22` / `--primary: #2c3e50` / etc. Previously, `index.html` used `--accent-color: #3498db` (different blue) and other pages used `--accent: #e67e22` (orange). The orange is canonical now; the index search card still uses #3498db locally for the "Найти" button to preserve that page's existing identity.

### Backward compatibility
- `style.css` is **untouched** — the desktop Lazarus app's exported standalone HTML continues to render identically.
- `result_fragment.html`, `standalone_page.html`, `full_page.html` are unchanged (they're either embedded fragments or downloadable exports, not full pages).

### Tests
- All 299 hermetic tests pass — the existing OG / canonical / breadcrumb / JSON-LD assertions effectively serve as snapshot tests for the refactor.
- Live-corpus smoke across all 6 page types confirms 200 responses, both stylesheets loaded, navbar present on chrome-using pages, suppressed on reader pages (intentional).

### Notes
- New pages should `{% extends "_base.html" %}` and provide only the blocks they need to override. Adding a page now costs ~40 lines instead of ~150.
- `site.css` is loaded by every template — no per-page CSS hash invalidation; one shared cache key. Browser caching wins.

## [1.16.2] - 2026-05-18 (Feature: slug-based source URLs)

### Added
- **`/sources/{slug}` is now the canonical source URL**. Slugs are derived from filename (extension stripped, Cyrillic transliterated to Latin, lowercased, hyphen-normalised) and stored in a new `sources.slug` column with a unique index. They survive re-ingests — unlike the numeric `id` which renumbers on every rebuild.
- **`/sources/{int_id}` issues a 301 redirect** to the canonical slug URL with query string preserved. Lets Google migrate its index without 404s on existing bookmarks.
- **`web/app/services/slug.py`** — pure `derive_slug` + `make_unique_slug` (collision suffix `-2`, `-3`, …) + Russian→Latin transliteration table. Live verification: 148/148 sources got clean unique slugs without disambiguation suffixes.
- **Startup migration** (`_ensure_slug_column_and_backfill`) in lifespan: idempotent ALTER TABLE + backfill that runs every boot. Pre-existing corpus.db files transparently gain slug routing on first start of the new code; no operator action required.
- **Ingest writes slug at insert time** so freshly-built corpus.db ships ready.

### Changed
- `result_fragment.html`, `compare_view.html`, `source_view.html` emit slug URLs in result links, citation copy URLs, social share URLs, and JSON-LD `@id`s.
- `/sitemap-sources.xml` emits slug URLs in `<loc>` and `<xhtml:link>` alternates — sitemap entries now survive re-ingest renumbering.
- `_fetch_source_slugs`, `_fetch_parallel_source_slugs` replace the numeric-ID variants in the sitemap pipeline (legacy `_fetch_source_ids` kept for backward compat).
- `build_line_quotation`, `_line_haspart_entry` now accept `slug=` instead of `source_id=` and emit slug-form anchor URLs in JSON-LD `@id` and `url`.
- `compare_service.VerseHit` gains `source_slug` so the compare page can deep-link to the slug-form source URL.

### Tests
- 24 new tests in `test_slug.py`: transliteration table (all letter classes, multi-char mappings ё/щ/ц/ч/ш, hard/soft signs, non-Cyrillic pass-through, mixed script), `derive_slug` on real-corpus filename shapes (ASCII, Cyrillic, mixed punctuation, underscore preservation, extension stripping), `make_unique_slug` collision resolution and purity.
- Fixtures in `test_source_metadata.py`, `test_language_filter.py`, `test_sitemap_hreflang.py`, `test_funnel.py`, `conftest.py` updated to seed `sources.slug` and yield slug values.
- 299/299 hermetic tests pass.

### Live corpus verification
- Migration: 148/148 sources got unique slugs, zero collisions needed `-2` suffix.
- Cyrillic transliteration works: `Словарь Смирнова.txt` → `slovar-smirnova`, `Кнауэр.txt` → `knauer`, `Индуизм. Джайнизм. Сикхизм.txt` → `induizm-dzhaynizm-sikkhizm`, `Эрман-Темкин.txt` → `erman-temkin`.
- Routing: `/sources/bhagavadgita-smirnov` → 200; `/sources/219` → 301 → `/sources/bhagavadgita-smirnov`; `/sources/slovar-smirnova` → 200; `?lang=sa` filter and hreflang alternates work on slug URLs; `/sources/{slug}/anchor/{link_id}` redirects to `/sources/{slug}?highlight={link_id}`.

### Notes
- Old `/sources/{int_id}` URLs in third-party indexes get 301'd cleanly; after Google re-crawls, only slug URLs remain in the index.
- `make_unique_slug` falls back to literal "source" for pathological filenames like ".html". None observed in live corpus.

## [1.16.1] - 2026-05-18 (Feature: `<xhtml:link>` alternates in /sitemap-sources.xml)

### Added
- **`/sitemap-sources.xml` now declares hreflang at the sitemap level** per Google's preferred convention for multilingual content. Parallel sources (119 of 148 on the live corpus) emit three `<url>` entries each — bare, `?lang=ru`, `?lang=sa` — and each entry carries the full `<xhtml:link rel="alternate" hreflang="…">` set including a self-reference. Non-parallel sources (dictionaries, Russian-only prose) keep their single-entry shape.
- **`xmlns:xhtml="http://www.w3.org/1999/xhtml"`** is added to the `<urlset>` element only when at least one parallel source exists in the corpus — keeps the namespace declaration out of dictionary-only corpora.
- **`_fetch_parallel_source_ids(db)`** — single SQL query with `EXISTS … LIMIT 1` short-circuit detects sources whose `corpus_lines.line_html` carries the `chapter_block iast` marker. Fails soft to an empty set so a DB hiccup degrades to no-hreflang rather than killing the sitemap.

### Math on live corpus
- **386 `<url>` entries** (was 148): 29 non-parallel × 1 + 119 parallel × 3 = 386.
- **1,071 `<xhtml:link>` alternates**: 119 sources × 3 variants × 3 alternates per variant.
- 357 each of `hreflang="ru"` / `hreflang="sa"` / `hreflang="x-default"` — perfectly balanced reciprocal declarations.
- Sitemap size grew 13 KB → 112 KB; total sitemap surface still well under spec limits.
- XML well-formed; namespace correctly declared.

### Implementation notes
- `_render_urlset(urls, include_xhtml=True)` conditionally adds the xhtml namespace to the envelope. Other child sitemaps (`-core`, `-compare`) don't use it.
- Same hreflang signal now ships in TWO places: in the source page's `<head>` (v1.16.0) and in the sitemap (this version). Google honours both; redundant declarations don't conflict.
- `/sitemap-compare.xml` is deliberately mono-variant — `/compare/{work}/{ch}.{v}` pages are inherently multilingual (10+ translations side by side), so a `?lang=` filter wouldn't make semantic sense.

### Tests
- 9 new tests in `test_sitemap_hreflang.py`: SQL helper finds/excludes correctly, namespace declared only when needed, parallel sources emit 3 entries with full alternate set, non-parallel sources stay mono-entry, well-formed XML across the parse, self-referential alternates per variant. 278/278 hermetic tests pass.

## [1.16.0] - 2026-05-18 (Feature: `?lang=ru|sa` filter + hreflang on source pages)

### Added
- **`/sources/{id}?lang=ru` and `?lang=sa`** strip the opposing language's `<div class="chapter_block …">` from each line on parallel-content sources (those packing IAST + Russian in one citation_block). Sanskrit IAST view and Russian-translation view get distinct URLs, distinct canonicals, distinct JSON-LD `inLanguage`, and reciprocal hreflang alternates — the SEO surface a multilingual scholarly corpus needs.
- **`<link rel="alternate" hreflang>` × 3** on parallel pages: `ru`, `sa`, `x-default`. Each variant declares all three (self-reciprocal) so Google can attribute the same content correctly across language searches.
- **`web/app/services/language_filter.py`** — three pure helpers:
  - `normalize_lang(raw)`: lowercase + whitespace-strip + allow-list match. Unknown values silently return None (stray bookmark with `?lang=fr` doesn't 4xx the request).
  - `filter_html_to_language(line_html, lang)`: regex strip of the opposing chapter_block. Anchored on the class name so non-parallel HTML passes through unchanged.
  - `is_parallel_source(line_htmls)`: short-circuit scan for `chapter_block iast` markers. Caller samples ~10 lines — one hit classifies the source.
- **JSON-LD `Book.inLanguage` reflects the filtered surface** (`sa` for `?lang=sa`, otherwise `ru`). The highlighted-line `Quotation.inLanguage` follows the same rule. `build_source_jsonld` and `build_line_quotation` gain an `in_language` kwarg defaulting to `"ru"`.

### Coverage
- **119 of 148 sources qualify as parallel** on the live corpus (80%) — all 10 Ṛgveda maṇḍalas, 19 Atharvaveda books, every Mahābhārata parvan that ships IAST, all 10 BhG translations that include Sanskrit, 25 Sürkin Upaniṣads, plus most kāvya/sūtra texts. Non-parallel sources (Russian-only prose translations, dictionaries, encyclopedias) keep their existing single-canonical behaviour with no hreflang emission.

### Implementation notes
- Hreflang URLs preserve `?highlight=` when present — a deep-linked verse URL `/sources/204?highlight=23.1` gets reciprocal alternates `/sources/204?highlight=23.1&lang=ru`, `…&lang=sa`, and bare-form `x-default`.
- Sitemap entries do NOT yet carry `<xhtml:link>` alternates per Google's hreflang-in-sitemap convention — deferred. Hreflang in the HTML head is the more important signal for v1.
- Compare-page `_split_iast_and_translation` continues to work independently — `language_filter` re-implements the regex as a module-local constant rather than introducing a cross-service dependency. The two patterns are kept in sync by convention.

### Tests
- 25 new tests in `test_language_filter.py`:
  - `normalize_lang` allow-list, case-insensitivity, whitespace handling, unknown-rejection.
  - `filter_html_to_language` symmetry (`ru`/`sa` strip the opposite block), pass-through on plain HTML, None/empty handling.
  - `is_parallel_source` short-circuit semantics and empty-input handling.
  - HTTP integration on a seeded parallel source: 3 hreflang alternates emitted, URLs are reciprocal and well-formed, `?lang=sa` strips Russian, `?lang=ru` strips IAST, canonical follows the variant, unknown lang silently drops, JSON-LD inLanguage reflects filter.
  - HTTP integration on a seeded Russian-only source: no hreflang emission, `?lang=` is a no-op, canonical still mirrors request.
- 269/269 hermetic tests pass.

## [1.15.6] - 2026-05-18 (Feature: sitemap index split)

### Changed
- **`/sitemap.xml` is now a `<sitemapindex>`** referencing three child sitemaps with their own `<lastmod>` per spec. Replaces the previous flat 1,420-URL urlset; total URL coverage is identical but distributed:
  - **`/sitemap-core.xml`** — 34 high-value URLs: root `/`, 3 work hubs (`/compare/{work}`), 30 popular-query landings (`/q/{slug}`). ~3 KB.
  - **`/sitemap-sources.xml`** — one URL per source. ~13 KB / ~148 URLs on the live corpus.
  - **`/sitemap-compare.xml`** — one URL per verse comparison page. ~129 KB / ~1,238 URLs on the live corpus.
- **Existing `robots.txt` directive `Sitemap: /sitemap.xml` keeps working** — Google transparently follows sitemap-index references to children.

### Why split
At 1,420 URLs / 145 KB the flat sitemap wasn't near the 50K/50MB cap, but it mixed high-value hub pages with long-tail verse URLs in one document. The split lets crawlers prioritise: `sitemap-core.xml` fetches first (small, hub pages — priorities 0.9–1.0), `sitemap-sources.xml` next, the big `sitemap-compare.xml` last (lower priority 0.7 leaves). Splitting also makes incremental updates cheaper if/when per-sitemap `lastmod` ever diverges.

### Implementation notes
- Extracted helpers: `_xml_response`, `_render_urlset`, `_render_sitemapindex`, `_sitemap_base`, `_fetch_source_ids`. Three new endpoints, one refactored index endpoint.
- Each child sitemap independently fetches `corpus_meta.generated_at` so the index's per-child `<lastmod>` can later diverge if we ever ingest per-sitemap (currently they all share the corpus build date).
- Backward-compat for tests: failing fixture corpora produce empty `<urlset>` envelopes (XML still well-formed, no exception).

### Tests
- 7 reshaped/new tests in `test_sitemap_lastmod.py`: sitemap-index shape, per-child lastmod, well-formed XML across all 4 endpoints, malformed-corpus_meta fail-soft, format validation across the family.
- `test_compare.py`, `test_popular_terms.py`, `test_funnel.py` updated to query the new child endpoints rather than the old flat sitemap.
- 244/244 hermetic tests pass.

## [1.15.5] - 2026-05-17 (Feature: parent-work `isPartOf` on source pages)

### Added
- **`parent_works.detect_parent_work(filename)`** — filename-pattern registry mapping ~73 corpus sources to their parent works. Three relationship kinds collapsed into `isPartOf` for v1 simplicity: volumes (parvans / mandalas / kāṇḍas / books), editions/translations (BhG, Yoga-Sūtra, Śatakatraya, Buddhacarita), and commentaries (Rāmānuja Gītābhāṣya, Abhinavagupta Gītārthasaṃgraha, Yāmunācārya summary).
- **`Book.isPartOf` becomes a 2-element array** when a parent is detected — `[WebSite, parent Book]`. Stays as a single dict when no parent matches (preserves backward-compat). Each parent Book entry carries both Cyrillic `name` and IAST `alternateName`, e.g. `{"name": "Махабхарата", "alternateName": "Mahābhārata"}`.

### Coverage on live corpus (73 / 148 sources)
- 19× Atharvaveda books (Books 1–19, Elizarenkova)
- 18× Mahābhārata parvans (I–XVIII, multiple translators)
- 14× Bhagavadgītā (10 translations + 1 anthology + 3 commentaries)
- 10× Ṛgveda maṇḍalas (I–X, Elizarenkova)
- 4× Rāmāyaṇa kāṇḍas (Grintser + Leonov)
- 4× Yoga-Sūtra editions (3 standalone + 1 anthology)
- 2× Buddhacarita (Leonov Sanskrit + Balmont 1913)
- 2× Śatakatraya (Leonov + Serebryakov)

Remaining 75 sources are standalone works (single Upaniṣads, Kāmasūtra, Manusmṛti, Kālidāsa kāvyas, etc.) with no obvious parent. Adding Upaniṣads as a corpus parent is feasible follow-up but semantically weaker (each is a distinct work, not a volume of a single book).

### Files
- `web/app/parent_works.py` — new registry module with `_PARENT_WORK_PATTERNS` and `detect_parent_work` lookup.
- `web/app/services/source_metadata.py` — imports the registry, builds `isPartOf` as list-or-dict accordingly.
- `web/tests/test_parent_works.py` — 13 tests covering each parent-work category, false-positive guard (anchored patterns, unrelated filenames), and the list-vs-dict shape preservation.

### Notes
- 241/241 hermetic tests pass.
- Schema.org purist would prefer `exampleOfWork` for translations and `about` for commentaries; collapsed into `isPartOf` for v1 — Google parses both leniently and the simpler model keeps the registry maintainable.

## [1.15.4] - 2026-05-17 (Feature: IAST alternateName on author Person)

### Added
- **Author IAST as `alternateName`** on the JSON-LD `Person` entity. The 14 source pages with detected authors now emit both the Cyrillic display form and the standard scholarly IAST transliteration — giving Google an unambiguous Latin-alphabet handle for disambiguation and Knowledge-Graph linking. Verified end-to-end on five real source pages including prefix-form (Bhartṛhari at sid=281), suffix-form (Bhartṛhari at sid=282), and multi-word (Vātsyāyana Mallanāga at sid=270).
- **`_AUTHOR_IAST` mapping** in `source_metadata.py`: 11 entries covering Abhinavagupta, Aśvaghoṣa, Bilhaṇa, Bhartṛhari, Vātsyāyana, Vātsyāyana Mallanāga, Jayadeva, Kālidāsa, Patañjali, Rāmānuja, Yāmunācārya.

### Changed
- **`KNOWN_SANSKRIT_AUTHORS` is now derived from `_AUTHOR_IAST.keys()`** — single source of truth so adding a new author requires one entry, not two. Existing membership tests (`in`, `len()`) continue to work unchanged.

### Tests
- 6 new tests: IAST mapping covers every known author, IAST values are Latin-only (catches accidental Cyrillic copy-paste), alternateName emission for prefix-form detection, Kālidāsa-specific shape, multi-word author IAST, suffix-form detection still attaches IAST. 228/228 hermetic tests pass.

## [1.15.3] - 2026-05-17 (Feature: `<lastmod>` on sitemap entries)

### Added
- **`<lastmod>YYYY-MM-DD</lastmod>` on every sitemap URL**, sourced from `corpus_meta.generated_at` (written by `ingest.ingest`). All 1,420 sitemap URLs now carry the corpus-build date as a freshness signal so Google can prioritise re-crawling after a re-ingest. Verified end-to-end on the live corpus: sitemap grew from 102 KB → 145 KB with `<lastmod>2026-05-16</lastmod>` on every `<url>` entry.
- **`_get_corpus_lastmod(db)`** helper parses the full ISO timestamp written by ingest down to date-only form (`'2026-05-17T12:34:56.789012'` → `'2026-05-17'`). W3C-DTF compliant; Google honours daily granularity for crawl signalling.

### Fail-soft behaviour
- Missing `corpus_meta.generated_at` → no `<lastmod>` emitted, sitemap still serves and remains well-formed XML.
- Malformed `generated_at` value → same fall-back. A single bad date would otherwise make Google reject the whole sitemap; the shape check (`YYYY-MM-DD` form) catches it locally and degrades to no-lastmod.

### Files
- `web/app/main.py` — `_get_corpus_lastmod` + threading `<lastmod>` through every URL builder in `/sitemap.xml`.
- `web/tests/test_sitemap_lastmod.py` — 8 tests covering parser (date extraction, missing/malformed handling), HTTP-level lastmod-per-URL parity, well-formed XML preservation, format validation, and fail-soft on malformed corpus_meta.

### Notes
- 222/222 hermetic tests pass.
- All URLs share the same lastmod because each one's content depends on the same corpus build (source pages directly, /compare/* and /q/* via FTS hits). Per-source ingest timestamps would need a schema change; deferred.

## [1.15.2] - 2026-05-16 (Feature: structured author on source-page JSON-LD)

### Added
- **`Book.author` JSON-LD field** when the source title attributes a Sanskrit-tradition writer. Curated allow-list (`KNOWN_SANSKRIT_AUTHORS`) of 11 names: Абхинавагупта, Ашвагхоша, Бильхана, Бхартрихари, Ватсьяяна, Ватсьяянга Маланга, Джаядева, Калидаса, Патанджали, Рамануджа, Ямуначарья. Detector supports both title conventions seen in the corpus: prefix form (`"Бхартрихари. Шатакатраям"`) and suffix form (`"Шатакатраям. Бхартрихари (1979)"`, `"Рагхуванша. Род Рагху. Калидаса (1996)"`). Longer names win on a prefix match (so "Ватсьяянга Маланга" beats any one-word substring).
- **False-positive guard**: work titles that contain periods but aren't author-prefixed — `"Ригведа. Мандала I"`, `"Атхарваведа. Книга 1"`, `"Махабхарата VI"` — correctly return empty author. Verified by dedicated regression test.

### Coverage on live corpus
- 14 of 148 sources now carry a structured author: 2× Rāmānuja, 1× Yāmunācārya, 1× Abhinavagupta, 2× Kālidāsa, 1× Jayadeva, 2× Aśvaghoṣa, 1× Bilhaṇa, 1× Vātsyāyana, 2× Bhartṛhari (both Leonov prefix-form and Serebryakov suffix-form), 1× Patañjali.

### Notes
- `Book.author` and `Book.translator` coexist when both are detected — the modern translator is a separate field from the original work's author.
- Anonymous works (Mahābhārata, Bhagavadgītā, Vedas, Upaniṣads) deliberately have no author — we don't fabricate "Vyāsa" for MBh or similar attributions.
- 9 new tests covering single-word and multi-word prefix detection, suffix-segment detection, false-positive guard, anonymous-work omission, JSON-LD field emission. 214/214 hermetic tests pass.

## [1.15.1] - 2026-05-16 (Feature: per-line Quotation JSON-LD on source pages)

### Added
- **`Book.hasPart` sample + `numberOfItems` on every source page** — the existing `Book` JSON-LD now nests up to 20 `Quotation` entries (the first verses with non-empty text) and carries a `numberOfItems` count of the full filtered verse set. Live measurements: Smirnov BhG `numberOfItems=720`, Bhīṣma-parvan `1459`, Īśa Upaniṣad `22`. Each hasPart entry has `@id` pointing at the `?highlight=` URL for that verse, so Google can crawl them as distinct sub-entities.
- **Per-page highlighted Quotation** — when `?highlight=X` is in the URL (typical for a deep link from a search hit or the comparison view), a third top-level `<script type="application/ld+json">` is emitted carrying just the highlighted verse as a `Quotation` with `@id` = canonical URL of that page variant, `isPartOf` linking back to the Book, and `citation` from chapter + link_id when available. Falls back to two-block output when the highlight doesn't resolve to any line — never fabricates structured data from missing content.
- **`line_text` truncation cap (1500 chars)** — protects against the few Smirnov-edition rows that pack ~6 KB of footnote prose into a single corpus_lines row. Most real verses are well under the cap.

### Changed
- **`reader.py` SQL now selects `line_text`** in addition to `line_html` so the JSON-LD builder has the plain-text content it needs. The template's display continues to use `line_html`.
- **`source_metadata.build_source_jsonld`** gains optional `sample_lines`, `sample_size`, and `base_url` keyword args. Existing calls without samples continue to work unchanged.
- **`source_metadata.build_line_quotation`** is the new single-Quotation builder used for the highlighted-line block.

### Files
- `web/app/services/source_metadata.py` — new builders + truncation helper.
- `web/app/routers/reader.py` — selects `line_text`, constructs highlight Quotation when present.
- `web/templates/source_view.html` — conditional third JSON-LD block.
- `web/tests/test_source_metadata.py` — 13 new tests: hasPart cap enforcement, empty-text skipping, missing-sample omission, base_url plumbing, single-Quotation shape, line_num fallback, URL encoding of `1.3-6` ranges, truncation cap, HTTP integration for hasPart, two-block vs three-block emission, unmatched-highlight defence.

### Notes
- 203/203 hermetic tests pass.
- Page-weight verification on real corpus: JSON-LD overhead is 10-22 KB per source page even for the 2.5 MB Bhīṣma-parvan — well within proportional bounds.

## [1.15.0] - 2026-05-16 (Feature: popular-query landing pages)

### Added
- **`GET /q/{slug}`** — SEO landing pages for ~30 high-intent Russian-language Sanskrit-studies queries. Each page renders a curated definition, IAST + Devanagari forms, 20 example verses from the primary corpus, related-term cross-links, and a "Все результаты →" deep-link to `/search?q={term}`. Canonical lowercase URL, OG/Twitter card, `DefinedTerm` JSON-LD inside a `WebPage`.
- **`web/app/popular_terms.py`** — registry of 30 terms across two tiers: 19 concepts (дхарма, карма, атман, брахман, мокша, сансара, йога, бхакти, нирвана, аватара, гуна, ом, мантра, дхьяна, варна, ашрама, веды, упанишады, пуруша) + 11 proper nouns (Кришна, Арджуна, Шива, Вишну, Брахма, Рама, Индра, Сарасвати, Лакшми, Хануман, Ганеша). Each entry carries Cyrillic display term + IAST + Devanagari + short neutral definition + `search_query` (morphological root for FTS5 prefix matching: "дхарм" matches дхарма/дхармы/дхарме/дхарму) + bidirectional `related` cross-links.
- **`REFERENCE_WORK_FILENAMES`** — exclusion set of 20 dictionary/lexicon/encyclopedia source filenames (Smirnov, Monier-Williams, Apte, KEWA, Vasmer, encyclopedias of Indian philosophy & mythology, per-work indexes). Landing pages restrict to corpus-text sources so example verses come from the Ṛgveda / Mahābhārata / Upaniṣads / Bhagavadgītā rather than dictionary glosses. Dictionary search remains unaffected on `/search` and `/api/search`. Verified end-to-end: `/q/dharma` now surfaces Ṛgveda mandala VIII/X, Mahābhārata I; `/q/atman` surfaces Atharvaveda 10–11, Mahābhārata III; `/q/moksha` hits Mahābhārata IX/XV with 5 ⇔ переводы cross-links flowing through to the Gītā comparison view.
- **Sitemap inclusion** — all 30 `/q/{slug}` URLs at priority 0.9.

### Files
- `web/app/popular_terms.py` — term registry + REFERENCE_WORK_FILENAMES.
- `web/app/routers/popular_terms.py` — handler + `_fetch_primary_source_ids` (excludes reference works).
- `web/templates/popular_term_page.html` — full page with hero (term + forms + definition), corpus examples block (reuses `result_fragment.html`), related-term grid, JSON-LD DefinedTerm.
- `web/app/main.py` — router registration + sitemap entries.
- `web/tests/test_popular_terms.py` — 21 tests: registry integrity (slug shape, bidirectional related links, no self-references, case-insensitive lookup), HTTP routing (200 / 404 / canonical / case-insensitivity / oversized / punctuation defence), template content (definition, forms, related, full-search link), JSON-LD validity, sitemap inclusion, reference-work exclusion sanity.

### Notes
- 190/190 hermetic tests pass.
- The ⇔ переводы compare-link from v1.13.1 surfaces automatically on landing pages whose hits land in comparison-eligible sources (Bhagavadgītā, Yoga-Sūtra, Śatakatraya, MBh-Bhīṣma-parvan).

## [1.14.1] - 2026-05-16 (Feature: JSON-LD on source pages)

### Added
- **`Book` JSON-LD on every `/sources/{id}` page** — schema.org graph with `@id`, `name`, `url`, `inLanguage: "ru"`, `translator` (Person), `datePublished`, and a `WebSite` parent. Smoke-verified on five real sources: Smirnov BhG (1977), Erman MBh VI (2009), Sürkin Īśa Upaniṣad (1992), Bhartṛhari Śatakatraya (2020), and Buddhacarita (no year — `datePublished` correctly omitted rather than emitted empty).
- **`BreadcrumbList` JSON-LD** — minimal two-step Site → Source breadcrumb. Parent-work levels (Mahābhārata → Bhīṣma-parvan) are deferred until a curated work-registry exists.
- **`<link rel="canonical">`** added to source pages.
- **`web/app/services/source_metadata.py`** — `parse_source_title(title)` decomposes the loose `[Author. ]Work (Year); Translator` convention used across the corpus. The full title stays as `name`; year and translator are extracted independently and only emitted when present, so anthologies (no translator) and undated translations (no year) don't pollute the JSON-LD with empty strings. Verified against the seven shape variants observed in the live corpus (with/without year, with/without author prefix, with/without semicolon, 18th-century years).

### Files
- `web/app/services/source_metadata.py` — parser + JSON-LD builders.
- `web/app/routers/reader.py` — calls builders, threads context into template.
- `web/templates/source_view.html` — renders canonical link + two JSON-LD `<script>` blocks.
- `web/tests/test_source_metadata.py` — 16 tests (7 parser, 5 builder, 2 breadcrumb, 2 HTTP integration).

### Notes
- 169/169 hermetic tests pass.
- **Deliberately deferred**: per-line `Quotation` entries (would balloon page weight to 100-200 KB for large works); parent-work `isPartOf` detection; structured author (the prefix in "Бхартрихари. Шатакатраям" → `author: Person`).

## [1.14.0] - 2026-05-16 (Feature: server-rendered /search page)

### Added
- **`GET /search?q=…`** — server-rendered search results page, the SEO surface for content queries. Distinct from `/` (live JS app) and `/api/search` (JSON API). Results are in the initial HTML payload — Googlebot doesn't need to execute JS to see them. Form is plain GET, so the page is functional without scripts.
- **Canonical URL normalisation**: `<link rel="canonical">` points at a deterministic form — query lowercased + stripped, default params (`mode=plain`, `cs=0`, `ww=0`, no `src`) dropped, source IDs sorted ascending. Mixed-case / reordered URLs converge on one canonical, preventing duplicate-content penalties. Verified end-to-end:
  - `?q=Кришна&cs=1` → `q=кришна&cs=1`
  - `?q=  Karma  ` → `q=karma`
  - `?q=dharma&mode=plain&cs=0&ww=0&src=219,217,204` → `q=dharma&src=204,217,219`
- **`noindex,follow` for junk pages**: 1-character queries, regex mode, zero-result pages get the robots meta to keep crawl budget clean. Normal multi-character plain queries with hits stay indexable.
- **JSON-LD `SearchResultsPage`** with `ItemList` numberOfItems and a `WebSite` parent carrying a `SearchAction` so Google can render a sitelinks search box. Emitted only when the page is indexable.
- **Cross-link integration retained**: the page reuses `html_service.render_fragment`, so the `⇔ переводы` cross-links from v1.13.1 work automatically. A search for "дхарма" renders 147 compare buttons in the server HTML; "карма" 403; "Кришна" 1030.

### Files
- `web/app/routers/search_page.py` — handler + `_canonical_search_url`, `_parse_source_ids`, `_should_noindex` helpers.
- `web/templates/search_page.html` — full page shell with navbar, form (plain GET), result fragment slot, JSON-LD, canonical/OG/Twitter meta.
- `web/app/main.py` — router registration.
- `web/tests/test_search_page.py` — 22 tests covering canonical normalisation, noindex rules, empty/normal/short/zero-result/regex paths, form input echo, malformed-input defence, oversized-query rejection, and regression check that `/` still serves the live app.

### Notes
- The live JS app at `/` is unchanged. The "Живой поиск ↗" link in the `/search` navbar points back to it.
- 153/153 hermetic tests pass. Pre-existing `test_publish.py` collection error remains unrelated.

## [1.13.2] - 2026-05-16 (Feature: per-work index page + sitemap entries)

### Added
- **`GET /compare/{work_slug}`** — per-work hub page listing every chapter with a grid of verse links. Acts as the navigation root for `/compare/{work}/{ch}.{v}` leaves and as a crawlable internal-linking hub. Renders against the real corpus at 89 KB for Bhagavadgītā (18 chapters / 734 verses), 27 KB for Yoga-Sūtra (4 / 195), 39 KB for Śatakatraya (3 / 309). Includes canonical link, OG/Twitter card, and JSON-LD `WebPage` → `mainEntity: ItemList` of 18/4/3 chapters.
- **`compare_service.enumerate_verses(db, work_slug)`** — returns the sorted `(chapter, verse)` set where the comparison view will surface at least one hit. Aggregates across every source listed for a work, expands range-merged link_ids (`1.3-6` → 4 pairs), and applies the inverse chapter offset for bridge sources (MBh Bhīṣma adhyāyas 23-40 → BhG chapters 1-18; pre- and post-Gītā Bhīṣma chapters are silently dropped). Helper `_expand_link_id(link_id)` factored out for reuse.
- **`/sitemap.xml`** now includes the 3 per-work hubs (priority 0.9) and **1,238 leaf comparison URLs** (priority 0.7): 734 Bhagavadgītā, 195 Yoga-Sūtra, 309 Śatakatraya. Total sitemap size ≈ 102 KB, 1,390 `<url>` entries — comfortably under the 50K-URL / 50 MB single-sitemap limit. Each URL is genuinely unique on the Russian-language web.

### Tests
- 13 new tests in `test_compare.py`: `_expand_link_id` helper coverage (exact, range, single-verse range, inverted range, non-verse anchors), `enumerate_verses` against fixtures (cross-source aggregation + range expansion, out-of-range bridge chapters dropped, unknown work returns empty), HTTP-level index route (hub renders, 404 on unknown work, empty-chapter messaging for Yoga-Sūtra without fixture data), and sitemap inclusion (all three hubs present, leaf URLs from BhG fixtures present). 131/131 hermetic tests pass.

## [1.13.1] - 2026-05-16 (Feature: search-result cross-link to comparison view)

### Added
- **Search results now surface a `⇔ переводы` cross-link** next to the `↗` source-view link whenever the hit's source is in any work's comparison set (Bhagavadgītā: 10 translations + 1 anthology + 2 commentaries + MBh-Bhīṣma bridge; Yoga-Sūtra: 4 sources; Śatakatraya: 2 sources). Clicking it opens `/compare/{work}/{ch}.{v}` in a new tab. For the rest of the corpus (Ṛgveda, Atharvaveda, Upaniṣads, Rāmāyaṇa, dictionaries, etc.) no link is rendered.
- **MBh-Bhīṣma bridge applies the inverse chapter offset**: a search hit at `link_id="23.1"` cross-links to `/compare/bhagavadgita/1.1`, letting users pivot from Erman's prose rendering to the 14-way Gītā comparison. Pre-Gītā (Bhīṣma chapters 1–22) and post-Gītā (chapters 41–117) hits are silently excluded — verified end-to-end: a search for "дхармы" inside Bhīṣma-parvan renders the compare link only for the `23.1` hit, not for the 8 surrounding battle-narrative range-merged blocks.
- **Range-merged link_ids** like `1.5-7` route to the first verse (`/compare/.../1.5`); the comparison page's own range-fallback then resurfaces the same merged block on the destination.

### Changed
- `web/app/services/search_service.py` SQL selects `s.filename as source_filename` (both plain and regex paths) so the renderer has the data it needs without an extra query.
- `web/app/services/html_service.py` enriches each result item with `compare_url` before grouping; the value is `None` for non-eligible sources and missing/empty link_ids.
- `web/app/services/compare_service.py` gains `compare_url_for_hit(filename, link_id)` with a reverse filename→work index built once at import.
- `web/templates/result_fragment.html` conditionally renders the `⇔ переводы` button before the source-view `↗`.

### Tests
- 11 new tests in `test_compare.py`: helper unit coverage (standalone, bridge, range-merge, out-of-range, non-comparison, empty) + rendering integration (eligible hit shows button, MBh bridge hit shows BhG URL, Ṛgveda hit omits link, missing filename is safe). 118/118 hermetic tests pass.

## [1.13.0] - 2026-05-16 (Feature: multi-translation comparison route)

### Added
- **`GET /compare/{work_slug}/{ch}.{v}`** — server-rendered multi-translation comparison view. For one verse coordinate, fetches every configured source and renders them side-by-side grouped by role (translation / anthology / commentary / context). End-to-end against the real corpus:
  - Bhagavadgītā 1.1 surfaces **14 hits** — 10 Russian translations (Petrov 1788 through Blinderman 2016), 1 collected-translations anthology, 2 medieval Sanskrit commentaries (Rāmānuja's Gītābhāṣya and Abhinavagupta's Gītārthasaṃgraha), and the Mahābhārata Bhīṣma-parvan source resolved via `chapter_offset=22` bridge (Gītā 1.1 → MBh `link_id=23.1`).
  - Yoga-Sūtra 2.46 surfaces 4 hits (3 standalone translations + 11-translation anthology).
  - Śatakatraya 1.1 surfaces both Serebryakov and Leonov.
- **Range-merge fallback**: a request for verse 1.5 will match a source whose `citation_block` is keyed `1.3-7` (covering 1.5), with the page badge `в блоке 1.3-7` shown so users see why the verse appears in a merged stanza.
- **IAST extraction**: Sanskrit `<div class="chapter_block iast">` content is pulled from the first source that has it and shown once at the top, then stripped from per-source HTML to avoid 10× duplication.
- **JSON-LD on every comparison page** (`WebPage` → `mainEntity: Quotation` → `workTranslation: [Quotation, …]`) with `inLanguage: "sa"` on the original and `inLanguage: "ru"` per translation. Plus `rel=canonical`, OG/Twitter card meta, and `og:locale:alternate=sa_IN` for parallel-language signal.
- **Files**: `web/app/compare_config.py` (work definitions for `bhagavadgita`, `yogasutra`, `shatakatrayam`), `web/app/services/compare_service.py` (data layer with `_link_id_covers`, `_split_iast_and_translation`, `get_comparison`), `web/app/routers/compare.py` (HTTP layer with validation, prev/next pager), `web/templates/compare_view.html` (responsive layout with role-grouped sections), and 17 unit tests in `web/tests/test_compare.py`.

### Notes
- **Buddhacarita is deliberately excluded** — Leonov (Sanskrit critical edition, 14 cantos) and Balmont (1913, translated from Beal's English of the Chinese/Tibetan expanded text, 29 cantos) coincidentally share `id="X.Y"` but address completely different source verses; spot-check at canto 1 verses 5/10/40 showed full content divergence by verse 1.5.
- **Sitemap not updated** in this commit — ~1,200 comparison URLs (BhG ~700 + YS ~195 + Śatakatraya ~300) are a separate concern. Hold off until per-work index pages exist.
- **Cross-link from search results** to comparison view is not yet wired — needs a small `result_fragment.html` change to detect when a hit's source is in the comparison-eligible set.
- **107/107 hermetic tests pass** (+17 new). Pre-existing `test_publish.py` collection error remains unrelated and unchanged.

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
