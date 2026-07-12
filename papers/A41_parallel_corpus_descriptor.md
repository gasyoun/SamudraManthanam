---
paper_id: A41
title: "Samudra Manthanam: A Markup-Aligned Sanskrit–Russian Parallel Corpus of 148 Sources"
status: draft (advanced, 4/5 proposed) — scaffolded 2026-06-26, advanced 2026-07-08 (H351), completed prose + §5 metrics 2026-07-11 (H676), §6 annotation comparison 2026-07-12 (H759)
readiness: 3/5 → 4/5 proposed
venue: "LREC-COLING (parallel-corpus) / eLex / JOHD (Journal of Open Humanities Data)"
author: "**Mārcis Gasūns**, independent scholar ([ORCID 0000-0003-4513-884X](https://orcid.org/0000-0003-4513-884X)), gasyoun@ya.ru"
data_source: "web/corpus_builder/jsonl/ (148 report sources = 574,939 segment records; directory holds 155 .jsonl files — 7 post-report additions excluded from all counts); web/corpus_builder/conversion_report.json (canonical counts); docs/ALIGNMENT_SPEC.md (alignment model); docs/TAG_CENSUS.md (structural inventory); web/corpus_builder/chronology/texts_chronology.json (date crosswalk); papers/data/A41_corpus_stats.json + papers/data/A41_gita_editions.tsv (recomputation record, papers/scripts/a41_stats.py); nkrya-parallel/export/annotation_3path_metrics.json (§6 annotation comparison, web/corpus_builder/nkrya_annotate.py)"
---

# Samudra Manthanam: A Markup-Aligned Sanskrit–Russian Parallel Corpus of 148 Sources

_Created: 26-06-2026 · Last updated: 12-07-2026_

> **Draft status (2026-07-11, H676; advanced 2026-07-08, H351; scaffolded 2026-06-26).**
> Manuscript built directly on the converted corpus and its design specs. Every numerical
> claim below is transcribed from the canonical
> [conversion_report.json](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/conversion_report.json)
> and re-verified against the committed JSONL layer (restricted to the 148 report
> sources — the `jsonl/` directory currently holds **155** `.jsonl` files; the 7
> post-report additions are excluded from every count, see §3.1 note and §11 row 1) and
> [ALIGNMENT_SPEC.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ALIGNMENT_SPEC.md).
> **Home repo for the manuscript: SamudraManthanam `papers/`** — the corpus and all its
> specs live here.
> **Advanced 08-07-2026 (readiness 2/5 → 3/5, H351, Fable 5 `claude-fable-5`):** §2
> Related work written (nearest neighbor = the Itihāsa Sa–En corpus; delta = markup-aligned
> Sa–**Ru** at 148-source scale with no aligner); headline discipline made explicit (§4.2 —
> **78,219 clean 1:1 pairs is the headline, never 574,939 total segments**); the Gītā
> demonstration renumbered to a proper §5 (was a dangling "§5.4"); claim→artifact
> inventory (now §11) and companion-paper scope block (now §12) added; References
> added; links upgraded to full blob URLs.
> **Completed 11-07-2026 (readiness 3/5 → 4/5 proposed, H676, Fable 5 `claude-fable-5`):**
> every statistic re-derived live by the committed
> [papers/scripts/a41_stats.py](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/scripts/a41_stats.py)
> (recomputation record: [papers/data/A41_corpus_stats.json](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/data/A41_corpus_stats.json))
> — the 148-source layer is byte-stable (574,939 records / 574,939 unique IDs; verse-group
> recount identical to 08-07: 78,139 / 10,009 / 80); §5 written in full — the per-edition
> translator/year/rights table
> ([papers/data/A41_gita_editions.tsv](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/data/A41_gita_editions.tsv))
> and the register metrics (TTR, Guiraud R, Sanskrit-loan retention) are now computed, with
> Figure 1 ([papers/figures/A41_gita_register.svg](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/figures/A41_gita_register.svg))
> committed; the post-report extras census updated (5 → 7 files, 11,056 records); the
> runtime `web/corpus.db` view layer (152 sources / 580,552 display lines, `v2026.07.06`)
> reconciled against the canonical JSONL layer in §3.1.
> **Added 12-07-2026 (H759, Fable 5 `claude-fable-5`):** §6 Sanskrit-side annotation —
> the three-path comparison (plain SLP1 baseline vs DCS crosswalk vs vidyut fresh
> tagging) run on the 11,055-pair НКРЯ pilot per roadmap rulings 3+8, with the
> committed metrics record
> ([annotation_3path_metrics.json](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/export/annotation_3path_metrics.json))
> and the full report
> ([ANNOTATION_3PATH_COMPARISON.md](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/export/ANNOTATION_3PATH_COMPARISON.md));
> former §§6–11 renumbered to §§7–12.
> **Open before submission:** (1) settle the RU-translation copyright triage that decides
> what ships as text vs index-only (a [@DO] human gate, §9 / Limitations); (2) mint a
> Zenodo DOI and complete the data-availability statement; (3) freeze ONE headline
> number at submission (78,219 spec figure vs 78,139 live re-count, reconciled in §4.2);
> (4) venue + byline (a human decides); (5) the §6.4 human adjudication verdict
> (51-group review sheet) folded in once voted.

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

The central observation, formalised in [`docs/ALIGNMENT_SPEC.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ALIGNMENT_SPEC.md)
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

## 2. Related work

Four strands frame the contribution. The novelty claim, stated crisply: a
**markup-aligned Sanskrit–Russian parallel corpus at 148-source scale with per-segment
cardinality/monolingual flags and a chronology crosswalk** — a *resource and
method-of-construction* contribution, **not** a new aligner.

**Sentence alignment as inference.** The standard parallel-corpus pipeline treats
pairing as an estimation problem: length-based dynamic programming (Gale & Church
1993), dictionary-assisted alignment for medium-density languages (Hunalign; Varga et
al. 2005), MT-mediated alignment (Bleualign; Sennrich & Volk 2010), and embedding-based
aligners over LASER/LaBSE sentence spaces (Vecalign; Thompson & Koehn 2019; Artetxe &
Schwenk 2019; Feng et al. 2022). All of these *infer* a pairing and attach an estimated
confidence. Our corpus is the contrasting case this literature rarely names: the
editions were **hand-aligned by their editors at the verse level before we arrived**,
so running any aligner would replace ground truth with an estimate of it (§3.2). The
right method is extraction plus a fidelity oracle, and the corpus is offered as a
worked example of that stance.

**Structure-derived bitext.** Reading alignment out of document structure — TEI
parallel editions, interleaved verse/translation layouts, table- and segment-based
publisher formats — is established practice in digital philology, but it is usually
applied per-edition and ad hoc. What this corpus adds is the *systematisation*: one
schema, one cardinality model (`1:1` / `0:1` / `1:0` per block, §3.4), one regression
oracle, applied uniformly across 148 heterogeneous sources.

**Sanskrit corpora and the Russian gap.** Sanskrit NLP rests on the Digital Corpus of
Sanskrit (Hellwig), GRETIL, the Sanskrit Library (Scharf & Hyman), and the Cologne
Digital Sanskrit Dictionaries. Parallel data is dominated by Sanskrit–**English**: the
nearest neighbor to this work is the **Itihāsa** corpus (Aralikatte et al. 2021), ~93k
Sanskrit–English śloka–translation pairs extracted from printed Rāmāyaṇa and
Mahābhārata editions. Our delta against Itihāsa is threefold: the target language is
**Russian** (to our knowledge no comparable machine-readable Sanskrit–Russian parallel
resource exists — the Russian indological tradition is deep but its digital layer was
per-source reading HTML, §1); the source base is **148 works across genres** (Veda,
epic, Upaniṣads, kāvya, śāstra) rather than the two epics; and the alignment is
**markup-recovered with explicit monolingual flagging** rather than extracted with
per-pair heuristics. The 15-dictionary lexical layer (321,672 head entries) additionally
connects the corpus to the lexicographic strand (A42, §12).

**Data-descriptor norms.** The paper is framed for FAIR-style data-descriptor venues
(JOHD, the LREC-COLING resource track; Wilkinson et al. 2016): the artefact, its schema,
its honest edge-case accounting (§4.2's two-number reconciliation, §3.4's monolingual
inventory), its rights triage (§9), and its reproducibility story (§3.5) are the
contribution, and the paper's structure follows that contract.

## 3. Data and method

### 3.1 Sources and structural classes
The corpus is built from **148 sources** (the canonical count in
[`conversion_report.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/conversion_report.json):
`total_sources: 148`, `total_records: 574939`). A structural inventory
([`docs/TAG_CENSUS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/TAG_CENSUS.md)) and a downstream backfill assign every
source one of three `structure` classes; the **final converter classification** is:

| `structure` | sources | segment records | dominant `seg` role |
|---|--:|--:|---|
| **verse** | 119 | 208,230 | `sa` / `ru` / `comm{n}` |
| **dictionary** | 15 | 321,672 | `head` |
| **prose** | 14 | 45,037 | `body` |
| **total** | **148** | **574,939** | |

*(Note for the methods text: the early heuristic tag-census in
[`TAG_CENSUS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/TAG_CENSUS.md) reports a provisional **70 verse / 15 dictionary /
67 prose** split — over **152** candidate sources, not the final 148; the table above is
the **final** converter/backfill classification recorded in the conversion report and
[`.ai_state.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/.ai_state.md). The discrepancy
is the heuristic-vs-final reclassification (and the 152→148 source-set trim) and must be
stated, not hidden.)*

*(Layer reconciliation, 11-07-2026: three counts coexist and none contradicts the
others. The **canonical corpus** is the 148 report sources / 574,939 JSONL records above.
The **`jsonl/` directory** additionally holds 7 post-report files (11,056 records:
`hitopadesha`, `naradasmriti`, `vishnu-smriti`, `yajnavalkyasmriti`,
`yajnavalkyasmriti_add`, and the two H534 Devībhāgavata files), excluded from every
count until a re-frozen conversion report folds them in. The **runtime search view**
`web/corpus.db` (`v2026.07.06`: 152 sources, 580,552 display lines) is built from the
reading HTML, includes navigation headings and a different source cut, and is never a
source of corpus statistics. Recomputation record:
[papers/data/A41_corpus_stats.json](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/data/A41_corpus_stats.json).)*

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
([`web/corpus_builder/html_to_canonical.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/html_to_canonical.py))
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
`head`; prose records carry `seg: null` in the live JSONL — the `body` label for their
45,037 records is the conversion report's `seg_counts` category, not a live field
value), `group`, `lang`, `script`, `text`, `html`, `slp1` (SLP1 for Sanskrit),
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
not the Sanskrit) and `mify-drind` (1,172 in the spec; 1,154 in the live JSONL — the
same post-spec drift §4.2 reconciles in aggregate) — together ≈10,024 of the 10,145, with the
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
[`web/corpus_builder/chronology/texts_chronology.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/chronology/texts_chronology.json)
maps each text onto **VisualDCS** period dates **without re-deriving them**: `dcs-exact`
= the text's own DCS date, `dcs-bucket` = its period-bucket date, `manual` = an
author-datable medieval work (flagged). For the 86 `parallel-ru` texts the method
breaks down as `dcs-exact` (20), `dcs-bucket` (27), `manual` (11), `n/a` (28 —
dictionaries / undatable), summing to 86. (Across both corpora `dcs-exact` totals 92,
but 72 of those are `wisdomlib-en` datings and must not be attributed to the Russian
corpus.) The same file also crosswalks 848 `wisdomlib-en`
texts (a separate English corpus, out of scope here but sharing the date spine).

## 4. Results

*All numbers below are verified against [`conversion_report.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/conversion_report.json)
and a live re-count of the JSONL layer restricted to the 148 report sources
(2026-06-26, re-verified 2026-07-08 and 2026-07-11 — the 11-07 recount by the committed
[papers/scripts/a41_stats.py](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/scripts/a41_stats.py)
reproduced every figure identically, confirming the 148-source layer is frozen).*

### 4.1 Corpus scale and composition
- **148 sources**, **574,939 segment records**.
- Structure split: **119 verse / 15 dictionary / 14 prose** sources;
  **208,230 / 321,672 / 45,037** segment records respectively.
- Whole-corpus `seg`-role totals: `head` 321,672 · `ru` 88,148 · `sa` 78,220 ·
  `body` 45,037 · commentary (`comm1`…`comm135`) ≈ 41,862 in total.

### 4.2 The headline: 78,219 clean 1:1 verse pairs
The Tier-1 figure reported in [`ALIGNMENT_SPEC.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ALIGNMENT_SPEC.md) §0 is
**78,219 clean 1:1 blocks** (both Sanskrit and Russian present), against **10,145**
Russian-only and **1** Sanskrit-only block, measured over the verse sources. A live
re-count of the current JSONL gives **78,139** groups with both sides non-empty,
**10,009** Russian-only, and **80** Sanskrit-only over **88,228** verse groups —
i.e. the clean-pair share is **88.56%** of verse groups. The ~80-pair difference from
the headline corresponds to the Sanskrit-only blocks the spec folded differently, and
to JSONL evolution since the 2026-06-12 corpus.db snapshot; **this paper reports
78,219 as the spec's canonical Tier-1 figure and 78,139 / 88.56% as the corroborating
current measurement, and states the reconciliation explicitly rather than presenting a
single tidy number.** (Recomputed 2026-07-11 by
[a41_stats.py](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/scripts/a41_stats.py):
78,139 / 10,009 / 80 over 88,228 verse groups — identical to the 08-07 recount, so the
live figure is stable; the remaining freeze-time act is choosing which of the two
reconciled numbers leads and footnoting the other, a one-line edit at submission.)

**Headline discipline.** The number this corpus is cited by is the clean 1:1 verse-pair
count (**78,219**), *never* the 574,939 total segment records: the total mixes verse
pairs with dictionary head entries, prose bodies, commentary, and both sides of each
pair, and quoting it as corpus size would overstate the bitext by ~7×. Every abstract,
table caption, and downstream citation of this resource uses the pair count as the
headline and the segment total only as the schema-level inventory figure.

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

## 5. Diachronic register demonstration — the Bhagavadgītā

The corpus contains **11 Russian Bhagavadgītā translation sources** (10 single
editions plus one multi-rendering anthology) and **three Gītā commentaries**, all keyed
on the same `{chapter}.{verse}` passage IDs, so a single verse lines up across all
editions via the shared compare key (ALIGNMENT_SPEC §5). Because every edition is
verse-pair-aligned to the *same* Sanskrit, the corpus supports a controlled diachronic
study of Russian translation register over ~230 years on a fixed source text. All
figures in this section are computed by the committed
[papers/scripts/a41_stats.py](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/scripts/a41_stats.py)
over the editions' Russian verse segments (aggregates only; full table with per-edition
metrics: [papers/data/A41_gita_editions.tsv](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/data/A41_gita_editions.tsv)).

### 5.1 The per-edition table

| source | translator | orig. year | rights class | clean pairs | TTR | Guiraud R | loan retention |
|---|---|--:|---|--:|--:|--:|--:|
| `bhagavadgita-1788` | А.А. Петров (via Wilkins' English) | 1788 | public domain (1914 reprint) | 697 | 0.242 | 33.1 | 13.9% |
| `bhagavadgita-1909` | А.П. Казначеева (verse) | 1909 | public domain | 691 | 0.263 | 33.2 | 11.1% |
| `bhagavadgita-1914` | А.А. Каменская, И.В. де Манциарли | 1914 | public domain | 701 | 0.309 | 36.4 | 22.0% |
| `bhagavadgita-smirnov` | Б.Л. Смирнов | 1977 | in-copyright (grey) | 700 | 0.203 | 32.2 | 32.4% |
| `bhagavadgita-prabhupada` | А.Ч. Бхактиведанта Свами Прабхупада | 1984 | in-copyright (grey) | 657 | 0.199 | 36.4 | 30.3% |
| `bhagavadgita-sementsov` | В.С. Семенцов | 1999 | in-copyright (grey) | 696 | 0.310 | 35.3 | 35.3% |
| `bhagavadgita-erman` | В.Г. Эрман | 2009 | in-copyright (grey) | 700 | 0.317 | 37.0 | 11.3% |
| `bhagavadgita-burba` | Д. Бурба | 2009 | in-copyright (grey) | 719 | 0.121 | 27.5 | 38.9% |
| `bhagavadgita-sharma` | Шайлендра Шарма | 2015 | in-copyright (grey) | 660 | 0.176 | 37.1 | 62.6% |
| `bhagavadgita-radha` | Р.Т. Блиндерман | 2016 | in-copyright (grey) | 647 | 0.101 | 42.6 | 76.0% |
| `bhagavadgity` (anthology, 1788–2016) | сборник переводов | — | in-copyright (grey) | 701 | 0.114 | 50.3 | 59.6% |
| `ramanuja_gitabhashya` (comm.) | В.С. Семенцов (пер.) | 2021 | in-copyright (grey) | 702 | 0.147 | 41.7 | 59.8% |
| `gitartha-samgraha_yamunacharya` (comm.) | Р.В. Псху | 2021 | in-copyright (grey) | 32 | 0.552 | 14.7 | 84.4% |
| `gitarthasamgraha-abhinavagupta` (comm.) | О.Н. Ерченков | 2008 | in-copyright (grey) | 748 | 0.239 | 42.0 | 47.5% |

*Reading the table.* "Orig. year" is the slug-encoded original edition year where
present (Petrov's 1788 translation circulates in the corpus as its 1914 reprint — the
per-source `meta.json` carries the imprint, the slug the original); "clean pairs" is
the per-edition count of passage groups with both a non-empty Sanskrit and Russian
side — it may exceed the canonical 700 verses where an edition sub-divides passages
(Burba 719; Abhinavagupta's commentary 748) or fall short where verses are ranged
together or absent (Radha 647). Yāmuna's Gītārthasaṅgraha is genuinely a 32-verse
epitome, not a truncation. **TTR** (type–token ratio) and **Guiraud R** (types/√tokens)
are computed over each edition's Russian verse segments; TTR is length-sensitive, so R
is the cross-edition comparator. **Loan retention** is the share of an edition's
Russian segments containing at least one of 18 fixed transliterated Sanskrit loan stems
(йога, карма, дхарма, брахман, атман, гуна, пракрити, пуруша, …; the exact list is in
the recomputation record) — a deliberately transparent surface proxy for
"Sanskrit-term retention vs. translation into native vocabulary."

### 5.2 What the metrics show

![Register metrics per edition, 1788–2016](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/figures/A41_gita_register.svg?raw=true)

The signal is **register, not merely time**. Loan retention does rise across the
corpus's ~230 years — from 11–22% in the three pre-revolutionary editions (1788, 1909,
1914) to 30–76% in the post-war ones — but the moderns split cleanly into two lines.
The **scholarly-literary line** keeps loans low or moderate: Erman's academic 2009
translation retains Sanskrit terms in only 11.3% of segments — *below* the 1914
theosophical rendering — while Smirnov (32.4%) and Sementsov (35.3%) sit mid-range.
The **terminological line** — the devotional and esoteric renderings (Prabhupāda
30.3%, Burba 38.9%, Sharma 62.6%, Radha 76.0%) — treats the Sanskrit lexicon as
technical vocabulary to be retained, not translated. The three commentaries behave
like the terminological line (47–84%), as expected for exegetical prose that must
quote its lemmata. Lexical richness (Guiraud R) separates the same groups more weakly
(27.5–42.6 across translations), with the interlinear-style Radha rendering scoring
highest — long glossing segments accumulate types. These are surface lexical measures
computed on ~700 segments per edition; they demonstrate that the corpus supports
controlled cross-edition register comparison on a fixed source text, and deeper
measures (calque detection, syntactic archaism) are downstream work, not claims of
this paper.

## 6. Sanskrit-side annotation: a three-path comparison

A parallel corpus entering a national-corpus infrastructure (the НКРЯ track,
[roadmap](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ROADMAP_NKRYA_PARALLEL_RUSCORPORA_2026_2027.md))
needs a position on Sanskrit-side linguistic annotation. Rather than assume one,
we compared three candidate paths head-to-head on the four pilot sources — MBh 3
and Rāmāyaṇa 1–3, 11,055 verse pairs / 40,269 half-verse lines / 203,623 surface
tokens: **(A)** the plain IAST/SLP1 surface already carried by the corpus (the
guaranteed floor), **(B)** a crosswalk onto the Digital Corpus of Sanskrit's
human-curated lemma + UD morphology (Hellwig; CC BY 4.0, so redistributable
inside НКРЯ with attribution), and **(C)** fresh automatic tagging with
vidyut-cheda 0.4. All figures recompute from the committed
[annotation_3path_metrics.json](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/export/annotation_3path_metrics.json)
by [web/corpus_builder/nkrya_annotate.py](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/nkrya_annotate.py);
the full method and per-tier tables are in
[ANNOTATION_3PATH_COMPARISON.md](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/export/ANNOTATION_3PATH_COMPARISON.md).

### 6.1 The crosswalk is text-keyed, and coverage measures editions

Verse loci cannot join the two corpora: our MBh 3 carries critical-edition
numbering (299 adhyāyas, same as DCS) but our Rāmāyaṇa kāṇḍas are
vulgate-numbered (77/119/75 sargas vs DCS's critical 76/111/71). The crosswalk
therefore matches **normalized half-verse text** in three tiers — exact,
consonant-skeleton (neutralizing sandhi differences: DCS's Rāmāyaṇa
`text_sandhied` is largely de-sandhied pada text), and bounded fuzzy:

| Source | Half-verses | Matched | **Coverage** |
|---|--:|--:|--:|
| MBh 3 (Āraṇyakaparvan) | 21,396 | 21,356 | **99.8%** |
| Rām 1 (Bālakāṇḍa) | 4,633 | 3,536 | **76.3%** |
| Rām 2 (Ayodhyākāṇḍa) | 9,093 | 4,936 | **54.3%** |
| Rām 3 (Araṇyakāṇḍa) | 5,147 | 2,827 | **54.9%** |
| **Total** | **40,269** | **32,655** | **81.1%** |

The unmatched residue is an **edition measurement, not annotation noise**: of
801 probed unmatched Ayodhyā lines, 795 are absent from the *entire* DCS
Rāmāyaṇa — vulgate text the critical edition excised. Matched lines carry
225,972 DCS tokens with lemma and UD features.

### 6.2 Fresh tagging is not yet competitive on epic verse

vidyut-cheda processed all 40,269 lines locally (zero engine failures) but
produced 293,775 tokens — **1.44× the surface count** — by shattering long
compounds and vṛddhi derivatives into short spurious roots
(*dhārtarāṣṭraiḥ* → five fragments); 5.4% of its tokens carry no lemma.

### 6.3 Agreement between the two annotated paths

On the 6,355 groups fully covered by DCS, per-group lemma-set agreement
(Jaccard, SLP1-normalized both sides) averages only **0.28–0.35** per source.
The disagreement decomposes into a lemma-granularity *convention* (vidyut
lemmatizes derivatives to the dhātu root, *rāmaḥ* → *ram*, where DCS uses the
nominal stem *rāma* — mitigated but not eliminated by extracting vidyut's
prātipadika stems) and *real* segmentation divergence (§6.2). A fixed-seed
stratified sample of 51 groups
([annotation_adjudication_sample.json](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/export/annotation_adjudication_sample.json))
is under human adjudication to apportion blame between the two causes.

### 6.4 The resulting annotation policy

**A always; B as the lemma/morph layer wherever a verse crosswalks to DCS, with
per-text coverage declared (partial by construction outside MBh); C not shipped
at current quality.** This mirrors the corpus's general stance (§3.2): consume
existing human-curated ground truth where it exists; never replace it with a
model's estimate of it.

## 7. Discussion

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

## 8. Limitations

- **The "1:1" headline depends on the measurement snapshot** (78,219 spec figure vs.
  78,139 live re-count); §4.2 reconciles the ~80-pair gap, but a single frozen number
  must be chosen at submission.
- **Monolingual text is not bitext.** Two whole translation-only texts (Balmont's
  Buddhacarita, mify-drind) account for ≈10,024 of the 10,145 Russian-only segments;
  they are valuable Russian witnesses but contribute no Sanskrit pair.
- **Provenance and rights are heterogeneous.** The Russian translations span 1788 to
  living authors; **redistribution of the Russian text is gated per translator**
  (copyright triage — a human gate, §9). The corpus can ship indices, passage IDs, and
  the Sanskrit freely while withholding in-copyright Russian text until cleared.
- **Dates are crosswalked, not re-derived** (VisualDCS), with `manual` flags on
  author-datable medieval works; the crosswalk inherits DCS's own dating uncertainty.
- **The §5 register metrics are surface lexical measures.** TTR/Guiraud R and the
  18-stem loan-retention proxy are computed on ~700 Russian segments per edition; they
  support the register-comparison demonstration but are not a full stylometric study
  (calque detection, syntactic archaism, and translator-attribution measures are
  downstream work). TTR is length-sensitive and is reported only alongside Guiraud R.
- **`structure`-class reclassification.** The heuristic census and the final
  classification differ (§3.1); the final converter classification governs.

## 9. Human gates (copyright triage and DOI)

Two decisions sit outside the data work:

1. **RU-translation copyright triage [@DO].** Decide, per translator/edition, what may
   be redistributed as full Russian *text* vs. shipped as **indices + passage IDs +
   the Sanskrit only**. The Sanskrit, the IDs, the alignment structure, and the
   metadata are releasable now; in-copyright Russian translations are gated until
   cleared (pre-1918/public-domain editions such as the 1788/1909/1914 Gītā and
   Kossovich are the safe first release; living-author translations are held).
2. **Mint a Zenodo DOI [@DO]** for the citable release once (1) is settled, and complete
   the data-availability statement accordingly.

## 10. Conclusion

Samudra Manthanam is a 148-source, 574,939-segment Sanskrit–Russian corpus whose
~78,219 clean verse pairs were recovered by **markup-faithful extraction rather than
statistical alignment**, with monolingual content flagged as a first-class state, a
chronology crosswalk onto DCS period dates, and a built-in diachronic demonstration in
its 11 Russian Bhagavadgītā translations. It is offered as a reproducible data
descriptor and a method case for the many digitised parallel editions whose alignment
already lives in their markup.

## Data and reproducibility

The corpus layer is the JSONL directory
[`web/corpus_builder/jsonl/`](https://github.com/gasyoun/SamudraManthanam/tree/main/web/corpus_builder/jsonl) — **148 report sources** define the corpus of record (the
directory currently holds 155 `.jsonl` files; the 7 post-report additions —
`hitopadesha`, `naradasmriti`, `vishnu-smriti`, `yajnavalkyasmriti`,
`yajnavalkyasmriti_add`, `devibhagavata-purana-1`, `devibhagavata-purana_s1.sanskrit`,
11,056 records — are excluded from every count until a re-frozen conversion report
folds them in; freeze-time TODO); canonical counts in
[`web/corpus_builder/conversion_report.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/conversion_report.json);
the converter is
[`web/corpus_builder/html_to_canonical.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/html_to_canonical.py);
the alignment model and gold/CI gates are in
[`docs/ALIGNMENT_SPEC.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ALIGNMENT_SPEC.md) and
[`docs/CONVERTER_SPEC.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/CONVERTER_SPEC.md); the structural inventory is
[`docs/TAG_CENSUS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/TAG_CENSUS.md); the date crosswalk is
[`web/corpus_builder/chronology/texts_chronology.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/chronology/texts_chronology.json).
*(TODO before submission: a Zenodo DOI; a one-line license/redistribution statement per
the §9 copyright triage; confirmation of which sources ship as full text vs. index-only.)*
The extraction is deterministic and re-runs from the committed HTML sources; it never
infers a pairing the source did not already encode. Every statistic in this paper is
recomputed in one pass by
[`papers/scripts/a41_stats.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/scripts/a41_stats.py),
whose dated output ([`papers/data/A41_corpus_stats.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/data/A41_corpus_stats.json),
[`papers/data/A41_gita_editions.tsv`](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/data/A41_gita_editions.tsv))
and figure ([`papers/figures/A41_gita_register.svg`](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/figures/A41_gita_register.svg))
are committed beside the manuscript.

## 11. Claim → artifact inventory

Every headline claim, its figure, and the committed artifact it recomputes from (per
the `/paper-scaffold` discipline — a claim without a committed artifact is a gap,
flagged as such):

| # | Claim | Figure(s) | Artifact | Status |
|--:|---|---|---|---|
| 1 | Corpus scale | 148 report sources, 574,939 segment records (the `jsonl/` dir holds 155 `.jsonl` files as of 11-07-2026; 7 post-report additions, 11,056 records, excluded from all counts and itemised in §3.1) | [conversion_report.json](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/conversion_report.json) (`total_sources`, `total_records`) + [A41_corpus_stats.json](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/data/A41_corpus_stats.json) extras census | ✅ committed; ⬜ fold or formally exclude the extras at freeze (re-frozen conversion report) |
| 2 | Final structure split | 119 verse / 15 dictionary / 14 prose; 208,230 / 321,672 / 45,037 records | [conversion_report.json](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/conversion_report.json) + final backfill in [.ai_state.md](https://github.com/gasyoun/SamudraManthanam/blob/main/.ai_state.md); the heuristic 70/15/67-of-152 census in [TAG_CENSUS.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/TAG_CENSUS.md) is superseded and said so in §3.1 | ✅ committed |
| 3 | Headline: clean 1:1 verse pairs | **78,219** (Tier-1) vs 78,139 / 88.56% live re-count (26-06, re-verified identically 08-07 and 11-07-2026) | [ALIGNMENT_SPEC.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ALIGNMENT_SPEC.md) §0 + [a41_stats.py](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/scripts/a41_stats.py) recount ([A41_corpus_stats.json](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/data/A41_corpus_stats.json)) | ✅ committed; ⬜ freeze-time choice of which reconciled figure leads (one-line edit) |
| 4 | Monolingual inventory | 10,145 RU-only, dominated by `buddhacharita-balmont` 8,852 + `mify-drind` 1,172 (≈10,024 of 10,145); 1 Sa-only (spec) / 80 (live) | [ALIGNMENT_SPEC.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ALIGNMENT_SPEC.md) §2 + JSONL re-count | ✅ committed |
| 5 | Whole-corpus `seg` roles | `head` 321,672 · `ru` 88,148 · `sa` 78,220 · `body` 45,037 · `comm*` ≈41,862 | [conversion_report.json](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/conversion_report.json) / JSONL | ✅ committed |
| 6 | Extraction fidelity | `needs_review: 0`; 574,939 unique IDs; 25 letter-suffixed duplicate-passage records; gold set + CI gates green | [conversion_report.json](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/conversion_report.json) + [ALIGNMENT_SPEC.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ALIGNMENT_SPEC.md) §§6–7 gate log (2026-06-13) | ✅ committed |
| 7 | Chronology crosswalk | 86 `parallel-ru` texts: `dcs-exact` 20 / `dcs-bucket` 27 / `manual` 11 / `n/a` 28 (cross-corpus `dcs-exact` = 92, of which 72 are `wisdomlib-en`) | [texts_chronology.json](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/chronology/texts_chronology.json) | ✅ committed |
| 8 | Gītā demonstration | 11 RU translation sources + 3 commentaries on shared `{chapter}.{verse}` keys; per-edition table + TTR/Guiraud R/loan-retention metrics (§5.1–5.2, Figure 1) | [A41_gita_editions.tsv](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/data/A41_gita_editions.tsv) + [A41_gita_register.svg](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/figures/A41_gita_register.svg), computed by [a41_stats.py](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/scripts/a41_stats.py) from per-source `meta.json` + JSONL | ✅ committed (11-07-2026) |
| 9 | Lexical layer | 321,672 head entries; Kochergina 29,180, Kossovich 13,488 | [conversion_report.json](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/conversion_report.json) per-source counts | ✅ committed |
| 10 | Annotation comparison (§6) | DCS crosswalk coverage 81.1% overall (MBh 3 99.8%, Rām 1–3 54–76%); vidyut 1.44× over-segmentation; B↔C Jaccard 0.28–0.35 on 6,355 fully-covered groups | [annotation_3path_metrics.json](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/export/annotation_3path_metrics.json) + [ANNOTATION_3PATH_COMPARISON.md](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/export/ANNOTATION_3PATH_COMPARISON.md), computed by [nkrya_annotate.py](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/nkrya_annotate.py) | ✅ committed (12-07-2026); ⬜ 51-group human adjudication verdict pending |

## 12. Scope versus companion papers (anti-salami)

- **A42 (the 1.09M-pair word-aligned Sa→Ru lexicon)** owns the *word-level* alignment
  story — an LLM-induced lexicon built in a different pipeline
  (SanskritLexicography/RussianTranslation). A41 is the *corpus descriptor*: it stops at
  the verse-pair level and cites A42 forward as the word-level companion; no word
  alignment is performed here.
- **A43 (the Russian Sanskrit lexicography family)** owns the *comparison* of the
  Russian dictionaries as lexicographic works (Kossovich / Knauer / Smirnov /
  Kochergina). A41 counts the 15 dictionary sources only as a record class in the
  schema (§4.4) and never analyses their content.
- **A38 (the DCS-2026 release)** owns the corpus and its dating; A41 *crosswalks onto*
  DCS period dates (§3.6) and never re-derives them.
- **A40 (the CDSL headword census)** owns the dictionary-inventory growth story; no
  overlap beyond both being resource papers.
- **The §6 annotation comparison is deliberately a *section*, not a companion paper**
  (roadmap ruling 8, 11-07-2026): it exists to justify the corpus's annotation policy,
  not to benchmark Sanskrit taggers; a tagger-benchmark paper would need gold
  annotation, multiple systems, and tuning — none of which A41 claims.
- A41 leads with exactly two things nothing else owns: the **markup-aligned Sa–Ru
  parallel corpus** and the **extraction-not-inference method case**.

## References ⬜

- Aralikatte, R., M. de Lhoneux, A. Kunchukuttan & A. Søgaard. 2021.
  [Itihāsa: A large-scale corpus for Sanskrit to English translation](https://aclanthology.org/2021.wat-1.22/).
  *Proceedings of the 8th Workshop on Asian Translation (WAT 2021)*.
- Artetxe, M. & H. Schwenk. 2019. Massively multilingual sentence embeddings for
  zero-shot cross-lingual transfer and beyond. *TACL* 7: 597–610. (LASER.)
- Feng, F., Y. Yang, D. Cer, N. Arivazhagan & W. Wang. 2022. Language-agnostic BERT
  sentence embedding. *ACL 2022*. (LaBSE.)
- Gale, W. A. & K. W. Church. 1993. A program for aligning sentences in bilingual
  corpora. *Computational Linguistics* 19(1): 75–102.
- GRETIL — Göttingen Register of Electronic Texts in Indian Languages —
  [gretil.sub.uni-goettingen.de](https://gretil.sub.uni-goettingen.de/).
- Hellwig, O. *Digital Corpus of Sanskrit (DCS)* — dating spine via the crosswalk in
  §3.6; the DCS-2026 release is described in the companion paper A38.
- Scharf, P. & M. Hyman. The Sanskrit Library — [sanskritlibrary.org](https://sanskritlibrary.org/).
- Sennrich, R. & M. Volk. 2010. MT-based sentence alignment for OCR-generated parallel
  texts. *AMTA 2010*. (Bleualign.)
- Thompson, B. & P. Koehn. 2019. Vecalign: Improved sentence alignment in linear time
  and space. *EMNLP-IJCNLP 2019*.
- Varga, D., P. Halácsy, A. Kornai, V. Nagy, L. Németh & V. Trón. 2005. Parallel
  corpora for medium density languages. *RANLP 2005*. (Hunalign.)
- Wilkinson, M. D., et al. 2016. The FAIR guiding principles for scientific data
  management and stewardship. *Scientific Data* 3: 160018.
- ⬜ A38, A42, A43 self-citations once their venues/DOIs freeze.

_Dr. Mārcis Gasūns_

