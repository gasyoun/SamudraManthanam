# Rāmāyaṇa verse-map + GRETIL-ref reconciliation (H906)

_Created: 25-07-2026 · Last updated: 25-07-2026_

The last open data item of [H906](https://github.com/gasyoun/Uprava/blob/main/handoffs/H906-Opus_SamudraManthanam_nkrya-sa-morphology-dcs-vidyut_14.07.26.md):
reconcile the Rāmāyaṇa verse map against DCS gold, and make the GRETIL-ingested
kāṇḍas resolve. Sibling of the gold build report
[`SA_MORPHOLOGY_H906_REPORT.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/SA_MORPHOLOGY_H906_REPORT.md)
and the analyzer diff
[`VIDYUT_DIFF_H906_REPORT.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/VIDYUT_DIFF_H906_REPORT.md).
Model: Opus 5 (`claude-opus-5[1m]`).

**Both diagnoses recorded in the earlier build report turned out to be wrong.**
Neither of the two Rāmāyaṇa problems had the cause it was written up with. The
corrections are the substance of this report.

## Finding 1 — the "0% coverage" kāṇḍas were never a parser problem

The build report recorded:

> **06/07 Rāmāyaṇa (yuddha/uttara) at 0%** — these were GRETIL-ingested (H765)
> with a different `passage` convention; the ref mapper doesn't yet parse it.

Measured: their `passage` values are plain `N.N`, the same convention as every
other kāṇḍa, and `dcs_target()` mapped them correctly all along —
`06_ramayana-yuddhakanda` `1.1` → `Rām, Yu, 1`. At the passage level they align
to DCS at **100.0 %** (4435/4436) and **99.9 %** (2688/2690), the two *best*
figures in the whole Rāmāyaṇa, not the worst.

The real cause is one line in
[`nkrya_export.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/nkrya_export.py):
`classify()` emits a pair only `if sa_txt and ru_txt`, because a pair models the
**bilingual** unit. Both GRETIL kāṇḍas are **Sanskrit-only** — no Russian
translation exists for them yet — so every group fell to `mono_sa`, `pairs` came
back empty, and the SA morphology layer, which iterated `pairs`, wrote a
header-only file. The layer was reading a bilingual-alignment structure to answer
a monolingual question.

**Fix:** a separate `sa_units()` builder — every group carrying a non-empty
Sanskrit side, translated or not — now feeds `sa_morph_tsv()` and
`vidyut_diff_tsv()`. `classify()`/`pairs` are untouched and still drive the
para-XML, TMX, TSV and RU-morphology outputs, which genuinely are bilingual.

| Source | pairs | SA units | covered (before) | covered (after) | gold tokens |
|---|---:|---:|---:|---:|---:|
| 06_ramayana-yuddhakanda | 0 | 4436 | 0 | **4435** | **61,223** |
| 07_ramayana-uttarakanda | 0 | 2690 | 0 | **2688** | **37,530** |

**+7,123 verses and +98,753 gold tokens** that already existed in DCS and were
being discarded. Rāmāyaṇa gold coverage rises 8,193 → 15,316 verses (**+87 %**).
Every previously-covered source is byte-for-byte unchanged — the fix is purely
additive (`01/02/03/05` and MBh Āraṇyakaparva all report identical counts).

## Finding 2 — the 62–80 % is DCS's own density, not a verse-number offset

The build report recorded:

> **Rāmāyaṇa is partial (62–80%)** — verse-numbering diverges more between our
> edition and DCS's; the misses are alignment (verse-number offset), not missing
> DCS data.

That is backwards. Categorising every chapter/verse of the four bilingual kāṇḍas:

| kāṇḍa | our verses | DCS verses | matched | ch. absent in DCS | verses ours-only | verses DCS-only |
|---|---:|---:|---:|---:|---:|---:|
| bālakāṇḍa | 2269 | 1939 | 1813 | 1 | 456 | 126 |
| ayodhyākāṇḍa | 4314 | 3125 | 2667 | 8 | 1647 | 458 |
| araṇyakāṇḍa | 2445 | 2061 | 1768 | 4 | 677 | 293 |
| sundarakāṇḍa | 2859 | 2488 | 1943 | 2 | 916 | 545 |

The dominant miss is **verses ours-only** (3,696 across the four) — verses our
edition carries that DCS never annotated. No mapping change can conjure gold that
does not exist.

The reverse residue (**verses DCS-only**, 1,422) is the only place an offset
could hide, so it was tested directly: of those 1,422, **1,403 (98.7 %) lie
beyond our last verse in that chapter** — DCS's chapter simply runs longer — and
only **19 in total** fall inside our numbering range as a genuine hole. Nineteen
verses across four kāṇḍas is not a systematic offset; it is ordinary
verse-division noise between recensions (our source and DCS split hemistichs into
numbered verses differently, sometimes ours finer, sometimes DCS's).

**Conclusion: the Rāmāyaṇa verse map is already correct and is at its ceiling.**
Where DCS holds a verse under a number we also use, we match it today. The
62–80 % is a property of DCS's annotation density and recension, and the honest
move is to report it as coverage, not to chase an offset that isn't there.

## Corrected coverage table (units-based, real sweep)

| Source | SA units | covered | % | gold tokens |
|---|---:|---:|---:|---:|
| 06_ramayana-yuddhakanda | 4436 | 4435 | **100.0 %** | 61,223 |
| 07_ramayana-uttarakanda | 2690 | 2688 | **99.9 %** | 37,530 |
| 01_ramayana-balakanda | 2268 | 1812 | 79.9 % | 24,673 |
| 03_ramayana-aranyakanda | 2447 | 1770 | 72.3 % | 24,721 |
| 05_ramayana-sundarakanda | 2859 | 1943 | 68.0 % | 27,337 |
| 02_ramayana-ayodhyakanda | 4307 | 2668 | 61.9 % | 37,734 |
| **Rāmāyaṇa total** | **18,997** | **15,316** | **80.6 %** | **213,218** |

(`03_mahabharata-aranyakaparva` re-measured unchanged at 2032/2033 and 152,196
gold tokens, confirming the change is additive.)

## Validation

- Two full `--sa-morph` runs of `06_ramayana-yuddhakanda` are **byte-identical**
  (61,224-line TSV including header).
- Alignment spot-checked verbatim at Yu 1.1: our
  `śrutvā hanumato vākyaṃ yathāvad abhibhāṣitam…` against DCS `Rām, Yu, 1`
  sent 1 — `śrutvā`→`śru` VERB (absolutive, no case), `hanumato`→`hanumant` NOUN
  Gen Masc Sing, `vākyaṃ`→`vākya` NOUN Acc Neut Sing. Correct.
- +4 tests (17 pass, 2 vidyut-data-pack-gated skips), including a regression
  pinning that a Sanskrit-only source yields zero pairs but a full unit list.

## What this does not do

- It does not add gold where DCS has none: the four bilingual kāṇḍas stay at
  62–80 % and that is the ceiling.
- The 19 inside-range numbering holes are left as-is — individually adjudicating
  them is manuscript work, not a mapping fix, and the yield would be ~19 verses.
- The inline `<w><ana/>` scheme shared with H905 remains open; morphology is
  still an additive TSV sidecar.

_Dr. Mārcis Gasūns_
