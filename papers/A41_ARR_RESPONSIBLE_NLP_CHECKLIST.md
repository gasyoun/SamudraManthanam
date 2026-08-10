# A41 — ARR Responsible NLP Research checklist (filled)

_Created: 10-08-2026 · Last updated: 10-08-2026_

Filled checklist for
[papers/A41_parallel_corpus_descriptor.md](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/A41_parallel_corpus_descriptor.md)
— *Samudra Manthanam: A Markup-Aligned Sanskrit–Russian Parallel Corpus of 148 Sources*.

**Checklist version:** fetched from
[aclrollingreview.org/responsibleNLPresearch](https://aclrollingreview.org/responsibleNLPresearch/)
on **10-08-2026**; the page states it was *"Updated for ARR October 2024 cycle by Anna
Rogers, based on discussions with ARR board"* (originally the NAACL 2022 program chairs;
filed through the submission form rather than as a separate PDF since February 2024).

**Venue calibration.** A41's target venues are LREC-COLING (resource track) / eLex /
JOHD. Only the LREC-family target is ARR-adjacent, so this file is a **quality gate
applied always** and an *attached submission artifact* only for the ACL-family route
(per [/paper-submission-pack](https://github.com/gasyoun/claude-config/blob/main/commands/paper-submission-pack.md)
Phase 3.5). Filled by Fable 5 (`claude-fable-5`) under
[H2403](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2403-Fable_SamudraManthanam_a41-resource-paper-acl-uplift_07.08.26.md).

## A. For every submission

| # | Item | Answer | Where / justification |
|---|---|---|---|
| **A1** | Limitations discussed? | **yes** | §8 Limitations — six items: the 78,219-vs-78,139 snapshot dependence, monolingual-is-not-bitext (≈10,024 segments), heterogeneous provenance, crosswalked-not-re-derived dates, surface-only register metrics, `structure`-class reclassification. Robustness across sources is stated per-source, not averaged away (§6.1 coverage 54–99.8%). |
| **A2** | Risks discussed? | **yes** | §8 + [data statement](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/data/A41_DATA_STATEMENT_SAMUDRA_SA_RU_CORPUS.meta.md) §H "known misuse": headline inflation (~7×), category-error denominators, register metrics misread as translation quality, translationese/relay-translation contamination of MT training, vulgate-vs-critical verse citation. No dual-use or population-harm surface: the data is published premodern literature and its print translations. |

## B. Scientific artifacts (used **and** created)

| # | Item | Answer | Where / justification |
|---|---|---|---|
| **B1** | Creators of used artifacts cited? | **yes** | DCS (Hellwig) with pinned snapshot [gasyoun/dcs-conllu@04e0778](https://github.com/gasyoun/dcs-conllu); vidyut 0.4.0 (ambuda-org); VisualDCS for the date spine; GRETIL; the Sanskrit Library; Itihāsa (Aralikatte et al. 2021) as nearest neighbor. Every Russian translator credited by name in [A41_TRANSLATORS.md](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/data/A41_TRANSLATORS.md) (19 distinct credits / 63 sources with committed metadata). |
| **B2** | Licences / terms discussed? | **yes** | Data statement §G, seven-row table: Sanskrit PD; RU pre-1930 PD; RU 20th–21st c. in-copyright grey with the settled **ship-all** ruling (MG 08-08-2026, H2440); code Apache-2.0; DCS layer **CC BY 4.0** (redistributable with attribution); vidyut MIT-family, **evaluated but not shipped**; DCS dates crosswalked not re-derived. Per-source rows: [RIGHTS_TABLE.md](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/export/RIGHTS_TABLE.md). |
| **B3** | Intended-use compatibility? | **yes** | Data statement §H states this corpus's intended use and its five known misuses. Used artifacts are consumed within their terms: the DCS layer is redistributed **with** CC-BY attribution; vidyut is run locally as an evaluated candidate and its output is not redistributed at all (§6.4 policy "C not shipped"). |
| **B4** | PII / offensive content checked? | **yes (n/a for PII)** | No personal data: every segment is published print text, premodern Sanskrit literature plus its published translations. The only living-person data is **translator attribution**, which is bibliographic credit deliberately recorded, not incidental PII. No anonymisation is applicable or desirable. Offensive-content screening not performed and not claimed — these are canonical literary texts carrying their own historical value systems (varṇa, gender roles in the dharmaśāstra), presented as edited sources, not as endorsed content. |
| **B5** | Artifact documentation (domain, languages, demographics)? | **yes** | The [data statement](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/data/A41_DATA_STATEMENT_SAMUDRA_SA_RU_CORPUS.meta.md) is the B5 artifact: §A rationale, §B language varieties (Vedic→late classical Sanskrit; Russian 1788–2021 incl. pre-reform orthography), §C author/translator demographics, §D **no annotator population**, §E genre/situation, §F preprocessing and quality. Schema in [ALIGNMENT_SPEC.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ALIGNMENT_SPEC.md) + descriptor §3.3. |
| **B6** | Relevant statistics (counts, splits)? | **yes** | §4 in full: 148 sources / 574,939 records; 119 / 15 / 14 structure split with 208,230 / 321,672 / 45,037 records; `seg`-role totals; cardinality 78,139 `1:1` / 10,009 `0:1` / 80 `1:0` over 88,228 verse groups (88.56% clean). §6.1 per-source crosswalk coverage. **No train/dev/test split is defined** — this is a resource descriptor, not a modelling paper; splitting is left to consumers (and flagged as such, so "no splits" is a stated design decision, not an omission). |

## C. Computational experiments

The paper trains nothing and tunes nothing; the one measurement pass is the §6 three-path
annotation comparison, which is a **deterministic tooling comparison**, not a learned
system. Items answered on that basis.

| # | Item | Answer | Where / justification |
|---|---|---|---|
| **C1** | Parameters / compute budget / infrastructure? | **partial** | No model is trained or fine-tuned, so parameter counts do not apply; vidyut-cheda 0.4.0 is a rule/lexicon-based segmenter, not a parameterised network. Both the statistics pass and the annotation pass run **locally on one CPU workstation in minutes**, with zero API spend and no GPU. Stated as a bounded claim rather than a measured GPU-hour figure — the exact wall-clock is not instrumented. |
| **C2** | Experimental setup / hyperparameter search? | **yes** | No hyperparameter search was run (nothing is trained). The one tunable is the crosswalk matcher, whose thresholds are **declared and committed**: three tiers (exact → consonant-skeleton with a ≥0.70 vowelled-similarity floor → difflib fuzzy ≥0.90), fixed sample seed 759 for the 51-group adjudication draw, first-hit policy on the 362 multiply-matching lines. Values recorded in [annotation_3path_metrics.json](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/export/annotation_3path_metrics.json) `_meta`, method in [ANNOTATION_3PATH_COMPARISON.md](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/export/ANNOTATION_3PATH_COMPARISON.md). |
| **C3** | Descriptive statistics / single-run vs mean? | **yes** | Every figure is a **single deterministic run over a frozen corpus, not a mean over seeds**, and is labelled as such — error bars would be meaningless for a census. Stability is evidenced by re-execution instead: the 26-06 / 08-07 / 11-07 re-counts are byte-identical (78,139 / 10,009 / 80). Per-source figures are reported individually (§6.1) rather than as one average, because coverage varies 54.3%–99.8% and a mean would hide the edition effect. Jaccard agreement is reported as a per-source range (0.28–0.35), not a single point. |
| **C4** | Package / tool versions reported? | **yes** | vidyut 0.4.0 (`vidyut-cheda`, local data pack); DCS snapshot pinned at commit `04e0778`; generator `nkrya_annotate.py` v0.1.0 with 6 green tests; `a41_stats.py` output self-dated `2026-07-11`; runtime view layer tagged `v2026.07.06`; service dependencies pinned exactly in [web/requirements.txt](https://github.com/gasyoun/SamudraManthanam/blob/main/web/requirements.txt). |

## D. Human annotators / participants

| # | Item | Answer | Where / justification |
|---|---|---|---|
| **D1** | Instructions text? | **n/a** | No crowdworkers or recruited participants. |
| **D2** | Recruitment / payment? | **n/a** | Nobody was recruited or paid. |
| **D3** | Consent? | **n/a** | No data about people is collected; translator names are published bibliographic credit. |
| **D4** | Ethics review / exemption? | **n/a** | No human-subjects research; published-text analysis only. |
| **D5** | Annotator demographics? | **n/a** | No annotator population — the alignment is extracted from source markup and the lemma layer is imported from DCS. The two human passes are the **author's own** (~25-group gold set; the pending 51-group adjudication), disclosed as single-author work rather than presented as independent annotation. Data statement §D. |

## E. AI assistants

| # | Item | Answer | Where / justification |
|---|---|---|---|
| **E1** | AI-assistant use disclosed? | **yes** | Disclosed in the descriptor's draft-status block and per-pass provenance: prose drafting, statistics-script authoring and the §6 comparison were carried out with Claude Code (Fable 5, `claude-fable-5`, and named tiers per pass; the ACL uplift pass is H2403, Fable 5). **No AI system produced any alignment, translation, lemma, or corpus content**: extraction is deterministic code and the lemma layer is human-curated DCS. Every reported statistic recomputes from committed scripts, so AI involvement is in drafting and tooling, never in the data of record. |

## Remaining work surfaced by this checklist

1. **Dataset DOI ≠ software DOI [@DO, a human decides].** [CITATION.cff](https://github.com/gasyoun/SamudraManthanam/blob/main/CITATION.cff) already carries Zenodo concept DOI [10.5281/zenodo.21317315](https://doi.org/10.5281/zenodo.21317315) for the **software**; the corpus release still needs its own dataset DOI before the data-availability statement is complete.
2. **C1 is `partial` by choice** — compute is described qualitatively (local CPU, minutes, no GPU/API). Instrumenting one timed run would raise it to `yes`; cheap, not blocking.
3. **B6 has no splits by design** — if a reviewer expects an MT-ready benchmark, that is the B4 unit of the [ACL footprint roadmap](https://github.com/gasyoun/Uprava/blob/main/ROADMAP_ACL_ANTHOLOGY_FOOTPRINT_2026_2027.md) (interlinear Sa→Ru MT resource), not A41.
4. **§6.4 adjudication verdict** (51 groups, seed 759) still owed before headline freeze.
5. **Headline freeze** — choose 78,219 or 78,139 as the lead figure, footnote the other.
6. **Extras census grew 18× (found by this pass, B6-relevant).** The `jsonl/` directory now
   holds 269 files with **121 post-report extras / 199,379 records** (was 7 / 11,056 on
   11-07-2026). None enters any reported figure, and the corpus of record is byte-stable
   across four re-counts — but a reviewer comparing the directory to the paper will see
   ~1.35× more data than the descriptor accounts for. Fold or formally exclude via a
   re-frozen conversion report before submission (§3.1, §11 row 1).

_Dr. Mārcis Gasūns_
