# Roadmap — Somadeva's Kathāsaritsāgara SA↔RU alignment: scale-up to all 18 lambakas

_Created: 14-07-2026 · Last updated: 26-07-2026_

> **Status (26-07-2026): SCALE-UP COMPLETE.** P1 (books 11–18, H910/H927) and
> P3 (books 1–10 śloka re-key, H928) are **done** — all 18 lambakas uniform
> śloka keys. This file is historical method + provenance; residual low-conf
> human review sheets are not re-alignment work. Living residual:
> [ROADMAP_SAMUDRAMANTHANAM_RESIDUAL_2026H2.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ROADMAP_SAMUDRAMANTHANAM_RESIDUAL_2026H2.md).

Handoffs: [H907](https://github.com/gasyoun/Uprava/blob/main/handoffs/H907-Opus_SamudraManthanam_somadeva_kss_ingest_scaleup_14.07.26.md) (10 books ingested) ·
[H910](https://github.com/gasyoun/Uprava/blob/main/handoffs/H910-Opus_SamudraManthanam_somadeva_kss_books11_18_alignment_14.07.26.md) (books 11–18, execution-ready) ·
Model: Opus 4.8 (`claude-opus-4-8[1m]`) ·
Upstream data: [Marc-Winner/somadeva](https://github.com/Marc-Winner/somadeva) @ `99a72bd` (private)

This roadmap resumes the [Marc-Winner/somadeva](https://github.com/Marc-Winner/somadeva)
parallel-text project, **absorbs** it into SamudraManthanam as the single home,
and scales from the 10 aligned lambakas to the **full Kathāsaritsāgara (18
lambakas)** using an **LLM-assisted** aligner.

> **Update 14-07-2026 — P0 is resolved.** The complete Serebryakov Russian and
> the śloka-keyed Sanskrit for **all 18 books** already exist as `.txt` in the
> upstream repo (see §2). Books 11–18 need no sourcing, OCR, or human decision —
> only alignment. The scale-up is now **execution-ready**, tracked by
> [H910](https://github.com/gasyoun/Uprava/blob/main/handoffs/H910-Opus_SamudraManthanam_somadeva_kss_books11_18_alignment_14.07.26.md).

---

## 1. Where we are

- **Books 1–10: aligned + ingested** ([H907](https://github.com/gasyoun/Uprava/blob/main/handoffs/H907-Opus_SamudraManthanam_somadeva_kss_ingest_scaleup_14.07.26.md),
  [PR #59](https://github.com/gasyoun/SamudraManthanam/pull/59)). 9 998 sentence-pairs
  from the upstream lingtrain alignment, converted via
  [`web/corpus_builder/somadeva_lingtrain_to_canonical.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/somadeva_lingtrain_to_canonical.py),
  ingested and proven searchable in the FTS5 corpus. Sentence-keyed
  (`lambaka.taraṅga.sentence-ordinal`); `structure="prose"`.
- **Books 11–18: text present, not aligned.** The upstream repo already holds,
  per book, `chapters_san/…_chap_{11-18}.txt` (Sanskrit, śloka-keyed) and
  `chapters_rus/…_chap_{11-18}.txt` (Russian prose). ~8 730 ślokas of Sanskrit
  and the matching Russian await alignment.

---

## 2. What "all Somadeva" means, and P0 (resolved)

**Scope.** The full Kathāsaritsāgara = **18 lambakas / ~124 taraṅgas / ~21 500
ślokas**. Each aligned/loaded "chapter" file = **one lambaka**.

**P0 — Russian availability — RESOLVED (14-07-2026).** Working assumption (MG):
*the `.txt` files in the upstream repo are the entirety of the digitized Russian
that exists.* Under that assumption the constraint is **fully satisfied**: the
Russian `chapters_rus/…_chap_01…18.txt` cover **all 18 books** — the cleaned
Russian ends *"Восемнадцатая книга… Книга Сомадева «Океан Сказаний» окончена"*
("Eighteenth book… Somadeva's Ocean of Stories is finished"). There is nothing
left to source. The corresponding śloka-keyed Sanskrit exists for all 18 books:

| Books | Sanskrit ślokas (`sokss_` refs) | Russian | Status |
|---|---:|---|---|
| 1–10 | 12 808 | present + aligned | ✅ ingested (H907) |
| 11–18 | 8 730 | present, prose + wave headers | ▶ align (H910) |
| **Total** | **21 538** | **complete, all 18 books** | — |

**Consequences of the resolved P0:**
1. **No human gate, no external fetch.** Books 11–18 are agent-doable now from
   in-repo text. The earlier "MG `@DECIDE` for Russian inventory" is closed.
2. **True śloka keying is available.** `chapters_san` carries GRETIL-style
   `sokss_LAMBAKA,TARAṄGA.ŚLOKA` refs (e.g. `sokss_11,1.2`), so books 11–18 can
   be keyed `lambaka.taraṅga.śloka` — richer than the sentence-ordinal keying
   forced on books 1–10 (whose upstream lingtrain preprocessing stripped `॥N॥`).
3. **"RU where it exists" degenerates to "RU everywhere"** for this work — every
   book has Russian, so no gap-marking is needed for the KSS itself (the
   gap-marking design in §4 stays as the general fallback).

**Locked decisions (MG, 14-07-2026):** LLM-assisted alignment · absorb into
SamudraManthanam · GRETIL/`sokss` Sanskrit spine · Russian = the in-repo `.txt`
(assumed complete).

---

## 3. Method comparison — lingtrain-manual vs LLM-assisted

Evidence: the [Marc-Winner/somadeva](https://github.com/Marc-Winner/somadeva) git
history (2023-07-30 → 2026-01-26) + the `web/corpus_builder/` LLM precedents
(mw_ru 287 358 cards; pwg_ru 749 roots via the Claude Workflow tool).

| Dimension | **Lingtrain manual** (as done) | **LLM-assisted** (projected) |
|---|---|---|
| Alignment unit | sentence (LaBSE + manual studio correction) | śloka (`sokss`-keyed) with sentence fallback |
| Books 1–10 — calendar | **~30 months** (Jul 2023 → Jan 2026) | — (done) |
| Book 9 / book 10 | **6.5 mo** / **10.7 mo** (~11 commits each) | ~hours run + QA |
| Marginal rate (recent) | **~8.6 months/book, rising** | minutes–hours/book |
| Remaining 8 books (11–18, ~8 730 ślokas) | **~2–6 years** | **days–weeks** + QA |
| Human cost | per-sentence manual correction | QA of low-confidence groups only |
| Reproducibility | GUI state in binary `.lt` | scripted, re-runnable, diffable |
| Śloka keying | lost (daṇḍa stripped) | **recovered** (`sokss` refs in-repo) |

**Headline.** 10 books took **~2.5 years** manually with the marginal cost still
*rising* (6.5 → 10.7 months for the last two). The remaining 8 books by the same
method is a **multi-year (≈2–6 yr)** effort. LLM-assisted alignment over the
already-present, śloka-keyed text collapses that to **days–weeks of runs plus
bounded QA** (≈50–100× calendar speed-up) *and* yields true śloka keys.

> Caveat: the manual calendar is part-time volunteer effort (overstates raw
> labour hours); the LLM figure below is now **measured** (book-11 pilot), not a
> forecast.

**Measured (book-11 pilot, 14-07-2026).** The agent aligned book 11 (116 ślokas)
in **8.8 minutes** (~13.1 ślokas/min, mean confidence 0.86) vs the human's recent
pace of **~7.4 ślokas/day** — book 11 would have taken ~15.7 days manually.
Projected books 11–18 (~8 730 ślokas): **~11 hours** of aligner compute + QA vs
**~3.2 years** manual. Full numbers + the Human-vs-Agent table:
[web/corpus_builder/SOMADEVA_KSS_ALIGNMENT_PILOT_REPORT.md](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/SOMADEVA_KSS_ALIGNMENT_PILOT_REPORT.md).

---

## 4. LLM-assisted alignment design (books 11–18)

Reuse the `web/corpus_builder/` contract; the inputs are already in-repo.

1. **Sanskrit side.** Parse `chapters_san/…_chap_{11-18}.txt` on the
   `// sokss_L,T.S //` refs → `#sa` JSONL keyed `lambaka.taraṅga.śloka`
   (zero-padded), IAST + SLP1, `structure="verse"`. `#` lines = lambaka header,
   `##` lines = taraṅga header. No GRETIL fetch — this text *is* the GRETIL
   recension with its refs.
2. **Russian side.** Parse `chapters_rus/…_chap_{11-18}.txt`: `КНИГА …` /
   `# …` = book, `## L.T. ВОЛНА …` = taraṅga, prose sentences beneath. (Book 14
   currently shows no `##` wave header — handle a single-taraṅga fallback.)
3. **Align (LLM).** Per taraṅga (matched on `L.T`), give the model the Sanskrit
   ślokas + the Russian prose and emit a śloka-id → Russian-span mapping with a
   per-group confidence. Serebryakov is prose, so one Russian sentence may cover
   several ślokas — this is exactly the judgement the LLM makes. One taraṅga per
   agent, fanned out via the Claude Workflow tool.
4. **Gap marking (general fallback).** Any śloka with no confident Russian →
   Sanskrit-only group; never fabricate. (Not expected for the KSS, since Russian
   is complete, but the aligner keeps the guard.)
5. **QA gate.** Low-confidence groups → a `/review-sheet` HTML voting sheet
   (markdown checkboxes banned); human adjudication feeds corrections back.
6. **Emit + ingest.** `build_corpus_html.py --split skandha` → `Data/*.html` +
   `data.txt`; `build-web-db.ps1` → FTS5; verify search — identical to H907.

---

## 5. Phased plan

**P0 — Russian inventory — ✅ RESOLVED** (§2): complete Russian for all 18 books
is in-repo. No action.

**P1 — Align books 11–18** — the actionable core, tracked by
[H910](https://github.com/gasyoun/Uprava/blob/main/handoffs/H910-Opus_SamudraManthanam_somadeva_kss_books11_18_alignment_14.07.26.md).
Sanskrit-side converter + LLM aligner + ingest, per §4. Start with the smallest
book (11, ~116 ślokas) as the pilot that fixes the confidence/QA loop, then fan
out 12–18. Agent-doable now.

**P2 — Measure.** From the P1 pilot, record real throughput + QA-hit rate to
replace the §3 projection with a number; log in the metadoc.

**P3 — Books 1–10 śloka re-key (optional, high value).** Re-align the 10 done
from the `sokss`-keyed Sanskrit to recover śloka keys and cross-check the
lingtrain sentence alignment (independent second opinion). Removes the mixed-keying
wrinkle (books 1–10 sentence-keyed, 11–18 śloka-keyed).

**P4 — Publish + hubs.** kosha `datasets.json` row, FEATURES_INDEX, НКРЯ export
(`nkrya_export.py`). **Gated on rights** — see
[SOMADEVA_KSS_RIGHTS_COPYRIGHT_UNLOCK.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/SOMADEVA_KSS_RIGHTS_COPYRIGHT_UNLOCK.md).

---

## 6. Rights

The Russian (Serebryakov et al., Nauka, 20th c.) is **in-copyright** and inherits
the corpus's standing **"grey per project ruling"** status (same as the Grintser
Rāmāyaṇa): corpus HTML/JSONL committed to this public repo, **`corpus.db` +
export bulk gitignored**, no redistribution. What changes if/when MG demonstrates
copyright ownership is documented separately in
[SOMADEVA_KSS_RIGHTS_COPYRIGHT_UNLOCK.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/SOMADEVA_KSS_RIGHTS_COPYRIGHT_UNLOCK.md).

---

## 7. Open questions (residual)

- **Book 14 Russian** shows no `## L.T.` wave header — confirm it is single-taraṅga
  or a formatting variant, and handle in the P1 parser.
- **Books 1–10 re-key** (P3): adopt śloka keys for the 10 done, or leave them
  sentence-keyed and accept mixed keying? (Recommendation: re-key — it is cheap
  once the P1 aligner exists and removes a search-UX wrinkle.)
- Preserve story (`h3`, "Рассказ") titles as corpus chapter-headings (the emitter
  supports headings) — worth a titles pass?

_Dr. Mārcis Gasūns_
