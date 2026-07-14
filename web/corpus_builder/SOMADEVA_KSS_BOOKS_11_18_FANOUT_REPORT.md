# Somadeva KSS books 11–18 — LLM-assisted alignment fan-out report (H910)

_Created: 14-07-2026 · Last updated: 14-07-2026_

Fan-out following the book-11 pilot
([SOMADEVA_KSS_ALIGNMENT_PILOT_REPORT.md](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/SOMADEVA_KSS_ALIGNMENT_PILOT_REPORT.md)).
Books **11, 13, 14, 15, 16, 17, 18** are aligned (śloka-keyed) and ingested; book
**12** is deferred (see below). Combined with books 1–10 (H907), **17 of 18
lambakas are now in the corpus**.

## Per-book status

| Book | Lambaka | ślokas | groups | mean conf. | notes |
|---|---|---:|---:|---:|---|
| 11 | Velā | 116 | 27 | 0.86 | pilot ([PR #66](https://github.com/gasyoun/SamudraManthanam/pull/66)) |
| 13 | Madirāvatī | 220 | 37 | 0.86 | clean; name-anchored |
| 14 | *pañca* / "Five Beauties" | 626 | 131 | **0.53** | **positional** — see §Data integrity + QA |
| 15 | Mahābhiṣeka | 301 | 44 | **0.92** | corrected pairing; strongest match |
| 16 | Suratamañjarī | 421 | 52 | 0.87 | clean; jātaka-anchored |
| 17 | Padmāvatī | 994 | 186 | 0.89 | clean |
| 18 | Viṣamaśīla | 1121 | 231 | 0.66 | hymns lower the mean (§QA) |
| **12** | **Śaśāṅkavatī** | **4931** | — | — | **deferred** — 37 taraṅgas, needs per-taraṅga fan-out |

Books 13–18 verified searchable via scoped `ingest.py` → FTS5 (e.g. `Мандарадева`
→ `15.1.41-48`, `madirāvatī` → `13.1.24-28`, correct SA↔RU pairs). Keyed
`lambaka.taraṅga.śloka(-range)`, `structure="verse"` — true śloka keys, unlike the
sentence-ordinal books 1–10.

## Data-integrity findings (this is the durable part)

Two real defects in the upstream [Marc-Winner/somadeva](https://github.com/Marc-Winner/somadeva)
data, both now handled reproducibly:

1. **SA/RU file swap at lambakas 14↔15.** The Sanskrit `chapters_san/…_chap_14`
   (*pañca* / "Five Beauties") pairs with the Russian `chapters_rus/…_chap_15`,
   and Sanskrit 15 (Mahābhiṣeka) with Russian 14 — the two editions number these
   two books differently. Detected independently by both aligners (zero proper-name
   overlap on the naïve same-number pairing; confidence 0.26 → **0.92** after
   correction). Handled by the `--ru-book` converter option; **passage keys always
   come from the Sanskrit lambaka**. The remaining files (11,12,13,16,17,18) pair
   1:1 (lambaka headers confirmed).
2. **Book-12 Vetāla-tale ref annotation.** Taraṅgas 9–31 of book 12 are the
   Vetālapañcaviṃśati, whose ślokas carry a dual ref `// sokss_12,10.1 (vet_3.1) //`.
   The original śloka regex required the ref immediately before `//`, silently
   **dropping 1 958 ślokas**. Fixed (regex allows the optional `(…)` annotation);
   book 12 now parses all 4 931 ślokas.

Also fixed: `build_corpus_html._ROMAN` only reached XII (Devībhāgavata's 12
skandhas) → extended to XX for the KSS's 18 books.

## Quality + QA

- **Book 14 is positional, not content-anchored** (mean 0.53, uniform 4–6-śloka
  ranges). Its aligner hit the 64 000-output-token limit on the full content pass
  (626 ślokas × 131 sentences); the retry produced a monotonic proportional
  partition. The SA and RU *are* the same book (confirmed), so search returns
  approximately-right spans, but the fine boundaries need review. **All 122
  low-confidence groups route to a `/review-sheet`.** A per-taraṅga re-run would
  lift it to the others' quality.
- **Book 18's** lower mean (0.66) is concentrated in three stotra/hymn passages
  where the Russian renders a hymn as many short lines against few ślokas (a real
  granularity mismatch); its narrative spans are high-confidence.
- Every book's colophon śloka is a forced low-confidence tail (the partition rule
  assigns it a range though it translates nothing) — a known, harmless artifact.

## Human vs. Agent — measured across the fan-out

| | Human (lingtrain + manual) | Agent (LLM-assisted) |
|---|---|---|
| Books 11,13,15,16,17,18 (3 173 ślokas) | ~14 months (at ~7.4 ślokas/day) | **~2.8 h** total compute (6 agents, ~1 h wall-clock in parallel) |
| Throughput | ~7.4 ślokas/day | **~19 ślokas/min** |
| Book 18 alone (1 121 ślokas) | ~5 months (at recent pace) | **~64 min** |

The rate rose vs the book-11 pilot (13 → 19 ślokas/min) — larger books amortise
the setup. The projection for the deferred book 12 (~4 931 ślokas) is a few hours
of per-taraṅga agent compute.

## Deferred — book 12 (Śaśāṅkavatī, the giant)

4 931 ślokas across 37 taraṅgas (911 Russian sentences), including the 25 Vetāla
tales. Too large for one aligner call (the book-14 token-limit failure at 626
ślokas is the warning); it needs a **per-taraṅga fan-out** (one agent per taraṅga
via the Workflow tool) — now unblocked since the parser reads it fully. Tracked in
[H910](https://github.com/gasyoun/Uprava/blob/main/handoffs/H910-Opus_SamudraManthanam_somadeva_kss_books11_18_alignment_14.07.26.md).

_Dr. Mārcis Gasūns_
