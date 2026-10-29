# RU-side annotation layer — build report (H6402, W9.2)

_Created: 29-10-2026_

What Wave 9 unit 9.2 ([H6402](https://github.com/gasyoun/Uprava/blob/main/handoffs/H6402-Opus_SamudraManthanam_nkrya-w9-2-ru-annotation-layer_10.10.26.md))
shipped: the Russian-side per-text annotation sidecar in the НКРЯ exporter.
Roadmap: [`docs/ROADMAP_NKRYA_PARALLEL_RUSCORPORA_2026_2027.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ROADMAP_NKRYA_PARALLEL_RUSCORPORA_2026_2027.md) §9.2.
Builds on H905 (`ru_morph.py`) and the W3 sanskritism package (H760).

## The artifact

`python nkrya_export.py --all-pilot --ru-annotate --out DIR` (or
`--all-ru` / `--showcase` / `--source`) writes `<slug>.ru_anno.tsv` beside
the para-XML/TMX/TSV triple — one row per Cyrillic token of **every
Russian-bearing group** (bilingual or not; the H906 `sa_units` lesson
applied to the RU side):

```
group_id  tok_index  surface  lemma  pos  case  number  lemma_src
```

`lemma_src` names each lemma's provenance — the layer's honesty column:

| value | meaning |
|---|---|
| `pymorphy` | tagger's own lemma (general vocabulary) |
| `sanskritizm` | W3 lexicon override, unambiguous candidate |
| `sanskritizm-amb` | W3 lexicon override, ambiguous set resolved by the deterministic sorted-first pick |
| `unknown` | no parse and no lexicon match — lemma = lowercased surface |

Bulk `.ru_anno.tsv` output is gitignored with the rest of the export
(`nkrya-parallel/.gitignore` `/export/*`; in-copyright RU running text).
Committed: the layer itself, its tests (validators), and this report
(counts + sample metadata only).

## Stack — pymorphy deterministic default, provenance recorded

The 9.1 verdict JSON (`reports/RU_SIDE_TAGGER_BENCHMARK*verdict*.json`,
[H6401](https://github.com/gasyoun/Uprava/blob/main/handoffs/H6401-Opus_SamudraManthanam_nkrya-benchmark-pymorphy-deeppavlov_10.10.26.md))
**does not exist yet** — 9.1 has not landed. The H6402 mission text
sanctions exactly this case: *pymorphy2 deterministic default when the
benchmark is undecided or its inputs are unavailable*. The estate's pymorphy
is **pymorphy3** (H905, `web/requirements.txt`): same OpenCorpora dictionary
family as the pymorphy2 the roadmap names, maintained.

`ru_annotate.resolve_stack()` re-reads the verdict at every run: when 9.1
lands and names a stack, the layer picks it up (DeepPavlov is attempted and,
if unimportable, falls back with the reason recorded). Nothing re-selects
silently: `export_report.json` carries `ru_anno_stack` +
`ru_anno_stack_src`, and the CLI prints them.

## The two overrides (the layer's reason to exist)

1. **Санскритизм-lexicon lemma override.** A token whose lowercased surface
   is a W3 paradigm-generated form, passing the extract.py trust filter
   (capitalized non-sentence-initial name, or a survivor of
   foreign-words/exception-list/`is_russian_word`), gets the LEMMA from the
   lexicon, not pymorphy's — the ВКР's core finding is that Russian
   lemmatizers break exactly here. POS is forced `NOUN` (the W3 pool is
   proper names + terms — nominal by construction; pymorphy's POS on these
   tokens is the named failure mode, e.g. Адхармахан → PRTS
   «адхармахать»). Case/number of the inflected surface are kept when the
   tagger parsed one, empty when it did not.
2. **Normalized name-index forms.** Override lemmas go through the W3
   index's own canonical merge (`merge_plural_singular_duplicates`:
   апсара/апсары → апсары), so the sidecar's lemmas agree with the committed
   proper-name index.

### The capitalized-«И» guard (found by the zero-empty-sides gate run)

First real-data run mis-tagged **642 tokens** in the Aranyakāṇḍa alone as
the pool lemma «и»/NOUN: poetic enjambment capitalizes «И вот…» after a line
break, and ВКР §3.3.1 stage 5's blanket capitalization exemption trusted it
(«и» is both a pool lemma and on Абрамович's loanword list; the exemption
bypasses both filters — and must keep doing so, because «Кали» is *also* on
that list and only the exemption rescues it). The discriminator: a
capitalized token pymorphy parses as a **closed function class**
(CONJ/PRCL/PREP/NPRO/INTJ/PRED) is never a proper name — those classes take
no loanword members. The guard is annotation-layer-only; the W3 index
pipeline is untouched. Regression test:
`test_ru_annotate_capitalized_conjunction_not_overridden`.

## Counts (the four pilots, 29-10-2026, run time ≈60 s)

| source | RU groups | tokens | overrides (amb) | unknown | empty sides | sha256₁₆ |
|---|---|---|---|---|---|---|
| 03_mahabharata-aranyakaparva | 2 033 | 199 570 | 12 266 (938) | 4 | 0 | `b1265e1ff2d86911` |
| 01_ramayana-balakanda | 2 265 | 38 206 | 3 138 (284) | 1 | 0 | `018ae9f64413c434` |
| 02_ramayana-ayodhyakanda | 4 292 | 72 060 | 4 199 (242) | 0 | 0 | `9765526352a047bd` |
| 03_ramayana-aranyakanda | 2 441 | 40 577 | 3 161 (371) | 1 | 0 | `c7bdac76df41b2ef` |

Top override lemmas (sample metadata — lemma, count): индра 384, бхарати
310, юдхиштхира 294, бхима 241, пандава 231, нала 214, рама 209, тиртха 195
(MBh III); рама 284, вишвамитра 218, дашаратхи 141, васиштхи 115, ганга 82,
рагху 80, индра 77, брахма 76 (Rām I). All name-shaped — the «и»-class
pollution is gone. The Rām kāṇḍas carry ~15 "pairs" whose RU side is the
upstream `{no rus data}` ingest sentinel; `ru_units` counts them as no
Russian side (see below).

## CI gates (all green)

`web/tests/test_nkrya_export.py`, hermetic + `-m corpus` conventions:

- **round-trip byte-stability** — two independent runs byte-identical, no
  BOM (hermetic fixture + each real pilot);
- **per-source coverage report** — `ru_anno_*` stats land in every
  `export_report.json`; the emitted rows' group set must equal `ru_units`
  (every Russian-bearing group, monolingual included);
- **zero empty sides** — `ru_anno_empty_side_groups == 0` (fixture +
  pilots);
- override semantics: Кали kept / кала not / адхармахан forced nominal /
  «И» not overridden / determinism.

## Open questions (not blockers)

- **`{no rus data}` inside bilingual pairs.** The sentinel (54 records in 6
  sources) also rides as the RU side of ~15 real "pairs" in the
  ayodhyakāṇḍa — classify()'s frozen H754/H821 semantics count and export
  it as a pair. The annotation layer refuses to annotate it (rightly);
  whether the pair exporter should treat it as `empty_side` is an H754-side
  question, deliberately not touched here (byte-stability of the frozen
  triple).
- **9.1 verdict swap-in.** When H6401 lands, re-run `--ru-annotate` over
  `--all-ru`; `resolve_stack()` picks the verdict stack up automatically and
  `ru_anno_stack_src` records it. The override layer is stack-independent
  (it corrects lemmas, not parses).
- **`sanskritizm-amb` volume** (242–938/source) is reported, not resolved —
  the ВКР's deeppavlov case-disambiguation path; same posture as W3.

## Files

- `web/corpus_builder/ru_annotate.py` — the layer (stack resolution,
  overrides, canonical name-index lemmas, closed-POS guard).
- `web/corpus_builder/nkrya_export.py` — `ru_units()`, `ru_anno_tsv()`,
  `--ru-annotate`, `NO_RUS_SENTINEL`, report stats.
- `web/tests/test_nkrya_export.py` — the H6402 gates (7 hermetic + 4 corpus).

_Dr. Mārcis Gasūns_
