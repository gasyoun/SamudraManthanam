# PDF_INGESTION_PIPELINE.md — metadoc

_Created: 10-07-2026 · Last updated: 11-07-2026_

Companion record for
[`PDF_INGESTION_PIPELINE.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/PDF_INGESTION_PIPELINE.md).

- **Purpose:** document the reusable PDF → canonical-JSONL → app-HTML pipeline
  (the free-toolchain successor to the Delphi `cb.exe` for new ingestion).
- **Audience:** any future session ingesting a print/PDF translation into the
  Samudra Manthanam corpus.
- **Provenance:** built for handoff **H534** (Devībhāgavata-purāṇa, A. Ignatjev),
  session of 10-07-2026, model **Opus 4.8 (`claude-opus-4-8`)**.

## Ranked improvement backlog

1. **Harden `parse_endnotes` for Vols 2/4/5** — the sequential-join desyncs
   (comment counts 18/2/71 vs hundreds expected). Likely an extra endnote-start
   shape (roman-numeral chapter ref, multi-target ref, or a per-chapter footnote
   restart in some skandhas). Status: OPEN — blocks full-corpus comment ingest.
2. **Batch-ingest skandhas 2–12** once (1) lands. Status: OPEN.
3. **Sanskrit source decision + alignment** — full DBhP absent from GRETIL;
   candidate sanskritdocuments.org. Status: OPEN (@DECIDE in GTD).
4. **Web-converter comment anchors** — emit `comment_{ch}_{v}` (or teach
   `html_to_canonical._parse_comment_anchor` the `comment_{fn}` form) so DBhP
   comments round-trip to their verse on the web-ingest path, not a `c.N.pM`
   fallback. Status: OPEN — cosmetic for the desktop app, matters for web.
5. **Combined multi-skandha file** — `--combined` is implemented but only
   exercised on the single-skandha pilot; verify the desktop app's
   `iRecordLimit`/load tolerates a full 6-volume single HTML. Status: OPEN.

## Known limitations / caveats

- First-line marker uses the corpus's actual `<!-- Title --!>` convention (note
  `--!>`, not `-->`); the handoff's acceptance-gate regex `^<!-- .+ -->$` was
  written against the ideal, but matching the 100+ existing `Data/*.html` files
  (all `--!>`) is what the desktop reader parses, so `--!>` is correct.
- Verse-count records run slightly below the edition's stated sloka count where
  the translator merged verse ranges (e.g. `(69)` spanning 68–69) — this is
  faithful, not a miss; gaps are logged in `report["verse_gaps"]`.

## Intended use / known misuse

- **Intended use:** ingesting a print-derived PDF translation (regular,
  colophon-marked source conventions — Ignatjev-style `Так … заканчивается
  <N> глава` chapter markers, trailing `(N)` verse numbering, numbered
  `Комментарий` endnote blocks) into the Samudra Manthanam desktop-app corpus
  (`Data/*.html`) and, on a best-effort basis, the web ingest path; optionally
  aligning a source-agnostic Sanskrit `#sa` JSONL onto the Russian `#ru` groups
  by `SKANDHA.CHAPTER.VERSE` key.
- **Known misuse / out of scope:**
  - Feeding a PDF whose structure does **not** follow the source's own regular
    colophon/verse-marker conventions — the parser recovers structure from
    those literal patterns, not layout heuristics, and will silently under- or
    mis-segment on an irregularly-formatted source (see the Vols 2/4/5
    endnote desync in the ranked backlog).
  - Treating `align_sanskrit.py` as a statistical/fuzzy aligner — it is a
    strict key join per
    [`ALIGNMENT_SPEC.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ALIGNMENT_SPEC.md)
    §0; passing mismatched-numbering Sanskrit sources will produce a large
    `ru_only` fallback rate, not a forced alignment.
  - Running the batch (`--combined`, multi-skandha) path unverified beyond the
    single-skandha pilot it was exercised on — the desktop app's
    `iRecordLimit`/load behaviour on a full 6-volume single HTML is unproven.
  - Relying on the web-ingest comment anchors for a work ingested through this
    pipeline before the `comment_{ch}_{v}`/`comment_{fn}` gap (backlog item 4)
    is closed — comment **text** round-trips, but verse linkage does not on
    that path.

## Maintenance & sunset plan

- **Maintainer:** whichever session/agent picks up the next Ignatjev-corpus
  handoff (no dedicated human owner beyond the standing project maintainer);
  treat as agent-maintained house tooling, not a pinned-owner service.
- **Trigger to revisit:** any of the five open backlog items above landing
  (especially #1, the endnote-desync fix that gates batch ingest of skandhas
  2–12), or a new translator's PDF needing a different parser module under the
  same three-stage shape.
- **Sunset condition:** none planned while Ignatjev-style PDF ingestion remains
  the active corpus-growth path; would retire only if the project moves off
  PDF-sourced translations entirely or a successor tool subsumes all three
  stages (parse → align → emit).

## Deprecation status

`active`

## Related documents

- [`docs/CONVERTER_SPEC.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/CONVERTER_SPEC.md),
  [`docs/ALIGNMENT_SPEC.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ALIGNMENT_SPEC.md),
  [`docs/LINE_ID_SCHEME.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/LINE_ID_SCHEME.md)
- [`Corpus_builder/ROADMAP.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/ROADMAP.md)
  (the Delphi tool this pipeline supersedes for new ingestion)

## Revision history

| Date | Change | Model |
|---|---|---|
| 10-07-2026 | Created with the pipeline (H534): parser + aligner + emitter, Skandha-1 pilot ingested | Opus 4.8 (`claude-opus-4-8`) |
| 11-07-2026 | template v2 backfill (H663) | Sonnet 5 (`claude-sonnet-5`) |

_Dr. Mārcis Gasūns_
