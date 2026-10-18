# НКРЯ parallel export — layout, metadata mapping, and the old-name audit

_Created: 18-10-2026 · Last updated: 18-10-2026_

**H6370** (W6 residual of [`docs/ROADMAP_NKRYA_PARALLEL_RUSCORPORA_2026_2027.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ROADMAP_NKRYA_PARALLEL_RUSCORPORA_2026_2027.md)). The field remap itself shipped earlier as **H5281** — [`nkrya_export.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/nkrya_export.py) v0.2.0 carries the real НКРЯ names in `NKRYA_HEADER_FIELDS`. What this document adds: the mapping table that used to live only in a code comment at ~l.249, the per-source layout a reader actually receives, and a one-pass **verdict table** over every emitter path for the old guessed keys.

## 1. What leaves this directory

One directory per source slug, produced by [`nkrya_export.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/nkrya_export.py):

| artifact | what it is | НКРЯ-bound? |
|---|---|:---:|
| `<slug>.nkrya.xml` | the submission file — `<header>` of НКРЯ metadata + `<body>` of alignment units (`<se>` pairs; optional per-token `<w><ana lex= gr=/>`) | **yes** |
| `<slug>.tmx` | TMX 1.4b, one `<tu>` per pair, no `creationdate` (determinism) | no — generic exchange |
| `<slug>.tsv` | `group_id, sa_iast, sa_slp1, ru, flags` — one row per pair | no |
| `<slug>.sanskritisms_index.json` | per-source proper-name index (H760 Wave 3) | no |
| `<slug>.ru_morph.tsv` | Russian morphology layer: `group_id, tok_index, surface, lemma, pos, case, number` | no |
| `<slug>.sa_morph.tsv` | Sanskrit morphology layer from DCS gold: `group_id, verse, tok_index, form, lemma, upos, case, gender, number` | no |
| `<slug>.vidyut_diff.tsv` | DCS-gold vs Vidyut analyser disagreement (optional) | no |
| `export_report.json` | per-run report: counts, `nkrya_header` echo, `needs_review`, artifact list | no |

`showcase/` holds the curated package: `MANIFEST.tsv` (one row per showcase source, columns in [`build_nkrya_showcase_package.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/build_nkrya_showcase_package.py) `MANIFEST_COLS`), the zip handed to НКРЯ, and `SHOWCASE_VALIDATION.md`.

Bulk export artifacts are **gitignored / release-only** — this directory carries the code-facing docs, the curated showcase rows and the rights table, not the 131-source bulk output.

## 2. Metadata mapping — old guessed name → real НКРЯ field

Promoted from the code comment at [`nkrya_export.py` ~l.249](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/nkrya_export.py) (H5281 v0.2.0):

| old header tag (guessed) | НКРЯ field now emitted | direction |
|---|---|---|
| `title` | `headers_all` | title block, all parts |
| `author` | `authors_all` | author strings, all |
| `date_source_ce` | `created` | date of the **original** work |
| `year` | `date_trans` | date of the **translation/printing** |
| `lang_source` | `lang_orig` | source language (`san`) |
| — | `translator` | kept as-is (already a real field) |
| — | `sphere` | added (НКРЯ sphere taxonomy) |
| — | `words` | added (word count) |

**Provenance of the names.** Not invented: read off the live НКРЯ parallel-corpus form schema (`/api/v1/para-lex-gramm/search-form`, subcorpus `PARA`, probed 23-09-2026) and recorded in [`docs/DECISIONS_NKRYA_PARALLEL_SUBMISSION_23-09-2026.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/DECISIONS_NKRYA_PARALLEL_SUBMISSION_23-09-2026.md). That decision doc's §2 still describes the *pre-H5281* state ("the exporter emits guessed names") — it is a dated record, not a live claim; read it with its date.

**What deliberately does NOT go into the header.** НКРЯ has no field for `title_orig`, `translator_role`, `publisher`, `imprint`, `series`, `lang_target`, `period`, `provenance`, `rights`, `bibliography_status`. Those ride the **package manifest** (`MANIFEST.tsv` columns after `words`) and this repo's [`RIGHTS_TABLE.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/export/RIGHTS_TABLE.md), never the XML header.

## 3. Old-name audit — one pass over every emitter path

Question asked of each path: does it emit `author` / `year` / `lang_source` / `date_source_ce` **as keys in the submission format** (not as internal meta-input reads, which are legitimate — `load_meta()` still reads `meta['year']` and must)?

| # | emitter path | what it emits | old guessed keys present? | verdict |
|---|---|---|---:|---|
| 1 | `nkrya_xml()` — `<header>` children | `for tag, val in nkrya_fields(...)` | **no** | ✅ CLEAN — the only header source is `NKRYA_HEADER_FIELDS` |
| 2 | `tmx()` — `<header><prop type=…>` | same `nkrya_fields(...)` + `slug`, `x-rights` | **no** | ✅ CLEAN |
| 3 | `tsv()` — pair table | `group_id, sa_iast, sa_slp1, ru, flags` | **no** (no metadata at all) | ✅ CLEAN by construction |
| 4 | `build_nkrya_showcase_package.py` — `MANIFEST.tsv` | `slug, *NKRYA_HEADER_FIELDS, publisher, series, edition, via_lang, rights_class, pairs, …` | **no** — the extras are manifest columns, not header fields | ✅ CLEAN |
| 5 | `sanskritisms_index.json` / `*_morph.tsv` / `export_report.json` | name index, morph rows, run report | **no** in the index/morph rows; `export_report.json` carries report-shaped `title` / `year` / `publisher` | ✅ CLEAN — report keys, never fed to the header |

**Residual, recorded rather than hidden:** `export_report.json` uses `title`, `year`, `publisher` as *report* keys while the header uses `headers_all`, `date_trans`, `publisher`-in-manifest. That is a report vocabulary, not a submission vocabulary — but it is the one place a future reader could copy a wrong name from. Change it only with a consumer check on whoever reads `export_report.json`.

**Regression guard already in place:** [`web/tests/test_nkrya_export.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/test_nkrya_export.py) asserts every header child is a member of `NKRYA_HEADER_FIELDS` and that none of `title, author, year, lang_source, date_source_ce` appears as a TMX prop type. The audit above is therefore enforced, not merely documented.

## 4. Re-running

```sh
cd SamudraManthanam
python web/corpus_builder/nkrya_export.py --source 03_mahabharata-aranyakaparva --out nkrya-parallel/export
python web/corpus_builder/nkrya_export.py --all-pilot --out nkrya-parallel/export
python web/corpus_builder/build_nkrya_showcase_package.py          # rebuild showcase/ + MANIFEST.tsv
```

The exporter is deterministic (no `creationdate`, stable artifact order), so a re-run over unchanged sources must be byte-identical.

## 5. Known limits

- `authors_all` is empty for anonymous Sanskrit works — expected, not a defect: the field carries translator/author *credit strings* only where the printed edition names one.
- `created` stays empty where the composition date is unknown or disputed; the exporter never guesses a date (see `nkrya_fields()` docstring).
- Un-translated sources (e.g. GRETIL *yuddha*/*uttarakāṇḍa*) still get Sanskrit-side layers — the SA layers key off Sanskrit-bearing groups, not bilingual pairs.
- Bulk 131-source re-export is **not** triggered by this document: it is the Wave-5 iteration after НКРЯ replies.

_к.ф.н. М.Ю. Гасунс_
