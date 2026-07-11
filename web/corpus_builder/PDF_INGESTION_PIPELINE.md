# PDF → Corpus Ingestion Pipeline (house standard)

_Created: 10-07-2026 · Last updated: 11-07-2026_

The reusable, agent-runnable pipeline that turns a print-derived **PDF**
translation into the app-ready corpus HTML the desktop reader «Пахтанье
океана» loads from `Data/` and the web platform ingests — the free-toolchain
replacement for the Delphi `cb.exe`
([`Corpus_builder/`](https://github.com/gasyoun/SamudraManthanam/tree/main/Corpus_builder))
for **new** ingestion. Built for H534 (Devībhāgavata-purāṇa, A. Ignatjev,
Касталия 2018).

It reuses the canonical JSONL schema and specs already in this folder — it does
**not** invent a new one:
[`docs/CONVERTER_SPEC.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/CONVERTER_SPEC.md) ·
[`docs/ALIGNMENT_SPEC.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ALIGNMENT_SPEC.md) ·
[`docs/LINE_ID_SCHEME.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/LINE_ID_SCHEME.md).

## The three stages

```
PDF ──(1) ignatjev_pdf_to_canonical.py──▶ *.raw.jsonl  (+ *.report.json)
                                              │
              (2) align_sanskrit.py ◀── Sanskrit *.jsonl (optional)
                                              │
                                       *.aligned.jsonl (+ *.alignment.json)
                                              │
              (3) build_corpus_html.py ──────▶ Data/<slug>[-<skandha>].html
                                               + .no_tags + .html.meta.json
                                               + append to Programdata/data.txt
```

### 1. `ignatjev_pdf_to_canonical.py` — PDF → canonical JSONL (Russian side)

[`ignatjev_pdf_to_canonical.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/ignatjev_pdf_to_canonical.py)
parses one Ignatjev volume with `pdftotext -enc UTF-8`, recovering structure
from the source's own very regular conventions (no layout heuristics):

- **Skandha / chapter** from the Russian colophons
  (`Так … заканчивается двадцатая глава, называющаяся «…».` +
  `ТАК ЗАКАНЧИВАЕТСЯ ПЕРВАЯ КНИГА …`), with feminine ordinal words decoded by
  [`ru_ordinals.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/ru_ordinals.py).
- **Verses** split on the trailing `(N)` marker; **speakers** (`X сказал:`)
  lifted into an `author` field and carried forward.
- **Endnotes** collected per skandha under `Комментарий`
  (`<n> <ch>.<verse>(<pada>). <text>`), re-joined across wrapped lines via the
  strictly-increasing footnote numbering, emitted as `comm{k}` segments
  attached to their verse via `annotates`.
- **Footnote superscripts** glued to words by pdftotext (`Знание2`) are stripped
  from the searchable `text` and re-linked as devi-gita-style `<sup>` refs in
  `html`.

Passage IDs follow [`LINE_ID_SCHEME.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/LINE_ID_SCHEME.md):
zero-padded `SKANDHA.CHAPTER.VERSE` (`1.006.006`) so the GRETIL cross-numbering
`DbhP_1,6.6` stays mechanically alignable and the ID grammar is uniform with the
rest of the corpus.

**Gotcha (logged):** pdftotext prepends a form-feed `\x0c` to the first line of
every page; it glues onto page-top text and breaks the endnote-number and
chapter-heading anchors. `extract_pdf_text` normalises `\x0c` → newline.

### 2. `align_sanskrit.py` — attach Sanskrit on the passage key

[`align_sanskrit.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/align_sanskrit.py)
is a **source-agnostic key join**, not a statistical aligner (per
[`ALIGNMENT_SPEC.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ALIGNMENT_SPEC.md)
§0): it pairs a Sanskrit `#sa` segment onto the Russian `#ru` group only when
their `SKANDHA.CHAPTER.VERSE` keys match; otherwise the verse stays
**Russian-only** (`0:1`, the sanctioned fallback) and the mismatch is itemised
in the alignment report — never dropped or fabricated. With no Sanskrit input
the whole work is Russian-only and the report records 100% `ru_only`.

The Sanskrit `#sa` JSONL is produced by
[`sanskritdocuments_dbhp_to_canonical.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/sanskritdocuments_dbhp_to_canonical.py)
(MG `@DECIDE` 10-07-2026, option (a) — the full DBhP is **not on GRETIL**, so the
Sanskrit comes from **sanskritdocuments.org**'s 12 per-skandha ITRANS files
`devIbhAgavatamNN.itx`, Vishwas Bhide / satsangdhara.net). It parses the
`\section{S\.C ...}` chapter markers + `|| N||` verse numbering, carries the
`X uvAcha` speaker rubrics into an `author` field, skips the
`iti shrImaddevIbhAgavate ...` colophons, and transcodes ITRANS → IAST (display)
+ SLP1 via `indic_transliteration.sanscript`, emitting the same `#sa` schema
keyed `SKANDHA.CHAPTER.VERSE`.

### 3. `build_corpus_html.py` — canonical JSONL → app HTML

[`build_corpus_html.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/build_corpus_html.py)
promotes the validation-only
[`render_for_reader.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/render_for_reader.py)
to the full emitter: the `<!-- Title --!>` first line, the shared
head/CSS/Yandex-Metrika wrapper, the
`chapters → chapter → citation_block` body (`chapter_block iast` +
`chapter_block translation` + `comments`), plus the `.no_tags` and
`.html.meta.json` sidecars, and appends every filename to
[`Programdata/data.txt`](https://github.com/gasyoun/SamudraManthanam/blob/main/Index/lib/x86_64-win64/Programdata/data.txt).
Output granularity is a parameter and **both** forms are house conventions:
`--split skandha` (one file per skandha) and `--combined` (one file per work).

## Run it (DBhP example)

```sh
cd web/corpus_builder
# 1. parse one volume (pilot: a single skandha) -> Russian side
python ignatjev_pdf_to_canonical.py \
  --pdf "../../AdnrejIgnatjev/devibhagavata-purana/Девибхагавата-пурана. Том 1.pdf" \
  --output-dir jsonl --skandha-only 1
# 1b. Sanskrit side from sanskritdocuments.org (devIbhAgavatamNN.itx)
python sanskritdocuments_dbhp_to_canonical.py \
  --itx sanskrit_src/devIbhAgavatam01.itx --skandha 1 --output-dir jsonl
# 2. align (omit --sa for Russian-only)
python align_sanskrit.py --ru jsonl/devibhagavata-purana_s1.raw.jsonl \
  --sa jsonl/devibhagavata-purana_s1.sanskrit.jsonl \
  --out jsonl/devibhagavata-purana-1.jsonl \
  --report jsonl/devibhagavata-purana-1.alignment.json
# 3. emit app HTML + sidecars + register in data.txt
python build_corpus_html.py --jsonl jsonl/devibhagavata-purana-1.jsonl \
  --report jsonl/devibhagavata-purana_s1.report.json \
  --meta devibhagavata-purana.meta.json \
  --data-dir ../../Index/lib/x86_64-win64/Data \
  --data-txt ../../Index/lib/x86_64-win64/Programdata/data.txt \
  --split skandha
```

## Validation

- **Acceptance test:**
  [`web/tests/test_ignatjev_dbhp.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/test_ignatjev_dbhp.py)
  (`-m corpus`) asserts the Vol-1/Skandha-1 counts against the PDF's printed
  numbering.
- **Round-trip:** `html_to_canonical.py` on the emitted HTML re-produces the
  source verse text **1181/1181** (zero divergence); all 429 comment texts are
  present. Known limitation: the web converter keys comments on
  `comment_{ch}_{v}` anchors, whereas this emitter uses the source's own
  `comment_{fn}` numbering (self-consistent for the desktop reader's inline
  links), so the web-ingest path files DBhP comments under a `c.N.pM` fallback
  key — the comment **text** still round-trips; only the verse linkage differs
  on that one path.

## Status: 12/12 skandhas ingested + Sanskrit-aligned (H558)

All twelve skandhas are live in `Data/` as `devibhagavata-purana-<N>.html`
(per-skandha) plus a combined `devibhagavata-purana.html`; every file is
registered in
[`Programdata/data.txt`](https://github.com/gasyoun/SamudraManthanam/blob/main/Index/lib/x86_64-win64/Programdata/data.txt).
Skandha 1 was the H534 pilot (99.9% aligned); skandhas 2–12 were added by H558.
Batch-reproducible via
[`build_dbhp_skandhas.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/build_dbhp_skandhas.py)
(RU parse → SA convert → align) then
[`emit_dbhp_corpus.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/emit_dbhp_corpus.py)
(HTML). Totals: **~17,300 RU verses, ~3,600 comments**; per-skandha RU→SA match
rate **~99%** (mirroring S1); **round-trip 16180/16180 RU verses reproduced
exactly** across skandhas 2–12.

### Volume → skandha map (2 per volume)

Vol N holds skandhas (2N-1, 2N): Vol 1 = 1,2 · Vol 2 = 3,4 · Vol 3 = 5,6 ·
Vol 4 = 7,8 · Vol 5 = 9,10 · Vol 6 = 11,12. The parser hard-derives
`base = 2N-1` (the per-volume first-colophon scrape is unreliable — pdftotext
drops skandha 7's «книга» colophon entirely) and rolls over to the next skandha
at the **end of each Комментарий note block** (notes close every skandha here).

### Multi-volume parse hardening (why the six volumes differ)

- **Endnote re-join** is gap-tolerant/monotonic, not strict `fn==next` — a note
  whose ref shape the old code missed (chapter-range `46 3-6.`, spaced dot
  `1. 4(1)`, numeric pada `(1)`) no longer stalls the join and glues the rest
  (the Vol 2/4/5 18/2/71 desync).
- **Note headings** vary: `Комментарий` / plural `Комментарии` (Vols 1–2),
  ALL-CAPS `КОММЕНТАРИЙ` / `КОММЕНТАРИИ` (Vols 3–6). Missing the plural dropped
  Vol 2 skandha 4's ~230 notes.
- **Chapter colophons** vary: the `называющаяся «title»` clause is often absent
  (whole skandhas 8/9 are title-less), the ordinal sometimes follows «глава»,
  and pdftotext wraps a colophon across two lines — all handled; a dropped
  colophon is recovered from the chapter's opening heading.
- **Devī-gītā** (DBhP 7.31–40) renumbers its chapters from 1 in-text; the parser
  detects the «Деви-гит» marker and offsets those chapters (and their notes)
  by +30 so they align with the Sanskrit's 7.31–7.40 and don't collide with the
  mula's chapters 1–10.
- A **duplicate passage-id integrity guard** and a **strictly-increasing chapter
  renumber** keep the corpus free of duplicate ids where OCR merges a chapter or
  the edition misprints one (skandha 10 prints two «пятая глава»).

### Data findings (in the alignment reports — logged, not forced)

- **Skandha 6 covers only Sanskrit chapters 1–15 of 31** in Ignatjev Vol 3 (923
  RU matched, **960 SA-orphans**) — a genuine source-coverage gap, not a parse
  loss.
- **Skandha 9 loses chapters 16 and 36** to OCR (both the closing colophon and
  the next opening heading are missing), merging them into their neighbours
  (169 SA-orphans; verses preserved, RU-only).
- **Reader record limit:** the combined `devibhagavata-purana.html` is **37,984
  records** and skandhas 9/7 are 7,056/5,301 — all above `iRecordLimit = 5000`
  (`program.ini`). The per-skandha files are the primary access; raising
  `iRecordLimit` or dropping the combined file is an open call for a human.

_Dr. Mārcis Gasūns_
