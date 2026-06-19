# Samudra Manthanam — Roadmap H2 2026: DH Standards + Cross-Platform Offline

**Status: CURRENT / LIVING STATUS** (supersedes the mobile/data-model portions of `ARCHITECTURE_REVIEW_6_MONTH_ROADMAP.md`; that document remains current for web-platform hardening).

**Last updated:** 2026-06-19
**Window:** mid-June — mid-December 2026
**Workforce:** maintainer + Claude Code sessions (same model as the v1.x web platform)
**Audience:** Russian-speaking Sanskrit scholars and students. UI stays Russian; metadata gains an English layer for discoverability only.

---

## Status legend

- **Done:** implemented or specified enough to be treated as a stable input.
- **In progress:** active implementation/spec work exists, but acceptance is not complete.
- **Blocked:** technically staged, but waiting on an external condition or rights/ops decision.
- **Next:** planned near-term work.
- **Deferred:** intentionally outside the current implementation lane.

## Where things stand (2026-06-19)

- **Phase 0 identity/metadata:** **In progress.** The stable-ID and converter contracts are specified in `docs/LINE_ID_SCHEME.md` and `docs/CONVERTER_SPEC.md`, but source metadata/rights surfacing and UI citation/version work are not fully complete.
- **Phase 1 canonical JSONL:** **In progress.** The converter exists at `web/corpus_builder/html_to_canonical.py`; specs are frozen enough for implementation; nested commentary extraction is fixed and covered by regression tests. Remaining work: intentional full-corpus JSONL regeneration, full round-trip verification, and switching ingest/build paths to canonical JSONL.
- **Phase 2/3 offline path:** **Designed / staged.** `docs/PHASE2_PLAN.md` and `docs/OFFLINE_SEARCH_DESIGN.md` contain the current design and implementation findings. Treat those as active design inputs, but do not mark the roadmap acceptance complete until current tests prove the PWA/offline-search gates.
- **Wisdomlib:** **Blocked candidate.** The catalog/crawler groundwork is complete and hardened, but bulk Stage C content capture is blocked by IP/rate limits and rights posture. It must not block the core Samudra canonical JSONL/offline-search roadmap.
- **Active PR context:** PR #7 on `offline-search` carries the wisdomlib workflow hardening and converter/commentary documentation updates.

---

## Settled decisions (June 2026)

1. **Corpus rights are knowingly grey.** The Russian translations (Елизаренкова and similar Наука editions) are not cleared for open redistribution. Therefore: **no Zenodo deposit, no DOI'd open data dumps, no public TEI downloads.** The corpus continues to ship *inside* the application (as it already does in the Windows release zips) and via the search service. Open publication is out of scope until rights change.
2. **Target: full offline search on Windows, macOS, Android, iOS.** Delivered through the browser (PWA + sqlite-wasm), not through native ports. The Lazarus desktop app is maintenance-frozen.
3. **Data model: lightweight structured canonical format** (JSONL per text), not full TEI. TEI export remains possible later *from* this format if rights ever permit.
4. **Six-month horizon, AI-driven implementation.**

---

## Why (DH-standards gap analysis, summary)

| Gap | Standard practice | Fix in this roadmap |
|---|---|---|
| Presentational HTML is the master format; alignment implicit in line order | TEI / explicit structured source with standoff alignment | Phase 1: canonical JSONL with explicit alignment groups; HTML becomes a generated view |
| Permalinks break on re-ingest (source IDs are ordinal) | Persistent identifiers (CTS-style `work.chapter.verse`) | Phase 0: stable IDs, filename-keyed sources |
| Code license (Apache 2.0) silently implies data license | Per-source rights statement | Phase 0: `rights` field in per-source metadata; explicit "data ≠ code license" note in README |
| IAST / SLP1 / Devanagari mixed, undeclared; equivalent queries diverge by script | One canonical internal encoding + declared script per segment + query-time transliteration | Phase 1: SLP1 canonical layer, script tags, transliterating query expansion |
| No machine-readable bibliography, no CITATION.cff, no corpus version visible to users | FAIR metadata, versioned citation | Phases 0 & 4 |
| Provenance of each text (edition, digitizer, corrections) unrecorded | Per-source provenance records (cf. Cologne `printchange.txt` discipline) | Phase 0 metadata schema includes provenance |
| HTML-only export | Structured exports (JSON/CSV) for reuse | Phase 4 |
| ~20 overlapping planning docs in repo root | Single docs index, archive for superseded plans | Phase 0 housekeeping |

---

## Phase 0 — Stable identity & metadata foundation (weeks 1–3)

**Status:** In progress / partially specified.

The cheapest, highest-leverage DH fixes. Everything later builds on these.

**Current notes:** Stable IDs are specified in `docs/LINE_ID_SCHEME.md`; the converter and validation contract are specified in `docs/CONVERTER_SPEC.md`. Remaining Phase 0 work is mostly metadata/rights propagation, corpus version surfacing, and UI/citation visibility.

1. **Stable line identifiers.** Define `work.chapter.verse[.line]` ID scheme; persist it in `corpus_lines` independent of ingest order. Anchor permalinks and the compare route switch from ordinal source IDs to filename/work-slug keys (already flagged in `.ai_state.md` as the long-term fix).
2. **Per-source metadata files.** `Data/<name>.meta.json` next to each corpus HTML: title (ru/en), translator, print edition, year, scripts present, provenance/digitization notes, rights note. Ingest copies it into `corpus.db`; the web UI source pages and JSON-LD read from it.
3. **Corpus versioning surfaced.** `corpus_meta` version shown in the UI footer, in exports, and in citation strings ("Samudra Manthanam corpus v2026.06").
4. **CITATION.cff + README rights clarification.** Code citable; explicit statement that Apache 2.0 covers code only and corpus texts carry their own rights.
5. **Docs housekeeping.** Move superseded plans (`roadmap.md`, `WEB_PLAN.md`, `gemini-*`, `GEMINI_*`, old reviews) to `docs/archive/`; root keeps `README.md`, `changelog.md`, `DOCUMENTATION_INDEX.md`, this file, and `ARCHITECTURE_REVIEW_6_MONTH_ROADMAP.md`.

**Acceptance:** re-ingesting the corpus does not break a single saved permalink; every source page shows edition + translator + rights; golden-query suite green.

## Phase 1 — Canonical data layer (months 1–2)

**Status:** In progress.

Replace "HTML is the truth" with "structured JSONL is the truth".

**Current notes:** `web/corpus_builder/html_to_canonical.py` exists and now extracts each `comment_item` as a full subtree, including nested `<div>` blocks. `docs/CONVERTER_SPEC.md` records this as a validation gate, and `web/tests/test_converter.py` includes a regression test. Next steps are deliberate JSONL regeneration, full-corpus round-trip verification, ingest/build switching, and a decision on which generated artifacts are committed versus local-only.

1. **Converter** `corpus_builder/html_to_canonical.py`: parses each existing HTML file into JSONL records — `{id, work, chapter, verse, seq, lang, script, text, html_class}` — with explicit **alignment groups** linking Sanskrit lines to their Russian translation lines (currently implicit in interleaving).
2. **Script normalization.** Detect script per segment; store canonical **SLP1** alongside the display form (use `indic-transliteration`/aksharamukha). Query layer expands an IAST/Devanagari/SLP1 query to all stored forms — fixes "same word, different script, different results".
3. **HTML becomes a generated view.** A renderer reproduces the current reader HTML (and the desktop app's files) from JSONL, byte-comparable where feasible. The `.no_tags` sidecars are retired (generated on demand).
4. **Ingest reads JSONL.** `corpus.db` build switches source; round-trip regression: line counts, link_ids, golden queries identical before/after.
5. **Correction workflow rebased.** Corrections apply to JSONL records (one record = one addressable unit), with an audit-trail change log per corpus version — same philosophy as the Cologne `updateByLine.py` pattern.

**Acceptance:** full corpus round-trips HTML → JSONL → HTML with no search regression; one text demonstrably queryable across all three scripts with identical hits.

## Phase 2 — Mobile-ready web + PWA shell (month 3, overlaps Phase 1)

**Status:** Partially designed / next implementation gate. See `docs/PHASE2_PLAN.md`.

Phase 2 stays decoupled from Phase 1 except where the offline reader later consumes the canonical JSONL format.

1. Responsive audit of all templates on 380 px viewports (search, reader, compare); touch-friendly result navigation; Devanagari/IAST font loading strategy for mobile (subset Charis SIL / Sahitya).
2. **PWA manifest + service worker:** installable on Android/iOS/macOS/Windows; app shell and static assets cached; online search unchanged.
3. **Offline reader:** user picks texts to keep offline; service worker caches the reader pages + per-text JSON. (First offline milestone, independent of wasm search.)

**Acceptance:** Lighthouse PWA installable on Android Chrome and iOS Safari; a cached text fully readable in airplane mode.

## Phase 3 — Full offline search (months 3–5) — the centerpiece

**Status:** Designed / staged. See `docs/OFFLINE_SEARCH_DESIGN.md`.

The offline-search design document records implementation findings, but roadmap acceptance remains open until current tests prove the PWA/offline-search gates end to end.

1. **Slim the database.** Current `corpus.db` ≈ 500 MB because lines are stored twice (HTML + plain) plus FTS index. Build an **offline pack format**: contentless/`content=` FTS5, no stored HTML (rendered from JSONL), per-text packs. Target ≤ 150 MB full corpus, downloadable per text group (Vedas / Epics / Kāvya…).
2. **sqlite-wasm in the browser** with OPFS storage: the same FTS5 queries run client-side. The `SEARCH_CONTRACT.md` semantics (prefix matching, AND logic) are the shared spec; golden queries run against the wasm build in CI.
3. **Search dispatcher with fallback:** offline-first when packs are installed, server search otherwise; identical result rendering (the existing `html_fragment` pipeline reused client-side via the same Jinja-rendered templates or a JS renderer fed by JSON results).
4. **Platform constraints handled explicitly:** iOS Safari OPFS quota and eviction (persist storage API, re-download path); Android background download; desktop browsers trivial.
5. **Regex + morphology offline:** regex via JS `RegExp` over the pack (bounded, same 5 s budget); stem/root lookup uses the pre-computed offline morphology cache (no Sanskrit Heritage dependency offline — consistent with the existing "offline morphology" roadmap item).

**Distribution note:** offline packs are served only from the app's own origin to its installed users — the same distribution posture as today's Windows release zips; no new rights exposure, and no public "download the corpus" endpoint.

**Acceptance:** on a phone in airplane mode, an installed PWA answers the golden-query suite with results identical to the server (modulo regex resource limits); pack download UX survives interruption.

## Phase 4 — Scholarly citation, exports, discoverability (months 5–6)

**Status:** Next / later.

Rights constraints remain unchanged: exporting search results is in scope; public bulk corpus exports remain out of scope.

1. **Citation strings everywhere:** reader, compare, exports emit "Work chapter.verse, trans. X, ed. Y — Samudra Manthanam corpus vN, URL#stable-anchor".
2. **Structured exports:** JSON and CSV export of search results (query, mode, corpus version, stable IDs) alongside HTML. These export *results*, not bulk texts — staying inside the rights posture.
3. **Discoverability layer:** English-language per-source metadata pages + JSON-LD (`schema.org/Dataset`-adjacent description of the *service*, `CreativeWork` per text), proper hreflang; UI remains Russian.
4. **Desktop endgame:** final Lazarus release whose update manifest announces the web/PWA successor; corpus-sync API kept read-only for stragglers; repo section marked maintenance-frozen.

**Acceptance:** a citation pasted into an article resolves to the same line a year later; an English Google query for "Elizarenkova Rigveda parallel corpus" can find the source page.

---

## Candidate Corpus Source: Wisdomlib

**Status:** Blocked candidate.

- **Catalog Stage A/B:** Done. The crawler catalog contains 848 entries and the human-readable summary lives in `web/corpus_builder/wisdomlib/CATALOG.md`.
- **Stage C crawler:** In progress / hardened. The code is proven on small clear-IP runs and now avoids committing content, validates cache state, and reports blocked runs clearly.
- **Operational block:** GitHub/datacenter egress is Cloudflare-blocked, and the currently tested hosting-range IP is rate-limited/exhausted. The workflow is manual and self-hosted only.
- **Required next step:** Install a self-hosted runner on a residential ISP connection, then trigger the `wisdomlib gentle crawl` workflow manually in small resumable passes.
- **Rights posture:** Stage C output remains cache/artifact-only and is never committed. Wisdomlib has no bulk-reuse license, so downloaded content is provisional and non-redistributable.
- **Roadmap implication:** Wisdomlib can inform future corpus expansion, but it is not a dependency for the core Samudra canonical JSONL, PWA, or offline-search work.

---

## Out of scope (explicitly)

- Open data dumps, Zenodo/DOI for the corpus, public TEI downloads — blocked on rights.
- Full TEI P5 master format — JSONL canonical instead; TEI is a possible future *export*.
- Native iOS/Android apps (Tauri/Capacitor) — revisit only if app-store presence becomes a goal.
- Porting the Lazarus app to macOS — superseded by PWA.
- Full inflection-aware morphology — separate initiative, unchanged from previous roadmaps.

## Top risks

1. **sqlite-wasm pack size / iOS storage eviction** — mitigate with per-text packs, `navigator.storage.persist()`, and a clean re-download path. Prototype in Phase 3 week 1 before committing.
2. **HTML→JSONL conversion fidelity** across 152 heterogeneous hand-made files — mitigate with byte-level round-trip tests and per-file converter quirks table; convert the messiest file first.
3. **Two search engines (server FTS5 + wasm FTS5) drifting** — mitigate: one pack-build pipeline, golden queries in CI against both.
