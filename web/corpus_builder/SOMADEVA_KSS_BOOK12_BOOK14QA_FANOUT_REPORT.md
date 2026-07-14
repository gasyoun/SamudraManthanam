# Somadeva KSS book 12 per-taraṅga fan-out + book 14 QA re-run (H927)

_Created: 14-07-2026 · Last updated: 14-07-2026_

Follow-on to the H910 fan-out ([SOMADEVA_KSS_BOOKS_11_18_FANOUT_REPORT.md](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/SOMADEVA_KSS_BOOKS_11_18_FANOUT_REPORT.md)), which shipped books 11 + 13–18 and deferred book 12 (too large for one aligner call) and left book 14's alignment positional (the one-shot aligner hit the 64,000-output-token limit at 626 ślokas). This handoff ([H927](https://github.com/gasyoun/Uprava/blob/main/handoffs/H927-Sonnet_SamudraManthanam_somadeva_kss_book12_pertaranga_book14_qa_14.07.26.md)) closes both gaps via a genuine per-taraṅga Workflow fan-out — 34 independent alignment agents, one per taraṅga.

**Session note:** the first attempt at this handoff (a separate Max account) hit its usage limit mid-run, after 6 of book 12's 37 taraṅgas (t0 hardcoded + t1–t5, t7) completed. This session (Sonnet 5 `claude-sonnet-5`, per the handoff's own filename — the intended executor) resumed by fanning out the remaining 30 book-12 taraṅgas (t6, t8–t36) + all 4 of book 14's content taraṅgas (t1–t4) in one 34-agent Workflow run.

## Result — book 12 (Śaśāṅkavatī), complete

- **4,931 ślokas across 37 taraṅgas** (t0–t36, incl. the 25 Vetālapañcaviṃśati tales, roughly t9–t31) ↔ **911 Russian sentences** → **900 aligned groups**, 1,800 canonical records.
- Confidence (all 37 taraṅgas): **min 0.15, mean 0.81**, 62 groups < 0.6 (mostly verse-form ślokas/refrains — a single ornate śloka renders to a short Russian fragment, a genuine granularity mismatch rather than mis-alignment; concentrated in taraṅgas 11, 19, and 36's closing hymns/colophon).
- The 30 taraṅgas fanned out this session (t6, t8–t36): 623 groups, confidence min 0.15 mean 0.80, 58 < 0.6.
- Ingested via the real `ingest.py` → FTS5; verified searchable — `Тривикрамасена` (the Vetāla-tale frame-story king) correctly clusters at taraṅgas 8–9, exactly where that story begins.

## Result — book 14, QA re-run (positional → content-anchored)

- **626 ślokas across 5 taraṅgas** (t0–t4) ↔ **131 Russian sentences** → 131 groups, 262 records.
- Confidence: **min 0.30, mean 0.80** (was min 0.50 mean **0.53**, uniform 4–6-śloka positional ranges, per H910) — 8 groups < 0.6, down from the old map's 122 low-confidence groups.
- Re-ran per-taraṅga (t1–t4, max 209 ślokas each) rather than one 626-śloka call, which is what caused the original 64,000-output-token failure.

## A real defect caught and fixed: taraṅga 36's first pass was malformed

The first fan-out pass for book 12 taraṅga 36 (245 ślokas, 55 Russian sentences) produced **inverted ranges** (`sloka_start > sloka_end`) for ~16 groups around local ru_idx 28–47 — a genuine LLM-alignment failure, not a data issue. Caught by `validate_mapping`'s contiguity check before ingest. Re-ran that one taraṅga with an explicit self-check instruction (walk the mapping, verify monotonic/contiguous/non-inverted before returning); the retry passed clean. **Lesson for future per-taraṅga fan-outs:** always run `validate_mapping` (or an equivalent inversion/gap/overlap check) on every task's raw output before merging — a single malformed task in a 34-task fan-out is easy to miss without it.

## Quality + QA

- 70 groups total (62 book 12 + 8 book 14) fall below the 0.6 confidence threshold. Routed to a `/review-sheet` — [samudramanthanam-kss_book12-14-lowconf_review.html](file:///C:/Users/user/Documents/GitHub/SamudraManthanam-h927/review/samudramanthanam-kss_book12-14-lowconf_review.html) (gitignored, local-only), registered in [Uprava/REVIEW_SHEETS_INDEX.md](https://github.com/gasyoun/Uprava/blob/main/REVIEW_SHEETS_INDEX.md).
- `csl_pyutil.render_review_sheet()` (the canonical `/review-sheet` emitter) could not be installed — the auto-mode classifier blocked the external git `pip install` (no manifest declaration, no user-named source). The sheet was hand-written to the same spec (three-vote buttons, running tally, localStorage persistence, File System Access API auto-save + download fallback, Russian-language legend footer) per the skill's own fallback clause.
- Both books verified searchable via a scoped `ingest.py` run (a temp `corpus-path` with just the affected sources, to avoid an unrelated pre-existing gap — see below).

## Reproducible artifacts (all committed)

- `somadeva_gretil_to_canonical.py` — `RU_WAVE` regex fix (trailing `.` after the wave number made optional; chapters 02/10/14/15's first wave header lacks it).
- `h927_prep_taranga_slices.py` — per-taraṅga SA/RU slicer for this handoff's scope (book 12 remainder + book 14), adapted from the sibling H928 worktree's book1–10 slicer.
- `somadeva_alignments/book12.alignment.json` — the 30-taraṅga (t6, t8–t36) alignment map fanned out this session. **Note:** t0 (hardcoded) + t1–t5, t7 predate this handoff (produced by the interrupted first attempt) and their raw mapping was not separately archived — only the final JSONL persists for those 7 taraṅgas.
- `somadeva_alignments/book14.alignment.json` — full replacement (t0 hardcoded + new t1–t4), superseding the old positional map.
- `jsonl/kathasaritsagara-12.jsonl` / `jsonl/kathasaritsagara-14.jsonl` · `Data/kathasaritsagara-12.html` / `-14.html` (+ sidecars).

## Out-of-scope defect found in passing

A full-corpus `ingest.py` run currently fails: `data.txt` lists `devibhagavata-purana.html` as active but no matching `devibhagavata-purana.jsonl` exists (the DBhP work shipped 12 per-skandha JSONL files instead — H558). Unrelated to this handoff; flagged separately for a dedicated fix rather than touched here. Verification for this handoff used a scoped `corpus-path` (3 sources) instead.

_Dr. Mārcis Gasūns_
