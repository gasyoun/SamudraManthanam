# PDF → Corpus Ingestion Pipeline (house standard)

_Created: 10-07-2026 · Last updated: 10-07-2026_

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
# 1. parse one volume (pilot: a single skandha)
python ignatjev_pdf_to_canonical.py \
  --pdf "../../AdnrejIgnatjev/devibhagavata-purana/Девибхагавата-пурана. Том 1.pdf" \
  --output-dir jsonl --skandha-only 1
# 2. align (omit --sa for Russian-only)
python align_sanskrit.py --ru jsonl/devibhagavata-purana_s1.raw.jsonl \
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

## Pilot status & what's next

- ✅ **Skandha 1 (Vol 1) ingested** — Russian-only: 20 chapters, 1181 verses,
  429 comments; live in `Data/devibhagavata-purana-1.html`.
- ⏭ **Skandhas 2–12** — the parser extracts verses cleanly across all 6 volumes,
  but the endnote sequential-join desyncs on Vols 2/4/5 (comment counts 18/2/71
  vs hundreds expected); harden `parse_endnotes` per-volume before batch ingest.
- ⏭ **Sanskrit alignment** — blocked on a source decision: the full DBhP is
  **not on GRETIL** (only the Devigita fragment, skandha 7). Candidate:
  sanskritdocuments.org (12 per-skandha files, Devanagari+IAST, `ch.verse`
  numbering — no `DbhP_` markers). A human decides the source; the aligner is
  already source-agnostic and ready.

_Dr. Mārcis Gasūns_
