# Chronology & Works index

Two reader-facing pages that classify the parallel Sanskrit–Russian corpus by
date, after DharmaMitra's
[sanskrit-dating chronology](https://dharmamitra.github.io/sanskrit-dating/sanskrit_chronology_interactive.html):

| Page | Route | What it shows |
|---|---|---|
| **Хронология** | [`/chronology`](../web/app/routers/chronology.py) | A BCE→CE period-lane scatter + sortable table of every *datable* text. |
| **Тексты** (works index) | [`/works`](../web/app/routers/works.py) | Every work, grouped by period, with a **size 1–10**; merged works beside separate parts. |

Both follow the same two-surface split as the search page — a JSON API plus a
Jinja page that fetches it — and both read a committed JSON data layer (read
once, cached in-process; a rebuild needs an app restart). A missing data file
fails soft to `503` so the rest of the app keeps serving.

## Data lineage (no dates are re-derived)

```
VisualDCS chronology (dcs_scatter.json + dcs_genres.json)
        │   crosswalk by title  (build_chronology.py)
        ▼
corpus_builder/chronology/texts_chronology.json   ← dates + period buckets
        │   + Sanskrit volume from jsonl/*.jsonl   (build_works_index.py)
        ▼
corpus_builder/works_index/works_index.json       ← size 1–10 + parts
```

Each chronology row carries its own DCS date, inherits its period bucket's date,
or (author-datable medieval works) a flagged scholarly date — never a fresh
guess. The works index **inherits** those dates verbatim and only *adds* size.

## Builders

### `corpus_builder/chronology/build_chronology.py`
Crosswalks the corpus onto the VisualDCS dates → `texts_chronology.json`
(`periods` + `texts`, where each text has `date_ce`, `period`, `method`,
`confidence`, `members`). See the module docstring for the `method` taxonomy
(`dcs-exact` / `dcs-bucket` / `manual` / `n/a`).

### `corpus_builder/works_index/build_works_index.py`
Keeps only the `parallel-ru` corpus (the works on samskrtam.ru/parallel-corpus)
and enriches each with a size and its parts. Run from `web/`:

```sh
python corpus_builder/works_index/build_works_index.py
```

Emits `works_index.json` (the data layer) and `works_index_report.md` (an audit
table). Reading ~530 MB of `jsonl/` takes ~1 min; it's a one-time build,
committed to git.

## Size 1–10 — methodology

- **Metric:** the number of Sanskrit characters in a work — the sum of
  `len(text)` over its `lang == "sa"` segments across `corpus_builder/jsonl/`.
- **Scale:** `log10`, because the corpus spans five orders of magnitude (a
  one-line Upaniṣad to the Mahābhārata); a linear scale would flatten everything
  below the epics to 1.
- **Domain:** the smallest literary *part* (→ 1) to the largest whole literary
  *work*, the Mahābhārata (→ 10). Anchoring on the **literary** works keeps the
  epics at the top of the scale.
- **Parts and works share one scale,** so a part always reads as smaller than
  its parent (a single parvan < the whole Mahābhārata).

### Three deliberate edge-case calls
1. **Reference dictionaries clamp at 10.** The Monier-Williams dictionary holds
   more Sanskrit than the Mahābhārata; rather than let it set the ceiling and
   push the literature down, works above the literary max clamp at 10.
2. **Russian-only studies are unsized (`—`).** A few modern studies/retellings
   (e.g. `Mify_*`, `Илиада_Гнедич`) contain no Sanskrit — they are not Sanskrit
   texts to measure, so they show `—` rather than being sized by their Russian
   character count.
3. **Translation-only primaries can be unsized.** A handful of dated primary
   works are present only in Russian translation in this corpus (e.g.
   `Viṣṇupurāṇa`) — they keep their date but show `—` for size.

## The two views (merged ⇄ split)

The chronology crosswalk already lists a work's `members` (Mahābhārata → its 18
parvans, Ṛgveda → its 10 maṇḍalas, the Gītā → its 11 translations). The page
renders both at once, side by side:

- **Left — Произведения:** one row per work; a multi-part work's size is the
  log of its *summed* Sanskrit volume.
- **Right — Части:** every member as its own row, inheriting the work's
  period/date and timeline anchor, with its own independently-computed size.

## Links

- **Title → live reading page:** `/sources/{slug}`. The builder's slug rule is a
  byte-for-byte copy of [`app/services/slug.py`](../web/app/services/slug.py)
  (duplicated, not imported, so the builder runs without the app package);
  `tests/test_works_index.py` guards that parity.
- **Size badge (◷) → timeline:** `/chronology?focus={work-slug}`. The chronology
  page scrolls the matching table row into view and flashes it on arrival.

## Tests

`web/tests/test_works_index.py` — slug parity, `log_scale` boundaries
(null/1/10/clamp/log-midpoint), `part_label`, and route + data-integrity checks
(`size ∈ {null} ∪ [1,10]`, declared counts match the payload). Run with the rest
of the hermetic suite:

```sh
cd web; $env:PYTHONPATH="."; python -m pytest -m "not corpus"
```
