# НКРЯ showcase package v1 — validation report (H5281)

_Created: 23-09-2026 · Last updated: 23-09-2026_

Showcase («витрина», MG ruling P3 in [DECISIONS_NKRYA_PARALLEL_SUBMISSION_23-09-2026.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/DECISIONS_NKRYA_PARALLEL_SUBMISSION_23-09-2026.md)): 24 texts, built by [`build_nkrya_showcase_package.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/build_nkrya_showcase_package.py). Pair counts are checked against the committed [FULL_CORPUS_VALIDATION.md](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/export/FULL_CORPUS_VALIDATION.md) (Wave-4 freeze, 13-07-2026). Commentary segments are excluded (MG P9). Sanskrit stays IAST with an SLP1 attribute (MG P5).

| Text | НКРЯ translator | date_trans | sphere | Pairs | Frozen | Match | SA inline (DCS) | DCS gold units |
|---|---|---:|---|---:|---:|:---:|---:|---:|
| `01_rigveda` | Т. Я. Елизаренкова | 1989 | художественная | 1976 | 1976 | ✅ | 0 | 0 |
| `02_rigveda` | Т. Я. Елизаренкова | 1989 | художественная | 429 | 429 | ✅ | 0 | 0 |
| `03_rigveda` | Т. Я. Елизаренкова | 1989 | художественная | 617 | 617 | ✅ | 0 | 0 |
| `04_rigveda` | Т. Я. Елизаренкова | 1989 | художественная | 589 | 589 | ✅ | 0 | 0 |
| `05_rigveda` | Т. Я. Елизаренкова | 1995 | художественная | 725 | 725 | ✅ | 0 | 0 |
| `06_rigveda` | Т. Я. Елизаренкова | 1995 | художественная | 765 | 765 | ✅ | 0 | 0 |
| `07_rigveda` | Т. Я. Елизаренкова | 1995 | художественная | 841 | 841 | ✅ | 0 | 0 |
| `08_rigveda` | Т. Я. Елизаренкова | 1995 | художественная | 1716 | 1716 | ✅ | 0 | 0 |
| `09_rigveda` | Т. Я. Елизаренкова | 1999 | художественная | 1108 | 1108 | ✅ | 0 | 0 |
| `10_rigveda` | Т. Я. Елизаренкова | 1999 | художественная | 1751 | 1751 | ✅ | 0 | 0 |
| `bhagavadgita-1788` | А. А. Петров | 1788 | нехудожественная: церковно-богословская | 697 | 697 | ✅ | 0 | 0 |
| `bhagavadgita-1909` | А. П. Казначеева | 1909 | нехудожественная: церковно-богословская | 691 | 691 | ✅ | 0 | 0 |
| `bhagavadgita-1914` | А. А. Каменская, И. В. де Манциарли | 1914 | нехудожественная: церковно-богословская | 701 | 701 | ✅ | 0 | 0 |
| `bhagavadgita-smirnov` | Б. Л. Смирнов | 1956 | художественная | 700 | 700 | ✅ | 0 | 0 |
| `bhagavadgita-sementsov` | В. С. Семенцов | 1985 | художественная | 696 | 696 | ✅ | 0 | 0 |
| `bhagavadgita-erman` | В. Г. Эрман | 2009 | художественная | 700 | 700 | ✅ | 0 | 0 |
| `bhagavadgita-burba` | Д. В. Бурба | 2009 | художественная | 719 | 719 | ✅ | 0 | 0 |
| `bhagavadgita-prabhupada` | А. Ч. Бхактиведанта Свами Прабхупада (англ. пер. и комм.) | 1984 | нехудожественная: церковно-богословская | 657 | 657 | ✅ | 0 | 0 |
| `bhagavadgita-radha` | Р. Т. Блиндерман | 2016 | нехудожественная: церковно-богословская | 647 | 647 | ✅ | 0 | 0 |
| `bhagavadgita-sharma` | Шайлендра Шарма | 2015 | нехудожественная: церковно-богословская | 660 | 660 | ✅ | 0 | 0 |
| `03_mahabharata-aranyakaparva` | Я. В. Васильков, С. Л. Невелева | 1987 | художественная | 2033 | 2033 | ✅ | 30 | 2032 |
| `01_ramayana-balakanda` | П. А. Гринцер | 2006 | художественная | 2268 | 2268 | ✅ | 23 | 1812 |
| `02_ramayana-ayodhyakanda` | П. А. Гринцер | 2006 | художественная | 4307 | 4307 | ✅ | 19 | 2668 |
| `03_ramayana-aranyakanda` | П. А. Гринцер | 2014 | художественная | 2447 | 2447 | ✅ | 4 | 1770 |

**24 of 24 texts match the frozen pair counts; 28,440 pairs in the package.**

## DCS morphology (MG P7, CC BY 4.0)

1. MBh III and Rām I–III: DCS gold ships in full as `<slug>.sa_morph.tsv`; inline `<w><ana/>` only where DCS tokens attach to the printed surface end-to-end (all-or-nothing, never guessed) — the same ~1 % as H906 ([INLINE_ANA_H906_REPORT.md](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/INLINE_ANA_H906_REPORT.md)).
2. Ṛgveda: DCS holds the Ṛgveda (1,028 hymns) but its sentences carry no verse number (sent_counter NULL), so gold cannot be attached per verse without guessing — not attached.
3. Bhagavadgītā: the DCS 2026 dump has no Bhagavadgītā text and no MBh 6.23–40 chapters — not covered.
4. Russian side: pymorphy3 inline `<w><ana/>` on 100 % of pairs.

## Artifact checksums (sha256)

- `nkrya-showcase-v1.zip` — `95a4711d53199d9b5dd994567dd2b0e43afa02d6996b0ff5fa3821b60d70237c`
- `nkrya-showcase-pd-v1.zip` — `830110cde446024080206fb2927f2b15f2bcbeb3a4727811c281a8b6d74bd91a`

_Dr. Mārcis Gasūns_
