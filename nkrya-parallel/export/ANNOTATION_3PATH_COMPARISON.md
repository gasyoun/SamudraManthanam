# Sanskrit-side 3-path annotation comparison — НКРЯ pilot (Wave 2)

_Created: 12-07-2026 · Last updated: 12-07-2026_

Head-to-head comparison of three Sanskrit-side annotation variants on the four
НКРЯ pilot sources (MBh 3 + Rāmāyaṇa 1–3, the 11,055 verse pairs of
[PILOT_VALIDATION.md](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/export/PILOT_VALIDATION.md)),
per ruling 3 of the
[НКРЯ roadmap](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ROADMAP_NKRYA_PARALLEL_RUSCORPORA_2026_2027.md)
and [H759](https://github.com/gasyoun/Uprava/blob/main/handoffs/H759-Fable_SamudraManthanam_nkrya-wave2-sanskrit-3path-annotation-a41-section_12.07.26.md).

- **Generator:** [`web/corpus_builder/nkrya_annotate.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/nkrya_annotate.py) v0.1.0
- **Tests:** [`web/tests/test_nkrya_annotate.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/test_nkrya_annotate.py) (5 hermetic + 1 corpus, all green 12-07-2026)
- **Metrics of record:** [annotation_3path_metrics.json](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/export/annotation_3path_metrics.json) (committed; every figure below recomputes from it)
- **Model:** Fable 5 (`claude-fable-5`)
- Per-source annotated TSVs are gitignored with the rest of `export/` bulk; the
  metrics JSON, the 51-group adjudication sample, and this report are the
  committed artifacts (all Sanskrit-side only — no Russian translation text).

## Verdict

**Path B (DCS crosswalk) is the production annotation path wherever DCS covers
the text; path C (vidyut 0.4 fresh tagging) is not competitive on epic verse;
path A (plain IAST/SLP1) remains the guaranteed floor.** DCS covers our MBh 3
essentially completely (99.8% of half-verses) because both sides carry
critical-edition text; on the vulgate-numbered Rāmāyaṇa kāṇḍas DCS's
critical-edition excisions cap coverage at 54–76%, so the Sanskrit annotation
layer shipped to НКРЯ must be declared **partial by construction** outside MBh —
path A carries the remainder.

## The three paths

| Path | Source | Licence | What it provides |
|---|---|---|---|
| **A** — plain IAST/SLP1 | canonical JSONL (already in the W1 export) | ours | script-level baseline, no lemma/morph; 203,623 surface tokens across 40,269 half-verses |
| **B** — DCS crosswalk | [Digital Corpus of Sanskrit](https://github.com/OliverHellwig/sanskrit) (Hellwig) via the [VisualDCS](https://github.com/gasyoun/VisualDCS) SQLite master, pinned snapshot [gasyoun/dcs-conllu@04e0778](https://github.com/gasyoun/dcs-conllu) | **CC BY 4.0** — redistribution inside НКРЯ is licence-compatible with attribution (*Hellwig, Oliver. The Digital Corpus of Sanskrit (DCS). 2010–2024*) | human-curated lemma + UD morphology (UPOS + FEATS) per token |
| **C** — fresh auto-tagging | [vidyut](https://github.com/ambuda-org/vidyut) 0.4.0 (`vidyut-cheda`), local data pack | MIT-family OSS, fully local/reproducible | automatic segmentation + lemma + Pāṇinian analysis |

## Path B — crosswalk coverage (the numbers)

The crosswalk is **text-keyed, not locus-keyed**: our MBh 3 carries
critical-edition numbering (299 adhyāyas, same as DCS) but our Rāmāyaṇa kāṇḍas
are vulgate-numbered (77/119/75 sargas vs DCS's critical 76/111/71), so verse
loci cannot be trusted across editions. Every DCS half-verse in scope is
indexed under an aggressive IAST normalization, and each of our half-verse
lines is matched in three tiers: **exact** (normalized string), **sandhi**
(consonant-skeleton equality — DCS's Rāmāyaṇa `text_sandhied` is largely
de-sandhied pada text, `sukhatantraḥ na ca alasaḥ`, where our vulgate surface
is sandhied, `sukhatantro nacālasaḥ`; deleting vowels/visarga/semivowels and
folding nasals neutralizes exactly that class, guarded by a ≥0.70 similarity
floor on the vowelled strings), and **fuzzy** (difflib ≥0.90 in a
shared-prefix bucket).

| Source | Half-verses | Exact | Sandhi | Fuzzy | Unmatched | **Coverage** | Groups full/partial/zero |
|---|--:|--:|--:|--:|--:|--:|---|
| MBh 3 (Āraṇyakaparvan) | 21,396 | 19,674 | 1,590 | 92 | 40 | **99.8%** | 1,997 / 36 / 0 |
| Rām 1 (Bālakāṇḍa) | 4,633 | 2,704 | 473 | 359 | 1,097 | **76.3%** | 1,497 / 498 / 273 |
| Rām 2 (Ayodhyākāṇḍa) | 9,093 | 1,019 | 3,161 | 756 | 4,157 | **54.3%** | 1,919 / 1,084 / 1,304 |
| Rām 3 (Araṇyakāṇḍa) | 5,147 | 398 | 1,853 | 576 | 2,320 | **54.9%** | 942 / 908 / 597 |
| **Total** | **40,269** | **23,795** | **7,077** | **1,783** | **7,614** | **81.1%** | **6,355 / 2,526 / 2,174** |

Matched lines carry **225,972 DCS tokens** with lemma + UD morphology. 17
damaged lemma strings (a known kḷp/ṝ-family mojibake in the 2026 SQLite
import) were dropped and counted, never silently eaten. 362 lines (0.9%)
matched more than one DCS half-verse (repeated epic formulae) — the first hit
is taken.

**The unmatched residue is real, not a matcher artifact.** A probe of 801
Ayodhyā unmatched lines against the *entire* DCS Rāmāyaṇa (all 7 kāṇḍas,
38,004 half-verses) relocated only 6; 795 are genuinely absent — vulgate text
the critical edition excised. Coverage on the Rām kāṇḍas is therefore an
**edition-difference measurement**, not an annotation-quality one: DCS Ay
scope holds 6,378 half-verses against our 9,093.

## Path C — vidyut fresh tagging

vidyut-cheda ran on all 40,269 half-verses (SLP1, transliterated from the same
IAST lines path B matched; zero engine failures) and produced **293,775
tokens** — **1.44× the surface token count**, i.e. systematic
over-segmentation. 15,721 tokens (5.4%) came back without a lemma. Observed
failure mode on epic verse: long compounds and vṛddhi derivatives shatter into
short spurious roots (`dhārtarāṣṭraiḥ` → 5 fragments, `tapaḥsvādhyāyanirataṃ`
→ `svādhī`/`i`/`ad` garbage) — the segmenter prefers *some* Pāṇinian
derivation over none.

## B ↔ C lemma agreement

Computed on the 6,355 groups where every line found a DCS counterpart
(apples-to-apples lemma sets, SLP1-normalized both sides):

| Source | Groups compared | Jaccard mean | median | p10 | p90 |
|---|--:|--:|--:|--:|--:|
| MBh 3 | 1,997 | 0.286 | 0.282 | 0.199 | 0.379 |
| Rām 1 | 1,497 | 0.283 | 0.273 | 0.125 | 0.444 |
| Rām 2 | 1,919 | 0.312 | 0.300 | 0.154 | 0.474 |
| Rām 3 | 942 | 0.347 | 0.333 | 0.182 | 0.526 |
| **All** | **6,355** | **~0.30** | | | |

Two causes decompose the low agreement, and only one of them is error:

1. **Lemma-granularity convention.** vidyut lemmatizes every derivative to its
   dhātu root (`rāmaḥ` → `ram`, `varam` → `vṛ`) where DCS lemmatizes nominals
   to the stem (`rāma`, `vara`). The comparison already extracts vidyut's
   prātipadika stem where the token is a Basic (non-kṛdanta) nominal; the
   kṛdanta residue is a *convention* mismatch, not a wrong analysis.
2. **Real segmentation divergence** — the over-segmentation shown above; this
   one is error, and the adjudication sample (below) lets a human apportion
   blame between the two causes.

**Human adjudication:** a fixed-seed stratified sample of 51 groups (17 per
low/mid/high-Jaccard tertile) is committed as
[annotation_adjudication_sample.json](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/export/annotation_adjudication_sample.json)
and rendered as an interactive review sheet (see
[REVIEW_SHEETS_INDEX.md](https://github.com/gasyoun/Uprava/blob/main/REVIEW_SHEETS_INDEX.md)).

## What ships to НКРЯ (recommendation)

1. **Path A always** — the W1 triple export as-is (IAST + SLP1 surface).
2. **Path B as the lemma/morph layer** wherever a verse crosswalks to DCS,
   with the CC BY 4.0 attribution line in the corpus header; coverage
   declared per text (MBh 3: ~100%; Rām 1–3: 54–76%, partial by
   construction).
3. **Path C not shipped** at vidyut 0.4 quality on epic verse; revisit only
   if a future vidyut/Dharmamitra release changes the picture, or for the
   non-DCS residue where partial annotation beats none — pending the human
   adjudication verdict.

## Reproduce

```
# from web/corpus_builder (DCS master + vidyut data paths have defaults)
python nkrya_annotate.py --all-pilot --out ../../nkrya-parallel/export
# tests
cd web; python -m pytest tests/test_nkrya_annotate.py -q          # hermetic
cd web; python -m pytest tests/test_nkrya_annotate.py -m corpus -q # real data
```

Determinism: no clock in any artifact, fixed sample seed (759), sorted sets —
two runs are byte-identical (hermetic gate d).

## Limitations

- The consonant-skeleton tier could in principle conflate distinct lines that
  differ only in vowels/visarga/semivowels; the ≥0.70 vowelled-string guard and
  the ambiguity counter (362 lines, 0.9%) bound this risk, and the adjudication
  sample double-checks matched pairs implicitly.
- B↔C agreement uses per-group lemma **sets** (no token alignment); it
  understates agreement when the same lemma appears with different token
  multiplicity, and cannot localize which token disagrees.
- DCS morphology is taken as the reference by construction; where DCS itself
  errs, "agreement" penalizes vidyut unfairly — the human sample is the check.
- vidyut ran with `vidyut-cheda` defaults; no beam/lexicon tuning was
  attempted.

_Dr. Mārcis Gasūns_
