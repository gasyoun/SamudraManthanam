# MANIFEST — local-only files in `diplom-rubanova/`

_Created: 11-07-2026 · Last updated: 11-07-2026_

Inventory of every file in this directory that is **untracked and gitignored**
(kept only on this disk). The curated reusable artifacts — санскритизм
indexes, name lists, stemmer rules, and the manual-adjudication /
epithet-synonym lists under `archive/` — are tracked directly and are **not**
listed here; see `git ls-files nkrya-parallel/diplom-rubanova/` for those.
This file exists so a future session (or human) knows what exists on disk
without having to `ls` a ~600 MB working tree. Feeds Wave 2/3 of
[`docs/ROADMAP_NKRYA_PARALLEL_RUSCORPORA_2026_2027.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ROADMAP_NKRYA_PARALLEL_RUSCORPORA_2026_2027.md).

## Top-level (`diplom-rubanova/`)

| File | Size | What it is |
|---|---|---|
| `01_part.txt` | 8.4 KB | Raw corpus text dump — partial excerpt of `01.txt` (MBh Āraṇyakaparva part 1). |
| `deeppavlov_01_part.txt` | 69 KB | DeepPavlov morphological-tagger output, partial run over `01_part.txt`. |
| `Рамаяна_3.txt` | 513 KB | Raw corpus text dump, Rāmāyaṇa kāṇḍa 3 (Araṇyakāṇḍa) — alt-naming duplicate of `Рам_03.txt`. |
| `01.txt` | 768 KB | Raw corpus text dump, MBh Āraṇyakaparva part 1. |
| `Рам_03.txt` | 894 KB | Raw corpus text dump, Rāmāyaṇa kāṇḍa 3. |
| `02.txt` | 1.3 MB | Raw corpus text dump, MBh Āraṇyakaparva part 2. |
| `Рам_01_02.txt` | 2.2 MB | Raw corpus text dump, Rāmāyaṇa kāṇḍas 1–2 combined. |
| `volume_3.txt` | 3.0 MB | Raw corpus text dump, full MBh book 3 volume. |
| `deeppavlov_ram_3.txt` | 4.1 MB | DeepPavlov morph output, Rāmāyaṇa kāṇḍa 3. |
| `deeppavlov_Рамаяна_3.txt` | 4.1 MB | DeepPavlov morph output, Rāmāyaṇa kāṇḍa 3 (alt-naming duplicate run). |
| `aranyakaparva_corpus2.txt` | 4.4 MB | Raw corpus text dump, MBh Āraṇyakaparva, second corpus variant. |
| `Презентация для защиты.pptx` | 5.2 MB | Defense presentation source (PPTX). PDF equivalent (`Prezentatsia_dlya_zaschity_Ed.pdf`) is tracked instead per H753 scope. |
| `deeppavlov_01.txt` | 6.0 MB | DeepPavlov morph output, MBh Āraṇyakaparva part 1 (full run). |
| `deeppavlov_Рам_03.txt` | 7.1 MB | DeepPavlov morph output, Rāmāyaṇa kāṇḍa 3 (full run). |
| `deeppavlov_sents2.txt` | 8.6 MB | DeepPavlov sentence-segmented output, variant 2. |
| `384000.txt` | 9.1 MB | Raw corpus text dump (numbered working-file variant, source unclear from filename). |
| `Mh_Book3_Oliver.csv` | 14 MB | MBh book 3, Oliver-translation reference CSV used for cross-checking. |
| `res.txt` | 16 MB | Raw results/output dump from a processing run. |
| `paral_corp (44).html` | 16 MB | Parallel-corpus HTML export snapshot (working checkpoint). |
| `deeppavlov_Рам_01_02.txt` | 18 MB | DeepPavlov morph output, Rāmāyaṇa kāṇḍas 1–2. |
| `deeppavlov_02.txt` | 18 MB | DeepPavlov morph output, MBh Āraṇyakaparva part 2. |
| `deeppavlov_mbh_3_oliver.txt` | 20 MB | DeepPavlov morph output, MBh book 3 (Oliver text variant). |
| `deeppavlov_mbh_3.txt` | 25 MB | DeepPavlov morph output, MBh book 3 (primary text). |
| `deeppavlov_sents.txt` | 46 MB | DeepPavlov sentence-segmented output (primary run). |
| `deeppavlov_volume3.txt` | 49 MB | DeepPavlov morph output, full MBh volume 3. |
| `dict.opcorpora.txt` | 271 MB | Third-party OpenCorpora Russian morphological dictionary (bulk reference data, not authored here). |

## `archive/` (bulk — candidate lists + large source dictionaries)

Only `archive/`'s manual-adjudication and epithet/synonym lists (≤120 KB each)
are tracked. Everything else — automated candidate lists awaiting review, and
the large source word-lists/dictionaries — stays local-only:

| File | Size | What it is |
|---|---|---|
| `preffix.txt` | 18 B | Tiny prefix helper list. |
| `suffix.txt` | 196 B | Tiny suffix helper list. |
| `rus_san_words.txt` | 312 B | Small Russian/Sanskrit word helper list. |
| `03_1_manually.txt` (companion) | 1014 B | *(tracked — listed here only for cross-reference; see `03_1.txt` below, its untracked automated-candidate source.)* |
| `03_1.txt` | 12 KB | Automated candidate index, book 3 part 1 — pre-adjudication (superseded by tracked `03_1_manually.txt`). |
| `03_2.txt` | 22 KB | Automated candidate index, book 3 part 2 — pre-adjudication. |
| `03_3.txt` | 8.8 KB | Automated candidate index, book 3 part 3 — pre-adjudication. |
| `03_4.txt` | 2.9 KB | Automated candidate index, book 3 part 4 — pre-adjudication. |
| `03_5.txt` | 7.0 KB | Automated candidate index, book 3 part 5 — pre-adjudication. |
| `03_all_index.txt` | 32 KB | Combined automated candidate index across all book-3 parts. |
| `03_my_cands.txt` | 1.3 KB | Rubanova's own candidate shortlist. |
| `03_py_cands.txt` | 776 B | Python-script-generated candidate list. |
| `morph_cands.txt` | 2.0 KB | Morphology candidate list (pre-adjudication). |
| `index_3.txt` | 46 KB | Automated candidate index, book 3 (combined). |
| `pavl_cands.txt` | 111 KB | Pavlovsky/DeepPavlov-derived candidate list. |
| `volume3_intersection.txt` | 21 KB | Candidate intersection list across volume 3 sources. |
| `sanskrit_names.txt` | 391 KB | Sanskrit name list — larger variant, over the 120 KB curated-archive threshold. |
| `upper_words.txt` | 253 KB | Uppercase-word extraction list. |
| `found.txt` | 928 KB | Found-word match dump from a processing run. |
| `zlz_efr_dict.txt` | 2.8 MB | Зализняк / Ефремова dictionary dump (source reference data). |
| `cands.txt` | 4.7 MB | Large raw candidate list (pre-adjudication, all books). |
| `synt_analized.txt` | 17 MB | Syntactic-analysis dump. |
| `rus_words.txt` | 122 MB | Large Russian word-list dictionary (source reference data). |

## Tracked for reference (not part of this manifest)

- Curated `diplom-rubanova/` lists (санскритизм indexes, name lists, stemmer
  rules, correction/translation helpers) — tracked directly, see
  `git ls-files nkrya-parallel/diplom-rubanova/`.
- `archive/03_1_manually.txt` … `archive/03_5_manually.txt`, `archive/03_manual.txt`,
  `archive/3_morph_manual.txt`, `archive/manual_words.txt` — manual adjudication
  results (tracked).
- `archive/epith_3.txt`, `archive/new_epith_3.txt`, `archive/syns_3.txt`,
  `archive/new_syns_3.txt` — epithet/synonym lists (tracked).
- `ВКР.mdx` / `ВКР.docx` / `ВКР_media/` — the thesis document itself, landed
  in [PR #38](https://github.com/gasyoun/SamudraManthanam/pull/38).

_Dr. Mārcis Gasūns_
