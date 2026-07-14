# Somadeva KSS books 11–18 — LLM-assisted alignment: book-11 pilot report (H910)

_Created: 14-07-2026 · Last updated: 14-07-2026_

Pilot for [H910](https://github.com/gasyoun/Uprava/blob/main/handoffs/H910-Opus_SamudraManthanam_somadeva_kss_books11_18_alignment_14.07.26.md).
Book 11 (**Velā**) aligned and ingested end-to-end from the in-repo text, proving
the pipeline for the remaining books 11–18.

## Result — book 11, end to end

- **116 ślokas** (`sokss_11,0.1` maṅgala + `11,1.1..115`) ↔ **27 Russian prose
  sentences** → **27 aligned groups** keyed by śloka range (`11.1.1`, `11.1.2-3`,
  `11.1.4-10`, …), `structure="verse"`. 54 canonical records.
- Ingested via the real `ingest.py` → FTS5; search returns the aligned SA↔RU pair
  (`купца` → 5 hits at `11.1.30-35`; Naravāhanadatta + the messenger).
- Rendered `citation_block` HTML matches the platform format; `.no_tags` parity holds.

**Reproducible artifacts** (all committed):
`somadeva_gretil_to_canonical.py` (converter + emit) ·
`somadeva_alignments/book11.alignment.json` (the alignment map) ·
`jsonl/kathasaritsagara-11.jsonl` · `Data/kathasaritsagara-11.html`.

## Human vs. Agent — measured

Book 11 was aligned by an LLM agent in **8.8 minutes**. The two most recent books
of the manual (human, lingtrain) effort took **months each**. Per śloka:

| | **Human** (lingtrain + manual) | **Agent** (LLM-assisted, this pilot) |
|---|---|---|
| Book 9 (1 739 ślokas) | ~6.5 months (Jun 2024 → Jan 2025) | — |
| Book 10 (2 126 ślokas) | ~10.7 months (Jan → Dec 2025) | — |
| **Book 11 (116 ślokas)** | **~15.7 days** (at the human recent pace) | **8.8 min** (measured) |
| Throughput | **~7.4 ślokas/day** (books 9–10 avg) | **~13.1 ślokas/min** (~787/hr) |
| Projected books 11–18 (~8 730 ślokas) | **~3.2 years** | **~11 hours** of aligner compute + QA |
| Human effort | per-sentence manual correction | QA of low-confidence groups only |
| Cost (book 11) | months of volunteer calendar time | 98 578 agent tokens |

> **Honest caveat.** The human figures are *part-time volunteer calendar* time
> (they overstate raw labour hours); the agent figure is *wall-clock compute* for
> the alignment step alone (the deterministic converter/emit add seconds; QA of
> flagged groups adds human minutes). The comparison is of **time-to-a-shippable
> book**, which is the metric that gated this project for 2.5 years. Even
> discounting heavily, the gap is three-plus orders of magnitude.

## Quality + QA

- Mean alignment confidence **0.86** (min 0.50). **2 of 27 groups** flagged
  `< 0.6` — both at the **final colophon boundary** (`11.1.114-115`): the Russian
  ends with the book's colophon ("Одиннадцатая книга… окончена"), which the
  coverage rule forces onto the last ślokas. This is an artifact of the
  partition constraint, not a mis-alignment of narrative content.
- `validate_mapping` confirmed the taraṅga-1 ranges are contiguous, non-overlapping,
  and cover ślokas 1..115 exactly (no gaps).
- For the larger books (12–18), low-confidence groups route to a `/review-sheet`
  HTML voting sheet (registered in `Uprava/REVIEW_SHEETS_INDEX.md`); for this
  2-group pilot they are documented here.

## Books 1–10 can also get true śloka keys (roadmap P3)

The `chapters_san` files for **books 1–10 also carry `sokss` refs**
(`sokss_1,8.38`, …, `sokss_10,10.193`). So the same converter can re-key the 10
already-ingested books from sentence-ordinals to **true ślokas**, removing the
mixed-keying wrinkle (1–10 sentence-keyed, 11–18 śloka-keyed). Optional, high value.

## Next — books 12–18

Same pipeline, one book at a time (book 12 = ~4 931 ślokas, the giant; book 14
Russian lacks `## L.T.` headers — single-taraṅga parser fallback). Fan out the
aligner per taraṅga via the Claude Workflow tool.

_Dr. Mārcis Gasūns_
