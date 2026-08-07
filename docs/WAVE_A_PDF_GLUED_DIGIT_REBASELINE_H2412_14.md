# Wave-A PDF glued-digit re-baseline (H2412–H2414)

_Created: 07-08-2026 · Last updated: 07-08-2026_

**Model:** Grok 4.5 (`grok-4.5`). **Front-end:** [H2377](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H2377-Grok_SamudraManthanam_h1438-maya-tantra-glued-digit_07.08.26.md) `--footnote-mode glued-digit`. **Siblings already done:** Māyā H2377 · Nirvāṇa H2385.

## Census (all registered Ignatiev works)

Measured 19 committed works under `archive_ignatiev_2026/Переводы с санскрита/` + `web/corpus_builder/jsonl/*.report.json`.

| Outcome | Works |
|---|---|
| **Already glued-digit pin** | maya-tantra, nirvana-tantra |
| **REBASELINE (this pass)** | yoni-tantra, niruttara-tantra, guptasadhana-tantra |
| **Skip — docx/bracket correct** | chinachara, nilamata, adbhuta, kularnava, yogini, mahabhagavata, kalika, brihannila, shaktisangama, devi-purana, padma, bhagavata |
| **Skip — PDF no comment gain** | linga-purana, devimahatmya (glued does not extract a useful note set) |

docx works **must stay on `bracket`**: forcing glued-digit drops endnotes (e.g. chinachara 154→0, kularnava 1113→0).

## Before / after (this PR)

| Work | Before v/c | After v/c | gaps | RT | stable |
|---|---:|---:|---:|---:|---|
| yoni-tantra | 221 / 0 | **221 / 192** | 0 | **100%** | yes |
| niruttara-tantra | 674 / 0 | **676 / 322** | 3 | **99.9%** (675/676) | yes |
| guptasadhana-tantra | 319 / 0 | **319 / 368** | 1 | **100%** | yes |

## Reproduce

```sh
cd web/corpus_builder
python ignatiev_book_to_canonical.py --input "<archive PDF>" \
  --work-slug <slug> --footnote-mode glued-digit --output-dir jsonl
# then align_sanskrit (ru_only) + build_corpus_html --slug <slug>
```

## Residual handoff

Not yet in `data.txt` from the archive: Kāma-samūha, Kādambara-svīkaraṇa-kārikā, Mahābhārata excerpt, Прочее → **H2415**.

_Dr. Mārcis Gasūns_
