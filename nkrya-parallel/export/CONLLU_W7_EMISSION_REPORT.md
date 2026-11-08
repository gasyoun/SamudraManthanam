# W7 CoNLL-U emitter from DCS path B — emission + coverage report

_Created: 29-10-2026 · By: H6371 (Opus 4.8, `claude-opus-4-8`) · Machine-readable twin: [`conllu_coverage.json`](conllu_coverage.json)_

**H6371** — Wave 7 of [`docs/ROADMAP_NKRYA_PARALLEL_RUSCORPORA_2026_2027.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ROADMAP_NKRYA_PARALLEL_RUSCORPORA_2026_2027.md): the 4th emitter in [`nkrya_export.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/nkrya_export.py) (`--conllu`, v0.3.0) serializes the Sanskrit-side morphology of the DCS crosswalk (path B, CC BY 4.0) as CoNLL-U — UPOS + lemma + FEATS per token, **sandhi modeled as multiword-token range rows** (sandhied surface = the `n-m` range row, desandhied words = interior rows), matched through the **W2 three-tier text-keyed crosswalk** ([`nkrya_annotate.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/nkrya_annotate.py): exact / sandhi-skeleton / fuzzy). Coverage stays honest: only DCS-covered lines are emitted — MBh full, Rāmāyaṇa partial by construction (the W2 finding).

## 1. What shipped

| artifact | what it is |
|---|---|
| `web/corpus_builder/nkrya_export.py` v0.3.0 | the 4th emitter: `conllu()` + `--conllu` wiring, per-source `<slug>.sa.conllu`, `conllu_*` stats in `export_report.json` |
| `web/corpus_builder/dcs_conllu.py` | data half: parses the pinned [gasyoun/dcs-conllu](https://github.com/gasyoun/dcs-conllu) snapshot, indexes every DCS sentence under the W2 crosswalk keys, carries the explicit `DCS_UPOS_MAP` |
| `web/corpus_builder/conllu_validate.py` | stdlib-only CoNLL-U structural validator (E1–E8 + W1–W3 tripwires), CLI exit-code 0/1 |
| `web/tests/test_dcs_conllu.py` | hermetic gates (a)–(g) + corpus-marked real-data gate; 10 passed hermetic |
| this report + `conllu_coverage.json` | committed evidence; the per-source `.sa.conllu` bulk stays gitignored with the rest of `export/` (release-asset material, same rule as W1/W2 bulk) |

The sqlite of W2 (`dcs_full.sqlite`, Mac-local) is **not** needed: the pinned public mirror carries the same annotation already in CoNLL-U shape, so W7 runs anywhere after one sparse clone (recipe in `dcs_conllu.py` docstring: MBh 3 + Rām Bā/Ay/Ār, 557 chapter files, 36,986 sentences).

## 2. DCS → UD UPOS mapping table (explicit; unmapped never coerced)

Audited 29-10-2026 over the pilot books — 252,476 DCS word tokens, 11 distinct tags:

| DCS tag | → UPOS | observed | note |
|---|---|---:|---|
| NOUN | NOUN | 99,957 | identity |
| VERB | VERB | 49,213 | identity |
| PRON | PRON | 28,742 | identity |
| ADJ | ADJ | 28,499 | identity |
| ADV | ADV | 16,445 | identity |
| PART | PART | 16,406 | identity |
| **CONJ** | **CCONJ** | 10,132 | the only real map: DCS's pre-UD coordinating tag; DCS already tags subordinators SCONJ |
| NUM | NUM | 1,696 | identity |
| SCONJ | SCONJ | 1,061 | identity |
| ADP | ADP | 250 | identity |
| INTJ | INTJ | 75 | identity |
| _other_ | — | 0 | none observed; any future tag passes through **verbatim**, counted in `conllu_unmapped_upos`, and trips validator W1 |

Unmapped tags in the emission: **0** (all four sources). `_`/empty UPOS (format's own unspecified marker) passes through uncounted.

DCS feature extensions ride verbatim, inventoried, never coerced: `Case=Cpd` ×27,501 and the `Formation=*` verb-class key ×892 in the emitted sentences; the validator reports each as W2 (28,393 total). `LemmaId`/`OccId`/`Unsandhied` MISC columns pass through untouched.

## 3. Per-source coverage (real run, 29-10-2026)

| source | groups | lines | covered | coverage | sentences | words | MWT ranges | lemma cov. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `03_mahabharata-aranyakaparva` | 2,033 | 21,396 | 21,356 | **99.81%** | 21,356 | 149,885 | 24,583 | 100.0% |
| `01_ramayana-balakanda` | 2,268 | 4,633 | 3,536 | 76.32% | 3,536 | 23,585 | 3,762 | 100.0% |
| `02_ramayana-ayodhyakanda` | 4,307 | 9,093 | 4,936 | 54.28% | 4,936 | 33,605 | 4,920 | 100.0% |
| `03_ramayana-aranyakanda` | 2,447 | 5,147 | 2,827 | 54.93% | 2,827 | 18,897 | 2,981 | 100.0% |
| **total** | **11,055** | **40,269** | **32,655** | **81.09%** | **32,655** | **225,972** | **36,246** | **100.0%** |

The bands reproduce W2 exactly: MBh 3 ≈99.8% full; Rām kāṇḍas 54–76% (residue = genuine critical-edition excisions absent from DCS Rām — partial **by construction**, not a matcher defect); overall 81.09% vs W2's 81.1%. Tier mix: exact 23,795 / sandhi 7,077 / fuzzy 1,783 / unmatched 7,614; 362 lines matched more than one DCS sentence (smallest `sent_id` taken deterministically, `# dcs_ambiguous = yes` recorded, never hidden).

Each emitted sentence carries provenance comments: `# sent_id = <slug>:<group>:L<n>` (our group key), `# source_line` (our IAST surface), `# dcs_sent_id`, `# dcs_chapter`, `# dcs_match = tier`, plus the file-level CC BY 4.0 attribution block.

## 4. Honesty ledger (counted, never silently eaten)

| defect class | count | handling |
|---|---:|---|
| lemma missing (`_`) on emitted word rows | 0 | W3 tripwire exists; the 61 empty lemmas in the raw snapshot all fall outside emitted sentences |
| lemma damaged (mojibake, the W2 kḷp/ṝ family) | 17 | kept **verbatim**, counted per source (`conllu_lemma_bad`) — not faked, not dropped |
| DCS `# text` ≠ DCS token rows | 332 | DCS-side defect (unanalyzed words present in text, absent from tokens): `# text` = the reconstructable surface, DCS's original kept as `# dcs_text`, counted (`conllu_text_mismatch`) |
| unmapped UPOS tags | 0 | W1 tripwire exists; table above is exhaustive for the observed tagset |

## 5. Gates (all PASS, 29-10-2026)

```
cd web && PYTHONPATH=. python -m pytest tests/test_dcs_conllu.py -q
  → 10 passed, 1 deselected (corpus-marked real-data gate)
PYTHONPATH=. python -m pytest -m "not corpus"      # CI lane: no regressions
python corpus_builder/nkrya_export.py --all-pilot --conllu --out DIR   # ×2 runs
diff -rq run1 run2                                  → byte-identical (DETERMINISTIC)
python corpus_builder/conllu_validate.py DIR/*/*.sa.conllu
  → TOTAL 4 file(s): 32,655 sentences, 0 errors W2=28393   (exit 0)
```

## 6. Positioning + follow-up

UD_Sanskrit-Vedic covers Vedic only (~4k sentences); Classical Sanskrit is absent from the UD ecosystem — this layer (225,972 words / 36,246 sandhi MWTs on the pilot alone) is the ready input for that gap. **Official UD inclusion stays a follow-up decision after A41** (roadmap ruling 10); the A41 data section gains the format at its next revision (manuscript edits route to the private paper-repo lane).
