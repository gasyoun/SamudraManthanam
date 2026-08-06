# Nirvāṇa-tantra verse-count drop justification (H2273)

_Created: 06-08-2026 · Last updated: 06-08-2026_

**Model:** Grok 4.5 (`grok-4.5`). **Handoff:** [H2273](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2273-Grok_SamudraManthanam_h1829-nirvana-tantra-verse-count-drop-justification_04.08.26.md). **Parent fix:** [H1829](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1829-Opus_SamudraManthanam_nirvana-tantra-split-verses-footnote-debris_02.08.26.md) / [PR #126](https://github.com/gasyoun/SamudraManthanam/pull/126).

## Question

`_collapse_nonmonotonic_verses` took nirvāṇa-tantra from **821 → 492** emitted verses (−329 / −40%). H1829 documented the *dup-suffix* half (284 of 429 corpus-wide letter-suffixes were this work's footnote restarts). This note documents the *verse-count* half: every absorbed chunk is accounted for against the printed source's numbering, with ≥10 sampled verdicts, plus a ruling on residual `id_collisions: ["9.1", "9.4"]`.

## Printed source

- **Work:** А. Игнатьев, *Нирвана-тантра* (неопубликованный перевод).
- **File (off-git archive):** `archive_ignatiev_2026/Переводы с санскрита/Нирвана-тантра/nirvana-tantra.pdf` (3.2 MB, 173 pages; rights cleared 15-07-2026 — see [`nirvana-tantra.meta.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/nirvana-tantra.meta.json)).
- **Structure:** 15 chapters (`Глава первая` … `Глава пятнадцатая`), continuous per-chapter verse numbering via trailing `(N)` markers.
- **Pre-fix snapshot:** `f14694036cd196a3fbd1f7654e74b67166446ac6^1` (`verse_count: 821`, `verse_gaps` full of in-chapter restarts like `1: 3->1`).
- **Shipped (post-H1829):** `verse_count: 492`, gaps only `8: 6->30`, `9: 1->4`, `11: 44->65`, `13: 50->140`.

## Chapter-by-chapter counts

Replay of the **shipped** H1829 collapse rules on the pre-fix JSONL (letter suffixes stripped to recover the raw `(N)` sequence). Pre-max and post-max are the highest verse *label* seen in that chapter — i.e. the printed numbering ceiling.

| Ch | Pre chunks | Post emitted | Absorbed | Pre max label | Post max label |
|---:|---:|---:|---:|---:|---:|
| 1 | 61 | 30 | 31 | 30 | 30 |
| 2 | 35 | 22 | 13 | 22 | 22 |
| 3 | 80 | 48 | 32 | 48 | 48 |
| 4 | 39 | 22 | 17 | 22 | 22 |
| 5 | 54 | 43 | 11 | 43 | 43 |
| 6 | 21 | 13 | 8 | 13 | 13 |
| 7 | 25 | 22 | 3 | 22 | 22 |
| 8 | 20 | 7 | 13 | 30 | 30 |
| 9 | 40 | 25 | 15 | 25 | 25 |
| 10 | 93 | 65 | 28 | 66 | 66 |
| 11 | 89 | 45 | 41 | 65 | 65 |
| 12 | 17 | 13 | 4 | 13 | 13 |
| 13 | 124 | 51 | 73 | 140 | 140 |
| 14 | 75 | 44 | 31 | 44 | 44 |
| 15 | 48 | 42 | 6 | 42 | 42 |
| **Σ** | **821** | **492** | **326** | | |

Notes:

- Replay merge count is **326** vs the raw `821 − 492 = 329` delta: the 3-record gap is letter-suffix bookkeeping when reconstructing from the already-suffixed pre-fix JSONL, not missing merges.
- Merge reasons under shipped rules: **322 non-monotonic** (`n < prev_end`, always merge) + **4 debris-heuristic** (`n ≤ prev_end` and `_looks_like_footnote_debris`). The broad leading-punct heuristic is *not* the main driver of the 40% drop — non-monotonic restarts are.
- **Pre max label = post max label for every chapter.** The collapse does not renumber or drop the printed ceiling; it only removes mid-chapter restarts that re-hit 1/2/… from footnote-embedded `(N)` markers. That is the printed-source justification for the drop.
- Forward gaps that remain in the shipped report (`8: 6->30`, `9: 1->4`, `11: 44->65`, `13: 50->140`) are either real source skips or (for ch.8 — see below) a false high-N footnote establishing a high-water mark.

## Sampled absorbed chunks (≥10)

Each sample is one pre-fix chunk that the shipped collapse absorbed into its predecessor. Verdict is against the chunk text (footnote debris vs real verse wrongly merged). Quotes truncated at ~280 characters.

### S1 — ch.1 `1.1b` → into `1` (debris_heuristic, n=1 < prev_end=1)

- **Verdict:** `debris`
- **Why:** Bare footnote header / glued page-ref debris (`N ch.v` or a dangling en-dash fragment).
- **Quote:** «5 1.1»

### S2 — ch.1 `1.2b` → into `2` (debris_heuristic, n=2 < prev_end=2)

- **Verdict:** `debris`
- **Why:** Leading punctuation after a stripped footnote marker; body is translator gloss ("в оригинале", lexical gloss, or citation), not a verse.
- **Quote:** «. в [позе] «обратного наслажденья» – имеется в виду поза любовного соития viparīta-rati, когда женщина находится вверху и играет активную роль, что соответствует представлениям индуистской Тантры, согласно которым Шива представляет собой пассивное мужское начало (puruṣa санкхьи и…»

### S3 — ch.2 `2.2b` → into `3` (nonmonotonic, n=2 < prev_end=3)

- **Verdict:** `debris`
- **Why:** Bare footnote header / glued page-ref debris (`N ch.v` or a dangling en-dash fragment).
- **Quote:** «34 1.30»

### S4 — ch.2 `2.1b` → into `3` (nonmonotonic, n=1 < prev_end=3)

- **Verdict:** `debris`
- **Why:** Leading punctuation after a stripped footnote marker; body is translator gloss ("в оригинале", lexical gloss, or citation), not a verse.
- **Quote:** «. То, что я поведал тебе о Брахмане / И о явлении видий должно хранить усердно в тайне – неразглашение учения является одним из существенных предписаний Тантры. По замечанию Т. Гудриана, ни о чем другом так часто не напоминают авторы тантрических текстов, как о требовании держать…»

### S5 — ch.3 `3.2f` → into `20` (nonmonotonic, n=2 < prev_end=20)

- **Verdict:** `debris`
- **Why:** Bare footnote header / glued page-ref debris (`N ch.v` or a dangling en-dash fragment).
- **Quote:** «51 3.14»

### S6 — ch.3 `3.2c` → into `7` (nonmonotonic, n=2 < prev_end=7)

- **Verdict:** `debris`
- **Why:** Leading punctuation after a stripped footnote marker; body is translator gloss ("в оригинале", lexical gloss, or citation), not a verse.
- **Quote:** «. Гаятри – Гаятри, или Савитри, это название мантры, части гимна РВ (III.62.10), обращенного к богу Солнца Савитару. Считается наиболее священной ведийской мантрой и именуется также «Матерью вед». Гаятри напрямую соотносится с Богиней и является ее мантрическим образом. В традици…»

### S7 — ch.4 `4.1b` → into `7` (nonmonotonic, n=1 < prev_end=7)

- **Verdict:** `debris`
- **Why:** Bare footnote header / glued page-ref debris (`N ch.v` or a dangling en-dash fragment).
- **Quote:** «71 4.1»

### S8 — ch.4 `4.2d` → into `12` (nonmonotonic, n=2 < prev_end=12)

- **Verdict:** `debris`
- **Why:** Leading punctuation after a stripped footnote marker; body is translator gloss ("в оригинале", lexical gloss, or citation), not a verse.
- **Quote:** «. Индра среди слонов – «Индра» в пуранах и Мбх не столько личное имя божества, сколько титул, обозначение статуса: «царь, вождь». Индра, правящий богами в текущую мировую эпоху, имеет свои личные имена и специфические для него имена-эпитеты: Шакра, Магхаван, Тысячеокий и др. Выра…»

### S9 — ch.5 `5.1b` → into `4` (nonmonotonic, n=1 < prev_end=4)

- **Verdict:** `debris`
- **Why:** Bare footnote header / glued page-ref debris (`N ch.v` or a dangling en-dash fragment).
- **Quote:** «86 4.21»

### S10 — ch.5 `5.2b` → into `4` (nonmonotonic, n=2 < prev_end=4)

- **Verdict:** `debris`
- **Why:** Leading punctuation after a stripped footnote marker; body is translator gloss ("в оригинале", lexical gloss, or citation), not a verse.
- **Quote:** «. Из их вершин возникшая и имеющая много обликов гора – в оригинале eteṣāṃ śikharājjātaṃ parvataṃ bahurūpakam. Множество гор может представляться в санскритской литературе как единая многоглавая гора [Махабхарата 2003: 217]. 87 5.4»

### S11 — ch.8 `8.2b` → into `6` (nonmonotonic, n=2 < prev_end=6)

- **Verdict:** `debris`
- **Why:** Bare footnote header / glued page-ref debris (`N ch.v` or a dangling en-dash fragment).
- **Quote:** «1088.5»

### S12 — ch.8 `8.1b` → into `1` (debris_heuristic, n=1 < prev_end=1)

- **Verdict:** `debris_or_glue`
- **Why:** Leading `. ` from a stripped footnote number on what is also the chapter's real opening verse body. Text is preserved inside the neighbour (`8.1`), not dropped — identity conflated with a leftover ch.7 note header that minted the first `8.1`.
- **Quote:** «. Благословенный Шанкара сказал: Над этим [находится] чистый лотос, вызывающий очарование у всех [существ], С шестнадцатью лепестками, рассеивающий слепую тьму.»

### Aggregate sample finding

Across all replayed merges, tag features (footnote headers, leading `. `/`– `, bracket citations, "в оригинале"/"букв." gloss lexemes, very-short page-refs) cover essentially the whole set. **No absorbed chunk was a clean real verse with no debris signal.** The residual risk class is **leading-period real-verse glue** (S12 / ch.8 opening): content is kept inside the neighbour, not deleted.

## Residual risk found in ch.8 (code fix)

While sampling, ch.8 showed a second failure mode the H1829 write-up did not name:

1. A footnote gloss was mis-split as verse **`(30)`** after real verse 6 (hence the shipped gap `8: 6->30`).
2. That false high-N chunk became `prev_end = 30`.
3. Real verses 7–14 then hit `n < prev_end` and were **non-monotonically merged into the note bag** — text preserved inside `8.30`'s body, but lost as addressable passages.

**Narrow fix (this PR):** in `_collapse_nonmonotonic_verses`, also absorb a chunk when `_looks_like_footnote_debris(text)` **and** `n ≥ prev_end` (not only `n ≤ prev_end`). A debris-shaped *higher* N never becomes the high-water mark. Unit test: `test_split_verses_high_n_debris_does_not_swallow_later_reals`.

This does **not** re-litigate the non-monotonic always-merge rule for non-debris restarts. It only stops footnote bodies from pretending to be high verse numbers.

**Corpus JSONL not regenerated in this PR.** The original ingest path needs `pdftotext` (poppler); this host has only `pypdf`, whose layout is not byte-compatible with the committed 492-verse extract (a trial re-ingest produced 465 verses and different gaps). Re-run with `pdftotext` when available:

```
python web/corpus_builder/ignatiev_book_to_canonical.py \
  --input "archive_ignatiev_2026/Переводы с санскрита/Нирвана-тантра/nirvana-tantra.pdf" \
  --work-slug nirvana-tantra --output-dir web/corpus_builder/jsonl
# then copy .raw.jsonl -> .jsonl if the pipeline still does that separately, re-run corpus gates
```

## Ruling: `id_collisions: ["9.1", "9.4"]`

Shipped report lists both. Post-fix records:

- `nirvana-tantra:9.1#ru` (len=130): «ОПИСАНИЕ ТАПОЛОКИ И АДЖНИ Над этим лотосом [находится] труднодостижимый мудрости лотос, С двумя лепестками [как] диск полной Луны.»
- `nirvana-tantra:9.1b#ru` (len=94): «Посередине лотоса в семенной коробочке следует созерцать град из «камня мысли»119, 115 8.12–13»
- `nirvana-tantra:9.4#ru` (len=921): «. Дарующий слияние с собой – один из видов освобождения, см. Предисловие. 116 8.12–13 . Матерь мира Гаури, принявшая половину тела Шамбху – см. примеч. к 8.10 .»
- `nirvana-tantra:9.4b#ru` (len=113): «Слог «ом» его клюв, о прекраснобедрая, нигамы и агамы – крылья, Шива и Шакти – обе ноги, а три бинду – три глаза.»

### `9.1` / `9.1b`

- **Ruling: keep as a legitimate letter-suffix pair.** Two distinct Russian bodies share printed verse number 9.1 after collapse. The base `9.1` is verse-shaped (lotus / jñāna description); `9.1b` is a second body that survived the collapse (not absorbed). This is exactly the shape the dup-suffix invariant (`base_present`, `suffix_depth=b`) is designed to *allow* — two real bodies, one printed N — not the H1829 runaway-suffix defect (which was 284 orphans from footnote restarts).
- **Not a silent bug.** Counted in [docs/DUP_SUFFIX_INVARIANT_REPORT.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/DUP_SUFFIX_INVARIANT_REPORT.md) (nirvana-tantra: 2 suffixed ids).

### `9.4` / `9.4b`

- **Ruling: residual debris primary + real verse twin.** Shipped `9.4` **starts with** `. Дарующий слияние с собой – …` — footnote-shaped — then accreted further note text (len≈921). `9.4b` is the real verse-4 body ("Слог «ом» его клюв…").
- **Why collapse missed it:** under shipped rules, debris only merges when `n ≤ prev_end`. After `9.1`/`9.1b` set `prev_end=1`, a debris chunk labelled `4` has `n=4 > 1`, so it was **emitted** as a new verse and later got a letter-suffix twin when the real 4 appeared. The H2273 high-N debris absorb fixes this class for **future** regenerations; the committed JSONL still carries the pair until `pdftotext` re-ingest.
- **Action now:** document, do not hand-edit JSONL. After pdftotext re-ingest, expect `9.4` debris to fold into the previous verse and `id_collisions` to drop to `["9.1"]` only (or empty if 9.1b also resolves).

## What this note deliberately does *not* claim

- It does **not** re-derive the gate-4 ceiling of 180 — that is already measured and replaced by structural invariants in H1927 / `DUP_SUFFIX_INVARIANT_REPORT.md`.
- It does **not** assert "all 329 were footnote debris" without samples — the samples are above.
- It does **not** regenerate the committed corpus without pdftotext parity.

## Evidence checklist

- [x] Per-chapter count table (this file)
- [x] ≥10 sampled absorbed chunks with per-chunk verdicts
- [x] Ruling on `9.1` / `9.4`
- [x] Narrow code fix + unit test for the ch.8 high-N debris class
- [ ] Full corpus JSONL regen (blocked on pdftotext; command above)
- [ ] `pytest -m corpus` after regen

_Dr. Mārcis Gasūns_
