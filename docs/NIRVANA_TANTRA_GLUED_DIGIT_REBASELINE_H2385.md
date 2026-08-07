# Nirvāṇa-tantra glued-digit re-baseline (H2385)

_Created: 07-08-2026 · Last updated: 07-08-2026_

**Model:** Grok 4.5 (`grok-4.5`). **Handoff:** [H2385](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2385-Grok_SamudraManthanam_nirvana-glued-digit-rebaseline_07.08.26.md). **Front-end:** [H2377](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H2377-Grok_SamudraManthanam_h1438-maya-tantra-glued-digit_07.08.26.md) `--footnote-mode glued-digit`. **Prior count path:** [H2273](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/NIRVANA_TANTRA_VERSE_COUNT_DROP_H2273.md) (465 verses / 0 comments under bracket + H1829 debris absorb).

## Why re-baseline

H2377 measured that Nirvāṇa-tantra's PDF also carries **page-local** glued-digit footnotes (same convention as Māyā). The Wave-A / H2273 path never extracted them: note bodies stayed in chapter text and were collapsed by `_collapse_nonmonotonic_verses`, freezing `comment_count: 0` and under-counting addressable verses once high-N debris was absorbed.

## Before / after (same archive PDF, pymupdf extract)

| Metric | H2273 committed (bracket) | H2385 glued-digit |
|---|---:|---:|
| chapters | 15 | 15 |
| verse_count | 465 | **527** (+62) |
| comment_count | 0 | **212** |
| verse_gaps | 64 | **3** |
| id_collisions | `["9.1"]` | **none** |
| re-run stable | yes | yes |
| HTML→JSONL RU exact | — | **527/527 (100%)** |

### Residual gaps (after)

- `2: 18->20`, `14: 4->6`, `14: 34->36` — even-N skips; not the old 1↔2 oscillation class.

### Per-chapter RU counts (H2385)

| Ch | Verses | Ch | Verses |
|---:|---:|---:|---:|
| 1 | 30 | 9 | 25 |
| 2 | 21 | 10 | 65 |
| 3 | 48 | 11 | 45 |
| 4 | 22 | 12 | 13 |
| 5 | 43 | 13 | 83 |
| 6 | 13 | 14 | 42 |
| 7 | 22 | 15 | 42 |
| 8 | 13 | **Σ** | **527** |

Compared to H2273's printed-ceiling table (post-max labels): ch.1/3–7/9/12/15 match the old ceiling; ch.8/11/13 no longer carry inflated high-N note water-marks as verse labels (ch.8 30→13 addressable real verses with notes extracted).

## Reproduce

```sh
cd web/corpus_builder
python ignatiev_book_to_canonical.py \
  --input "../../archive_ignatiev_2026/Переводы с санскрита/Нирвана-тантра/nirvana-tantra.pdf" \
  --work-slug nirvana-tantra \
  --footnote-mode glued-digit \
  --output-dir jsonl
python align_sanskrit.py --ru jsonl/nirvana-tantra.raw.jsonl \
  --out jsonl/nirvana-tantra.jsonl --report jsonl/nirvana-tantra.alignment.json
python build_corpus_html.py --jsonl jsonl/nirvana-tantra.jsonl \
  --report jsonl/nirvana-tantra.report.json --meta nirvana-tantra.meta.json \
  --data-dir ../../Index/lib/x86_64-win64/Data \
  --data-txt ../../Index/lib/x86_64-win64/Programdata/data.txt \
  --slug nirvana-tantra
```

## Non-goals

- Re-baselining other Wave-A PDFs (Yoni/Niruttara/Guptasādhana) unless a human asks.
- Statistical SA alignment (still `ru_only`).
- Changing `auto` detector (stays `bracket` per H2377 Wave-A lock).

_Dr. Mārcis Gasūns_
