# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
- **Sanskritisms index was non-deterministic** — the singular/plural canonical merge
  (`sanskritisms/disambiguate.py`) and the candidate-set iteration (`extract.py`) depended on
  hash order, flipping the index `lemma`/`display` across runs. Now sorted → byte-identical
  output even across `PYTHONHASHSEED`, guarded by a new order-independence unit test. This was
  the blocker on Wave 4's determinism gate.

## [0.3.1] - 2026-07-12

### Fixed
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

