# SA-side morphology — DCS-anchored gold, build report (H906)

_Created: 14-07-2026 · Last updated: 25-07-2026_

What the Sanskrit-side morphology pass ([H906](https://github.com/gasyoun/Uprava/blob/main/handoffs/H906-Opus_SamudraManthanam_nkrya-sa-morphology-dcs-vidyut_14.07.26.md))
shipped. Model: Opus 4.8 (`claude-opus-4-8[1m]`). Sibling of the RU-side
[`RU_MORPHOLOGY_H905_REPORT.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/RU_MORPHOLOGY_H905_REPORT.md);
builds on [`docs/RUBANOVA_NKRYA_PIPELINE_MANUAL.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/RUBANOVA_NKRYA_PIPELINE_MANUAL.md) §6.

## Approach — DCS is the gold, and it aligns

The shipped export's Sanskrit `se` carries only an SLP1 transliteration. MG:
"the Sanskrit side used **DCS** as the markup source… DCS is gold, vidyut the
second opinion." The [DCS](http://www.sanskrit-linguistics.org/dcs/)
`dcs_full.sqlite` is a sandhi-split, annotated gold corpus (5.7M tokens); its
`token` table gives per word **lemma · UPOS · case · gender · number**
(+ tense/mood/person/voice). Rather than run a fresh analyzer as primary, we
**align each seg=sa verse to the matching DCS chapter and emit those gold
analyses** — the most faithful reading of "DCS is gold".

Alignment (in [`dcs_align.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/dcs_align.py)):
our `passage` `B.C.V[-V]` → DCS chapter `MBh, B, C` (Mahābhārata) or
`Rām, <kāṇḍa>, C` (Rāmāyaṇa); DCS `sentence.sent_counter` == our verse number.
Proven verbatim: our MBh 3.1.1 `evaṃ dyūtajitāḥ pārthāḥ…` → DCS `MBh, 3, 1`
sent 1.2, tokens `evam` ADV · `dyūta` NOUN Cpd · `jitāḥ`→ji VERB Nom Masc Plur…

Emitted behind `nkrya_export.py --sa-morph` as an additive
`<slug>.sa_morph.tsv` (group_id, verse, tok_index, form, lemma, upos, case,
gender, number). Deterministic (explicit `ORDER BY sent_counter, sent_subcounter,
id` then `idx`; byte-identical across runs). The DCS sqlite is **local-only**
(920 MB, in the sibling VisualDCS repo); `dcs_align.py` degrades to an
empty layer if it's absent (`$DCS_SQLITE` overrides the path).

## Coverage (pairs with DCS gold, real sweep)

| Source | pairs | covered | % |
|---|---:|---:|---:|
| 03_mahabharata-aranyakaparva | 2033 | 2032 | **100.0%** |
| 04_mahabharata-virataparva | 360 | 360 | 100.0% |
| 05_mahabharata-udyogaparva | 1006 | 1006 | 100.0% |
| 08_mahabharata-karnaparva | 618 | 618 | 100.0% |
| 12_mahabharata-shantiparva | 12692 | 12681 | 99.9% |
| 01_mahabharata-adiparva | 1387 | 1368 | 98.6% |
| 07_mahabharata-dronaparva | 1219 | 1202 | 98.6% |
| 13_mahabharata-anushasanaparva | 6537 | 6445 | 98.6% |
| 09_mahabharata-shalyaparva | 533 | 522 | 97.9% |
| 02_mahabharata-sabhaparva | 438 | 387 | 88.4% |
| 01_ramayana-balakanda | 2268 | 1812 | 79.9% |
| 03_ramayana-aranyakanda | 2447 | 1770 | 72.3% |
| 05_ramayana-sundarakanda | 2859 | 1943 | 68.0% |
| 02_ramayana-ayodhyakanda | 4307 | 2668 | 61.9% |
| **06_mahabharata-bhishmaparva** | 1337 | 637 | **47.6%** |
| 06/07_ramayana-yuddha/uttarakanda | — | 0 | 0.0% |

(MBh 10–11, 14–18 also 100%; omitted for brevity.) `03_mahabharata-aranyakaparva`:
**152,196 gold tokens** emitted.

**Findings, not silently swallowed:**
- **Bhishmaparva (MBh 6) at 47.6% is the Bhagavadgītā gap** — the Gītā (MBh
  6.23–40) is absent from DCS ([H848](https://github.com/gasyoun/Uprava/blob/main/handoffs/H848-Opus_SanskritLexicography_dcs-reading-pack-data-path_13.07.26.md)); its verses simply have no gold. Expected, and now measured.
- ~~**Rāmāyaṇa is partial (62–80%)** — verse-numbering diverges more between our
  edition and DCS's; the misses are alignment (verse-number offset), not missing
  DCS data.~~ **⚠️ CORRECTED 25-07-2026 — this diagnosis was backwards.** The
  misses are overwhelmingly *missing DCS data*, not misalignment: 3,696 verses
  our edition carries were never annotated by DCS, while of the 1,422 verses DCS
  holds that we do not match, 98.7 % simply lie beyond our last verse in that
  chapter and only **19 in total** are genuine in-range holes. There is no
  offset; the verse map is already correct and at its ceiling. Evidence:
  [`RAMAYANA_VERSE_MAP_H906_REPORT.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/RAMAYANA_VERSE_MAP_H906_REPORT.md).
- ~~**06/07 Rāmāyaṇa (yuddha/uttara) at 0%** — these were GRETIL-ingested (H765)
  with a different `passage` convention; the ref mapper doesn't yet parse it.~~
  **⚠️ CORRECTED 25-07-2026 — never a parser problem.** Their passages are plain
  `N.N` and mapped correctly all along; at the passage level they align to DCS at
  **100.0 %** and **99.9 %**, the best figures in the Rāmāyaṇa. They read 0 %
  because both are **Sanskrit-only** (untranslated), so `classify()` — which
  requires both sides to form a *bilingual* pair — yielded zero pairs, and the SA
  morphology layer iterated `pairs`. Fixed by keying the SA layers off
  `sa_units()` instead: **+7,123 verses, +98,753 gold tokens**. Same report.
- **MBh is essentially complete** (most parvas 98–100%): the epic core of the
  corpus now carries real gold Sanskrit morphology.

## Validation
Hand-checked the MBh 3.1.1 sample against the printed analysis: lemmas
(`ji`, `pārtha`, `durātman`, `dhārtarāṣṭra`) and case/gender/number agree with
DCS gold. A regression test pins `janamejaya`→NOUN/Nom/Masc/Sing.

## Deferred — the vidyut second-opinion diff
H906's goal also asks for a **vidyut layer diffed against DCS**. vidyut 0.4.0 is
installed but ships **no linguistic data locally** — it needs
`vidyut.download_data` (a large fetch) + a `vidyut.cheda.Chedaka` segment→analyse
wiring. Since DCS already supplies the gold (the primary requirement) and vidyut
is explicitly the *second* opinion, the diff is scoped as a **bounded
follow-up**: download vidyut data, analyse the same tokens, join on
(verse, form), emit a per-token agreement rate + a categorised disagreement
sample. The `sa_morph.tsv` schema is the join key it will consume.

## Status
| Piece | Status |
|---|---|
| DCS-gold per-token SA morphology (lemma/upos/case/gender/number) | ✅ shipped (`dcs_align.py`, `--sa-morph`) |
| Alignment MBh + Rāmāyaṇa; coverage measured | ✅ (MBh ~99%, Rāma partial) |
| Determinism + tests | ✅ (+3 tests, 12 pass) |
| vidyut diff / agreement report | ✅ shipped 25-07-2026 ([`VIDYUT_DIFF_H906_REPORT.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/VIDYUT_DIFF_H906_REPORT.md)) |
| Rāmāyaṇa verse-map + GRETIL-ref reconciliation | ✅ shipped 25-07-2026 ([`RAMAYANA_VERSE_MAP_H906_REPORT.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/RAMAYANA_VERSE_MAP_H906_REPORT.md)) — both diagnoses above corrected; +7,123 verses |
| Inline `<w><ana/>` in the `<se>` (shared RU+SA scheme) | ✅ shipped 25-07-2026 ([`INLINE_ANA_H906_REPORT.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/INLINE_ANA_H906_REPORT.md)) — RU 100 %, SA 15.5 % of gold-bearing verses (sandhi-split alignment is the limit; sidecar keeps 100 %) |

_Dr. Mārcis Gasūns_
