# H2450 — Prose commentary apparatus (`N. …` / `N. Источник:`)

_Created: 08-08-2026 · Last updated: 08-08-2026_

**Executor:** Grok 4.5 (`grok-4.5`)  
**Handoff:** [H2450](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2450-Grok_SamudraManthanam_h2415-ignatiev-prose-commentary-layer_08.08.26.md)  
**Parent:** [H2415 remainder census](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2415_IGNATIEV_ARCHIVE_REMAINDER_CENSUS.md)  
**CLI:** `--footnote-mode prose` on [`ignatiev_book_to_canonical.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/ignatiev_book_to_canonical.py)

## Problem

H2415 registered remainder works with honest `comment_count=0`. Their
`КОММЕНТАРИЙ` section is **not** pandoc bracket endnotes (`[N] ch.v(pada).`)
and **not** page-local glued-digit notes (H2377). It is print-style numbered
prose, e.g.:

```
109. Источник: комментарий к «Куттани-мате» (147).
```

The verse pipeline already cut the body at `КОММЕНТАРИЙ`; this handoff adds a
**third** front-end that ingests that apparatus.

## Design decisions (resolved in-session)

| Question | Ruling | Evidence |
|---|---|---|
| Link key | **note number == verse number** within the chapter that emitted that verse | Kāma-samūha notes 1…747 track verse labels; no `к шлоке N` markers in the pilot |
| Multi-line body | Continue until next accepted `^\d+\.\s+\S` start | Sample note 1 spans ~14 physical lines |
| False starts | Reject when previous non-empty line ends with `№` / `к №` / `коммент. к №` | Line-wrap of `см. коммент. к №\n580. …` must not mint note 580 |
| Gap / order | Accept only strictly increasing note numbers with gap ≤ 20 | Real gaps are 1–8; larger jumps are wrap debris |
| Unlinked residue | Exact or range-cover match only — **never** nearest-guess | 17 notes with no emitted verse stay in `unlinked_prose_notes` |
| ALL-CAPS `КОММЕНТАРИЙ` | Skip notes-head lines in the back-matter scan so the note block is collected | `_NOTES_HEAD_RE` ∩ `_BACKMATTER_RE` both matched; previously notes_start was never set |

## Modes

| `--footnote-mode` | Behaviour |
|---|---|
| `prose` | Always parse the trailing note block with `parse_prose_endnotes` |
| `auto` | Bracket first; if zero bracket notes and ≥3 prose starts → upgrade to `prose` |
| `bracket` | No upgrade (Wave-A count lock) |
| `glued-digit` | Unchanged (H2377) |

## Pilot — Kāma-samūha

| Metric | Value |
|---:|---:|
| Verses | **685** (H2415 baseline stable) |
| Prose notes parsed | 506 |
| Comments linked | **489** |
| Unlinked residue | **17** |
| HTML→JSONL verse RT | **100%** |
| Comment-text RT (number prefix stripped) | **100%** |

Machine artifact: [`web/corpus_builder/jsonl/h2450_kama_samuha_prose_pilot.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/jsonl/h2450_kama_samuha_prose_pilot.json).

Reproduce:

```sh
python web/corpus_builder/h2450_prose_commentary_pilot.py
# unit tests
cd web && PYTHONPATH=. python -m pytest tests/test_ignatiev_book_units.py -q -k prose
```

## HTML comment ids

`build_corpus_html.py` now emits `comment_{ch}_{v}_{fn}` when `annotates` is
`ch.v…`, so `html_to_canonical` recovers the verse target. Legacy `comment_{fn}`
remains the fallback when `annotates` is missing.

## Generalization plan (not this PR)

1. Re-parse other H2415 remainder works with `footnote-mode auto` (upgrade when
   applicable).
2. **Kādambara** uses a different grammar (`N(pada).` + OLE hyperlink debris) —
   separate residual, not this mode.
3. MBH 16–18 shared endnote volume: census prose vs bracket before bulk re-emit.
4. Do **not** re-baseline Wave A–D glued-digit / bracket works unless the same
   `N.` grammar appears free.

## Non-goals (unchanged)

- Glossary / bibliography layers → [H2449](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2449-Grok_SamudraManthanam_h2415-ignatiev-backmatter-glossaries_08.08.26.md)
- Inventing SA alignment
- Human gold adjudication of every note

_Dr. Mārcis Gasūns_
