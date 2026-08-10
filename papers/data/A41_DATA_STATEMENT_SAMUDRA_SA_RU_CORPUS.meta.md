# Data statement — Samudra Manthanam Sanskrit–Russian parallel corpus (A41)

_Created: 10-08-2026 · Last updated: 10-08-2026_

**Dataset:** the markup-aligned Sanskrit–Russian parallel corpus described in
[papers/A41_parallel_corpus_descriptor.md](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/A41_parallel_corpus_descriptor.md)
— **148 sources / 574,939 segment records**, headline **78,219 clean 1:1 verse pairs**.

Form: Bender & Friedman (2018) data statement, extended with the Gebru et al. (2021)
datasheet provenance/maintenance fields and the org metadoc-v2 additions (intended use
and known misuse, maintenance plan, deprecation status) — the same template as the
[kosha data statements](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/README.md).
Written for [H2403](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2403-Fable_SamudraManthanam_a41-resource-paper-acl-uplift_07.08.26.md)
to close checklist items B2–B6 of the
[ARR Responsible NLP checklist](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/A41_ARR_RESPONSIBLE_NLP_CHECKLIST.md).

## A. Curation rationale

The Russian indological tradition (Kossovich, Smirnov, Sementsov, Erman, Grintser and
others) is deep, but its digital layer existed only as **per-source reading HTML** on
samskrtam.ru — not as a queryable parallel corpus. This dataset converts those pages
into one uniform, segment-addressable JSONL layer, preserving the **verse-level
alignment the print editors had already made by hand**. Sources were included because
they were already digitised for the reading environment; no source was selected or
excluded on linguistic grounds, so the corpus inherits samskrtam.ru's coverage
(Veda, epic, Upaniṣads, kāvya, śāstra, plus a dictionary and a prose apparatus layer)
rather than sampling a designed balance.

## B. Language varieties

- **Sanskrit** (`sa`) — Vedic through late classical, in IAST and SLP1 transliteration,
  as printed in the source editions (largely vulgate; **not** normalised to any critical
  edition). 78,220 `sa` segments.
- **Russian** (`ru`) — literary Russian, 1788 → 2021, spanning pre-reform orthography in
  the earliest editions (Petrov 1788, Kaznacheeva 1909) through contemporary academic and
  devotional registers. 88,148 `ru` segments. Pre-reform spelling is preserved as printed,
  not modernised.
- **Contact effect:** a large share of the Russian is *translationese* from Sanskrit, and
  in two cases relay translation from English (Petrov 1788 via Wilkins; Balmont's
  Buddhacarita via Arnold). This is a property to model, not a defect — see §5 of the
  descriptor and the loan-retention metric.

## C. Speaker / author demographic

Not a speaker corpus: every segment is **published print text**. The Sanskrit side is
premodern authored/redacted literature with no recoverable individual demographics. The
Russian side is the work of **19 distinct named translators/credits across 63 sources
with committed metadata**, inventoried in
[A41_TRANSLATORS.md](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/data/A41_TRANSLATORS.md)
(machine twin [A41_TRANSLATORS.tsv](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/data/A41_TRANSLATORS.tsv));
the remaining sources lack a committed `meta.json` credit (H821 metadata-loss residue)
and are marked `—` rather than guessed. Translators are overwhelmingly male
20th-century Russian academics, with a devotional/esoteric minority (Prabhupāda, Sharma,
Blinderman) — a register split the corpus makes measurable (§5.2) but does not correct.

## D. Annotator demographic

**None.** No crowdworkers, no paid annotators, no human-subjects component. The corpus
carries no human-added linguistic annotation layer: the bilingual pairing is read out of
the source markup (§3.2), and the optional lemma/morphology layer is **imported** from
the Digital Corpus of Sanskrit rather than annotated here (§6). The two human passes that
do exist are the author's own: a ~25-group gold set for extraction fidelity, and a
pending 51-group adjudication of DCS↔vidyut lemma disagreement.

## E. Speech situation and text characteristics

Written, edited, published; no spontaneous or spoken material. Genre classes are explicit
fields: **verse** (119 sources / 208,230 records), **dictionary** (15 / 321,672),
**prose** (14 / 45,037). Segments carry their canonical passage ID, a `structure` class,
and a `seg` role (`sa` · `ru` · `comm{n}` · `head`), so verse pairs, monolingual content,
commentary, and lexical entries are separable **by query**, never by re-parsing.

## F. Preprocessing and data quality

- **Extraction, not inference.** [`html_to_canonical.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/html_to_canonical.py)
  reads each citation block's sibling `#sa` / `#ru` / `#comm{n}` children into one
  alignment group keyed `{work}:{passage}`. No statistical aligner, embedding similarity,
  or heuristic pairing is used anywhere in the pipeline.
- **Cardinality is measured, not assumed:** `1:1` 78,139 · `0:1` (RU-only) 10,009 ·
  `1:0` (Sa-only) 80, over 88,228 verse groups (live re-count; the spec's Tier-1 figure
  is 78,219 / 10,145 / 1 — the ~80-pair gap is reconciled in §4.2 rather than hidden).
- **Monolingual is a flagged state, not an alignment failure** — ≈10,024 of the 10,009–10,145
  Russian-only segments are two whole translation-only texts.
- **Fidelity gates:** `needs_review: 0` across all 148 sources; 574,939 records /
  574,939 unique IDs; 25 correctly letter-suffixed duplicate-passage records; the gold set
  and five CI gates (group completeness, cardinality, no-phantom-pairing, gold-set-green,
  reader-toggle parity) per [ALIGNMENT_SPEC §§6–7](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ALIGNMENT_SPEC.md).
- **Known quality caveats:** the `jsonl/` directory has grown well past the corpus of
  record — **269 files, of which 121 are post-report extras carrying 199,379 records**
  (re-measured 10-08-2026; was 7 files / 11,056 records on 11-07). They are excluded from
  every reported figure until a re-frozen conversion report folds them in, so a consumer
  reading the directory rather than the report will see ~1.35× more data than this
  statement describes;
  `web/corpus.db` (152 sources / 580,552 display lines) is a **runtime search view built
  from the reading HTML**, never a statistics source; the Rāmāyaṇa kāṇḍas are
  vulgate-numbered, so DCS crosswalk coverage there is capped at 54–76% by
  critical-edition excisions (an edition measurement, not annotation noise).

## G. Rights, licence, and distribution

Recorded once, per the org's standing policy that **rights uncertainty is not a stop**
([STANDING_POLICY_RIGHTS_UNCERTAINTY_IS_NOT_A_STOP_2026.md](https://github.com/gasyoun/Uprava/blob/main/docs/STANDING_POLICY_RIGHTS_UNCERTAINTY_IS_NOT_A_STOP_2026.md)):

| Layer | Rights position |
|---|---|
| **Sanskrit source text** | Public domain by age. |
| **Russian translations, pre-1930 editions** | Public domain (Petrov 1788/1914 reprint, Kaznacheeva 1909, Kamenskaya & de Manziarli 1914). |
| **Russian translations, 20th–21st c.** | In copyright, grey residual. **MG 08-08-2026 (H2440): ship all RU text** — this is a settled ruling, **not** a per-translator gate to re-open. The residual duty is *documenting* translators, done in [A41_TRANSLATORS.md](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/data/A41_TRANSLATORS.md) and the §5 Gītā table. Per-source rows: [RIGHTS_TABLE.md](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/export/RIGHTS_TABLE.md) (131 sources). |
| **Code / schema / this documentation** | Apache-2.0, per the repository [LICENSE](https://github.com/gasyoun/SamudraManthanam/blob/main/LICENSE). |
| **Imported DCS lemma/morphology layer (§6)** | **CC BY 4.0** (Hellwig) — redistributable with attribution; pinned snapshot [gasyoun/dcs-conllu@04e0778](https://github.com/gasyoun/dcs-conllu). |
| **vidyut 0.4.0 (evaluated, path C)** | MIT-family OSS. Evaluated and **not shipped** at current quality — no vidyut output is redistributed. |
| **VisualDCS chronology dates** | Crosswalked, never re-derived; inherits DCS's own dating uncertainty. |

**Citation split (already encoded in [CITATION.cff](https://github.com/gasyoun/SamudraManthanam/blob/main/CITATION.cff)):**
the software carries Zenodo concept DOI [10.5281/zenodo.21317315](https://doi.org/10.5281/zenodo.21317315);
the **corpus texts carry their own rights and must be cited by their print editions**. A
*dataset* DOI distinct from the software DOI is still owed — see the descriptor's human-gates
section.

## H. Intended use, and known misuse

**Intended:** Sanskrit–Russian retrieval and reading tools; bilingual lexicon induction
(the word-level companion is A42); diachronic translation and register study on a fixed
source text; low-resource Sa→Ru MT training data; a worked method case for
markup-aligned bitext.

**Known misuse to avoid:**

1. **Quoting 574,939 as the corpus size.** That total mixes both sides of each pair with
   dictionary heads, prose bodies and commentary — it overstates the bitext by ~7×. The
   citable size is the clean 1:1 verse-pair count.
2. **Treating dictionary heads or prose bodies as failed alignments.** They are intended
   monolingual reference content, outside the pair denominator by design.
3. **Reading the register metrics as translator quality.** TTR / Guiraud R / 18-stem loan
   retention are surface lexical proxies on ~700 segments per edition, not evaluations.
4. **Training an MT system on the Russian side without provenance.** Two texts are relay
   translations from English, and much of the Russian is translationese; a model trained
   on it learns that register.
5. **Citing verse numbers against a critical edition.** Numbering is largely vulgate.

## I. Maintenance and deprecation

Maintained in [gasyoun/SamudraManthanam](https://github.com/gasyoun/SamudraManthanam)
alongside the search platform that consumes it; the canonical layer is regenerated by
re-running the deterministic converter over the committed HTML sources. Every statistic in
the descriptor recomputes in one pass via
[papers/scripts/a41_stats.py](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/scripts/a41_stats.py)
(record: [A41_corpus_stats.json](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/data/A41_corpus_stats.json)).
**Status: active, not deprecated.** Open maintenance items: fold or formally exclude the
**121 post-report sources (199,379 records)** at freeze — the gap grew 18× between 11-07
and 10-08-2026 and is now the largest freeze-time decision; mint the dataset DOI; fill `—`
translator rows when the H821 `meta.json` credits are restored.

**Reproducibility note (10-08-2026, H2403).** `papers/scripts/a41_stats.py` used to abort
with `no such table: sources` from any fresh clone or linked worktree, because
`web/corpus.db` is gitignored (742 MB runtime view) and resolves to a 0-byte stub there.
The `corpus.db` probe feeds one reconciliation *footnote*, so it now degrades to null
fields with a stderr notice instead of taking the headline recompute down with it — the
"every statistic recomputes in one pass" claim is true from a clean checkout as of this
date, verified by re-running it in a fresh worktree.

_Dr. Mārcis Gasūns_
