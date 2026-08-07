# Māyā-tantra glued-digit footnote mode (H2377)

_Created: 07-08-2026 · Last updated: 07-08-2026_

**Mode name:** `glued-digit`  
**CLI:** `--footnote-mode glued-digit|bracket|auto`  
**Module:** [`web/corpus_builder/ignatiev_book_to_canonical.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/ignatiev_book_to_canonical.py)

## Problem

Māyā-tantra's PDF does **not** collect footnotes once after the last chapter.
Notes sit at the bottom of nearly every page (old press convention also used
by DBhP volumes):

- Inline refs are digits glued to Cyrillic words: `другую6`, `мир7`.
- Note bodies start `N ch.v(pada). text` (spaced) or `Nch.v(pada). text`
  when the space is lost (`61.1(1).` = fn 6 + `1.1(1).`).
- Optional ALL-CAPS `КОММЕНТАРИЙ` heading appears only rarely (once at the
  start of ch.1 in this PDF).

The generalized single-book parser only searched for a trailing
`Комментарий` block after the last chapter. Per-page note prose stayed in
every chapter body; `split_verses` treated note markers like `1.1(2)` as
verse boundaries → wild `verse_gaps` / `id_collisions` (1↔2 oscillation;
bogus high-N jumps).

## Design

### Front-end strip (before chapter walk)

1. Split extract on form-feed page markers (`\x0c` from `pdftotext` or the
   pymupdf fallback).
2. Per page, find the first **strong note-start** (or ALL-CAPS
   `КОММЕНТАРИЙ`), walk backward over note-continuation lines left from the
   previous page, and peel everything from that index to page end into the
   note stream.
3. Parse the note stream with a monotonic fn gate (DBhP-style gap tolerance)
   into `fn_map`.
4. Body (page tops only) proceeds through the existing chapter / `(N)` /
   H1829 collapse path, with **aggressive** scholarly-debris heuristics
   enabled so residual leaks (`[Там же: N]`, botanical Latin glosses) do not
   mint high-N false verses.
5. Inline linking uses DBhP glued-digit `link_footnotes_glued` (digits glued
   to letter/bracket/quote ends), not pandoc `[N]`.

### Mode selection

| Mode | Behaviour |
|---|---|
| `bracket` | Pre-H2377 path (pandoc `[N]` end-block). Default for `auto`. |
| `glued-digit` | Page-local strip + glued inline linking. |
| `auto` | **Conservative: always `bracket`.** Wave-A PDFs (Nirvāṇa, Yoni, …)
  also carry page-local notes whose committed counts were frozen under the
  old path; density-based auto would re-baseline them. Force
  `--footnote-mode glued-digit` for Māyā-class works. Density diagnostics:
  `glued_digit_signal(text)`. |

### Rejected alternatives

1. **Regex-only body cleanup without a mode** — would silently change Wave-A
   counts; fails the regression gate.
2. **Always-on glued strip for every PDF** — same regression; Nirvāṇa verse
   count jumps ~465→527 under full strip.
3. **Density-only auto** (pages_with_notes ≥ 20) — selects Nirvāṇa and Māyā
   alike; blocked until a Wave-A re-baseline handoff.
4. **Re-using DBhP multi-skandha path as-is** — DBhP ids are
   `SKANDHA.CHAPTER.VERSE` and skandha rollover is volume-specific; flat
   `CHAPTER.VERSE` single-book path is the right host for the front-end.

## Before / after (Māyā-tantra, pymupdf extract)

| Metric | bracket (defect) | glued-digit |
|---|---:|---:|
| chapters | 12 | 12 |
| verse_count | 295 | 343 |
| comment_count | 0 | 148 |
| verse_gaps | 51 | 16 |
| 1↔2 oscillation gaps | 31 | 0 |
| id_collisions | 1 (`3.20` source duplicate) | 1 (`3.20`) |
| re-run stable | yes | yes |
| HTML→JSONL round-trip (RU text) | — | **343/343 (100%)** |

### Sample false-splits fixed (debris verdict)

| # | Before (bracket) | After | Verdict |
|---|---|---|---|
| 1 | Note `7 1.1(2). небо…` minted restart verse near 1.1 | note → `comm` on 1.1 | **fixed** (false verse) |
| 2 | `61.1(1).` glued header read as body | fn 6 → endnote | **fixed** |
| 3 | Scholarly `[Там же: 72]` block as 4.26 | absorbed / stripped | **fixed** (debris) |
| 4 | Botanical `Ocimum sanctum` note as 4.52 | absorbed / stripped | **fixed** (debris) |
| 5 | ToC bare `Глава N` doubled chapter run (24 ch) | ToC window + empty-ghost drop → 12 ch | **fixed** (structure) |

Residual `verse_gaps` are mostly N→N+2 (likely pada/print skips or unstripped
residue); not the 1↔2 oscillation class. Collision `3.20` is two real verses
both printed `(20)` in ch.3 — letter-suffix disambiguation is correct.

## Reproduce

```sh
cd web/corpus_builder
python ignatiev_book_to_canonical.py \
  --input "../../archive_ignatiev_2026/Переводы с санскрита/Майя-тантра/Майя-тантра.pdf" \
  --work-slug maya-tantra \
  --footnote-mode glued-digit \
  --output-dir jsonl
python align_sanskrit.py --ru jsonl/maya-tantra.raw.jsonl \
  --out jsonl/maya-tantra.jsonl --report jsonl/maya-tantra.alignment.json
python build_corpus_html.py --jsonl jsonl/maya-tantra.jsonl \
  --report jsonl/maya-tantra.report.json --meta maya-tantra.meta.json \
  --data-dir ../../Index/lib/x86_64-win64/Data \
  --data-txt ../../Index/lib/x86_64-win64/Programdata/data.txt \
  --slug maya-tantra
```

PDF extract: `pdftotext -enc UTF-8` when on PATH; else pymupdf with
form-feeds between pages (same page-local contract).

## Tests

[`web/tests/test_ignatiev_book_units.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/test_ignatiev_book_units.py)
— H2377 block: strip, false-verse class, aggressive debris, ToC ghost
chapters, conservative `auto`.

_Dr. Mārcis Gasūns_
