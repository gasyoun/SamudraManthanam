# PDF_INGESTION_PIPELINE.md — metadoc

_Created: 10-07-2026 · Last updated: 10-07-2026_

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

_Dr. Mārcis Gasūns_
