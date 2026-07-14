# Roadmap — Somadeva's Kathāsaritsāgara SA↔RU alignment: scale-up to all 18 lambakas

_Created: 14-07-2026 · Last updated: 14-07-2026_

Handoff: [H907](https://github.com/gasyoun/Uprava/blob/main/handoffs/H907-Opus_SamudraManthanam_somadeva_kss_ingest_scaleup_14.07.26.md) ·
Model: Opus 4.8 (`claude-opus-4-8[1m]`) ·
Upstream data: [Marc-Winner/somadeva](https://github.com/Marc-Winner/somadeva) @ `99a72bd` (private)

This roadmap resumes the [Marc-Winner/somadeva](https://github.com/Marc-Winner/somadeva)
parallel-text project, **absorbs** it into SamudraManthanam as the single home
(the somadeva repo becomes an upstream snapshot), and plans the scale-up from
the 10 aligned lambakas to the **full Kathāsaritsāgara (18 lambakas)** using an
**LLM-assisted** aligner over the complete GRETIL Sanskrit, keeping the Russian
where it exists and marking gaps.

---

## 1. Where we are (this session, H907)

The 10 aligned lambakas were ingested end-to-end into the SamudraManthanam
corpus and proven searchable in both front-ends' shared substrate.

- **Source.** The upstream lingtrain alignment (Lingtrain Studio v8.4-labse):
  `xml/somadeva_ch{1-3,5-9}.xml` (author's committed exports) + reconstruction
  from `lt_files/somadeva_ch{4,10}.lt` `doc_index` for the two chapters lacking
  XML. Each "chapter" file = **one lambaka (book)**: ch1 = कथापीठ (bk 1, 8
  taraṅgas), … ch10 = book 10.
- **Extractor.** [`web/corpus_builder/somadeva_lingtrain_to_canonical.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/somadeva_lingtrain_to_canonical.py)
  — XML + `doc_index` → canonical JSONL; Devanagari → IAST/SLP1 via
  `indic_transliteration`; keyed `lambaka.taraṅga.sentence-ordinal`,
  `structure="prose"`.
- **Result.** **9 998 aligned sentence-pairs** across lambakas 1–10 (~66
  taraṅgas), 19 994 canonical records, 0 malformed. Emitted as
  `jsonl/kathasaritsagara.jsonl` + per-lambaka `kathasaritsagara-{1..10}.jsonl`,
  10 `Data/kathasaritsagara-{N}.html` + `.no_tags` + meta sidecars, registered
  in `Programdata/data.txt`.
- **Verified.** Real `ingest.py` → FTS5 `corpus.db` (gitignored) with 10 sources
  / 19 994 rows; live search returns aligned SA↔RU pairs (`somaprabhā` → 33
  hits, `океан` → 58 hits). Schema `test_contract.py` + `test_converter.py` green
  (27 passed).

### Why sentence-keyed, not verse-keyed

SamudraManthanam's native alignment unit is the **verse** (`lambaka.taraṅga.śloka`,
key-joined). The lingtrain output is **sentence**-aligned (LaBSE) and the `॥N॥`
śloka numbers were destroyed in the upstream preprocessing ("add dots for lt to
split"). We therefore ingested the *existing* alignment directly rather than
re-aligning it — keying `lambaka.taraṅga.sentence-ordinal`. This is faithful but
loses śloka anchoring and story (`h3`, "Рассказ о…") boundaries. **The scale-up
recovers śloka keying** by re-aligning from the GRETIL Sanskrit, which retains
`॥N॥` (see §4).

---

## 2. What "all Somadeva" means, and the decided approach

**Scope.** The full Kathāsaritsāgara = **18 lambakas / ~124 taraṅgas / ~21 000
ślokas** (Durgāprasād & Parab / Nirṇaya-sāgara; GRETIL `sa_kathAsaritsAgara`).
Books **1–10 are aligned** (this session). Remaining: **8 books (11–18)**.

**Four decisions locked this session (MG, 14-07-2026):**

1. **GRETIL spine, RU where it exists.** Take the complete GRETIL Sanskrit as the
   backbone for all 18 books; align whatever Russian we hold; mark untranslated
   spans as explicit gaps (Sanskrit-only groups — the sanctioned `align_sanskrit.py`
   Russian-only fallback, inverted).
2. **LLM-assisted alignment** (not manual lingtrain — see §3).
3. **Absorb into SamudraManthanam** as the single home. somadeva = upstream
   snapshot; reproduce ch4/ch10 by re-cloning `Marc-Winner/somadeva @ 99a72bd`.
4. **First deliverable = prove ingest of the 10 done + this roadmap** — done (§1).

**Russian coverage is the binding constraint, and it is partial.** The upstream
Russian is the multi-volume Serebryakov et al. Nauka translation; the repo cites
only «Дальнейшие похождения царевича Нараваханадатты» (1976) but the aligned
content spans books 1–10 (so more than one volume is in play). Per-book Russian
availability for books 11–18 is **unverified** and is prerequisite P0 (§5).

---

## 3. Method comparison — lingtrain-manual vs LLM-assisted

Evidence base: the [Marc-Winner/somadeva](https://github.com/Marc-Winner/somadeva)
git history (2023-07-30 → 2026-01-26) and the SamudraManthanam
`web/corpus_builder/` LLM pipeline precedents (mw_ru: 287 358 cards; pwg_ru: 749
DCS-attested roots run through the Claude Workflow tool at scale).

| Dimension | **Lingtrain manual** (as actually done) | **LLM-assisted** (projected) |
|---|---|---|
| Alignment unit | sentence (LaBSE embedding + manual studio correction) | śloka (GRETIL `॥N॥`-keyed) with sentence fallback |
| Books 1–10 — calendar | **~30 months** (Jul 2023 → Jan 2026) | — (already done) |
| Book 9 alone | **~6.5 months** (2024-06-29 7% → 2025-01-15 done), ~11 commits | ~hours run + QA |
| Book 10 alone | **~10.7 months** (2025-01-21 → 2025-12-10), 2256 units, ~11 commits | ~hours run + QA |
| Marginal rate (recent books) | **~8.6 months/book and rising** | minutes–hours/book |
| Remaining 8 books (11–18) | **~2–6 years** (3 mo/book lifetime avg → 8.6 mo/book recent) | **days–weeks** + human QA |
| Dominant human cost | per-sentence manual correction in the GUI | QA / adjudication of flagged low-confidence groups only |
| Reproducibility | GUI state frozen in binary `.lt`; not scriptable | fully scripted, re-runnable, diffable |
| Śloka keying | **lost** (daṇḍa stripped in preprocessing) | **recovered** from GRETIL |
| Gap handling | none (only translated spans exist) | explicit Sanskrit-only gap groups |
| Cost profile | ~free but multi-year human calendar | API tokens + bounded QA hours |

**Headline.** Bringing 10 books to committed-aligned state took **~2.5 years**,
and the *marginal* cost was still **rising** (6.5 → 10.7 months for the last two
books). Extrapolated, the remaining 8 books by the same method is a **multi-year
(≈2–6 yr)** effort. An LLM-assisted aligner over the already-complete GRETIL
Sanskrit collapses that to **days–weeks of automated runs plus bounded human QA**
— an order-of-magnitude (≈50–100×) calendar speed-up — while *also* recovering
śloka keying and marking Russian gaps, which the manual method never produced.

> Caveat on the numbers: the manual calendar is part-time volunteer effort, not
> full-time, so it overstates raw labour hours; and the LLM projection is a
> forecast grounded in the mw_ru/pwg_ru throughput, not a measured KSS run. The
> comparison is of **calendar time to a shippable corpus**, which is the metric
> that actually gated this project for 2.5 years.

---

## 4. LLM-assisted alignment design (books 11–18, then a books 1–10 re-key option)

Reuse the `web/corpus_builder/` contract; do **not** re-invent the schema.

1. **Sanskrit spine (all 18 books).** `gretil_tei_to_canonical.py`-style
   converter over GRETIL `sa_kathAsaritsAgara` → `#sa` JSONL keyed
   `lambaka.taraṅga.śloka` (zero-padded), IAST + SLP1, `structure="verse"`.
   GRETIL retains `॥N॥`, so śloka keys are authoritative.
2. **Russian side (where it exists).** Per available Serebryakov volume: OCR/clean
   → `#ru` JSONL. Because Serebryakov is prose (one Russian sentence spans several
   ślokas or vice-versa), the RU→śloka mapping is **not** a clean key-join — this
   is the step the LLM does: given a taraṅga's Sanskrit ślokas + the Russian
   passage, emit an alignment (śloka-id → Russian span), with a confidence per
   group. Model: Claude via the Workflow tool, one taraṅga per agent, fanned out.
3. **Gap marking.** Ślokas with no confident Russian → Sanskrit-only groups
   (`align_sanskrit.py` fallback, inverted); never fabricate a translation.
4. **QA gate.** Low-confidence groups → a `/review-sheet` HTML voting sheet
   (markdown checkboxes are banned); human adjudication feeds back corrections.
   Mirror the pwg_ru gate-selftest discipline (`LANG_PARITY.md`).
5. **Emit + ingest.** `build_corpus_html.py --split skandha` → `Data/*.html` +
   `data.txt`; `build-web-db.ps1` → FTS5; verify search. Identical to §1.

**Books 1–10 re-key (optional, high value).** The same pipeline can re-align the
existing 10 books from the GRETIL spine to *recover śloka keying* and cross-check
the lingtrain sentence alignment (an independent second opinion). Decide after
the 11–18 pilot proves the aligner.

---

## 5. Phased plan

**P0 — Russian inventory (prerequisite, human + agent).** Establish, per lambaka
11–18, which Serebryakov volume covers it and whether it is digitized. Output: a
coverage table in this repo. Gates everything else. → **MG `@DECIDE` / `@DO`.**

**P1 — GRETIL Sanskrit spine, all 18 books.** Fetch GRETIL `sa_kathAsaritsAgara`
(not in the local mirror), write the converter, emit `#sa` JSONL for all 124
taraṅgas, śloka-keyed. Ingest the **Sanskrit-only** corpus first (searchable
immediately, gaps explicit). Agent-doable now, independent of Russian.
`Read C:\Users\user\Documents\GitHub\SamudraManthanam\docs\ROADMAP_SOMADEVA_KSS_ALIGNMENT_SCALEUP_2026_2027.md and execute P1.`

**P2 — LLM aligner pilot (one taraṅga).** Build the Workflow-tool aligner on one
book-11 taraṅga where Russian exists; tune confidence + QA sheet. Measure real
throughput to replace the §3 projection with a number.

**P3 — Scale books 11–18.** Fan out P2 over all available Russian; gap-mark the
rest; ingest per lambaka.

**P4 — Books 1–10 re-key (optional).** Re-align the 10 done from the spine;
compare to the lingtrain sentence alignment; adopt śloka keys.

**P5 — Publish + hubs.** kosha `datasets.json` row, FEATURES_INDEX, НКРЯ export
(`nkrya_export.py`) once bibliography is verified (P0).

---

## 6. Rights, coverage, provenance

- **Rights.** The Russian (Serebryakov et al., Nauka, 20th c.) is **in-copyright**.
  It inherits the corpus's standing **"grey per project ruling"** status — the
  same as the Grintser Rāmāyaṇa already committed (138 files): corpus HTML/JSONL
  committed to this public repo, **export bulk + `corpus.db` gitignored**, no
  redistribution. This is a *new* in-copyright work on a public repo — flagged for
  MG awareness, not a fresh policy call. See
  [`web/corpus_builder/kathasaritsagara.meta.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/kathasaritsagara.meta.json)
  `rights`.
- **Bibliography is provisional** (`needs_review: true`). Verify per-lambaka
  volume/translator/year against the physical editions before НКРЯ submission.
- **Reproducibility.** ch4/ch10 were reconstructed from the private upstream
  `.lt`; re-run requires cloning `Marc-Winner/somadeva @ 99a72bd`. The `.lt`
  binaries are **not** vendored (upstream-snapshot policy); the derived JSONL +
  extractor + documented SHA are the durable artifacts.
- **Pre-existing issue observed (not H907's):** `data.txt` lists
  `devibhagavata-purana.html` but its combined `devibhagavata-purana.jsonl` is
  absent, so a *full-corpus* `ingest.py` rebuild currently fails on that source.
  Independent of KSS; logged here so the next full rebuild expects it.

---

## 7. Open questions

- **P0 blocker:** does digitized Russian exist for books 11–18, and in which
  volumes? (Only books 1–10 are proven to have it.)
- Adopt śloka keying for books 1–10 (P4), or leave them sentence-keyed and only
  śloka-key 11–18? (Mixed keying within one work is a search-UX wrinkle.)
- Preserve story (`h3`, "Рассказ") titles as corpus chapter-headings (the
  emitter supports headings) — worth a `--report` titles pass?

_Dr. Mārcis Gasūns_
