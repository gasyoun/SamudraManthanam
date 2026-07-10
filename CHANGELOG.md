# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Reusable **PDF → canonical-JSONL → app-HTML** corpus-ingestion pipeline in
  `web/corpus_builder/` (the free-toolchain successor to the Delphi `cb.exe` for
  new ingestion): `ignatjev_pdf_to_canonical.py`, `align_sanskrit.py`,
  `build_corpus_html.py` — documented in `web/corpus_builder/PDF_INGESTION_PIPELINE.md` (H534).
- **Devībhāgavata-purāṇa Skandha 1** (A. Ignatjev, Касталия 2018) ingested
  Russian-only as `Data/devibhagavata-purana-1.html` (20 chapters, 1181 verses,
  429 comments); 152 → 153 active sources. Sanskrit alignment deferred (full DBhP
  absent from GRETIL — pending a source decision).

### Changed

### Deprecated

### Removed

### Fixed

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

