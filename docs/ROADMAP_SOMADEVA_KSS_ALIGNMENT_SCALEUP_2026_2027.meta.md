# Metadoc — ROADMAP_SOMADEVA_KSS_ALIGNMENT_SCALEUP_2026_2027.md

_Created: 14-07-2026 · Last updated: 29-07-2026_

Companion record for [ROADMAP_SOMADEVA_KSS_ALIGNMENT_SCALEUP_2026_2027.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ROADMAP_SOMADEVA_KSS_ALIGNMENT_SCALEUP_2026_2027.md).

## Purpose
Orientation + plan for scaling the Somadeva Kathāsaritsāgara SA↔RU parallel corpus
from the 10 aligned lambakas (ingested in H907) to the full 18-lambaka work, using
an LLM-assisted aligner over the complete GRETIL Sanskrit spine.

## Audience
A future session (or MG) resuming the KSS scale-up; anyone deciding the LLM-vs-manual
alignment method or the Russian-coverage prerequisite.

## Provenance
- Handoff [H907](https://github.com/gasyoun/Uprava/blob/main/handoffs/H907-Opus_SamudraManthanam_somadeva_kss_ingest_scaleup_14.07.26.md), Opus 4.8 (`claude-opus-4-8[1m]`), 14-07-2026.
- Upstream alignment data: [Marc-Winner/somadeva](https://github.com/Marc-Winner/somadeva) @ `99a72bd` (private).
- Method-comparison numbers derived from that repo's git history (2023-07-30 → 2026-01-26).

## Ranked improvement backlog
1. ~~**P0 Russian inventory**~~ ✅ **RESOLVED 14-07-2026 (H910):** the complete Serebryakov Russian + śloka-keyed Sanskrit for all 18 books already exist as `.txt` in the upstream repo; books 11–18 need alignment only, no sourcing.
2. ~~**Execute P1 (align books 11–18)**~~ ✅ **RESOLVED — H910/H927:** all 18 lambakas now uniform śloka-keyed (see the roadmap's own status banner, updated 26-07-2026).
3. ~~**Replace the §3 LLM projection with a measured number**~~ ✅ **RESOLVED** alongside P1 execution (H910/H927) — the projection in §3 is superseded by the measured book-11 pilot figures.
4. ~~**Decide śloka-rekey policy for books 1–10 (P3)**~~ ✅ **RESOLVED — H928:** books 1–10 re-keyed to śloka; no mixed-keying wrinkle remains (see §Limitations below, now stale for the same reason — flagged 29-07-2026).
5. Verify the provisional per-lambaka bibliography before НКРЯ submission — the one item still genuinely open.

## Limitations
- ~~The LLM throughput is projected, not measured (stated honestly in §3).~~ **Stale (29-07-2026):** superseded by the measured book-11 pilot figures once P1 executed.
- ~~Books 1–10 are sentence-keyed (śloka anchoring lost upstream); books 11–18 will be śloka-keyed (§2) — a mixed-keying wrinkle until the optional P3 re-key.~~ **Stale (29-07-2026):** P3 (H928) re-keyed books 1–10 too; all 18 lambakas are now uniformly śloka-keyed, no mixed-keying wrinkle remains.
- Book 14 Russian shows no `## L.T.` wave header — a P1 parser edge case to confirm (not yet re-verified this pass).

## Related
- [ROADMAP_NKRYA_PARALLEL_RUSCORPORA_2026_2027.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ROADMAP_NKRYA_PARALLEL_RUSCORPORA_2026_2027.md) — the НКРЯ export workstream that P5 feeds.
- [web/corpus_builder/PDF_INGESTION_PIPELINE.md](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/PDF_INGESTION_PIPELINE.md) — the canonical-JSONL pipeline reused here.

## Revision history
- 14-07-2026 (Opus 4.8 `claude-opus-4-8[1m]`, H907): created alongside the roadmap; documents the 10-lambaka ingest + scale-up plan.
- 14-07-2026 (Opus 4.8 `claude-opus-4-8[1m]`, H910): **P0 resolved** — complete Russian + śloka-keyed Sanskrit for all 18 books found in-repo; roadmap rewritten execution-ready (books 11–18 align now, no human gate); added sibling [SOMADEVA_KSS_RIGHTS_COPYRIGHT_UNLOCK.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/SOMADEVA_KSS_RIGHTS_COPYRIGHT_UNLOCK.md).
- 29-07-2026 (Sonnet 5 `claude-sonnet-5`, H1878 roadmap-drift sweep): backlog items 2–4 and the Limitations section were stale — `.ai_state.md` and the roadmap's own 26-07-2026 status banner show P1 (H910/H927) and P3 (H928) both DONE, all 18 KSS lambakas uniformly śloka-keyed. Struck the stale rows; item 5 (НКРЯ bibliography verification) is the one genuinely open item.
