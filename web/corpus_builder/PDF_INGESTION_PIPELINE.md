# PDF → Corpus Ingestion Pipeline (house standard)

_Created: 10-07-2026 · Last updated: 07-08-2026_

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

## Single-book generalization (H1438)

[`ignatiev_book_to_canonical.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/ignatiev_book_to_canonical.py)
generalizes stage 1 for А. Игнатьев's ~20 other translations (tantras +
upapurāṇas, `archive_ignatiev_2026/Переводы с санскрита/`) — each a
standalone work with no skandha/volume level, sourced as a single `.docx`,
`.doc`, or `.pdf` file rather than DBhP's 6-volume PDF set. Rights: cleared for
"all my works ... whether published or unpublished" — see
[RIGHTS_GRANT_IGNATJEV_DBHP_2026H2.md](https://github.com/gasyoun/Uprava/blob/main/RIGHTS_GRANT_IGNATJEV_DBHP_2026H2.md).

### Legacy `.doc` extract (H2352)

`extract_text()` accepts Word 97–2003 binary `.doc` as follows:

| Path | When | Notes |
|---|---|---|
| **antiword** (preferred) | `antiword` on PATH | `-m cp1251.txt`, 120 s timeout; non-zero / empty / timeout → fall through |
| **OLE UTF-16** (fallback) | antiword missing or failed | `olefile` WordDocument stream scan — hermetic CI path |

**CI policy:** antiword is **optional** — hermetic unit tests always cover the OLE
path with a synthetic fixture (`test_ignatiev_book_units.py`); antiword/archive
smokes `pytest.skip` when the binary or gitignored archive is absent. Never
return a silent empty string; both paths raise `RuntimeError` with the source
path. Do **not** commit `archive_ignatiev_2026/` blobs. No `soffice` dependency.

Differences from the DBhP path (module docstring has the full rationale):

- **Passage ids are flat `CHAPTER.VERSE`** (no skandha level), matching the
  house convention for standalone works (`gitagovinda.jsonl`).
- **Chapter boundaries come from the OPENING heading alone** — a closing
  colophon's wording is not uniform across Ignatjev's translations (some
  texts, e.g. Cīnācāra-tantra, never say «заканчивается» at all) — so it is
  never required to split a chapter. The heading itself has two forms: bare
  (`Глава первая`, the docx convention) or ordinal+ALL-CAPS-title on one line
  (`Глава третья ГАЯТРИ`, the PDF convention) — both recognised.
- **Endnotes are real Word footnotes** in the docx sources: pandoc's plain
  writer renders both the inline ref and the endnote text bracket-wrapped
  (`...его[1].` / `[1] 1.1(1). <text>`) — an exact `[N]` match, not the DBhP
  PDF's glued-digit superscript guess. PDF sources (e.g. Nirvāṇa-tantra) may
  simply have no endnote section — handled as zero found, not an error.
- Text extraction branches on file extension: `pandoc -f docx -t plain` or
  `pdftotext -enc UTF-8` (same form-feed normalisation as the DBhP path).

**Status: 18/~20 works ingested (H1438).** Wave A (5) + Wave B (5) + Wave C (2) + Wave D (6) landed.
Wave A tail (the 4 PDF tantras) plus the pilot's 2 works:

- **Cīnācāra-tantra** (docx, pilot): 5 ch, 225 verses, 154/168 endnotes
  attached — the long tail is verse-range note targets like `5.49(2)–50(1)`
  the endnote regex doesn't yet parse, gracefully merged into the preceding
  note's text rather than lost.
- **Nirvāṇa-tantra** (PDF, pilot): 15 ch, 821 verses, 0 endnotes (source has
  none).
- **Niruttara-tantra** (PDF): 15 ch, 674 verses, round-trip 674/674.
- **Guptasādhana-tantra** (PDF): 12 ch, 319 verses, round-trip 319/319.
- **Yoni-tantra** (PDF): 8 ch, 221 verses, round-trip 221/221 — ch.8's true
  colophon closes the translated work; the source PDF appends supplementary
  hymns quoted from OTHER named tantras after it (`meta.json` `provenance`
  notes this) — excluded, not part of Yoni-tantra itself.

All five registered in `Programdata/data.txt`; all five FTS5-searchable
(verified against a scratch `ingest.py` DB build, real hit counts per work).
`html_to_canonical.py` round-trip reproduces every emitted verse exactly
(100%, clear of the ≥99% bar) for all three Wave-A-tail works.

**Three parser hardening rounds this pass** (mirroring the DBhP path's own
six-round history — this generalized parser is a proven base, not a
zero-touch batch run):

1. **Chapter heading glued to its own first body sentence, no paragraph
   break** (Niruttara-tantra ch.5: `"Глава пятая Благословенная Богиня
   сказала: ..."` on one physical line) — `_CHAPTER_OPEN_RE` gained a `rest`
   group that keeps the trailing text as the new chapter's opening body line
   instead of silently dropping it (which had merged ch.5 into ch.4).
2. **An ALL-CAPS running section title glued onto the FRONT of a chapter
   heading** (Yoni-tantra ch.1: `"ЙОНИ-ТАНТРА. ПЕРЕВОД Глава первая"`) —
   `_CHAPTER_OPEN_RE` gained a `prefix` group. Both `prefix` and the
   pre-existing `title` group had to be scoped case-sensitive
   (`(?-i:...)`): under the pattern's overall `re.IGNORECASE`, an unscoped
   `[А-ЯЁ]` class also matches lowercase Cyrillic, so a mixed-case
   table-of-contents line satisfied the "ALL-CAPS" signal just as readily as
   a real title/prefix — this over-matched Niruttara-tantra's own ToC line
   and corrupted its chapter numbering before the scoping fix.
3. **Back-matter/appendix heading glued to its own first line of content, and
   an appendix's own later "Комментарий" section for ITS OWN citations**
   (Yoni-tantra: ch.8's true colophon is followed by `"ТЕКСТЫ ПО ПОЧИТАНИЮ
   ЙОНИ Созерцание йони. Оригинал ..."` — an appendix of hymns quoted from
   other named tantras — which itself contains an unrelated, later
   `"КОММЕНТАРИЙ"` heading for its own footnotes). `_BACKMATTER_RE` lost its
   end-of-line anchor (min run length raised to 7+ chars so a short in-text
   work-abbreviation like `"НТ (11.6)"` can never masquerade as a heading),
   and the endnote-block search is now bounded ABOVE by the backmatter
   boundary rather than running unbounded to EOF — otherwise the appendix's
   own notes heading was mistaken for this work's endnotes and dragged the
   body 140+ lines past the real chapter-8 boundary.

6 new regression tests added (16 total) in
[`test_ignatiev_book_units.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/test_ignatiev_book_units.py),
one per bug found; all previously-shipped works (Cīnācāra/Nirvāṇa-tantra)
byte-identical before/after each fix (regression-diffed against their
committed `.raw.jsonl`).

**Māyā-tantra: glued-digit front-end landed (H2377, Grok 4.5 `grok-4.5`).**
Page-local footnotes (DBhP-style digits glued to words + `N ch.v.` note
bodies at page bottoms) are stripped by
`--footnote-mode glued-digit` before the chapter walk. Result: **12 ch /
343 RU verses / 148 comments**, HTML→JSONL round-trip **343/343 (100%)**,
re-run stable. Design + before/after table:
[`docs/MAYA_TANTRA_GLUED_DIGIT_MODE_H2377.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/MAYA_TANTRA_GLUED_DIGIT_MODE_H2377.md).
`auto` stays conservative (`bracket`) so Wave-A committed counts are not
re-baselined; force `glued-digit` for Māyā-class PDFs.

### Wave B (docx tantras + upapurāṇas) — landed 01-08-2026

Executed as Grok 4.5 override dual-run of Sonnet-locked H1438 (residual
Sonnet compare handoff minted at close). Five works, all `ru_only`, all
registered in `Programdata/data.txt`, all HTML block-count round-trip ≥99%:

| Work | Source | Ch | Verses | Endnotes | Notes |
|---|---|---:|---:|---:|---|
| Nīlamata-purāṇa | docx | 1 | 410 | 0 | partial śl. 1–411; no chapter headings → implicit ch.1 |
| Adbhuta-rāmāyaṇa | docx | 6 | 308 | 0 | selected ch.17–20, 22–23; source order quirks preserved |
| Kulārṇava-tantra | 2× docx | 17 | 2049 | 1113 | multi-part continuous chapter numbers |
| Yoginī-tantra | docx + `.doc` | 19 | 1285 | 340 | ch.8–19 via OLE UTF-16 extract (antiword/Word COM absent) |
| Mahābhāgavata-purāṇa | 2× docx | 78 | 4232 | 265 | source lacks ch.36–37 and 56 headings; ch.55 renumbers mid-chapter |

**Three Wave-B parser hardenings** (3 new unit tests; 23 total in
[`test_ignatiev_book_units.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/test_ignatiev_book_units.py) —
corrected 06-08-2026, [H2076 compare memo](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/H2076_SONNET_WAVEB_DUAL_RUN_COMPARE.md); the "19" figure was a doc slip):

1. **ToC leader-dot reject** — `Глава восьмая ……… 48` is not a chapter open.
2. **Per-part multi-file parse** — each `--input` file is parsed alone, then
   records merge; part-1 endnotes can no longer leak into part-2 as fake
   `(N)` verse markers.
3. **Last-chapter ALL-CAPS title ≠ back-matter** — scan for `_BACKMATTER_RE`
   starts after the last chapter's own running title, otherwise Kulārṇava
   ch.8/17 and Mahābhāgavata ch.35/81 emptied to 0 verses.

Also: `.doc` OLE WordDocument UTF-16 fallback when antiword is missing;
`.txt` pre-extract input accepted; `build_corpus_html` flat-work skandha
fix (2-part `CHAPTER.VERSE` ids no longer misread as skandha).

**Reproducibility caveat (Sonnet dual-run, 06-08-2026 — full memo:
[H2076_SONNET_WAVEB_DUAL_RUN_COMPARE.md](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/H2076_SONNET_WAVEB_DUAL_RUN_COMPARE.md)):**
stage 1 depends on `pandoc`'s docx→plain-text output, and pandoc's paragraph
handling is **not pinned** anywhere in this repo. Ingested against pandoc
`3.9.0.2`. An independent re-run on the same pandoc version reproduced
Nīlamata / Kulārṇava / Yoginī byte-for-byte, but a **different pandoc
build** measurably diverged on two source-side edge cases already flagged
above — Adbhuta-rāmāyaṇa's out-of-order ch.23 verse numbering (off by 1
verse) and Mahābhāgavata's ch.55 mid-chapter renumber (off by 63 verses /
~1.5%, all inside the already-logged `id_collisions` set). The corpus
currently live is correct (it preserves both anomalies explicitly rather
than silently merging them); **any future re-ingestion of these two works
should re-verify verse counts against this table, not assume byte-identical
reproduction, until pandoc is pinned.**

### Wave C (in-DCS purāṇas + SA where keyed) — landed 07-08-2026 (H2353)

| Work | Source | Ch | Verses | Endnotes | SA | Notes |
|---|---|---:|---:|---:|---|---|
| Devīmāhātmya | `.doc` (OLE) | 13 | 595 | 0 | **497 matched** / 98 ru_only / 90 sa_orphan (GRETIL MarkP 81–93 → flat 1–13) | 13 empty bare-`(N)` after heading skipped; HTML round-trip 595/595 (100%) |
| Kālikā-purāṇa | 6-part `.doc`/`.docx` | 90 | 8137 | 3 | **none** (no keyed GRETIL/sanskritdocuments witness) | ch.62 recovered via OLE glued-ordinal peel; absurd high-N colophon drop; HTML round-trip 8137/8137 (100%) |

**Three Wave-C parser hardenings** (3 new unit tests; 31 total + 2 optional skips in
[`test_ignatiev_book_units.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/test_ignatiev_book_units.py)):

1. **OLE glued unit-ordinal peel** — `Глава шестьдесят втораяовно…` opens ch.62
   (tens-prefix alone is rejected).
2. **Colophon / absurd forward-jump drop** — body colophon with false
   `(1401-1464)` after real verse 158 is not a verse.
3. **Empty-verse emit filter** — bare `(N)` with blank body does not mint cards.

SA converter: [`gretil_markp_devimahatmya_to_canonical.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/gretil_markp_devimahatmya_to_canonical.py)
(source `sanskrit_src/mkp1-93u.htm`). Summary: `jsonl/wave_c_summary.json`.

### Wave D (fragments / selected — explicit partial provenance) — landed 07-08-2026 (H2376)

| Work | Source | Ch | Verses | Endnotes | SA | Notes |
|---|---|---:|---:|---:|---|---|
| Devī-purāṇa | docx | 1 | 18 | 0 | none | **ch.22 only** (`Из двадцать второй главы`); RT 18/18 (100%) |
| Liṅga-purāṇa | 2× PDF | 2 | 124 | 0 | none | **ch.17 + 29 only**; pdftotext absent → pypdf fallback; RT 124/124 (100%) |
| Padma-purāṇa | `.doc` (OLE) | 16 | 1039 | 0 | none | **Jālandhara tale only — NOT whole Padma**; RT 1038/1039 (99.9%) |
| Bhāgavata-purāṇa | RTF-as-`.doc` | 13 | 1176 | 0 | none | **partial** (sk.4 ch.2–5 + 14–21,23); prose, no `(N)` → paragraph units; RT 1176/1176 (100%) |
| Bṛhannīla-tantra | docx Избранное | 18 | 1387 | 1146 | none | **selected**; non-monotonic ch order; RT **1351/1387 (97.4%)** honest residue (36 endnote-adjacent passages re-keyed as `.commN` by `html_to_canonical`) |
| Śāktisaṅgama-tantra | docx Избранное | 28 | 1494 | 1 | none | **selected**; multi-khaṇḍa overlap → `id_collisions`; RT 1491/1494 (99.8%) |

**Four Wave-D parser/extract hardenings** (unit tests in
[`test_ignatiev_book_units.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/test_ignatiev_book_units.py);
35 passed + 3 optional skips):

1. **Excerpt heading** — `Из <ordinal gen> главы` (Devī ch.22) + genitive
   feminine ordinals in `ru_ordinals.py`.
2. **Trailing period on chapter open** — `ГЛАВА ВТОРАЯ.` (RTF/print).
3. **Digit chapter heads** — `ГЛАВА 14` (Bhāgavata partial).
4. **Extract front-ends** — pypdf PDF fallback when `pdftotext` missing;
   RTF-as-`.doc` via pandoc + cp1251 mojibake reverse; prose chapters without
   `(N)` markers fall back to paragraph units (`prose_paragraph_split_chapters`
   in the report).

Summary: [`jsonl/wave_d_summary.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/jsonl/wave_d_summary.json).
Corpus-manifest pin rebuilt in the same pass (H2351 discipline: append, do not
drop existing sources).

**Remaining** under H1438: Māyā-tantra → [H2377](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2377-Grok_SamudraManthanam_h1438-maya-tantra_07.08.26.md)
(if still open); Kāma-samūha / Kādambara / Прочее miscellany deferred.

_Dr. Mārcis Gasūns_
