# НКРЯ pilot triple-export — validation report (Wave 1)

_Created: 12-07-2026 · Last updated: 12-07-2026_

Pilot export of the four НКРЯ Wave-1 sources (MBh 3 + Rāmāyaṇa 1–3) from the
canonical verse-aligned JSONL into three formats — best-guess НКРЯ parallel
para-XML, TMX 1.4b, and TSV — per [H754](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H754-Opus_SamudraManthanam_nkrya-wave1-pilot-triple-export_11.07.26.md)
and rulings 1 & 7 of [ROADMAP_NKRYA_PARALLEL_RUSCORPORA_2026_2027.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ROADMAP_NKRYA_PARALLEL_RUSCORPORA_2026_2027.md).

- **Generator:** [`web/corpus_builder/nkrya_export.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/nkrya_export.py) v0.1.0
- **Tests:** [`web/tests/test_nkrya_export.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/test_nkrya_export.py)
- **Bibliographic metadata:** per-source `web/corpus_builder/<slug>.meta.json` sidecars (best guess, `needs_review: true` — verify against the physical editions before НКРЯ submission)
- **Model:** Opus 4.8 (`claude-opus-4-8`)
- **Export artifacts** (`nkrya-parallel/export/<slug>/*.nkrya.xml|.tmx|.tsv`) are **gitignored** (in-copyright translations); only this report is committed. Bulk ships later as a release artifact after per-translator clearance.

## Per-source results

| Source | Groups | Exported pairs | Monolingual-RU (flagged) | Untranslated-SA (flagged) | Commentary segs (excluded) | Empty side |
|---|---:|---:|---:|---:|---:|---:|
| 03_mahabharata-aranyakaparva | 2033 | **2033** | 0 | 0 | 1319 | 0 |
| 01_ramayana-balakanda | 2268 | **2268** | 0 | 0 | 519 | 0 |
| 02_ramayana-ayodhyakanda | 4307 | **4307** | 0 | 0 | 944 | 0 |
| 03_ramayana-aranyakanda | 2447 | **2447** | 0 | 0 | 694 | 0 |
| **Total** | **11 055** | **11 055** | **0** | **0** | **3476** | **0** |

Each pilot is a clean 1:1 corpus — every group carries both a Sanskrit verse and
its Russian translation, so exported-pairs == group-count for all four. The
`Exported pairs` column equals the `seg_counts.sa` figure in
[conversion_report.json](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/conversion_report.json)
for each source (parity gate a). Monolingual and untranslated units are **counted
and reported, never silently dropped** (all zero here); Russian commentary notes
are excluded from the pair export by design.

> Commentary count is *distinct commentary segments per group*; the raw
> `conversion_report.json` commentary record total is 1320 for MBh 3 (one
> duplicate comm-seg key collapses on grouping). Commentary is excluded from the
> parallel export either way, so this does not affect any gate.

## Gate results

| Gate | Check | Result |
|---|---|---|
| a | per-source pair count == both-sides group count == `conversion_report` `seg_counts.sa` | ✅ 2033 / 2268 / 4307 / 2447 |
| b | every emitted `.nkrya.xml` + `.tmx` well-formed (`xml.etree` parse) | ✅ all 8 parse |
| c | TMX carries the required 1.4b elements (`tmx@version=1.4`, `header@srclang`, `tu`/`tuv xml:lang`/`seg`) | ✅ |
| d | two runs byte-identical (no clock in artifact; natural-sorted canonical IDs) | ✅ 0 diffs across all 12 files |
| e | zero pairs with an empty side | ✅ |
| f | monolingual-RU counted, not dropped | ✅ (reported = 0) |

Test run (from `web/`):

```
python -m pytest tests/test_nkrya_export.py -m "not corpus" -q   # 5 passed  (hermetic)
python -m pytest tests/test_nkrya_export.py -m corpus -q         # 9 passed  (real pilots)
```

## Exact commands

```
# from repo root
python web/corpus_builder/nkrya_export.py --all-pilot --out nkrya-parallel/export
# or one source
python web/corpus_builder/nkrya_export.py --source 03_mahabharata-aranyakaparva --out nkrya-parallel/export
```

Each run writes `nkrya-parallel/export/<slug>/<slug>.nkrya.xml`, `.tmx`, `.tsv`,
and a machine-readable `export_report.json`.

## НКРЯ XML — documented assumptions (revisit in Wave 5)

The para-XML shape is a **best guess** — the artifact most likely revised once
НКРЯ answers the format question (roadmap ruling 4/Wave 5). Every modeling
assumption is stated in the [`nkrya_export.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/nkrya_export.py)
module docstring ("НКРЯ XML MODEL"):

- Root `<document corpus="parallel" subcorpus="sanskrit-russian">` with a
  `<header>` bibliographic block and a `<body>` of alignment units.
- One unit = `<para id=GROUP align="1-1">` holding exactly two `<se>` children,
  Sanskrit before Russian (source-before-target).
- Sanskrit `<se lang="san" script="iast" slp1="…">IAST</se>` — printed IAST is
  the element text, SLP1 the machine-key attribute; Russian `<se lang="ru">`.
- `lang` codes follow the H754 spec literally (`san`/`ru` in the para-XML;
  ISO `sa`/`ru` in the TMX `xml:lang`). Single point of change if НКРЯ's tag set
  differs: `LANG_SA_XML` / `LANG_RU_XML` in the module.
- Verse text is emitted **verbatim** (dandas + ॥n॥ verse numbers preserved), not
  the token-stripped form the L0 aligner uses — a faithful parallel corpus keeps
  the verse surface intact.

## Bibliographic caveat

The `.meta.json` sidecars carry **provisional** bibliography (translator,
publisher, year). MBh III year (1987, Vasilkov/Nevelева) is confirmed by an
in-text comment citation; the Rāmāyaṇa entries (Grintser, Ladomir/Nauka) and
especially Book III (year/translator unconfirmed from repo data) are flagged
`needs_review: true` and must be checked against the physical editions before the
НКРЯ submission.

_Dr. Mārcis Gasūns_
