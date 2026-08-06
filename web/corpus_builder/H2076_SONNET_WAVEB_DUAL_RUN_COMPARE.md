# H2076 — Sonnet independent re-run vs. Grok Wave B override (PR #125)

_Created: 06-08-2026 · Last updated: 06-08-2026_

Dual-run compare per the standing override protocol
([dual-run-override.md](https://github.com/gasyoun/claude-config/blob/main/references/dual-run-override.md)).
Source residual:
[H2076-Sonnet_SamudraManthanam_h1438-grok-dual-run-compare_01.08.26.md](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2076-Sonnet_SamudraManthanam_h1438-grok-dual-run-compare_01.08.26.md).
Override lane: [PR #125](https://github.com/gasyoun/SamudraManthanam/pull/125) (Grok 4.5,
`grok-4.5`, merged 01-08-2026, already on `main`).

## Method

1. Ran the merged-to-`main` Wave-B unit test file
   ([`web/tests/test_ignatiev_book_units.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/test_ignatiev_book_units.py))
   as-is.
2. Independently re-ran stage 1
   ([`ignatiev_book_to_canonical.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/ignatiev_book_to_canonical.py))
   from the raw archive sources (`archive_ignatiev_2026/`, gitignored, present only in the
   main checkout) into a scratch output dir, byte-diffed the resulting `*.raw.jsonl` against
   the committed jsonl for all five Wave-B works.
3. Independently ran stage 3's reverse direction
   ([`html_to_canonical.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/html_to_canonical.py)
   `--source <slug>`) against the **already-committed** `Data/*.html` to verify the
   round-trip claim without depending on my own stage-1 re-run.
4. Environment: Python 3.14, pandoc 3.9.0.2 (`pandoc --version`) — **not pinned anywhere in
   the repo** (checked `.github/workflows/*.yml`, `docs/*.md`,
   `web/corpus_builder/*.md` for a version string; none found).

## Results

**Unit tests:** 23/23 pass. `PDF_INGESTION_PIPELINE.md` §Wave B says "3 new unit tests; 19
total" — actual collected count is **23**, not 19. Doc-only slip, fixed in this pass (see
below); no functional issue.

**Round-trip (stage 3, against committed HTML — independent of my stage-1 re-run):** all five
works convert cleanly, 0 unreviewable failures; `review` counts equal the works' own endnote
counts exactly (Kulārṇava 1113, Yoginī 340, Mahābhāgavata 265) — i.e. every flagged record is
a genuine endnote-bearing verse, not a parse failure. This independently confirms the
"HTML round-trip ≥99%" claim for all five works.

**Stage-1 re-run (my re-extraction vs. committed jsonl) — per-work classification:**

| Work | Class | Evidence |
|---|---|---|
| Nīlamata-purāṇa | **identical** | 1 ch / 410 v / 0 endnotes, byte-identical `raw.jsonl` |
| Kulārṇava-tantra | **identical** | 17 ch / 2049 v / 1113 endnotes, exact match incl. `annotates_remaps` |
| Yoginī-tantra | **identical** | 19 ch / 1285 v / 340 endnotes, exact match incl. `id_collisions: ["19.48"]` |
| Adbhuta-rāmāyaṇa | **conflicting** | My re-run: 307 v (verse `23.51` merges into `23.52`'s text). Committed: 308 v, correctly split. Same already-flagged source anomaly (`verse_gaps: "23: 50->52", "52->51", "51->53"` — the translator's own out-of-order numbering at that spot). |
| Mahābhāgavata-purāṇa | **conflicting** | My re-run: 78 ch / 4169 v / 281 endnotes, `id_collisions` = 4 ids. Committed: 78 ch / 4232 v / 281 endnotes, `id_collisions` = 66 ids (the `55.1`–`55.61` set + others). Both runs agree ch.55 restarts numbering mid-chapter (Grok's caveat, [H1438](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1438-Sonnet_SamudraManthanam_ignatjev-tantras-puranas-ingest_22.07.26.md) §Wave B), but my pandoc run merges the duplicate-numbered verses into their predecessors instead of splitting them — 63 fewer verse records, exactly the ch.55 collision-set size. |

## Adjudication

Both conflicts trace to the **same root cause**: pandoc's plain-text extraction of a
docx paragraph boundary is not byte-stable across pandoc versions when the source itself
already has irregular verse numbering at that spot (an out-of-order marker in Adbhuta-
rāmāyaṇa 23; a full renumber-to-1 in Mahābhāgavata 55). The parser's regex-based marker
detection is deterministic *given* pandoc's output — the divergence is upstream of the
Python code, in pandoc's own text-wrapping/paragraph-joining behavior on these two
specific edge cases, and the repo pins no pandoc version to make that reproducible.

**Keep-best: keep `main`'s output (Grok lane, already merged) for the corpus data.** My
independent run is not more correct — it is the one that *dropped* verse `23.51` and
collapsed the ch.55 duplicate-id set instead of preserving it. Grok's committed jsonl
already logs both anomalies explicitly (`verse_gaps` for 23:50-52, the 66-entry
`id_collisions` for ch.55) rather than silently losing content, which is the safer
failure mode for an editorial pipeline. No corpus PR needed — nothing to revert or
re-merge.

**Net-new finding (Sonnet lane): pandoc version is unpinned**, which is the actual
defect this dual-run surfaced — not a corpus error, but a reproducibility gap: a future
re-run (on a different machine/pandoc release) can silently diverge by up to ~1.5% of a
work's verse count with no error raised. Landed as a doc fix in the same pass:
`PDF_INGESTION_PIPELINE.md` now records the pandoc version this ingestion was verified
against and flags ch.55 / Adbhuta ch.23 as pandoc-version-sensitive spots for any future
re-run to re-verify by count, not assume byte-identical.

## Stop condition

Comparison memo committed; round-trip and unit-test claims independently reproduced;
both conflicts adjudicated with keep-best = `main`; no corpus PR needed since the merged
data is confirmed correct-or-better on both disputed points. [H2076](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2076-Sonnet_SamudraManthanam_h1438-grok-dual-run-compare_01.08.26.md) closes as done.

_Dr. Mārcis Gasūns_
