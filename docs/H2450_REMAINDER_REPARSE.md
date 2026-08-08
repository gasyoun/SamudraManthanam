# H2450 residual reparse — free-bracket + auto census

_Created: 08-08-2026 · Last updated: 08-08-2026_

**Executor:** Grok 4.5 (`grok-4.5`)  
**Parent:** [H2450 prose apparatus](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2450_PROSE_COMMENTARY_APPARATUS.md)  
**Driver:** [`web/corpus_builder/h2450_remainder_reparse.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/h2450_remainder_reparse.py)  
**Summary:** [`jsonl/h2450_remainder_reparse_summary.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/jsonl/h2450_remainder_reparse_summary.json)

## What changed

1. **`bracket-free` mode** — free-form pandoc notes `[N] text…` without `ch.v` target; link by **first inline `[N]` use** in a verse body.
2. **`auto` chain** — structured bracket → prose `N.` (≥10 starts) → free `[N]` (≥3 starts). Prose floor 10 avoids Kādambara `N(pada).` debris.
3. **Colophon skip** — `ТАК ЗАКАНЧИВАЕТСЯ …` no longer steals `search_end` before `КОММЕНТАРИЙ` (MBH Ignatiev).
4. **Shared notes on books 16–18** — the volume’s single note block is attached to each of the three H2415 slugs so each book’s inline refs resolve.

## Results (`footnote-mode auto`)

| Work | Mode | Verses | Comments | Notes |
|---|---|---:|---:|---|
| `kama-samuha` | prose | 685 | **489** | 17 unlinked (no verse) |
| `kadambara-svikarana-karika` | bracket | 128 | **0** | residue: `N(pada).` + OLE noise |
| `mahabharata-mausalaparva-ignatiev` | bracket-free | 285 | **154** | shared 340-note block |
| `mahabharata-mahaprasthanikaparva-ignatiev` | bracket-free | 110 | **55** | shared block |
| `mahabharata-svargarohanikaparva-ignatiev` | bracket-free | 319 | **127** | shared block |
| `yoni-puja-texts` | bracket-free | 16 | **13** | 13 unlinked (no body ref) |
| `bhagavati-manasa-puja-stotra` | bracket | 69 | **0** | residue: bullet `ПРИМЕЧАНИЯ` |

**MBH union:** 154+55+127 = **336 / 340** notes linked across the triple (per-book unlinked lists are the notes for other books).

## Residues (not this front-end)

- **Kādambara** — `1(1). gloss` grammar + OLE hyperlink shatter; needs a dedicated parser.
- **Bhagavatī-mānasa** — unnumbered `-` glossary lines under `ПРИМЕЧАНИЯ`.

## Reproduce

```sh
python web/corpus_builder/h2450_remainder_reparse.py
# unit tests
cd web && PYTHONPATH=. python -m pytest tests/test_ignatiev_book_units.py -q
```

_Dr. Mārcis Gasūns_
