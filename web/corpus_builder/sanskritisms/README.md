# sanskritisms — санскритизм detection layer

_Created: 14-07-2026 · Last updated: 14-07-2026_

Detects Sanskrit loanwords/proper names ("санскритизмы") in the Russian side
of the parallel corpus, resolves each to a lemma, and emits a per-source
санскритизм lexicon + proper-name index. Ported from M. Rubanova's 2020 ВКР
(see [`nkrya-parallel/diplom-rubanova/ВКР.mdx`](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/diplom-rubanova/%D0%92%D0%9A%D0%A0.mdx))
— Wave 3 of the [НКРЯ roadmap](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ROADMAP_NKRYA_PARALLEL_RUSCORPORA_2026_2027.md).
Full design rationale: [`SPEC.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/sanskritisms/SPEC.md)
— read it before modifying the algorithm; this file is usage + limitations.

## Usage

```bash
# single source
python -m web.corpus_builder.sanskritisms.build_index --source 03_mahabharata-aranyakaparva

# every verse-structure source with canonical JSONL
python -m web.corpus_builder.sanskritisms.build_index --all
```

Requires `pymorphy3` + `pymorphy3-dicts-ru` (in `web/requirements.txt`).
Output lands in `nkrya-parallel/export/sanskritisms/<slug>.sanskritisms.jsonl`
(one row per resolved lemma: `lemma`, `surface_forms`, `count`,
`needs_review`, `lemma_candidates`) + `<slug>.sanskritisms_report.json`
(source-level counts).

## Algorithm (summary — see SPEC.md for the full derivation)

1. Tokenize Russian text, track sentence-initial position.
2. Six stem-matching conditions against a Cyrillic Sanskrit-lemma pool
   (Sørensen's 9460-name index) — thesis §3.3.1.
3. КРС (Russian-dictionary) exclusion filter, substituted with `pymorphy3`
   (`word_is_known()`) since the thesis's own 271 MB OpenCorpora dump is not
   present in this environment — verified against the thesis's own
   loanword-collision examples (`сома`/`яма`/`брахман`).
4. Capitalization rescue: mid-sentence capitalized tokens bypass the КРС
   filter (recovers `Сома`/`Яма`/`Кала`-type collisions).
5. Multi-candidate lemma disambiguation: the 9 suffix rules + an
   attested-elsewhere/declinability check — thesis §3.3.3.
6. Plural/singular pseudo-duplicate merge (canonical = plural form).

## What is NOT ported (read before trusting recall/precision numbers)

- **deeppavlov-tier residual case disambiguation** (~20% of multi-candidate
  cases in the thesis) is not reimplemented — deeppavlov is a multi-GB BERT
  model and was judged disproportionate for a residual tail. Those cases are
  emitted as `needs_review: true` rows with `lemma_candidates` populated,
  never silently guessed.
- **The missing 354k-word Sanskrit dictionary** the thesis used alongside
  Sørensen's list was never committed to this repo and is not rebuilt here.
  The lemma pool is Sørensen's 9460 MBh-scoped names only — recall is
  correspondingly lower on non-MBh/non-Rāmāyaṇa texts (Vedic corpus,
  Purāṇas, kāvya), where Sørensen has essentially no coverage. See SPEC.md
  §6 (W3b) for the deferred fix (needs an IAST/SLP1→Cyrillic transcription
  scheme that doesn't exist anywhere in the org yet).
- **The 1.09M-pair `corpus_lexicon.jsonl`** (Sa→Ru word-alignment lexicon)
  is not integrated for the same reason — its `ru` field is a phrase-level
  gloss, not a Cyrillic lemma list.

## Measured results

Validated against the two gold indices already tracked in
`nkrya-parallel/diplom-rubanova/` — Rubanova's own finished output for these
two texts, used as regression gold, never as lexicon input
(`pytest -m corpus web/tests/test_sanskritisms.py`):

| Source | Gold | Predicted (resolved) | Recall | Precision |
|---|---|---|---|---|
| MBh book 3 (`03_mahabharata-aranyakaparva`) | `3_INDEX_oneword.txt`, 1164 names | 1339 lemmas | ~69% | ~60% |
| Rāmāyaṇa book 3 (`03_ramayana-aranyakanda`) | `Ramayana_names_clean_united.txt`, ~314 bare-word names | 343 lemmas | ~56% | ~54% |

These are floors the tests assert (0.55/0.45 and 0.40/0.35 respectively,
with margin below the measured numbers), not the thesis's own reported
figures (98% recall on MBh-3) — the gap is the deeppavlov-tier residual
above, not a bug in the ported stages.

**Corpus-wide run (14-07-2026, 123 of the 123 discoverable verse sources
with canonical JSONL — 1 skipped, `devibhagavata-purana`, still HTML-only
per H558):** 34,134 lemma entries across all sources, 11,070 (32.4%) flagged
`needs_review`, 42,277 capitalization-rescued detections, 135,623 Russian
segments scanned. Per-source counts vary enormously by how well the source
matches Sørensen's MBh/epic-scoped coverage — e.g. `13_mahabharata-anushasanaparva`
correctly yields 0 (its `ru` segments are placeholder `…` text, not real
translation — a pre-existing corpus gap, not a stemmer bug), while
`03_mahabharata-aranyakaparva` yields 1650.

## Files

- `SPEC.md` — full design spec, input inventory, honest scope boundaries.
- `lexicons.py` — Cyrillic lemma pool (Sørensen), КРС (pymorphy3) wrapper,
  foreign-words carve-out, Russian-epithet declined-forms loader.
- `stemmer.py` — tokenizer + the 6 stem-matching conditions + КРС filter +
  capitalization rescue.
- `disambiguate.py` — the 9 suffix disambiguation rules + attested-elsewhere
  check + plural/singular merge.
- `build_index.py` — CLI runner (`--source` / `--all`).

_Dr. Mārcis Gasūns_
