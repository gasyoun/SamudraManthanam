---
paper_id: A41
title: "Samudra Manthanam: A Markup-Aligned Sanskrit–Russian Parallel Corpus of 148 Sources"
status: draft (skeleton, 2/5) — scaffolded 2026-06-26
readiness: 2/5
venue: "LREC-COLING (parallel-corpus) / eLex / JOHD (Journal of Open Humanities Data)"
author: "**Mārcis Gasūns**, independent scholar ([ORCID 0000-0003-4513-884X](https://orcid.org/0000-0003-4513-884X)), gasyoun@ya.ru"
data_source: "web/corpus_builder/jsonl/ (148 JSONL files, 574,939 segment records); web/corpus_builder/conversion_report.json (canonical counts); docs/ALIGNMENT_SPEC.md (alignment model); docs/TAG_CENSUS.md (structural inventory); web/corpus_builder/chronology/texts_chronology.json (date crosswalk)"
---

# Samudra Manthanam: A Markup-Aligned Sanskrit–Russian Parallel Corpus of 148 Sources

> **Draft status (2026-06-26).** Manuscript skeleton built directly on the converted
> corpus and its design specs. Every numerical claim below is transcribed from the
> canonical [`web/corpus_builder/conversion_report.json`](../web/corpus_builder/conversion_report.json)
> and re-verified against the 148 committed JSONL files and
> [`docs/ALIGNMENT_SPEC.md`](../docs/ALIGNMENT_SPEC.md). **Open before submission:**
> (1) write §2 Related work; (2) finalise byline + ORCID; (3) settle the
> RU-translation copyright triage that decides what ships as text vs. as index-only
> (a [@DO] human gate, see §8 / Limitations); (4) mint a Zenodo DOI and complete the
> data-availability statement; (5) flesh out the diachronic Bhagavadgītā register
> demonstration (§5.4) — the slug-derived translator dates (1788 / 1909 / 1914 / 20th–21st c.)
> are real but the full per-edition date/translator/rights table is a **TODO**. The
> "1:1 verse pairs" headline is **78,219** (the [`ALIGNMENT_SPEC.md`](../docs/ALIGNMENT_SPEC.md)
> §0 Tier-1 figure measured over the verse sources); a live re-count of the current
> JSONL gives **78,139** clean both-sides-present groups — the ~80-pair gap (exactly
> the Sanskrit-only blocks) is reconciled in §4.2 and must be stated, not smoothed over.

## Abstract

We present **Samudra Manthanam** ("the churning of the ocean"), a Sanskrit–Russian
parallel corpus assembled from **148 digitised sources** and released as a uniform,
segment-addressable JSONL layer of **574,939 records**. Unlike most parallel corpora,
whose sentence pairs are produced by a statistical or neural aligner and carry an
estimated alignment probability, this corpus is **markup-aligned**: in the source
editions the Sanskrit verse and its Russian translation were already interleaved by
the human editors as sibling blocks inside one citation unit. Recovering the bilingual
pairing is therefore a **deterministic markup-extraction problem, not an inference
problem** — no statistical aligner, heuristic, or embedding similarity is used or
needed. From the 119 verse sources this yields **78,219 clean 1:1 verse pairs**
(both the Sanskrit and the Russian side present and non-empty), alongside **10,145**
first-class monolingual (Russian-only) segments that are flagged rather than discarded,
and a long tail of **commentary** segments linked to their host verses. The remaining
sources are **15 bilingual dictionaries** (321,672 head entries) and **14 prose works**
(45,037 body segments), kept in the same schema but outside the verse-pair count. Each
segment carries its canonical passage ID, transliteration in both IAST and SLP1 (for
Sanskrit), an explicit `structure` class, and a per-segment `seg` role, so that
confidence, monolinguality, and commentary status are queryable fields rather than
buried assumptions. We add a **chronology crosswalk** that maps each text onto
VisualDCS period dates without re-deriving them, and we use the corpus's 11 Russian
Bhagavadgītā translations (1788 → present) as a worked **diachronic register
demonstration**. The contribution is a reproducible, FAIR-leaning data descriptor:
the artefact, its extraction method, its honest edge-case accounting, and the path
from these data to downstream Sanskrit–Russian NLP — not a new alignment algorithm.

## 1. Introduction

Sanskrit is comparatively rich in *English* digital resources and comparatively poor
in machine-readable *Russian* ones, despite a deep and continuous Russian indological
tradition (Kossovich, Smirnov, Sementsov, Erman, and others). The texts exist — many
nineteenth- and twentieth-century Russian translations of the Veda, the epics, the
Upaniṣads, the kāvya, and the philosophical śāstra were digitised for the
samskrtam.ru reading environment — but they existed as **per-source HTML reading
pages**, not as a queryable, segment-addressable parallel corpus. This paper describes
the artefact that results from converting those pages into a single uniform layer, and
argues that the way the conversion was done is itself the methodological point.

The central observation, formalised in [`docs/ALIGNMENT_SPEC.md`](../docs/ALIGNMENT_SPEC.md)
§0, is that **the alignment already exists in the markup**. When the editors built the
reading HTML, they placed each Sanskrit verse and its Russian translation as sibling
`div`s inside one citation block, hand-aligned at the verse (or atomic-range) level.
A parallel-corpus builder who treats this as a sentence-alignment task would discard
ground truth and re-introduce error. We therefore frame extraction as a markup-faithful
operation whose correctness is checked by a **regression oracle** ("did we extract the
existing pairing faithfully?"), not by scoring a guesser.

Our claims:

1. **Markup-faithful recovery.** The bilingual pairing is read straight out of the
   source structure; the 78,219 clean 1:1 verse pairs are extracted, not inferred,
   and the n:m problem is pre-solved by the source's own range-merging.
2. **Honest edge-case accounting.** Monolingual (Russian-only) content is a
   first-class, *expected* state with a per-segment flag, not an alignment failure;
   its 10,145 segments are itemised and bounded, dominated by two whole
   translation-only texts.
3. **A FAIR-leaning descriptor, not an algorithm.** The deliverable is the corpus, its
   schema, its chronology crosswalk, and its reproducibility story — positioned for
   reuse in Sanskrit–Russian retrieval, lexicography, and diachronic translation study.

## 2. Related work  *(TODO — to be written)*

Position against: (a) **parallel-corpus construction and sentence alignment** — the
standard pipeline (Gale–Church length-based, Hunalign, Bleualign, Vecalign and
LASER/LaBSE-embedding aligners) against which this corpus's *no-aligner* stance is the
contrast; (b) **markup-/structure-derived bitext** — TEI-parallel and document-structure
exploitation, where pairing is read from layout rather than estimated; (c) **Sanskrit
NLP resources and corpora** — the Digital Corpus of Sanskrit (DCS), GRETIL, the
Sanskrit Library, and the Cologne Digital Sanskrit Dictionaries — and the comparative
scarcity of Sanskrit–*Russian* parallel data specifically; (d) **data-descriptor /
FAIR-data venues and norms** (JOHD, LREC-COLING resource track, the FAIR principles).
The novelty claim to land crisply: a **markup-aligned Sanskrit–Russian parallel corpus
at 148-source scale with per-segment confidence/monolingual flags and a chronology
crosswalk** — a *resource and method-of-construction* contribution, **not** a new
aligner. *(Prior-art check before writing: confirm the DCS / GRETIL / Sanskrit Library
citations and whether any prior Sanskrit–Russian parallel set exists; cite, do not
re-derive.)*

## 3. Data and method

### 3.1 Sources and structural classes
The corpus is built from **148 sources** (the canonical count in
[`conversion_report.json`](../web/corpus_builder/conversion_report.json):
`total_sources: 148`, `total_records: 574939`). A structural inventory
([`docs/TAG_CENSUS.md`](../docs/TAG_CENSUS.md)) and a downstream backfill assign every
source one of three `structure` classes; the **final converter classification** is:

| `structure` | sources | segment records | dominant `seg` role |
|---|--:|--:|---|
| **verse** | 119 | 208,230 | `sa` / `ru` / `comm{n}` |
| **dictionary** | 15 | 321,672 | `head` |
| **prose** | 14 | 45,037 | `body` |
| **total** | **148** | **574,939** | |

*(Note for the methods text: the early heuristic tag-census in
[`TAG_CENSUS.md`](../docs/TAG_CENSUS.md) reports a provisional 66 verse / 15 dictionary /
67 prose split; the table above is the **final** converter/backfill classification
recorded in the conversion report and [`.ai_state.md`](../.ai_state.md). The discrepancy
is the heuristic-vs-final reclassification and must be stated, not hidden.)*

The verse sources span the Ṛgveda and Atharvaveda, the full Mahābhārata (18 parvans)
and three Rāmāyaṇa kāṇḍas, ~30 Upaniṣads, the classical kāvya (Meghadūta,
Kumārasambhava, Gītagovinda, Amaruśataka, …), the dharma- and yoga-śāstra
(Manusmṛti, the Yogasūtra with multiple commentaries), and **11 Russian translations of
the Bhagavadgītā** plus three Gītā commentaries. The 15 dictionaries are
Sanskrit–Russian and Russian-indological reference works (Kochergina, Kossovich,
Smirnov, the Grintser glossaries, etc.); the 14 prose works are translations and
scholarly apparatus (Mahābhārata commentary and indices, Gnedich's Iliad as a
register foil, Biruni, the Viṣṇu Purāṇa).

### 3.2 The decisive finding: alignment is extraction, not inference
In the source HTML the Sanskrit and its Russian translation are **already interleaved
as sibling blocks inside one citation block**. The converter
([`web/corpus_builder/html_to_canonical.py`](../web/corpus_builder/html_to_canonical.py))
reads the pairing directly: each citation block yields one **alignment group** keyed by
its canonical passage (`{work}:{passage}`), whose members are the `#sa`, `#ru`, and any
`#comm{n}` segments sharing that key. No statistical aligner is run. The apparent n:m
case is **pre-solved by the source**: where a Russian block spans several Sanskrit
verses, the editors emitted a single range-keyed block (e.g. `01_rigveda:65.1-2`),
which the scheme treats as one atomic 1:1 group rather than splitting (ALIGNMENT_SPEC
§1.1).

### 3.3 Segment schema and queryable flags
Each JSONL record is one segment. Verified fields (from the live JSONL) include:
`id` (`{work}:{passage}#{seg}`), `work`, `passage`, `seg` (`sa` | `ru` | `comm{n}` |
`head` | `body`), `group`, `lang`, `script`, `text`, `html`, `slp1` (SLP1 for Sanskrit),
`structure`, `chapter`, `seq`, and `deleted`. Dictionary `head` segments additionally
carry a `forms` object. Because `structure`, `seg`, and group membership are explicit,
the three properties a consumer cares about — **is this a clean bilingual pair, is this
monolingual, is this commentary** — are *fields*, recoverable by query rather than by
re-parsing.

### 3.4 Cardinality and monolingual handling
Cardinality is computed **per block** from which sides are non-empty (ALIGNMENT_SPEC §2):
`1:1` (`markup`, both present), `0:1` (`monolingual`, Russian only), `1:0`
(`monolingual`, Sanskrit only). Monolingual is a first-class state, not an error. The
10,145 Russian-only segments are dominated by two **whole translation-only texts** —
`buddhacharita-balmont` (8,852 blocks; Balmont rendered Aśvaghoṣa from Arnold's English,
not the Sanskrit) and `mify-drind` (1,172) — together ≈10,024 of the 10,145, with the
rest stray in-text interpolations and one partially parallel text
(`vedanga_jyotisha`, ~59% Russian-only). Cross-source alignment of these to an external
Sanskrit Buddhacarita is explicitly **out of scope** (it would be inference, the thing
the corpus deliberately avoids).

### 3.5 Reproducibility and validation
Extraction fidelity is enforced by a gold set of ~25 hand-verified groups spanning every
shape (clean 1:1, atomic range, refrain, monolingual `0:1`, partial-parallel,
commentary-bearing, nav heading) plus CI validation gates (group completeness,
cardinality correctness, no-phantom-pairing, gold-set-green, reader-toggle parity;
ALIGNMENT_SPEC §§6–7). The converter run reports **0 records needing review**
(`needs_review: 0` summed across all 148 sources) and **574,939 unique IDs** with 25
correctly letter-suffixed duplicate-passage records.

### 3.6 Chronology crosswalk
[`web/corpus_builder/chronology/texts_chronology.json`](../web/corpus_builder/chronology/texts_chronology.json)
maps each text onto **VisualDCS** period dates **without re-deriving them**: `dcs-exact`
= the text's own DCS date, `dcs-bucket` = its period-bucket date, `manual` = an
author-datable medieval work (flagged). For the 86 `parallel-ru` texts the method
breaks down as `dcs-exact` (92 across both corpora), `dcs-bucket` (27), `manual` (11),
`n/a` (dictionaries / undatable). The same file also crosswalks 848 `wisdomlib-en`
texts (a separate English corpus, out of scope here but sharing the date spine).

## 4. Results

*All numbers below are verified against [`conversion_report.json`](../web/corpus_builder/conversion_report.json)
and a live re-count of the 148 JSONL files on 2026-06-26.*

### 4.1 Corpus scale and composition
- **148 sources**, **574,939 segment records**.
- Structure split: **119 verse / 15 dictionary / 14 prose** sources;
  **208,230 / 321,672 / 45,037** segment records respectively.
- Whole-corpus `seg`-role totals: `head` 321,672 · `ru` 88,148 · `sa` 78,220 ·
  `body` 45,037 · commentary (`comm1`…`comm135`) ≈ 41,862 in total.

### 4.2 The headline: 78,219 clean 1:1 verse pairs
The Tier-1 figure reported in [`ALIGNMENT_SPEC.md`](../docs/ALIGNMENT_SPEC.md) §0 is
**78,219 clean 1:1 blocks** (both Sanskrit and Russian present), against **10,145**
Russian-only and **1** Sanskrit-only block, measured over the verse sources. A live
re-count of the current JSONL gives **78,139** groups with both sides non-empty,
**10,009** Russian-only, and **80** Sanskrit-only over **88,228** verse groups —
i.e. the clean-pair share is **88.56%** of verse groups. The ~80-pair difference from
the headline corresponds to the Sanskrit-only blocks the spec folded differently, and
to JSONL evolution since the 2026-06-12 corpus.db snapshot; **this paper reports
78,219 as the spec's canonical Tier-1 figure and 78,139 / 88.56% as the corroborating
current measurement, and states the reconciliation explicitly rather than presenting a
single tidy number.** (TODO before submission: pick one as the headline, recompute once
more at freeze time, and footnote the other.)

### 4.3 Clean pairs against the whole corpus
The 78,219 clean 1:1 verse pairs are **13.60%** of all 574,939 segment records and
**37.56%** of the 208,230 verse-source segment records — the rest of the verse-source
segments being the Russian sides without a non-empty Sanskrit sibling, the
duplicated-counted opposite sides, and the ~41,862 commentary segments. (The corpus is
*not* "37% aligned text and 63% noise"; the dictionary head entries and prose bodies are
intended monolingual reference content, not failed pairs — §4.4.)

### 4.4 Dictionaries and prose (not verse pairs, by design)
The 15 dictionaries contribute **321,672 head entries** (the single largest record
class, led by Kochergina 29,180 and Kossovich 13,488) and the 14 prose works
**45,037 body segments**. These are kept in the same schema and the same IDs space but
are **outside the 1:1 verse-pair denominator** — counting a dictionary headword as a
"failed alignment" would be a category error. They are the corpus's lexical and
apparatus layer.

### 4.5 Commentary
≈41,862 commentary segments (`comm1`…`comm135`) are linked to their host verses via an
`annotates` relation; CI confirms every commentary record resolves to an emitted verse
passage. Commentary is rendered as annotation, never as a translation pane, and is
excluded from sa/ru cardinality.

### 5.4 Diachronic register demonstration — the Bhagavadgītā  *(partial; see TODO)*
The corpus contains **11 Russian Bhagavadgītā translations** plus three Gītā
commentaries, all keyed on the same `{chapter}.{verse}` passage IDs, so a single verse
lines up across all editions via the shared compare key (ALIGNMENT_SPEC §5). The
editions span from the **1788** Russian Gītā (the first, rendered from a European
intermediary) through **1909** and **1914** to the twentieth- and twenty-first-century
scholarly translations (Smirnov, Sementsov, Erman, Burba, and the devotional
Prabhupāda/Radha/Sharma renderings). Because every edition is verse-pair-aligned to the
*same* Sanskrit, the corpus supports a controlled diachronic study of Russian
translation register over ~230 years on a fixed source text. *(TODO: the 1788/1909/1914
dates are read from the source slugs and are reliable; the full per-edition
translator + exact-year + rights table is not yet assembled, and the register metrics
(lexical drift, calque rate, Sanskrit-term retention) are described here as a planned
demonstration, not yet computed. Build the table from the source metadata and run the
metric before this section's claims are finalised.)*

## 6. Discussion

The corpus's value is twofold. As an **artefact**, it is, to our knowledge, the largest
uniform Sanskrit–Russian parallel resource, with ~78k verse pairs spanning the Vedic to
the late classical period and a lexical layer of >320k dictionary entries. As a
**method case**, it argues that for editions whose translators already aligned the text
by hand, the right move is markup-faithful extraction with a fidelity oracle, not a
statistical aligner that would overwrite ground truth and add probabilistic error. The
per-segment confidence/monolingual flags and the chronology crosswalk make the resource
honest about what it is — clean where the source is clean, explicitly monolingual where
it is not — which is exactly what a downstream consumer (retrieval, bilingual
lexicon induction, diachronic translation study) needs.

## 7. Limitations

- **The "1:1" headline depends on the measurement snapshot** (78,219 spec figure vs.
  78,139 live re-count); §4.2 reconciles the ~80-pair gap, but a single frozen number
  must be chosen at submission.
- **Monolingual text is not bitext.** Two whole translation-only texts (Balmont's
  Buddhacarita, mify-drind) account for ≈10,024 of the 10,145 Russian-only segments;
  they are valuable Russian witnesses but contribute no Sanskrit pair.
- **Provenance and rights are heterogeneous.** The Russian translations span 1788 to
  living authors; **redistribution of the Russian text is gated per translator**
  (copyright triage — a human gate, §8). The corpus can ship indices, passage IDs, and
  the Sanskrit freely while withholding in-copyright Russian text until cleared.
- **Dates are crosswalked, not re-derived** (VisualDCS), with `manual` flags on
  author-datable medieval works; the crosswalk inherits DCS's own dating uncertainty.
- **The diachronic Gītā demonstration (§5.4) is partially scaffolded** — edition table
  and register metrics are TODO.
- **`structure`-class reclassification.** The heuristic census and the final
  classification differ (§3.1); the final converter classification governs.

## 8. Human gates (copyright triage and DOI)

Two decisions sit outside the data work:

1. **RU-translation copyright triage [@DO].** Decide, per translator/edition, what may
   be redistributed as full Russian *text* vs. shipped as **indices + passage IDs +
   the Sanskrit only**. The Sanskrit, the IDs, the alignment structure, and the
   metadata are releasable now; in-copyright Russian translations are gated until
   cleared (pre-1918/public-domain editions such as the 1788/1909/1914 Gītā and
   Kossovich are the safe first release; living-author translations are held).
2. **Mint a Zenodo DOI [@DO]** for the citable release once (1) is settled, and complete
   the data-availability statement accordingly.

## 9. Conclusion

Samudra Manthanam is a 148-source, 574,939-segment Sanskrit–Russian corpus whose
~78,219 clean verse pairs were recovered by **markup-faithful extraction rather than
statistical alignment**, with monolingual content flagged as a first-class state, a
chronology crosswalk onto DCS period dates, and a built-in diachronic demonstration in
its 11 Russian Bhagavadgītā translations. It is offered as a reproducible data
descriptor and a method case for the many digitised parallel editions whose alignment
already lives in their markup.

## Data and reproducibility

The corpus layer is the **148 JSONL files** in
[`web/corpus_builder/jsonl/`](../web/corpus_builder/jsonl/); canonical counts in
[`web/corpus_builder/conversion_report.json`](../web/corpus_builder/conversion_report.json);
the converter is
[`web/corpus_builder/html_to_canonical.py`](../web/corpus_builder/html_to_canonical.py);
the alignment model and gold/CI gates are in
[`docs/ALIGNMENT_SPEC.md`](../docs/ALIGNMENT_SPEC.md) and
[`docs/CONVERTER_SPEC.md`](../docs/CONVERTER_SPEC.md); the structural inventory is
[`docs/TAG_CENSUS.md`](../docs/TAG_CENSUS.md); the date crosswalk is
[`web/corpus_builder/chronology/texts_chronology.json`](../web/corpus_builder/chronology/texts_chronology.json).
*(TODO before submission: a Zenodo DOI; a one-line license/redistribution statement per
the §8 copyright triage; confirmation of which sources ship as full text vs. index-only.)*
The extraction is deterministic and re-runs from the committed HTML sources; it never
infers a pairing the source did not already encode.

