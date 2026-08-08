# H2449 — Ignatiev preface + glossary/bibliography layers census

_Created: 08-08-2026 · Last updated: 08-08-2026_

**Handoff:** [H2449-Grok_SamudraManthanam_h2415-ignatiev-backmatter-glossaries_08.08.26](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2449-Grok_SamudraManthanam_h2415-ignatiev-backmatter-glossaries_08.08.26.md)  
**Executor:** Grok 4.5 (`grok-4.5`)  
**Parent:** [H2415](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2415-Grok_SamudraManthanam_ignatiev-archive-remainder-ingest_07.08.26.md) (verse bodies only; front/back-matter deliberately cut)

## Goal

Register Ignatiev **prefaces**, **glossaries**, **bibliographies/sources**, and **about-author** blocks that H2415 left outside the verse pipeline as searchable corpus layers in `Programdata/data.txt`.

Sibling residual (prose `N. Источник:` commentary): [H2450](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2450-Grok_SamudraManthanam_h2415-ignatiev-prose-commentary-layer_08.08.26.md) — **not** this pass.

## Gate

Layer text RT ≥99% (HTML→JSONL for prose; line match for dictionary `.txt`). Latin accent-only folds from `html_to_canonical` (`littérature`→`litterature`) count as soft matches with residue log; emitted HTML keeps the accented form.

## Registered layers (17)

| Parent | Layer slug | Kind | Records | Artifact | RT % |
|---|---|---|---:|---|---:|
| kama-samuha | `kama-samuha-preface` | preface | 86 | `.html` | 100 |
| kama-samuha | `kama-samuha-slovar-imen` | glossary | 34 | `.txt` | 100 |
| kama-samuha | `kama-samuha-slovar-predmetov` | glossary | 21 | `.txt` | 100 |
| kama-samuha | `kama-samuha-slovar-toponimov` | glossary | 19 | `.txt` | 100 |
| kama-samuha | `kama-samuha-slovar-flory` | glossary | 27 | `.txt` | 100 |
| kama-samuha | `kama-samuha-istochniki` | bibliography | 21 | `.html` | 100 |
| kama-samuha | `kama-samuha-antologii` | bibliography | 4 | `.html` | 100 |
| kama-samuha | `kama-samuha-literatura` | bibliography | 81 | `.html` | 100 |
| kama-samuha | `kama-samuha-ob-avtore` | about_author | 6 | `.html` | 100 |
| kadambara-svikarana-karika | `…-preface` | preface | 22 | `.html` | 100 |
| kadambara-svikarana-karika | `…-literatura` | bibliography | 42 | `.html` | 100* |
| kadambara-svikarana-karika | `…-ob-avtore` | about_author | 11 | `.html` | 100 |
| mahabharata-ignatiev-xvi-xviii | `…-preface` | preface | 18 | `.html` | 100 |
| mahabharata-ignatiev-xvi-xviii | `…-slovar-imen` | glossary | 190 | `.txt` | 100 |
| mahabharata-ignatiev-xvi-xviii | `…-slovar-predmetov` | glossary | 66 | `.txt` | 100 |
| mahabharata-ignatiev-xvi-xviii | `…-literatura` | bibliography | 50 | `.html` | 100 |
| mahabharata-ignatiev-xvi-xviii | `…-ob-avtore` | about_author | 2 | `.html` | 100 |

\* 41 hard + 1 soft Latin-accent fold (`Tāntrikābhidhānakośa 2000` entry); HTML artifact has `littérature`.

**Totals:** 17 layers, **700** records (86+34+21+19+27+21+4+81+6 + 22+42+11 + 18+190+66+50+2).

Corpus-manifest pin rebuilt: **230** sources / **723 277** records (`bundle_version` 2026.08).

MBH XVI–XVIII front/back matter is shared across the three verse works registered in H2415; layers use volume slug `mahabharata-ignatiev-xvi-xviii-*` so the three parva HTML files stay verse-only.

## Deliberate skips

| Parent | Reason |
|---|---|
| `yoni-puja-texts` | No `ПРЕДИСЛОВИЕ` / `СЛОВАРЬ` / `ЛИТЕРАТУРА` / `ОБ АВТОРЕ` sections |
| `bhagavati-manasa-puja-stotra` | Only `ПРИМЕЧАНИЯ` (notes apparatus → H2450), no glossary/preface/biblio |
| Prose commentary `N. Источник:` after `КОММЕНТАРИЙ` | **H2450** |

## Implementation

| Piece | Path |
|---|---|
| Parser | [`web/corpus_builder/ignatiev_backmatter.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/ignatiev_backmatter.py) |
| Driver | [`web/corpus_builder/h2449_backmatter_ingest.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/h2449_backmatter_ingest.py) |
| Unit tests | [`web/tests/test_ignatiev_backmatter.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/test_ignatiev_backmatter.py) |
| Summary JSON | [`web/corpus_builder/jsonl/wave_h2449_backmatter_summary.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/jsonl/wave_h2449_backmatter_summary.json) |

**Shapes:**

* glossary → `structure=dictionary`, `seg=head`, `passage=eN`, desktop `.txt` (Dic_Apte-style one entry/line) + `.no_tags`
* preface / bibliography / about → `structure=prose`, `seg=ru`, `passage=1.N`, desktop `.html` via `build_corpus_html.render_document`

**OLE hardenings:** strip `HYPERLINK "…"` fields; cut about-author tails at binary-junk runs (Kādambara `.doc`).

## Reproduce

```sh
# requires local gitignored archive_ignatiev_2026/
python web/corpus_builder/h2449_backmatter_ingest.py \
  --archive-root "path/to/archive_ignatiev_2026/Переводы с санскрита"

cd web && PYTHONPATH=. python -m pytest tests/test_ignatiev_backmatter.py -q
```

_Dr. Mārcis Gasūns_
