# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.19.27] - 2026-08-08
### Changed
- **Corpus_builder Phase 2 shared utils via OtherUnitFiles (H2430, Grok 4.5 `grok-4.5`).** `cb.lpi` / `cb_headless.lpi` set `OtherUnitFiles=dcu;..\..\Units`; single [`Units/uTypes.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Units/uTypes.pas) (promoted `TWideStringArr`; obsolete `dcu/uTypes` removed). Builder `TextU` dual-kept in `dcu/` (name collision with Index `textu`, H2429). Phase-2 common-dir + SHARED_CODE registration checkboxes ticked. Doc: [`docs/H2430_OTHERUNITFILES_SHARED_UTILS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2430_OTHERUNITFILES_SHARED_UTILS.md). `lazbuild` green: cb (7318 lines), cb_headless, Index.

### Fixed
- **`cb_headless.lpr` program terminator** was `end;` (FPC Fatal 2003); corrected to `end.` so headless `lazbuild` links again (noticed while proving H2430).

## [0.19.26] - 2026-08-08
### Added
- **H2394 P9 UX acceptance on prod (Grok 4.5 `grok-4.5`).** Bilingual Sa+Ru + deep-link probes against `https://samudra.193.232.229.92.sslip.io/` — **11/11 PASS** (vishnu-smriti, yajnavalkyasmriti, ṛgveda). Checklist + probe script + JSON: [`docs/acceptance/H2394_UX_ACCEPTANCE_BILINGUAL_DEEPLINK_CHECKLIST.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/acceptance/H2394_UX_ACCEPTANCE_BILINGUAL_DEEPLINK_CHECKLIST.md). Wave P P9 ticked.
- **Production deploy runbook (H2388, Grok 4.5 `grok-4.5`).** New
  [OPS.md](https://github.com/gasyoun/SamudraManthanam/blob/main/OPS.md):
  copy-paste pull `--ff-only` / pip / `systemctl restart samudra` / smoke /
  code rollback, grounded in live LXC layout (`/opt/samudra` on
  `193.232.229.92`). [DEPLOYMENT.md](https://github.com/gasyoun/SamudraManthanam/blob/main/DEPLOYMENT.md)
  points day-2 ops there; layout/`state.db` path aligned with prod; corpus vs
  code rollback separated. Wave P2 exit.

## [0.19.25] - 2026-08-08
### Added
- **Corpus_builder Phase 4 headless CLI flags (H2432, Grok 4.5 `grok-4.5`).** [`cb_headless.lpr`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/cb_headless.lpr) accepts `cb_headless --build <config.ini|dir> [--out <file.html>] [--check]`; wires progress/error sinks to stdout; Confirm auto-yes (no MessageDlg hang); exit **1** on `HasErrors`, **2** on usage/missing config. Engine: public `OutFileOverride` on `TMhHTMLBuilder` for `--out`. Legacy `cb_headless <dir> [check]` kept for H2427 golden. Roadmap Phase 4 CLI unit ticked. README § Headless CLI. Doc: [`docs/H2432_CLI_HEADLESS_BUILD.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2432_CLI_HEADLESS_BUILD.md).

## [0.19.24] - 2026-08-08
### Added
- **Corpus_builder Phase 2 dcu vs Units canonical diff (H2429, Grok 4.5 `grok-4.5`).** Written comparison of builder `TextU`/`uTypes` vs `Units/` twins: sizes, API deltas, consumer-safe **split** ruling (builder TextU for `cb`; Index `textu` is not a twin; `uTypes` master = builder). Phase-2 first roadmap checkbox ticked. Report: [`docs/H2429_DCU_UNITS_CANONICAL_DIFF.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2429_DCU_UNITS_CANONICAL_DIFF.md).
- **Corpus_builder Phase 0 golden + Phase 3 re-verify (H2427, Grok 4.5 grok-4.5).** case01 fixtures under tests/golden/case01/; headless cb_headless (console) drives TMhHTMLBuilder + CheckAll; run_golden_case01.py --verify byte-exact PASS ×2. CheckPages base-count fix; portable check JSON input basename; RusPage init. Doc: [docs/H2427_GOLDEN_CAPTURE_P3_VERIFY.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2427_GOLDEN_CAPTURE_P3_VERIFY.md).

### Fixed
- **Bṛhannīla-tantra JSONL duplicate comment IDs** (48 identical double rows) blocked full-pin web publish; dropped dups (2533→2485 records). Rebuild corpus-manifest pin: **230** sources / **723 229** records. `*.jsonl text eol=lf` in `.gitattributes` so Windows pin builds match Linux publish.
- **Search stats show server elapsed time** permanently in the result strip (not only a 1.2 s flash on the progress bar).
- **AI Разбор `[object Object]`** on long context lines: client truncates each line to 2000 chars (server cap) and formats FastAPI validation `detail` arrays as readable messages (H2426).

### Changed
- **Compact source overview** replaces the multi-screen SVG bar chart (159×24 px for «огонь»). Top-15 text list + residue + optional scroll for the rest.

### Added
- **`web/scripts/source_overview.py`** — CLI text report of hits by source (top-N + residue, optional `--out` / `--json`).
- **H2415 residual: Ignatiev preface + glossary/bibliography layers (H2449, Grok 4.5 `grok-4.5`).** 17 registered companion sources (700 records): prefaces, four Kāma-samūha glossaries, MBH name/term glossaries, literature/sources, about-author — cut by H2415 as non-verse. Parser [`ignatiev_backmatter.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/ignatiev_backmatter.py); driver [`h2449_backmatter_ingest.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/h2449_backmatter_ingest.py); census [`docs/H2449_IGNATIEV_BACKMATTER_LAYERS_CENSUS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2449_IGNATIEV_BACKMATTER_LAYERS_CENSUS.md); summary [`jsonl/wave_h2449_backmatter_summary.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/jsonl/wave_h2449_backmatter_summary.json). Layer RT **100%** (1 soft Latin-accent fold on Kādambara literatura). Prose commentary remains H2450.
## [0.19.22] - 2026-08-08
### Added
- **H1438 archive remainder ingest (H2415, Grok 4.5 `grok-4.5`).** Seven new ru_only sources registered in `Programdata/data.txt`: Kāma-samūha (685 v), Kādambara-svīkaraṇa-kārikā (128 v), MBH XVI–XVIII Ignatiev (285+110+319 v; distinct from Vasilkov/Neveleva 16–18_*), yoni-pūjā texts (16 v), Bhagavatī-mānasa-pūjā-stotra (69 v). All HTML→JSONL RT **100%**. Driver [`h2415_remainder_ingest.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/h2415_remainder_ingest.py); census [`docs/H2415_IGNATIEV_ARCHIVE_REMAINDER_CENSUS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2415_IGNATIEV_ARCHIVE_REMAINDER_CENSUS.md); summary [`jsonl/wave_h2415_remainder_summary.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/jsonl/wave_h2415_remainder_summary.json). Corpus-manifest pin rebuilt (209 sources / 693 990 records).

### Changed
- **Chapter-open trailing footnote ref (H2415).** `Глава четвертая[249]` opens ch.4 (MBH Ignatiev book 18); unit test `test_chapter_open_allows_trailing_footnote_ref`. Doc: [`PDF_INGESTION_PIPELINE.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/PDF_INGESTION_PIPELINE.md) § Wave remainder.

## [0.19.21] - 2026-08-08
### Added
- **Corpus_builder Phase 3 Lazarus/FPC LCL port (H2417, Grok 4.5 `grok-4.5`).** New [`PSRCBuilder/cb.lpr`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/cb.lpr) + [`cb.lpi`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/cb.lpi); forms as `.lfm`; `{$MODE Delphi}` on engine/utility units. FPC portability fixes (WideString digit ranges in `uMhHTML`, CP-1251 set-of-char → Ord/`IsRussian*` helpers). **`lazbuild` green** on Windows x64 (1603 lines → `lib/x86_64-win64/cb.exe`). Log: [`docs/H2417_LAZARUS_BUILD_WIN64.log`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2417_LAZARUS_BUILD_WIN64.log). Residuals: golden `expected/` capture (Phase 0), Linux `lazbuild`, lazUTF8 encoding layer, Phase 2 unit dedupe.

## [0.19.20] - 2026-08-08
### Changed
- **Wave-A PDF tantras glued-digit re-baseline (H2412–H2414, Grok 4.5 `grok-4.5`).** Yoni 221/0→221/192, Niruttara 674/0→676/322, Guptasādhana 319/0→319/368 comments; HTML→JSONL ≥99.9%; all re-run stable. Census of all Ignatiev registered works: docx stay bracket. Doc: [`docs/WAVE_A_PDF_GLUED_DIGIT_REBASELINE_H2412_14.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/WAVE_A_PDF_GLUED_DIGIT_REBASELINE_H2412_14.md). Residual archive remainder: H2415.

## [0.19.8] - 2026-08-07
### Changed
- **H2370 optional FPC compile residual (Grok 4.5 `grok-4.5`).** Installed Free Pascal 3.2.2 (user prefix); portable stack `mytypes`…`uSort` **compiles and runs** smoke after Dialogs removal. Full `cb.dpr` still needs Delphi 7 `dcc32` (absent). `TextU` has one pre-existing CP-1251 char-set FPC error (not H2370). Logs: [`docs/H2370_FPC_USORT_COMPILE.log`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2370_FPC_USORT_COMPILE.log), [`docs/H2370_DEAD_VCL_STATIC_PROOF.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2370_DEAD_VCL_STATIC_PROOF.md) § FPC compile proof.
- **Nirvāṇa-tantra glued-digit re-baseline (H2385, Grok 4.5 `grok-4.5`).** Re-ingest with H2377 `--footnote-mode glued-digit`: **465 → 527** RU verses, **0 → 212** comments, gaps 64→3, no id_collisions, HTML→JSONL **100%**. Doc: [`docs/NIRVANA_TANTRA_GLUED_DIGIT_REBASELINE_H2385.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/NIRVANA_TANTRA_GLUED_DIGIT_REBASELINE_H2385.md). H2273 debris-path note updated with supersession pointer.

## [0.19.9] - 2026-08-07
### Changed
- **H2370 optional FPC compile residual (Grok 4.5 `grok-4.5`).** Installed Free Pascal 3.2.2 (user prefix); portable stack `mytypes`…`uSort` **compiles and runs** smoke after Dialogs removal. Full `cb.dpr` still needs Delphi 7 `dcc32` (absent). `TextU` has one pre-existing CP-1251 char-set FPC error (not H2370). Logs: [`docs/H2370_FPC_USORT_COMPILE.log`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2370_FPC_USORT_COMPILE.log), [`docs/H2370_DEAD_VCL_STATIC_PROOF.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2370_DEAD_VCL_STATIC_PROOF.md) § FPC compile proof.
- **Nirvāṇa-tantra glued-digit re-baseline (H2385, Grok 4.5 `grok-4.5`).** Re-ingest with H2377 `--footnote-mode glued-digit`: **465 → 527** RU verses, **0 → 212** comments, gaps 64→3, no id_collisions, HTML→JSONL **100%**. Doc: [`docs/NIRVANA_TANTRA_GLUED_DIGIT_REBASELINE_H2385.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/NIRVANA_TANTRA_GLUED_DIGIT_REBASELINE_H2385.md). H2273 debris-path note updated with supersession pointer.

## [0.19.7] - 2026-08-07
### Added
- **Māyā-tantra glued-digit front-end + ingest (H2377, Grok 4.5 `grok-4.5`).** New `--footnote-mode glued-digit|bracket|auto` on `ignatiev_book_to_canonical.py`: page-local DBhP-style notes stripped before verse split; inline glued-digit linking; ToC ghost-chapter drop. Māyā registered: **12 ch / 343 RU verses / 148 comments**, HTML→JSONL round-trip **100%**, re-run stable. `auto` stays `bracket` (Wave-A count lock). Design: [`docs/MAYA_TANTRA_GLUED_DIGIT_MODE_H2377.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/MAYA_TANTRA_GLUED_DIGIT_MODE_H2377.md). Corpus-manifest pin rebuilt.

## [0.19.5] - 2026-08-07
### Added
- **H1438 Wave D: six Ignatiev fragments / selected works (H2376, Grok 4.5 `grok-4.5`).** All registered in `Programdata/data.txt` with desktop HTML + JSONL + `*.meta.json` carrying **explicit partial provenance**. Devī-purāṇa ch.22 (18 v); Liṅga-purāṇa ch.17+29 (124 v); Padma Jālandhara tale only (16 ch / 1039 v — NOT whole Padma); Bhāgavata partial prose (13 ch / 1176 paragraph units); Bṛhannīla selected (18 ch / 1387 v / 1146 notes); Śāktisaṅgama selected (28 ch / 1494 v). HTML→JSONL round-trip ≥99% except Bṛhannīla **97.4%** (documented: 36 endnote-adjacent passages re-keyed as `.commN`). Parser/extract hardenings: excerpt `Из … главы`, trailing-period chapter open, digit `ГЛАВА N`, pypdf PDF fallback, RTF-as-`.doc` + cp1251 reverse, prose paragraph split. Summary: [`jsonl/wave_d_summary.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/jsonl/wave_d_summary.json). Doc: [`PDF_INGESTION_PIPELINE.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/PDF_INGESTION_PIPELINE.md) § Wave D. Corpus-manifest pin rebuilt (201 sources). Māyā-tantra remains **H2377**.

### Changed
- **Corpus_builder dead VCL cleanup (H2370, Grok 4.5 `grok-4.5`).** Dropped unused `Dialogs` from [`uSort.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/dcu/uSort.pas). Split VCL list/clipboard/RichEdit helpers out of [`TextU.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/dcu/TextU.pas) into [`TextUVCL.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/dcu/TextUVCL.pas) so the engine path (`uMhHTML` → `TextU`) no longer imports `CheckLst`/`StdCtrls`/`ComCtrls`/`ClipBrd`/`Windows`. Roadmap unit ticked; inventory §4–§5/§7 updated. Static proof (no dcc32/FPC on this host): [`docs/H2370_DEAD_VCL_STATIC_PROOF.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2370_DEAD_VCL_STATIC_PROOF.md).
## [0.19.4] - 2026-08-07

### Added
- **H1438 Wave C: Kālikā-purāṇa + Devīmāhātmya (H2353, Grok 4.5 `grok-4.5`).** Both works registered in `Programdata/data.txt` with desktop HTML + JSONL. Devīmāhātmya: 13 ch / 595 RU verses / **497 SA matched** (83.5%) via GRETIL Mārkaṇḍeya adhy. 81–93 key-join. Kālikā-purāṇa: 90 ch / 8137 RU verses, `alignment: none` (no keyed SA witness). HTML→JSONL round-trip **100%** on both. Parser hardenings: OLE glued unit-ordinal peel (ch.62), colophon/absurd-jump drop, empty-verse filter. Converter: [`gretil_markp_devimahatmya_to_canonical.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/gretil_markp_devimahatmya_to_canonical.py). Doc: [`PDF_INGESTION_PIPELINE.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/PDF_INGESTION_PIPELINE.md) § Wave C. Corpus-manifest pin rebuilt in the same pass (H2351).

## [0.19.3] - 2026-08-07
### Added
- **Committed corpus pin + hard corpus-gate (H2351, Grok 4.5 `grok-4.5`).** Generated and committed [`web/corpus_builder/manifest/corpus-manifest.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/manifest/corpus-manifest.json) (`bundle_version` 2026.08, **197** sources / **703,699** records, full SHA-256 verify). [`corpus-gate.yml`](https://github.com/gasyoun/SamudraManthanam/blob/main/.github/workflows/corpus-gate.yml) no longer only warns “NOT a pinned-bundle run”: missing pin exits 1; present pin is schema-validated always and full-hash + rebuild-diff validated when checkout JSONL is present. Optional `source_file`/`metadata` blocks that would fall outside `corpus_root` (schema-illegal `..` paths) are omitted. Spec: [`docs/CORPUS_BUNDLE_SPEC.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/CORPUS_BUNDLE_SPEC.md).

### Changed
- **Wave-1 journal truth-pass (H2350, Grok 4.5 `grok-4.5`).** `.ai_state.md` Queue/WIP no longer claim H1926 “in flight” or print an H1927 execute starter — Lanes A–D are recorded as shipped (v0.16.0–v0.19.1); residuals point only at H2351–H2354. Hub GTD execute block for H1924–H1927 closed in the same pass.

## [0.19.2] - 2026-08-07

### Added
- **Legacy `.doc` extract front-end hardened for H1438 remainder (H2352, Grok 4.5 `grok-4.5`).** `extract_text()` prefers `antiword` (cp1251, 120 s timeout, path-bearing errors) and falls back to the OLE WordDocument UTF-16 scan via `olefile`; never returns a silent empty string. Hermetic unit tests cover the OLE path with a synthetic minimal OLE fixture; antiword/archive smokes skip when absent (CI policy: antiword optional). Doc: [`PDF_INGESTION_PIPELINE.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/PDF_INGESTION_PIPELINE.md) § Legacy `.doc` extract. Dep: `olefile==0.47`. Full Wave C/D ingest remains **H2353**.

### Changed
- **Single state-migration runner (H2354, Grok 4.5 `grok-4.5`).** Canonical-reference SQL from H1925 Lane B (`canonical_state_migrations` / `canonical_ref_migrations`) is refiled as [`0004_canonical_reference_columns.sql`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/migrations/state/0004_canonical_reference_columns.sql) and [`0005_canonical_reference_indices.sql`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/migrations/state/0005_canonical_reference_indices.sql). Startup calls the D1 runner once; a one-time bridge imports any pre-absorb B ledger rows into `schema_migrations` under versions `0004`/`0005` with **current** newline-normalised file checksums (old B hashes are not carried). Dual-ledger apply path is gone; `app.canonical_state_migrations` remains as backup/restore + thin path wrappers for the backfill script. Design note: [`web/app/migrations/README.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/migrations/README.md).

## [0.19.1] - 2026-08-06
### Changed
- **Nirvāṇa-tantra re-ingest after H2273 high-N fix (Grok 4.5 `grok-4.5`).** Regenerated `nirvana-tantra.jsonl` / `.raw.jsonl` / `.report.json` from a `pypdf` text-layer extract of the archive PDF: **492 → 465** verses; `id_collisions` shrinks to `["9.1"]` (debris `9.4` primary removed); ch.8 recovers addressable 9/11/12–13/14 (no more `6->30` note bag); ch.13 51→74. Not `pdftotext`-byte-identical — documented in [`docs/NIRVANA_TANTRA_VERSE_COUNT_DROP_H2273.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/NIRVANA_TANTRA_VERSE_COUNT_DROP_H2273.md).

### Added
- **Nirvāṇa-tantra 821→492 verse-count drop justified (H2273, Grok 4.5 `grok-4.5`).** Chapter-by-chapter pre/post table against the printed Ignatiev PDF numbering, ≥12 sampled absorbed chunks with debris verdicts, and a ruling on residual `id_collisions` `9.1`/`9.4`. Narrow fix: high-N footnote debris no longer becomes `prev_end` and swallows later real verses (ch.8 measured). Doc: [`docs/NIRVANA_TANTRA_VERSE_COUNT_DROP_H2273.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/NIRVANA_TANTRA_VERSE_COUNT_DROP_H2273.md).

### Fixed
- **Bṛhannīla-tantra JSONL duplicate comment IDs** (48 identical double rows) blocked full-pin web publish; dropped dups (2533→2485 records). Rebuild corpus-manifest pin: **230** sources / **723 229** records. `*.jsonl text eol=lf` in `.gitattributes` so Windows pin builds match Linux publish.
- **Wave-B Ignatiev dual-run compare (H2076, Sonnet 5 `claude-sonnet-5`).** Independent Sonnet re-run of Grok's Wave-B ingest ([PR #125](https://github.com/gasyoun/SamudraManthanam/pull/125)) confirms 3/5 works byte-identical (Nīlamata, Kulārṇava, Yoginī) and independently reproduces the ≥99% round-trip claim for all 5 via `html_to_canonical.py` against the live corpus. Two works (Adbhuta-rāmāyaṇa, Mahābhāgavata-purāṇa) diverge under a different pandoc build on already-flagged out-of-order source verse numbering — root cause is an unpinned pandoc version, not a corpus defect; the merged corpus (which explicitly logs both anomalies) is confirmed correct-or-better and kept as-is. Also fixes a doc slip (Wave-B unit test count "19" → actual 23). Full memo: [`web/corpus_builder/H2076_SONNET_WAVEB_DUAL_RUN_COMPARE.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/H2076_SONNET_WAVEB_DUAL_RUN_COMPARE.md).

## [0.19.0] - 2026-08-05
### Added
- **Durable corpus identity and the zero-orphan gate (H1925, Wave-1 Lane B, Opus 5 `claude-opus-5`).** Every retained reference moves from the ordinal pair `(source_id, line_num)` — both re-assigned on every ingest, so one inserted line silently re-points every stored reference below it at the wrong verse — to the canonical tuple `(source_slug, canonical_id, corpus_version)`. [`web/app/canonical_refs.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/canonical_refs.py) holds one dual-read resolver used by the request path, the backfill and the gate alike: canonical tuple → explicit mapping pinned to the recorded corpus version → same-version ordinal → otherwise **report, never bind**. A legacy ordinal recorded against version X is never bound in version Y without an explicit mapping, because it *would* resolve — that is precisely the danger.
- **The tuple now reaches every durable-reference site.** Search results (all three modes share one SELECT), `/api/search/context`, JSON and CSV export rows, the reader's JSON-LD `Quotation` (`identifier`, no longer dropped by the segment merge), the corrections queue, and the offline packs (which already carried it). The census — including the four sites whose verdict is "carries no corpus reference", asserted by test rather than assumed — is [DURABLE_REFERENCE_INVENTORY.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/DURABLE_REFERENCE_INVENTORY.md); the additive public fields are in [SEARCH_CONTRACT.md](https://github.com/gasyoun/SamudraManthanam/blob/main/web/SEARCH_CONTRACT.md) §6. All fields are additive and the legacy ordinals still resolve, so existing clients keep working.
- **Checksum-tracked, reversible state migrations** ([`canonical_state_migrations.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/canonical_state_migrations.py)) add the canonical columns plus `legacy_ref_map`. Ordered, idempotent, genuinely transactional (Python's `sqlite3` auto-commits DDL by default, so a half-applied migration was possible until the runner took explicit transaction control), and an edited-after-apply migration fails loudly on its recorded checksum instead of drifting. Backup/restore is exercised, not asserted.
- **Backfill checks its own pin.** [`scripts/backfill_canonical_refs.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/scripts/backfill_canonical_refs.py) may read an unversioned pre-migration ordinal as belonging to the operator-pinned corpus — that is the only way such a row can ever be resolved — but then verifies the pin against the text the correction itself remembers. A mis-pinned corpus surfaces as `text_mismatch` and the row stays unresolved rather than binding to a plausible wrong line.
- **Zero-orphan evidence command** ([`scripts/zero_orphan_report.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/scripts/zero_orphan_report.py)) resolves every retained reference against both the recorded and the candidate corpus and compares identity *and* content fingerprint. `identity_changed` / `orphaned` / `ambiguous` fail the gate; `content_changed` is reported but not fatal, since corrected text is the point of the project. `--rollback-rehearsal` proves the previous corpus still resolves everything.
- 45 hermetic tests, each named for the B1–B6 criterion it proves; full suite 750 passed, no regressions. Measured 05-08-2026 against the production corpus (`v2026.07.15`, 611,569 lines, 100% canonical-id and slug coverage, zero duplicate canonical ids) under a simulated rebuild that shifts every ordinal: **5,000/5,000 canonical-addressed references survived with identity intact while all their ordinals moved, and 5,000/5,000 ordinal-only references were refused — zero silently re-bound.** Left open deliberately: the ordinals are still stored as compatibility fields pending a clean gate run over a real production rebuild, and the gate compares two built corpus DBs rather than monitoring a live one.

## [0.18.0] - 2026-08-05
### Added
- **Bounded regex and public-boundary trust — Wave-1 Lane C (H1926, Opus 5 `claude-opus-5[1m]`).** Every bound on user-supplied regex now lives in one module, [`web/app/services/regex_executor.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/services/regex_executor.py): a 2 s hard scan deadline, the H1830 per-match timeout, caps on pattern length (512) and count (10), and **one** stable error payload — `{"error", "detail"}` with no engine text, pattern echo or offsets — shared by `POST /api/search`, `/export` and `/stream`. The three used to disagree (POST returned pydantic's 422 quoting the offending pattern; GET returned 400), and a *third* copy of the validation lived in [`models.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/models.py). This also closes the gap H1927's Lane D7 baseline reported and deliberately left for this lane: `search_service.MAX_TIME` was 5.0 s against a documented 2 s deadline, so a catastrophic regex measured 3358 ms. Without the timeout-capable `regex` package the mode is now **refused** (503 `regex_unavailable`) rather than served by unbounded `re.search` in the event loop. New contract sections: [SEARCH_CONTRACT.md §3](https://github.com/gasyoun/SamudraManthanam/blob/main/web/SEARCH_CONTRACT.md) (accepted syntax, caps, deadlines, error codes) and a new [IDENTITY_TRUST_CONTRACT.md](https://github.com/gasyoun/SamudraManthanam/blob/main/web/IDENTITY_TRUST_CONTRACT.md).
- **Measured adversarial regex fixture (H1926 C1).** The textbook ReDoS shapes are **defused by the `regex` engine** — `(a+)+$`, `(a*)*b`, `(x+x+)+y`, `(.*a){20}` all complete in under 4 ms at length 40, so freezing them would have produced a fixture that proves nothing while looking rigorous. Independently measured the same day as H1927's identical finding on its smoke probe. [`regex_adversarial_backtracking.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/fixtures/regex_adversarial_backtracking.json) instead uses overlapping-alternation shapes (`(a|aa)+$`, `([ab]|[ab][ab])+$`, IAST and Cyrillic variants), each measured to exhaust the per-match budget; the same cases do not finish in 120 s under stdlib `re` at length 24. Paired with a 22-case scholarly compatibility corpus ([`regex_compat_scholarly.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/fixtures/regex_compat_scholarly.json)) that pins documented semantics across the engine change. 43 tests in [`test_regex_bounded.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/test_regex_bounded.py).
- **Verified sessions, correction trust tiers and rate limits (H1926 C4/C6/C7).** State migration [`0003_correction_trust_and_sessions.sql`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/migrations/state/0003_correction_trust_and_sessions.sql) adds `email_verifications`, `user_sessions`, `correction_audit` and `rate_limits`, plus `trust_tier` / `actor_ip_hash` / `contact_email` / `link_id` / `corpus_version` on `corrections`. Anonymous proposals stay open at 10/hour; a redeemed session raises the cap to 60/hour and is the **only** thing that grants attribution. Delivery of the verification token is out of scope and deliberately not faked — non-production returns it, production logs it for an operator, stated as a limitation in the trust contract. 30 tests in [`test_correction_trust.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/test_correction_trust.py).
### Changed
- **Admin authentication moves from `?key=` to a header (H1926 C3/C5).** `POST /api/admin/vacuum` and `GET /api/corrections/pending` accept `X-Admin-Key` or `Authorization: Bearer`, compared with `hmac.compare_digest`; **any** credential-shaped query parameter is refused with 400 *without being compared*, including the correct one — by the time the application sees it, nginx and uvicorn have already logged it and browsers have it in history. No time-bounded compatibility path: the only callers were this repo's tests and the operator runbook, both updated here. A credential-scrubbing logging filter is attached to the application loggers **and the root handlers** (a logger-level filter never sees records propagated from child loggers). Operator migration in [DEPLOYMENT.md](https://github.com/gasyoun/SamudraManthanam/blob/main/DEPLOYMENT.md).
### Fixed
- **Bṛhannīla-tantra JSONL duplicate comment IDs** (48 identical double rows) blocked full-pin web publish; dropped dups (2533→2485 records). Rebuild corpus-manifest pin: **230** sources / **723 229** records. `*.jsonl text eol=lf` in `.gitattributes` so Windows pin builds match Linux publish.
- **Typed email text no longer grants attribution (H1926 C6).** `POST /api/corrections/propose` resolved the `email` field of the request body against the users table and attached the matching account to the correction — so typing a known scholar's address filed corrections under their name, with no verification step in the loop. The address is now stored as `contact_email` only; `user_id` comes from a redeemed session or is null. `POST /api/identity/lead` also stops returning the internal `users.id`. **Pre-existing `user_id` links written by the old lookup are not evidence of verification** and should not be read as attribution.

## [0.17.0] - 2026-08-05
### Added
- **Ordered checksum-tracked state migrations (H1927 Lane D1, Opus 5 `claude-opus-5[1m]`).** [`web/app/migrations/`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/migrations/README.md) replaces the inline `CREATE TABLE`/`ALTER TABLE` block that `init_state_db` re-executed on every startup. Each applied file is recorded in `schema_migrations` with a SHA-256 over its **newline-normalised** bytes — normalisation is load-bearing, not cosmetic: this repo is authored on Windows and cloned on Linux CI, so a CRLF checkout would otherwise change every checksum and refuse every deployment. Two refusals are deliberate: an applied migration later edited (`MigrationChecksumError`), and a recorded migration missing from disk (`MigrationMissingError`, i.e. the DB is ahead of the code). `0001` is written entirely `IF NOT EXISTS` so an existing production `state.db` is adopted with no dump/restore, verified by a test that migrates a legacy-shaped DB with its rows intact. SQLite has no conditional `ALTER`, so `0002` uses a per-statement `-- @idempotent-error:` directive rather than a file-level `try/except` that would hide a genuine failure in any other statement.
- **corpus.db rebuild-not-migrate policy (H1927 Lane D2).** [`corpus_policy.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/migrations/corpus_policy.py) declares `CORPUS_SCHEMA_VERSION` and probes it at startup. It never raises and never mutates — a stale corpus is served with a loud log rather than taking search down. The one pre-existing in-place shim (the slug backfill) moves to [`corpus_compat.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/corpus_compat.py), documented as grandfathered instead of silently tolerated.
- **One shared deployment contract for both production profiles (H1927 Lane D4).** [`deployment_contract_smoke.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/scripts/deployment_contract_smoke.py) takes only a base URL and asserts readiness, corpus-version exposure, plain search, a bounded catastrophic regex, opaque error payloads, service-worker scope, COOP on HTML, CORP on static, the reader deep-link route, sitemaps, and admin refusal of a bogus key. CI now boots the built image against fixture databases and runs it; [`deployment-contract-bare.yml`](https://github.com/gasyoun/SamudraManthanam/blob/main/.github/workflows/deployment-contract-bare.yml) runs the *same* script on a scheduled/pre-release bare profile through the repo's own `deploy/samudra.nginx`. That second profile is the point: nginx serves `/static/` directly and bypasses the `security_headers` middleware, so those headers are hand-duplicated in the vhost — and the container profile cannot see them drift.
- **Categorised duplicate-suffix invariant (H1927 Lane D7).** [`dup_suffix_report.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/scripts/dup_suffix_report.py) + [docs/DUP_SUFFIX_INVARIANT_REPORT.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/DUP_SUFFIX_INVARIANT_REPORT.md). Gate 4 asserted a bare count ceiling; H1829 showed what that costs, with `<= 200` concealing 284 of 429 suffixed ids in a single work. A count can only ask *how many*, so a splitting bug that stays under the number is invisible to it. The gate now asserts structure — every suffixed id has its un-suffixed twin, suffixes never run past `b`, segments are `sa`/`ru` pairs or commentaries, and no work exceeds 60% of the population — shapes that debris has and genuine collisions do not. Measured over 675,139 records: 147 suffixed ids across 18 works, all invariants holding. The count survives only as a coarse backstop that prompts re-derivation.
- **Full-corpus gate on corpus-changing PRs and releases (H1927 Lane D5).** [`corpus-gate.yml`](https://github.com/gasyoun/SamudraManthanam/blob/main/.github/workflows/corpus-gate.yml) path-filters converters, ingest, the corpus gates and the schema policy. Ordinary CI runs `-m "not corpus"`, so until now a PR that changed a converter ran none of the checks that could tell whether it had damaged the corpus.
- **Recorded performance baselines (H1927 Lane D7).** [docs/PERFORMANCE_BASELINES.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/PERFORMANCE_BASELINES.md), measured by [`performance_baseline.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/scripts/performance_baseline.py) against a live deployment on the real 183-source corpus. Plain search p95 52–119 ms and health p95 33 ms sit well inside budget. **Two exceptions are recorded rather than the budgets deleted:** reader lookup p95 1079 ms against a 500 ms budget (2.2×), and a catastrophic regex completing in 3358 ms against the documented 2 s hard deadline (1.7×) — `search_service.MAX_TIME` is 5.0 s, so the implementation's whole-scan budget was never aligned to the 2 s spec. That file belongs to Lane C2 (H1926), so the finding is reported, not unilaterally patched.
### Changed
- **`web/app/main.py` 611 → 120 lines (H1927 Lane D2).** Split into `lifespan`, `http_headers`, `static_assets`, `site_context`, `corpus_compat` and the `home`/`pwa`/`seo` routers, leaving a composition root that does nothing but create the app, wire middleware and register routers. Handlers moved byte-for-byte so headers and sitemap XML cannot drift; the route table was diffed before and after and is identical; and `app.main` still re-exports every private helper the test modules import, because an import path is behaviour too.
- **CI test matrix extended to Python 3.10–3.14 (H1927 Lane D3).** The Dockerfile has run `python:3.14-slim` while CI tested only 3.10–3.12, so every release shipped on an interpreter no test had ever executed and nothing would have reported it. The full hermetic suite was measured passing on 3.14.4 *before* choosing to extend the matrix rather than downgrade the image. [`test_runtime_alignment.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/test_runtime_alignment.py) parses the Dockerfile `FROM` against the workflow matrix so the two cannot silently re-diverge, and carries a fixture replaying the pre-fix state to prove the guard goes red there.

### Fixed
- **Bṛhannīla-tantra JSONL duplicate comment IDs** (48 identical double rows) blocked full-pin web publish; dropped dups (2533→2485 records). Rebuild corpus-manifest pin: **230** sources / **723 229** records. `*.jsonl text eol=lf` in `.gitattributes` so Windows pin builds match Linux publish.
- **Two checks that would have passed without testing anything (H1927).** The deployment smoke's admin probe pointed at `/api/admin/corrections`, which does not exist — it 404'd and reported PASS; it now hits the real `/api/admin/vacuum`, and a test pins the probe path to a registered route. And every regex bound was being exercised with the textbook `(a+)+$`, which this app's `regex` engine optimises away in ~1 ms; measured 05-08-2026, `(a|a)*$` is an alternation the optimiser cannot collapse and does reach the 0.05 s per-match timeout. Both call sites were switched.

## [0.16.0] - 2026-08-05
### Added
- **Canonical corpus manifest and immutable bundle contract (H1924, Wave-1 Lane A, Opus 5 `claude-opus-5`).** The enumeration of record moves from `Programdata/data.txt` — a bare list of legacy HTML filenames that could say *which* sources exist but never *what they contain* — to a content-addressed manifest. [`web/corpus_builder/corpus_manifest.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/corpus_manifest.py) builds, validates and diffs it against [`schema-v1.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/manifest/schema-v1.json) (`jsonschema` is now a real dependency precisely so the published schema is the *only* validator — a hand-written twin would drift from it silently). Each source carries SHA-256, byte count, live record count and first/last canonical id of the JSONL that is actually published. **The manifest deliberately carries no wall clock:** `bundle` is a pure function of its inputs, so two builds from identical inputs are byte-identical and `content_hash` is a usable identity; event time lives in build reports instead, and a test asserts no clock-shaped key ever reappears. `content_hash` covers `bundle` only, so the same content rebuilt at a new git revision keeps one identity.
- **Publication now validates the bytes it publishes.** [`ingest/publish.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/ingest/publish.py) `--manifest` opens and hashes every canonical JSONL the manifest names, and [`ingest/ingest.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/ingest/ingest.py) re-verifies each hash before inserting a row and rejects a manifest whose declared record count disagrees with what it inserted. A one-character edit inside a JSONL string — valid JSON, unchanged record count, so only a hash can catch it — now aborts publish, while the legacy `validate_corpus` tree check still passes it: that gap is asserted in the suite rather than assumed. Ingest writes `input_manifest_hash`/`bundle_version` into `corpus_meta` and `corpus_version` becomes the bundle version, not a build date. The manifest-less path survives behind an explicit warning that it does not hash what it publishes.
- **Every generated view names its input bundle.** New [`build_report.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/build_report.py) ties each derivative to one manifest hash; the web DB (from the manifest it published), the offline packs (inherited via `corpus.db`'s `corpus_meta`, and re-recorded in `pack_meta`) and the desktop HTML plus its `.no_tags` sidecars (from `--manifest`) all now emit one. A generator whose source DB carries no `input_manifest_hash` is **refused** rather than given a placeholder — a derivative of an unregistered corpus must not fabricate a lineage.
- **Checksum-pinned, vendor-neutral artifact resolution.** [`ingest/artifact_resolver.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/ingest/artifact_resolver.py) stages a download, hashes it there, and moves it into place only on a match — nothing extracts or opens an unverified file, and `extract_verified` takes a verified artifact rather than a path so the check cannot be bypassed. `file://`, bare paths and `http(s)://` share one `Transport` interface (no vendor SDK), a cached copy is re-hashed rather than trusted, and every URL in a log line or exception passes through `redact_url` — object stores authenticate with pre-signed query strings, so an un-redacted URL in a build log is a leaked credential.
- **Rollback is now a rehearsed path, not a hope.** `restore_backup()` re-activates a previous bundle from the copy publish records, refusing a backup that fails its own integrity check, and a failed candidate publication is proven to leave the live corpus byte-identical.
- 59 hermetic tests ([`test_corpus_manifest.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/test_corpus_manifest.py), [`test_artifact_resolver.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/test_artifact_resolver.py)), each named for the A1–A7 criterion it proves; the HTTP transport is tested against a real loopback server because a mocked socket cannot show a transport that streams to disk without hashing. Full suite 705 passed, no regressions; CI green on Python 3.10/3.11/3.12, ruff, black and the Docker image (the one red job, `npm audit`, is a pre-existing advisory that failed identically on the preceding main commit). Measured on the real JSONL directory: 197 sources / 703,726 records, two builds byte-identical, full-hash validation 3.1 s. That run also caught a real defect — the fallback enumerator would have pulled 22 converter intermediates (`*.raw.jsonl`) into a bundle as sources; they are now excluded **and named on every build**, since a bundle that silently drops or absorbs a file is the failure the manifest exists to prevent. Spec + stated limits: [CORPUS_BUNDLE_SPEC.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/CORPUS_BUNDLE_SPEC.md).

## [0.15.3] - 2026-08-04
### Changed
- **Corpus Builder: `TMhHTMLBuilder` cut free of VCL/GUI (H1485, Opus 5 `claude-opus-5[1m]`).** [`uMhHTML.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/uMhHTML.pas)'s implementation `uses` drops to `SysUtils, textu, windows, MyUtils` — `dialogs`, `fMainForm`, `Forms`, `controls` and `ShellApi` are gone, and with them the `uMhHTML → fMainForm` reverse edge the H2064 inventory measured. Every VCL call site is replaced by a nil-safe sink the host assigns after `Create`: `Form1.StatusBar1` writes (×5, panel index preserved — including the one `Panels[1]` site) → `Progress(APanel, AText)`, `MessageDlg` → `Confirm`, `ShowMessage` (×3) → `ReportError`, which appends to `ErrList` unconditionally — so the standing `CLAUDE.md` rule "`ErrList` is the sole error channel, never `ShowMessage` in builder logic" now holds by construction rather than by convention. `ShellExecute` of `Err.txt` moves to the caller via new `HasErrors` / `ErrFileFullPath`; [`fMainForm.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/fMainForm.pas) implements the three sinks and wires them at all three construction sites, preserving the ordering relative to `RenameErrFile`. Two intentional host-side deltas: progress now refreshes *and* pumps messages at every site (the engine used to do one or the other), and a load error no longer halts a multi-book batch on a modal — it lands in `Memo1`, `ErrList` and `Err.txt`. **Not compiled:** no Delphi 7 machine in the session, so `dcc32` never ran; the source-level verification and the human residual are written up in [Corpus_builder/DEPENDENCY_INVENTORY.md](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/DEPENDENCY_INVENTORY.md) §3a. Ticks [Corpus_builder/ROADMAP.md](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/ROADMAP.md) Phase 1 «Отделить движок от формы»; the dead-VCL-import cleanup in `uSort`/`TextU` is explicitly still open.

## [0.15.1] - 2026-08-04
### Added
- **Annotates-remap provenance for the H1828 orphan fix (H2219, Opus 5 `claude-opus-5[1m]`, dual-run compare of the Grok 4.5 override).** H1828 removed every gate-5 dead anchor by re-pointing an endnote at the *nearest emitted verse* and rewriting the record id with it — destroying the target the endnote actually named, with no flag separating a genuine anchor from a heuristic one. Measured on shipped data, both readings occur: `6.5.559 → 6.005.059` is an OCR-digit repair the remap gets right, while `12.8.111 → 12.008.092` moves a note 19 verses with nothing behind it; gate 5 reported zero orphans for both. Commentary records now carry `annotates_resolution` (`exact`/`nearest`) plus `annotates_requested` when the anchor moved, and the conversion report gains `annotates_remapped` / `annotates_remap_max_delta` / a per-remap list. New corpus gate 5b asserts a moved anchor never loses its requested target; the gate-5 `chinachara-tantra` exemption is narrowed from a blanket work-level skip to a count-bounded budget (1), so a *second* orphan there fails again. The shipped JSONL predates the fields and needs regeneration from the off-git source PDFs.
- **Regex match-timeout observability (H2219, follow-on to H1830).** `search_regex` now reports `match_timeouts` / `match_errors` / `regex_timeout_engine` in `search_metadata` and marks the result `truncated` when rows were abandoned mid-match — previously a swallowed catastrophic-backtracking timeout silently under-reported matches while the metadata still read clean. Import falls back to stdlib `re` only with a loud `logging.warning`, so a deployment missing the `regex` package can no longer serve an unprotected `mode=regex` in silence.
- **Corpus Builder Phase 1 dependency inventory (H2064, Grok 4.5 `grok-4.5`).** Full `uses` graph from `PSRCBuilder/cb.dpr`: every local unit is reachable (no dead modules); VCL/WinAPI vs RTL classification; concrete proof that `uMhHTML` / `TMhHTMLBuilder` is **not** GUI-free today (`Form1.StatusBar1`, `ShowMessage`, `MessageDlg`, `ShellExecute`, `Application.ProcessMessages`). Portable core named (`myutils`/`uTypes`/`ArtMath`/`CalcSimU`/`StatProcs`/`uSort`). Builder `TextU.pas` ~3× larger than main-app `Units/TextU.pas` — Phase 2 must re-diff, not assume subset. Artifact: [Corpus_builder/DEPENDENCY_INVENTORY.md](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/DEPENDENCY_INVENTORY.md). Tick: [Corpus_builder/ROADMAP.md](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/ROADMAP.md) Phase 1 inventory. Feeds H1485 (engine↔GUI decouple).
- **Ignatiev Wave B ingest: 5 docx/doc tantras + upapurāṇas (H1438, Grok 4.5
  override dual-run).** Nīlamata-purāṇa (1 ch / 410 v, partial śl. 1–411),
  Adbhuta-rāmāyaṇa (6 selected ch / 308 v), Kulārṇava-tantra (17 ch / 2049 v +
  1113 endnotes), Yoginī-tantra (19 ch / 1285 v + 340 endnotes; ch.8–19 via
  OLE WordDocument UTF-16 extract of legacy `.doc`), Mahābhāgavata-purāṇa
  (78 ch / 4232 v; source lacks ch.36–37 and 56 headings). All registered in
  `Programdata/data.txt`, all ru_only-aligned (no Sanskrit e-text for these),
  all HTML round-trip ≥99% (measured 100%±0.1). Parser hardening this wave:
  ToC leader-dot reject; per-part multi-file parse so part-1 endnotes cannot
  leak; last-chapter ALL-CAPS title no longer mistaken for back-matter
  (which had emptied Kulārṇava ch.8/17 and Mahābhāgavata ch.35/81). Three new
  regression tests (19 total in `test_ignatiev_book_units.py`). Māyā-tantra
  and Waves C–D remain open. Dual-run residual for intended Sonnet tier
  minted at close.


## [0.15.0] - 2026-07-31
### Added
- **Regression guard for Cyrillic homoglyphs in `#sa` corpus fields (H1694, issue #16, Sonnet 5
  `claude-sonnet-5`).** The 5 words / 21 field-occurrences named in #16 were already fixed on `main`
  (PR #46, 12-07-2026) via `web/corpus_builder/scan_cyrillic_homoglyphs.py`; this session re-verified the
  corpus jsonl is clean (`saṃcukoca`, `calāgramukuṭaprāṃśuś`, `cekṣvākuvaṃśasya`, `chīlavān`,
  `tad-vipāka-anuguṇānām` all round-trip to their Latin-IAST form, no Cyrillic remains in any `#sa`
  segment) and added `web/tests/test_cyrillic_homoglyphs.py` — a hermetic pytest guard (imports the
  existing scanner, no `corpus.db` needed) so a future re-ingest can't silently reintroduce the leak.
  Russian-field mixed script (e.g. Vasmer `*Dunajь`) is untouched by design — the scanner is
  script-tag-gated to `#sa` only.
- **KSS book 12–14 low-confidence alignment groups re-verified with quoted evidence (H1687, Sonnet 5
  `claude-sonnet-5`).** The H927 review sheet's 70 low-confidence (<0.6) SA↔RU alignment groups were
  re-derived directly from `web/corpus_builder/jsonl/kathasaritsagara-12.jsonl`/`-14.jsonl` (the original
  sheet HTML had been lost — gitignored `/review/`, its worktree removed before copy-out — but the
  underlying jsonl counts matched exactly: 62+8=70) and each group now carries an agent verdict
  (`alignment-holds`/`confirmed-break`/`uncertain`) with quoted SA/RU evidence, committed as
  `web/corpus_builder/jsonl/kathasaritsagara-12-14_lowconf_agent-verdicts.json`. Result diverges sharply
  from H927's prior note ("mostly granularity mismatches, not mis-alignment"): **27 alignment-holds · 40
  confirmed-break · 3 uncertain** — several real off-by-one/displacement clusters found (a Russian
  passage's true translation turns up verbatim in a *neighboring* group instead of its own paired
  Sanskrit line). Human vote reduced to the 43 confirmed-break+uncertain rows only, in
  `web/corpus_builder/jsonl/kathasaritsagara-12-14_lowconf_reduced-human-ask.json`. No alignment jsonl
  file was changed by this pass — re-alignment fixes are applied only after the human vote (per H1687 DoD).

### Removed
- **Dead `morph_cache` table dropped from `corpus.db` schema (H1503, Sonnet 5
  `claude-sonnet-5`).** `web/app/db.py::create_schema` no longer creates
  `morph_cache` — it was migrated to `state.db` in Track B (v1.9.1) and had
  been re-created empty on every fresh `corpus.db` since. `create_schema` now
  runs an idempotent `DROP TABLE IF EXISTS morph_cache` so existing DB files
  get the leftover table dropped on next startup. +2 hermetic tests
  (`web/tests/test_db_schema.py`).

### Added
- **Structured JSON/CSV export for search results (H1502, Sonnet 5 `claude-sonnet-5`).**
  `GET /api/search/export` now accepts `format=json` and `format=csv` alongside the
  existing HTML default, reusing the same `dispatch_search` result set and metadata
  block (`query`, `mode`, `corpus_version`, `timestamp`, `source_filter`,
  `live_search_url`) already rendered into the HTML export. JSON returns
  `{metadata, results}` with the full result fields (`source_id`, `source_title`,
  `chapter`, `line_num`, `link_id`, `line_html`, `line_text`); CSV writes the same
  metadata as `# key,value` comment rows followed by a data table. +4 tests; existing
  HTML export and its tests unaffected.
- **Residual replan pack (stale-roadmap `/ask-batch`, Grok 4.5 `grok-4.5`, 26-07-2026):** living status [docs/ROADMAP_SAMUDRAMANTHANAM_RESIDUAL_2026H2.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ROADMAP_SAMUDRAMANTHANAM_RESIDUAL_2026H2.md) + unattended [docs/PLAN_SAMUDRAMANTHANAM_RESIDUAL_2026H2.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/PLAN_SAMUDRAMANTHANAM_RESIDUAL_2026H2.md) with ARCHITECTURE / IMPLEMENTATION / VERIFICATION / `.meta.md`. Supersede banners on H2 mobile roadmap, Somadeva scale-up roadmap, and ARCHITECTURE_REVIEW_6_MONTH. Wave-1 spine: H1502/H1503 + integrity (DBhP IDs, #16) + SSE tests; H1438 parallel; H1485 wave-2.

## [0.14.0] - 2026-07-25
### Added
- **Shared inline `<w><ana/>` scheme for both corpus sides — the last H905/H906
  item (Opus 5 `claude-opus-5[1m]`).** `nkrya_export.py --inline-ana` folds the
  morphology *into* the para-XML as НКРЯ `<w><ana lex= gr= gramset=/>` per token,
  instead of only alongside it as a TSV. Both handoffs had deferred this so
  neither side would fix the attribute scheme unilaterally; the agreement is one
  element shape with two honest tagsets (`opencorpora` for RU via pymorphy3,
  `dcs-ud` for SA via DCS gold — they do not map 1-to-1, and merging them would
  have silently corrupted the grammar). The annotated unit is the **surface
  word**: `<se>` text is never rewritten or re-segmented, and concatenating the
  `<w>` content reproduces the segment byte-for-byte (test-enforced). A word may
  carry several `<ana>` children — the RNC ambiguity construct, reused for the
  sandhi-split compound (`tapaḥsvādhyāyanirataṃ` = one word, three DCS tokens).
  **RU coverage 100 %** of pairs. **SA coverage 15.5 %** of gold-bearing verses
  (37.6 % / 34.9 % on the analytically-printed GRETIL kāṇḍas, ~1 % on the
  bilingual editions that write long unresolved compounds) — H905 had called this
  step "small, mechanical", but DCS is sandhi-*split*: it holds more tokens than
  surface words in ~89 % of verses and its gold does not re-concatenate to the
  surface, because sandhi is undone. So the SA side attaches gold only where a
  sandhi-tolerant matcher accounts for the verse end-to-end, and emits plain text
  otherwise — never a guessed analysis, following the rule `align_sanskrit.py`
  already sets. Precision was not traded for coverage: on the 18,228 annotated
  Yuddhakāṇḍa words an initial-consonant gate found **0 disagreements**. The
  `sa_morph.tsv` sidecar still carries 100 % of the gold. +6 tests (23 pass);
  two runs byte-identical. Full write-up:
  [`web/corpus_builder/INLINE_ANA_H906_REPORT.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/INLINE_ANA_H906_REPORT.md).

## [0.13.0] - 2026-07-25
### Fixed
- **Bṛhannīla-tantra JSONL duplicate comment IDs** (48 identical double rows) blocked full-pin web publish; dropped dups (2533→2485 records). Rebuild corpus-manifest pin: **230** sources / **723 229** records. `*.jsonl text eol=lf` in `.gitattributes` so Windows pin builds match Linux publish.
- **SA morphology no longer keyed off bilingual pairs — unlocks 7,123 Rāmāyaṇa
  verses of DCS gold (H906, Opus 5 `claude-opus-5[1m]`).** The `--sa-morph` and
  `--vidyut-diff` layers iterated `classify()`'s `pairs`, which by design require
  **both** a Sanskrit and a Russian side. The GRETIL-ingested
  `06_ramayana-yuddhakanda` and `07_ramayana-uttarakanda` are **Sanskrit-only**
  (untranslated), so they produced zero pairs and wrote header-only morphology
  files — recorded in the build report as "0 % DCS coverage; the ref mapper
  doesn't parse their passage convention". That diagnosis was wrong: their
  passages are plain `N.N`, `dcs_target()` mapped them correctly all along, and
  at the passage level they align to DCS at **100.0 %** and **99.9 %** — the best
  figures in the whole Rāmāyaṇa. A new `sa_units()` builder (every group with a
  non-empty Sanskrit side, translated or not) now feeds the SA-side layers, while
  `classify()`/`pairs` keep driving the genuinely bilingual para-XML/TMX/TSV/RU
  outputs. Net **+7,123 covered verses and +98,753 gold tokens**; Rāmāyaṇa gold
  coverage 8,193 → 15,316 verses (**+87 %**). Purely additive — every
  previously-covered source re-measures byte-identical. +4 tests (17 pass).
- **Rāmāyaṇa "verse-number offset" diagnosis corrected — there is no offset
  (H906, Opus 5 `claude-opus-5[1m]`).** The build report attributed the 62–80 %
  Rāmāyaṇa coverage to verse-numbering divergence ("the misses are alignment, not
  missing DCS data"). Categorising every chapter/verse of the four bilingual
  kāṇḍas shows the opposite: the dominant miss is **3,696 verses our edition
  carries that DCS never annotated**, and of the 1,422 verses DCS holds that we
  don't match, **98.7 % lie beyond our last verse in that chapter** (DCS's
  chapter simply runs longer) with only **19 in total** a genuine in-range hole.
  The verse map is already correct and at its ceiling; the 62–80 % is DCS's own
  annotation density and recension, and is now reported as such. Full evidence:
  [`web/corpus_builder/RAMAYANA_VERSE_MAP_H906_REPORT.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/RAMAYANA_VERSE_MAP_H906_REPORT.md).

### Added
- **vidyut second-opinion layer + agreement diff against the DCS gold (H906,
  Opus 4.8 `claude-opus-4-8[1m]`).**
  [`web/corpus_builder/vidyut_diff.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/vidyut_diff.py)
  runs vidyut 0.4.0's `cheda.Chedaka` over each `seg=sa` group's SLP1 surface and
  pairs its tokens against the DCS gold tokens of the same group, emitting
  `<slug>.vidyut_diff.tsv` behind `nkrya_export.py --vidyut-diff` (one row per
  matched / dcs-only / vidyut-only token, tri-state agree flag per feature) plus a
  `vidyut_diff` aggregate block in `export_report.json`. The join is a group-level
  multiset match on the sandhi-folded SLP1 form (`M`→`m`, `H`→`s`), which buys a
  measured **+14 pp** form-match (35 %→49 %) because DCS keeps the printed surface
  (`evaM`, `pArTAH`) where vidyut returns the underlying pada form (`evam`,
  `pArTAs`); both sides are mapped into the DCS feature vocabulary so the
  comparison is like-for-like. **Headline result on Āraṇyakaparva** (2033 pairs,
  152,196 gold tokens): form-match **49.2 %**, and over the matched tokens
  lemma 69.3 % · coarse POS 69.3 % · case 70.5 % · gender 73.7 % · number 90.4 %.
  The 49 % is a property of vidyut, not a bug in the diff — its unsupervised
  segmenter picks different token boundaries from DCS on roughly half of this
  compound-heavy epic text (`dyūtajitāḥ` → `dyU·ut·ajitAs`), and feeding it
  danda-delimited hemistichs instead of whole groups moved this by <0.1 pp. This
  **vindicates the DCS-is-gold ordering**: on epic register vidyut is not close
  enough to arbitrate, but on the half it segments identically it is a useful
  independent check. Categorised disagreement sample (Nom/Acc/Voc syncretism,
  vidyut's masculine over-assignment, its subanta-fallback NOUN labelling, and
  the pronoun-lemma split) in
  [`web/corpus_builder/VIDYUT_DIFF_H906_REPORT.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/VIDYUT_DIFF_H906_REPORT.md).
  Deterministic; the vidyut data pack (`$VIDYUT_DATA`) is a large local-only
  fetch and the layer degrades to empty when absent, never guessed — same
  contract as the DCS sqlite. +5 tests (14 pass, 2 data-pack-gated skips).

## [0.12.0] - 2026-07-22
### Added
- **Ignatiev Wave-A-tail ingest: 4/4 remaining PDF tantras (H1438, Sonnet 5
  `claude-sonnet-5`).** Niruttara-tantra (15 ch, 674 verses), Guptasādhana-tantra
  (12 ch, 319 verses) and Yoni-tantra (8 ch, 221 verses) ingested via the
  generalized `ignatiev_book_to_canonical.py`, all registered in
  `Programdata/data.txt`, all FTS5-searchable, all round-trip
  `html_to_canonical.py`-verified at 100% verse reproduction. Three real parser
  bugs found and fixed along the way (each with its own regression test, 6 new
  tests, 16 total): a chapter heading glued to its own first body sentence with
  no paragraph break (Niruttara ch.5); an ALL-CAPS running section title glued
  onto the FRONT of a chapter heading, which also exposed a latent
  case-sensitivity bug (`re.IGNORECASE` made the "ALL-CAPS" class match
  lowercase too, letting a table-of-contents line masquerade as a heading and
  corrupt Niruttara's own chapter numbering — fixed with scoped `(?-i:...)`
  groups); and an appendix's own later "Комментарий" section (for its own
  quoted-hymn citations) being mistaken for Yoni-tantra's real endnotes,
  dragging its chapter-8 body 140+ lines past the true boundary. Full writeups:
  `web/corpus_builder/PDF_INGESTION_PIPELINE.md` §Single-book generalization.
  **Māyā-tantra deliberately deferred** — a different, larger front-end gap
  (per-page glued-digit footnotes, not the bracket-style `[N]` convention) that
  needs a real design extension, not a regex tweak; see the pipeline doc and
  `.ai_state.md` for the diagnosis. Remaining ~14 works (Waves B–D) stay scoped
  in [H1438](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1438-Sonnet_SamudraManthanam_ignatjev-tantras-puranas-ingest_22.07.26.md).
- **Generalized single-book Ignatiev converter + 2-work proof (H1438, Sonnet 5
  `claude-sonnet-5`).**
  [`web/corpus_builder/ignatiev_book_to_canonical.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/ignatiev_book_to_canonical.py)
  generalizes the DBhP-shaped `ignatjev_pdf_to_canonical.py` pipeline
  (H534/H558) to А. Игнатьев's ~20 other tantra/upapurāṇa translations —
  standalone single-book works (flat `chapter.verse` ids, heading-only
  chapter splitting, bracket-style `[N]` Word-footnote endnotes) sourced as
  a single `.docx` (pandoc) or `.pdf` (pdftotext), not DBhP's 6-volume set.
  Rights cleared for "all my works ... whether published or unpublished" —
  [RIGHTS_GRANT_IGNATJEV_DBHP_2026H2.md](https://github.com/gasyoun/Uprava/blob/main/RIGHTS_GRANT_IGNATJEV_DBHP_2026H2.md).
  Proved on 2 works as the H1438 pilot: Cīnācāra-tantra (docx, 5 ch, 225
  verses, 154 endnotes) and Nirvāṇa-tantra (PDF, 15 ch, 821 verses), both
  registered in `Programdata/data.txt` and browser-verified searchable via
  FTS5. 10 hermetic unit tests
  ([`web/tests/test_ignatiev_book_units.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/test_ignatiev_book_units.py)).
  Remaining ~18 works scoped as a wave-ordered backlog in
  [H1438](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1438-Sonnet_SamudraManthanam_ignatjev-tantras-puranas-ingest_22.07.26.md)
  and `PDF_INGESTION_PIPELINE.md` §Single-book generalization.
- **Re-implementация склонения рубрик указателя в порту — генератор вместо
  статического импорта (H1207, Sonnet 5 `claude-sonnet-5`).**
  [`web/corpus_builder/sanskritisms/ru_rubric_decline.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/sanskritisms/ru_rubric_decline.py) —
  reproduce+fix для [`rus_index_declined.txt`](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/diplom-rubanova/rus_index_declined.txt)
  (292 рубрики), закрывает H1204-статус-документ. `Index_items_declension.ipynb`
  + `index_lone_declined_manual.json` + `pyphrasy` не найдены ни в этом репо, ни
  выше по потоку в `github.com/evgeniarubanova/sanskrit_stemmer` (полное дерево
  из тех же 18 плоских файлов, без ноутбука и без манульного gold) — метод
  переизобретён из `rus_index.txt` + наблюдаемых дефектов старого файла:
  числительное согласование (два/три/четыре → gen.sg в им./вин., пять+ → gen.pl,
  во всех остальных падежах — plural формы), общий per-word декленатор с
  предпочтением ADJF/PRTF при завязанном скоре (чинит «вездесущия»→«вездесущий»),
  фиксация уже-косвенных хвостов («сын дхармы», предложные дополнения), класс
  «тот, …» для относительных придаточных (были пустыми в старом файле — 7 рубрик),
  список из 9 хэндлd homograph-ловушек (гады/дроны/лука/ганги/манасы/паки/балы/
  знак/индра/пасть — где pymorphy3 однозначно выбирает не ту лемму). Правит
  «три мира»→«три мир» и «вездесущия», плюс truncation-баг старого `both`-класса
  (терял 3-е+ слово фразы — «владыка рыжих» вместо «владыка рыжих коней», 15+
  рубрик) и полностью пустые формы у 11 рубрик (comma-list-перестановки +
  «тот, …»-класс). Ручной gold —
  [`rus_index_declined_manual_gold.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/diplom-rubanova/rus_index_declined_manual_gold.json)
  (104 рубрики, независимо выведенные по правилам грамматики): **paradigm
  accuracy 100 % (было 86.5 % в заметке 2024-11)**. Тесты:
  [`web/tests/test_ru_rubric_decline.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/test_ru_rubric_decline.py) —
  26 hermetic + 2 `-m corpus` (parity: регенерация == закоммиченный файл;
  accuracy-gate ≥86.5 %); существующие sanskritisms corpus-тесты (эпитет-слой
  всё ещё находит известные имена) прогнаны заново, зелёные. ё вырезано из
  вывода (дом. стиль); `тридесять` не в OpenCorpora — парадигма задана вручную.

## [0.11.1] - 2026-07-17
### Added
- **Документ-ответ: склонение рубрик указателя — учтено ли, есть ли функционал
  (Opus 4.8 `claude-opus-4-8`).** [`docs/RUBANOVA_NKRYA_RUBRIC_DECLENSION_STATUS_2024_11.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/RUBANOVA_NKRYA_RUBRIC_DECLENSION_STATUS_2024_11.md):
  по запросу — есть ли в репо функционал склонения рубрик указателя из заметки
  2024-11 (`Index_items_declension`). Вывод: **результат** склонения есть и уже
  используется в поиске (файл [`rus_index_declined.txt`](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/diplom-rubanova/rus_index_declined.txt) —
  292 рубрики / 1346 форм, 1148 многословных синонимичных фраз; именно их ищет
  ускоренный H1204 Ахо-Корасик слой), но **генератор** (`Index_items_declension.ipynb`,
  `index_lone_declined_manual.json`, `pyphrasy`, разбивка на синонимичные фразы,
  лог точности 89.6 % / 86.5 %) в репо **отсутствует** — из склонятелей есть только
  упрощённый `decline()` Рубановой (pymorphy2 + ручная таблица ~50 многословных).
  H1204-ускорение — ниже по потоку (поиск по уже склонённым формам), склонение не
  трогает и не воспроизводит.

## [0.11.0] - 2026-07-17
### Changed
- **Ускорение пайплайна Рубановой — код-ревью + оптимизация горячих путей
  (H1204, Opus 4.8 `claude-opus-4-8`).** Stage B ([`sans_stemmer.ipynb`](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/diplom-rubanova/sans_stemmer.ipynb))
  был тем самым «слишком медленно»: его собственная ячейка `%%time` показывает
  **5 мин 8 с на 32 предложения**. Исправлены горячие пути во всех трех ноутбуках
  **и** в Python-порте — **без изменения вывода** (каждое исправление проверено
  побайтово либо доказано идентичным на репрезентативных данных; структура Colab —
  Drive-mount, `input()`, `!pip` — сохранена). Таблица before/after и разбор причин:
  [`docs/RUBANOVA_NKRYA_PIPELINE_MANUAL.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/RUBANOVA_NKRYA_PIPELINE_MANUAL.md) §10.
  - **Порт** [`web/corpus_builder/sanskritisms/extract.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/sanskritisms/extract.py):
    слой эпитетов сканировал плоскую `re`-альтернацию из 1346 склоненных форм по
    каждому стиху (`O(текст × формы)`) → автомат Ахо-Корасик (новый
    [`_aho.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/sanskritisms/_aho.py),
    без зависимостей). На МБх Араньякапарве (2033 стиха, 199 570 токенов) extract+index
    **10.82 с → 3.45 с (3.1×)**; отпечатки lexicon/epithets/index не изменились (0
    расхождений по всем 2033 стихам), 30 hermetic + 3 corpus теста зеленые.
  - **`sans_stemmer.ipynb`**: `open_files` (`lem not in forn + sans` пересобирал
    ~24 k-список на каждую из ~390 k парадигм OpenCorpora → `set(forn) | set(sans)`
    один раз, ~1900× на этом шаге); `search` (`.lower()` пересчитывался на каждый
    ключ-рубрику + list-comp на каждое слово → вынос `sent_low`/`text_low` +
    префиксные множества, ~15× на ядре сопоставления); `index_unite` (пересборка
    `list(set(clean))` во внутреннем цикле + `re.match` на элемент за проход → вынос
    `uniq` + предвычисление слова, ~3–4×); `get_wordforms` (перечитывал+чистил весь
    файл на каждый вызов → кэш очищенных токенов); `capital_search` (конкатенация
    `sans + index3 + tr` на каждое слово → вынос).
  - **`corpus_marker.ipynb`**: `translate()` (IAST→кириллица, вызывается на каждое
    слово и на каждый символ в `proc_short`/`proc_long`) мемоизирован по входу —
    чистая функция, вывод не изменился.

## [0.10.0] - 2026-07-17
### Added
- **Стиховая проверка: различают ли русские переводчики санскритские прошедшие времена
  (H1052, Fable 5 `claude-fable-5`; директива адъюдикации A65 к HB-57).** Новый инструмент
  [`nkrya-parallel/export/past_tense_translation_check.py`](nkrya-parallel/export/past_tense_translation_check.py)
  (+ stats JSON + отчет [`PAST_TENSE_TRANSLATION_CHECK.md`](nkrya-parallel/export/PAST_TENSE_TRANSLATION_CHECK.md)):
  41 023 эпические пары стих⇄перевод, DCS-выведенные лексиконы высокой точности (имперфект
  342 форм по тегам · аорист 179 по formation-тегам · перфект 193 через тест редупликации —
  редуплицированный перфект в DCS не тегирован). **Итог: перевод НЕЙТРАЛИЗУЕТ
  противопоставление** — и перфектные, и имперфектные стихи уходят в русское прошедшее
  совершенного вида (64,7 % против 67,7 %), профили почти совпадают; χ² = 38,7 значим, но
  V Крамера = 0,084 — размер эффекта ничтожен. Прямое подтверждение доктрины «то же
  значение» переводческой практикой. Остаток: перфектные стихи чуть чаще идут настоящим
  историческим (10,3 % vs 5,5 %); клише «uvāca → говорит» его не объясняет (3,5 % из 2 652).

## [0.9.0] - 2026-07-16
### Added
- **Chronology dashboard — Minimal design mockup (H563 fan-out, H1057).** [web/corpus_builder/chronology/mockups/minimal.html](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/chronology/mockups/minimal.html): CSS-only restyle of the live [chronology page](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/chronology/index.html) into the Minimal direction (paper-white, single indigo accent, hairline rules) — markup, 934-text data island and render JS byte-identical (sha1-verified); JSON parses, JS syntax-checked. The Flask compare pages (`web/templates/compare_*.html`) need a live backend and are out of mockup scope (H815 precedent). Live page untouched pending a human's promotion call. Fable 5 (`claude-fable-5`).

## [0.8.0] - 2026-07-14

### Added
- **Somadeva KSS books 1–10 sloka re-key (H928) — all 18 KSS books now uniformly
  śloka-keyed.** Re-ingested books 1-10 from lingtrain sentence-ordinal keys to true
  śloka keys (`lambaka.taraṅga.śloka(-range)`, `structure="verse"`), matching books
  11-18's H910 keying. Per-taraṅga Workflow fan-out (76 tasks: 66 taraṅgas + 10 maṅgala
  verses), ground-truth sliced directly from `parse_sanskrit`/`parse_russian`'s own
  record grouping (`web/corpus_builder/h928_prep_taranga_slices.py`, assertion-checked
  exact match against whole-book totals: 12,806 ślokas / 1,658 RU sentences) — supersedes
  an inherited `h928_plan.json` found to drift from real per-book counts. Fixed the RU
  wave-header regex in `somadeva_gretil_to_canonical.py` (optional trailing dot — books
  1-10's first `## L.T` header per chapter lacks it, previously misattributing taraṅga-1
  Russian text to taraṅga 0). Two genuine alignment defects caught by `validate_mapping`
  and fixed via targeted re-alignment: book 10 taraṅga 3 (8 Russian sentences degenerately
  collapsed onto one śloka) and book 8 taraṅga 6 (off-by-one at a real source-numbering
  gap, śloka 244 skipped). Final: 1,658 groups, mean confidence 0.82 (0.68–0.87 per book),
  searchable in FTS5. `web/corpus_builder/h928_aggregate_and_emit.py` converts per-taraṅga
  local Russian indices to global per-book indices and runs the existing
  `validate_mapping`/`emit_jsonl` pipeline.

### Fixed
- **Bṛhannīla-tantra JSONL duplicate comment IDs** (48 identical double rows) blocked full-pin web publish; dropped dups (2533→2485 records). Rebuild corpus-manifest pin: **230** sources / **723 229** records. `*.jsonl text eol=lf` in `.gitattributes` so Windows pin builds match Linux publish.
- **Full-corpus `ingest.py` was failing on the combined DBhP source (H941).**
  `data.txt` lists the real, intentionally-built `devibhagavata-purana.html`
  but its canonical `web/corpus_builder/jsonl/devibhagavata-purana.jsonl` was
  never persisted (H558's `emit_dbhp_corpus.py` only ever wrote it to a temp
  path). Regenerated by concatenating skandhas 1–12 in order (37,984 lines,
  matching the documented record count, zero id collisions); full ingest now
  completes 182/182 sources with exit 0.

## [0.7.0] - 2026-07-14

### Added
- **Somadeva KSS book 12 complete (all 37 taraṅgas) + book 14 QA re-run (H927).**
  Book 12 (Śaśāṅkavatī, 4 931 ślokas incl. the 25 Vetālapañcaviṃśati tales) fully
  aligned via a 34-agent per-taraṅga Workflow fan-out — 900 groups, 1 800 records,
  confidence min 0.15 mean 0.81. Book 14's old positional alignment (mean 0.53,
  a token-limit fallback from H910) replaced with a content-anchored per-taraṅga
  re-run — mean confidence 0.53 → 0.80, low-confidence groups 122 → 8. **18 of 18
  lambakas now in the corpus.** Caught + fixed a real fan-out defect: one taraṅga's
  first pass produced inverted śloka ranges, re-run with an explicit self-check.
  70 low-confidence groups routed to a review sheet. Reproducible artifacts:
  `somadeva_alignments/book12.alignment.json` / `book14.alignment.json`,
  `h927_prep_taranga_slices.py`. Report:
  `web/corpus_builder/SOMADEVA_KSS_BOOK12_BOOK14QA_FANOUT_REPORT.md`.
- **Somadeva KSS books 13–18 aligned + ingested (H910 fan-out).** Six more
  lambakas śloka-keyed and searchable (13 Madirāvatī, 14 *pañca*, 15 Mahābhiṣeka,
  16 Suratamañjarī, 17 Padmāvatī, 18 Viṣamaśīla) — **17 of 18 books now in the
  corpus**. 3 683 ślokas → 681 groups; alignment maps committed under
  `web/corpus_builder/somadeva_alignments/`. Two upstream data defects found +
  handled reproducibly: the **SA/RU file swap at lambakas 14↔15** (added a
  `--ru-book` converter option; passage keys always from the Sanskrit lambaka) and
  the **book-12 Vetāla-ref annotation** that silently dropped 1 958 ślokas (regex
  loosened). `build_corpus_html._ROMAN` extended XII→XX for 18 books. Book 12
  (giant, 4 931 ślokas) deferred to a per-taraṅga run; book 14 is positional
  (token-limit fallback), flagged for review. Report:
  `web/corpus_builder/SOMADEVA_KSS_BOOKS_11_18_FANOUT_REPORT.md`.
- **Somadeva KSS book-11 pilot — LLM-assisted śloka alignment (H910).** New
  `web/corpus_builder/somadeva_gretil_to_canonical.py` parses the in-repo
  `sokss`-keyed Sanskrit + Serebryakov Russian prose for books 11–18; an LLM
  aligner produces a monotonic śloka-range mapping. **Book 11 (Velā) aligned +
  ingested end-to-end**: 116 ślokas ↔ 27 Russian sentences → 27 śloka-range groups
  (`structure="verse"`, keys like `11.1.4-10`), searchable in FTS5. Reproducible
  artifacts: converter, `somadeva_alignments/book11.alignment.json`,
  `jsonl/kathasaritsagara-11.jsonl`, `Data/kathasaritsagara-11.html`. **Measured
  Human vs. Agent:** 8.8 min (agent) vs ~15.7 days (human pace) for book 11 —
  `web/corpus_builder/SOMADEVA_KSS_ALIGNMENT_PILOT_REPORT.md`.
- **`/corpus-rights-unlock` skill** referenced in
  `docs/SOMADEVA_KSS_RIGHTS_COPYRIGHT_UNLOCK.md` (+ a plain-language "what opens up
  when copyright clears" example): the reusable playbook for publishing any
  grey-rights corpus once rights are cleared.

### Changed
- **`morph_service.py` dropped `indic_transliteration` for the canonical
  `sanskrit-util` package (H922 momentum-axis track).** The three transliterate
  calls (IAST/Devanāgarī→SLP1, SLP1→IAST, SLP1→Devanāgarī) now use
  `sanskrit_util.to_slp1`/`deva_to_slp1`/`from_slp1`/`slp1_to_devanagari`.
  Vendored (not pip-installed) as `web/app/vendor/sanskrit_util.py` — a
  byte-identical copy of `sanskrit-util/py/sanskrit_util/__init__.py` v0.4.0 —
  because the Docker build (`COPY web/ .`) has no access to the sibling
  `sanskrit-util` repo; same "re-copy on update, never hand-edit" pattern as the
  org's JS vendor copies (csl-atlas, csl-apidev). 96 old-vs-new comparisons
  across 4 directions on real Sanskrit words matched byte-for-byte; the one
  intentional difference found is a **fix**, not a regression — the old library
  silently passed `ṁ` (U+1E41) through unconverted, sanskrit-util correctly
  folds it to SLP1 `M`. All 568 pre-existing tests (9 in `test_morph.py`) pass
  unchanged before and after. `indic-transliteration` stays in
  `web/requirements.txt` — `web/corpus_builder/html_to_canonical.py` (an offline
  ingestion script, not part of the running app) still depends on it; that file
  and `slug.py` (Cyrillic transliteration, out of scope) are unchanged. See
  [SHARED_CODE.md](https://github.com/gasyoun/github-spine/blob/main/SHARED_CODE.md)
  §1-2 row 4.

## [0.6.0] - 2026-07-14

### Added
- **SA-side morphology anchored on DCS gold (H906).** New
  [`web/corpus_builder/dcs_align.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/dcs_align.py)
  aligns each `seg=sa` verse to the matching DCS chapter (`passage B.C.V` →
  `MBh, B, C` / `Rām, <kāṇḍa>, C`; DCS `sent_counter` = verse) and emits the DCS
  **gold** per-token analysis (lemma · UPOS · case · gender · number) behind
  `nkrya_export.py --sa-morph` as an additive `<slug>.sa_morph.tsv` (deterministic).
  Coverage: **MBh ~99%** (most parvas 98–100%; 152k gold tokens on Āraṇyakaparva),
  Rāmāyaṇa partial (62–80%, verse-map divergence). The Bhagavadgītā gap surfaces
  as bhishmaparva 47.6% (Gītā absent from DCS, H848). DCS sqlite is local-only
  (`$DCS_SQLITE`); the layer degrades to empty if absent. +3 tests (12 pass).
  Report: [`SA_MORPHOLOGY_H906_REPORT.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/SA_MORPHOLOGY_H906_REPORT.md).
  The vidyut second-opinion diff is a scoped follow-up (needs the vidyut data download).

## [0.5.0] - 2026-07-14

### Added
- **RU-side morphology + Кали→кал filter (H905).** New [`web/corpus_builder/ru_morph.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/ru_morph.py)
  tags every Cyrillic token of a `seg=ru` segment with **lemma · POS · case · number** via
  **pymorphy3** (which ships the OpenCorpora dictionary — the same КРС data Rubanova's 271 MB
  `dict.opcorpora.txt` held), emitted behind `nkrya_export.py --ru-morph` as an additive
  `<slug>.ru_morph.tsv` (deterministic, byte-identical across `PYTHONHASHSEED`). The inline НКРЯ
  `<w><ana/>` fold is deferred to the H906-coordinated per-token scheme.
### Fixed
- **Bṛhannīla-tantra JSONL duplicate comment IDs** (48 identical double rows) blocked full-pin web publish; dropped dups (2533→2485 records). Rebuild corpus-manifest pin: **230** sources / **723 229** records. `*.jsonl text eol=lf` in `.gitattributes` so Windows pin builds match Linux publish.
- **Кали→кал false positives (H905).** `sanskritisms/filters.py` gains `is_russian_word()`
  (pymorphy3 `word_is_known`, minus Rubanova's curated collision exceptions); `extract.py` now
  drops any non-capitalized candidate that is a known Russian wordform — reproducing Rubanova's
  `rus_words` opcorpora filter without the 271 MB dump. Lowercase «кала» (genitive of the common
  word *кал*) no longer captured as the Sanskritism *кала*; capitalized proper names stay exempt.
  Measured 41→37 lemmas on `01_atharvaveda` (4 false positives removed). +3 regression tests.
  Report: [`web/corpus_builder/RU_MORPHOLOGY_H905_REPORT.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/RU_MORPHOLOGY_H905_REPORT.md).
### Changed
- **Somadeva KSS scale-up P0 resolved + made execution-ready (H910).** Confirmed
  the complete Serebryakov Russian and śloka-keyed Sanskrit (`sokss_L,T.S` refs)
  for **all 18 books** already exist as `.txt` in the upstream repo (~21 538
  ślokas; books 11–18 = ~8 730). Books 11–18 need alignment only — no sourcing,
  no external fetch, no human gate. Rewrote
  `docs/ROADMAP_SOMADEVA_KSS_ALIGNMENT_SCALEUP_2026_2027.md` execution-ready and
  added `docs/SOMADEVA_KSS_RIGHTS_COPYRIGHT_UNLOCK.md` (what a proven copyright /
  redistribution licence unlocks: НКРЯ export, kosha datasets.json, Zenodo DOI,
  bulk download).

## [0.4.1] - 2026-07-14

### Added
- **Somadeva Kathāsaritsāgara SA↔RU corpus — 10 lambakas ingested (H907).**
  Absorbed the [Marc-Winner/somadeva](https://github.com/Marc-Winner/somadeva)
  lingtrain alignment into the corpus: new
  `web/corpus_builder/somadeva_lingtrain_to_canonical.py` converts the Lingtrain
  XML (8 chapters) + `.lt` `doc_index` (ch4, ch10) into canonical JSONL —
  **9 998 aligned sentence-pairs across lambakas 1–10**, keyed
  `lambaka.taraṅga.sentence-ordinal`, Devanagari→IAST/SLP1. Emitted
  `kathasaritsagara.meta.json`, combined + per-lambaka `jsonl/kathasaritsagara*.jsonl`,
  10 `Data/kathasaritsagara-{N}.html`+`.no_tags`+meta, `data.txt` registration.
  Verified searchable via real `ingest.py` → FTS5 (10 sources / 19 994 rows;
  `somaprabhā` 33, `океан` 58 hits) + schema contract tests green. Russian inherits
  the corpus "grey per project ruling" rights status (`corpus.db` gitignored).
  Scale-up plan (full 18 lambakas, LLM-assisted, GRETIL spine) +
  lingtrain-vs-LLM method comparison in
  `docs/ROADMAP_SOMADEVA_KSS_ALIGNMENT_SCALEUP_2026_2027.md`.
- **НКРЯ morphology Wave 0: Rubanova pipeline documented (H904).** E. A.
  Rubanova's two source notebooks (`sans_stemmer.ipynb` +
  `deeppavlov_parsing.ipynb`, as updated by Marsel) are now tracked in
  `nkrya-parallel/diplom-rubanova/`, and `docs/RUBANOVA_NKRYA_PIPELINE_MANUAL.md`
  (+ `.meta.md`) documents the whole pipeline line-by-line: the 10 data inputs,
  Stage A (DeepPavlov UD morphosyntax) → Stage B (sanskritism proper-name index),
  the **Кали→кал root cause** (the dropped 271 MB opcorpora corpus filter), and an
  original-vs-current-port delta table that is the work-list for the RU-morphology
  (H905) and SA-morphology (H906) builds. The Sanskrit side used **DCS** as its
  markup source (no home-grown analyzer) — documented as a reproduction target for
  H906, not a port.
- **Third notebook + upstream source (H904 follow-up).** Took
  `corpus_marker.ipynb` from Rubanova's upstream repo
  ([evgeniarubanova/sanskrit_stemmer](https://github.com/evgeniarubanova/sanskrit_stemmer))
  — the **RU↔SA word aligner** that transliterates IAST→Cyrillic (via
  `translation.txt`/`correct_trans.txt`) and prefix-matches Russian sanskritisms
  to their Sanskrit source words over a verse-block-aligned corpus, then
  colour-highlights both sides. Now tracked as Stage C; the manual's §6 corrected
  accordingly — the SA side uses **transliteration+alignment, not DCS** (DCS
  morphology stays an H906 reproduction target). MANIFEST now points at the
  upstream repo for the bulk data; noted that `dict.opcorpora.txt` is absent even
  upstream (third-party OpenCorpora).

## [0.4.0] - 2026-07-13

### Added
- **НКРЯ Wave 4: full-corpus export freeze (H821).** `nkrya_export.py` gains an
  `--all-ru` mode that exports **every seg=ru source** (131, via `discover_ru_sources()`)
  with `--with-sanskritisms`, not just the 4-source pilot: **95,260 pairs across 131 sources**.
  Two committed sidecars — `nkrya-parallel/export/RIGHTS_TABLE.md` (per-source rights; 4 of 131
  documented from the H231 pilot meta, 127 flagged `needs_review` with no sidecar yet — a noted
  metadata-population follow-up) and `FULL_CORPUS_VALIDATION.md` (per-source classify() stats).
  The bulk per-source export bundle stays gitignored and ships as a **release artifact**.
### Fixed
- **Bṛhannīla-tantra JSONL duplicate comment IDs** (48 identical double rows) blocked full-pin web publish; dropped dups (2533→2485 records). Rebuild corpus-manifest pin: **230** sources / **723 229** records. `*.jsonl text eol=lf` in `.gitattributes` so Windows pin builds match Linux publish.
- **Sanskritisms index was non-deterministic** — the singular/plural canonical merge
  (`sanskritisms/disambiguate.py`) and the candidate-set iteration (`extract.py`) depended on
  hash order, flipping the index `lemma`/`display` across runs. Now sorted → byte-identical
  output even across `PYTHONHASHSEED`, guarded by a new order-independence unit test. This was
  the blocker on Wave 4's determinism gate.

## [0.3.1] - 2026-07-12

### Fixed
- **Bṛhannīla-tantra JSONL duplicate comment IDs** (48 identical double rows) blocked full-pin web publish; dropped dups (2533→2485 records). Rebuild corpus-manifest pin: **230** sources / **723 229** records. `*.jsonl text eol=lf` in `.gitattributes` so Windows pin builds match Linux publish.
- **Cyrillic homoglyph contamination in Sanskrit-IAST (`sa`) segments** — 7 verses
  across 4 corpus files carried a Cyrillic letter mis-encoded where a Latin IAST
  letter belongs (`с` U+0441 → `c`, `а` U+0430 → `a`): Sundarakāṇḍa 1.35 / 22.25 /
  31.4 / 37.12 and yoga-sūtra 4.8 (Vyāsa, Sharma, Zagumennov editions), in the
  `text` / `html` / `slp1` fields. Surfaced by the CommentaryStrategies
  helayo-alignment apparatus run (those verses were quarantined out of
  `apparatus_sundara_variants.json`). Fixed in place; re-scan confirms zero remain
  ([#45](https://github.com/gasyoun/SamudraManthanam/issues/45)).

### Added
- **`web/corpus_builder/scan_cyrillic_homoglyphs.py`** — stdlib-only corpus-integrity
  scanner/fixer for Cyrillic homoglyphs inside `sa` segments. Token-aware: only a
  Cyrillic letter inside a mixed Latin+Cyrillic letter-run (the homoglyph signature)
  is substituted; pure-Cyrillic runs — legitimate Russian editorial notes such as
  `{Проверить!}` or `[на GRETIL не шлока]`, 2802 of them corpus-wide — are left
  verbatim. `--fix` rewrites in place; report mode is read-only.

## [0.3.0] - 2026-07-12

### Added
- **Sanskrit-side 3-path annotation comparison** (НКРЯ Wave 2, H759):
  `web/corpus_builder/nkrya_annotate.py` (+ `web/tests/test_nkrya_annotate.py`)
  compares plain SLP1 (A) vs a text-keyed DCS lemma/morph crosswalk (B) vs
  vidyut-cheda fresh tagging (C) on the 11,055-pair pilot; committed
  metrics/report/adjudication-sample under `nkrya-parallel/export/`
  (`ANNOTATION_3PATH_COMPARISON.md`); new A41 §6 records the resulting
  annotation policy (A always; B where DCS covers, CC BY 4.0; C not shipped).
- **НКРЯ / ruscorpora parallel-export programme** — `nkrya-parallel/`: the
  Sanskrit↔Russian corpus export track toward the Russian National Corpus.
  Wave 0 landed the export roadmap and its eight MG rulings ([PR #39](https://github.com/gasyoun/SamudraManthanam/pull/39),
  H753) plus the curated diplom-rubanova reference artifacts and hardened bulk
  `.gitignore` ([PR #40](https://github.com/gasyoun/SamudraManthanam/pull/40)).
- **НКРЯ Wave-1 pilot triple export** (H754) — Mahābhārata 3 + Rāmāyaṇa 1–3
  exported in the parallel `#sa`/`#ru`/annotation triple schema
  ([PR #41](https://github.com/gasyoun/SamudraManthanam/pull/41)), the first
  end-to-end pilot of the export pipeline over real books.
- **Docusaurus review-packet site** for the ВКР/VKR review of the НКРЯ export,
  with a GitHub Pages deploy workflow ([PR #38](https://github.com/gasyoun/SamudraManthanam/pull/38)).
- Reusable **PDF → canonical-JSONL → app-HTML** corpus-ingestion pipeline in
  `web/corpus_builder/` (the free-toolchain successor to the Delphi `cb.exe` for
  new ingestion): `ignatjev_pdf_to_canonical.py`, `align_sanskrit.py`,
  `build_corpus_html.py` — documented in `web/corpus_builder/PDF_INGESTION_PIPELINE.md` (H534).
- **Devībhāgavata-purāṇa Skandha 1** (A. Ignatjev, Касталия 2018) ingested as
  `Data/devibhagavata-purana-1.html` (20 chapters, 1181 verses, 429 comments);
  152 → 153 active sources.
- **Sanskrit verse alignment for DBhP Skandha 1** — `sanskritdocuments_dbhp_to_canonical.py`
  transcodes the sanskritdocuments.org ITRANS source (`devIbhAgavatam01.itx`) to
  the canonical `#sa` schema; the source-agnostic aligner joins it onto the
  Russian at **1180/1181 verses (99.9%)**. Sanskrit source chosen by MG
  (`@DECIDE` 10-07-2026) because the full DBhP is absent from GRETIL. Aligned
  IAST now renders alongside the Russian in `Data/devibhagavata-purana-1.html`.

- **Devībhāgavata-purāṇa skandhas 2–12** (A. Ignatjev, Касталия 2018) ingested
  and Sanskrit-aligned (H558): 11 per-skandha `Data/devibhagavata-purana-<N>.html`
  files plus a combined `devibhagavata-purana.html` (all registered in
  `data.txt`), completing the 12-skandha work. ~17,300 RU verses / ~3,600
  comments; per-skandha RU→Sanskrit match ~99% (from `devIbhAgavatam02–12.itx`,
  sanskritdocuments.org). 153 → 165 active sources.
- Batch drivers `web/corpus_builder/build_dbhp_skandhas.py` (RU parse → Sanskrit
  convert → align) and `emit_dbhp_corpus.py` (per-skandha + combined HTML).

### Changed
- Hardened `ignatjev_pdf_to_canonical.py` for all six Ignatjev volumes (H558):
  gap-tolerant endnote re-join (fixes the Vol 2/4/5 18/2/71 comment desync),
  plural/all-caps note headings, varied/wrapped chapter colophons, note-block
  skandha rollover, Devī-gītā chapter offset, and a duplicate passage-id
  integrity guard. Skandha 1 output unchanged (20 ch / 1181 v / 429 c).

### Deprecated

### Removed

### Fixed
- **Bṛhannīla-tantra JSONL duplicate comment IDs** (48 identical double rows) blocked full-pin web publish; dropped dups (2533→2485 records). Rebuild corpus-manifest pin: **230** sources / **723 229** records. `*.jsonl text eol=lf` in `.gitattributes` so Windows pin builds match Linux publish.
- `html_to_canonical.py` now unescapes HTML entities in searchable text, so
  Ignatjev's OCR-mangled editorial brackets (`>…@`) round-trip exactly (16180/
  16180 RU verses reproduce); `build_corpus_html.py`'s sort key tolerates the
  integrity guard's disambiguation suffix.

### Security

## [0.2.0] - 2026-07-07

### Added
- Re-ingested 4 dharmaśāstra texts (`naradasmriti`, `vishnu-smriti`, `yajnavalkyasmriti`, `yajnavalkyasmriti_add`) that existed on disk but were never added to the corpus manifest; 148 → 152 active sources.

## [0.1.1] - 2026-07-06

### Changed
- Filled `title_en`/`provenance`/`rights` across all 148 active corpus `meta.json` (Phase 0 hygiene, H231) via a reproducible per-slug script (`web/ingest/fill_meta_phase0.py`).

## [0.1.0] - 2026-06-30

### Added
- Initial release of Samudra Manthanam project structure and web platform foundation.

