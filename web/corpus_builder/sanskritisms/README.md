# sanskritisms -- sanskritism extraction + proper-name index (H760)

_Created: 12-07-2026 · Last updated: 12-07-2026_

Ports [Wave 3 of the НКРЯ / ruscorpora.ru export programme](https://github.com/gasyoun/Uprava/blob/main/handoffs/H760-Sonnet_SamudraManthanam_nkrya-wave3-sanskritism-layer-corpus-package_12.07.26.md):
Е. Рубанова's ВКР ("Полуавтоматическая морфологическая разметка
параллельного русско-санскритского корпуса" -- [`nkrya-parallel/diplom-rubanova/ВКР.mdx`](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/diplom-rubanova/ВКР.mdx),
original code: [github.com/evgeniarubanova/sanskrit_stemmer](https://github.com/evgeniarubanova/sanskrit_stemmer))
sanskritism-extraction method from her notebooks into a documented, tested
package, run across every ru-bearing verse source in this repo's canonical
corpus.

Directly answers Arkhangelskiy's ВКР review point that the санскритизм
extraction lived only in notebooks, not a reusable tool.

## What a "санскритизм" is here

Per the thesis's own definition (§2.1): not just common loanwords
(*йога, карма, гуру*) but **any** Sanskrit proper name or term appearing in
Russian running text -- people, places, ethnonyms, plants/animals, objects,
and ritual terms. This package extracts that broad category, then presents
it in two views (see "Outputs" below): a raw counting **lexicon** and an
annotated, "printed-index"-style **index**.

## Algorithm (ported from ВКР §3.2-§3.3.3)

1. **Lemma pool** (`lexicon.py`): union of Sørensen's ~9,460 Mahābhārata
   proper names (`9460-osnov-sanskritskikh-slov.txt`) and the printed MBh
   vol.3 index's single-word items (`3_INDEX_oneword.txt`, covers
   plants/objects/terms a name-only list misses).
2. **Paradigm generation** (`paradigms.py`): each lemma is classified into
   one of three Russian declension classes from `decl_rules.txt`
   (consonant stem / -а stem / -я stem; -и/-у/-ю-final lemmas are
   indeclinable per §2.4) and expanded to its full case paradigm. A
   reverse index maps every generated surface form back to its lemma(s).
3. **Matching** (`extract.py`): every Cyrillic token in a source's `seg=ru`
   text is looked up in the reverse index. A capitalized, non-sentence-
   initial token is trusted as a proper name (§3.3.1 stage 5); other
   matches must survive the `foreign_words.txt` / `rusforms.txt` exclusion
   filters (`filters.py`).
4. **Disambiguation** (`disambiguate.py`): when a surface form maps to
   >1 lemma, the thesis's nine suffix-based rules (§3.3.3) narrow the
   candidate set; a rule that would eliminate every candidate is skipped.
   Residual multi-candidate matches are kept `ambiguous=True` rather than
   force-resolved.
5. **Number merge** (`disambiguate.py`): singular/plural pseudo-duplicate
   lemmas sharing a stem (e.g. апсара/апсары) are merged into the plural
   form (§3.3.3 final step, 525->380 rubrics on her own Rāmāyaṇa pilot).
6. **Annotation** (`annotations.py`): for the index view, each surviving
   lemma is displayed via, in priority order: a context-resolved homonym
   option (`3_INDEX_options.txt`, disambiguated against the containing
   verse group's text), a curated rubric (`3_INDEX_phrases.txt` /
   `append if found.txt`), or the bare lemma.
7. **Epithet layer** (`extract.py`, independent of 1-6): curated Russian
   epithet phrases and their declined forms (`rus_index.txt` /
   `rus_index_declined.txt`, e.g. "Великий Владыка") are searched directly
   in the running text as a second index layer, exactly as the thesis
   used them (§3.3.2) -- these refer to Sanskrit entities by translation,
   not transliteration, so they never go through the paradigm/lemma path.

## Scope vs. the thesis (deliberate, documented deviations)

- **Forward paradigm generation from `decl_rules.txt`, not the thesis's
  six ad hoc backward-stemming sub-conditions (§3.3.1 stage 1) or its
  `pymorphy2.lexeme`-based generation (§3.2).** `decl_rules.txt` *is* the
  thesis's own hand-authored declension table; driving generation from it
  directly is more robust than either alternative (pymorphy2 frequently
  mis-tags Sanskrit names as verbs/adjectives, corrupting the generated
  paradigm -- e.g. Адхармахан -> a fictitious verb). Cross-checked against
  the tracked `Ram3_automated_index_forms.txt` reference output
  (индра -> индра/индре/индры/индрой/индру): exact match.
- **No Russian-word-corpus (КРС) filter.** The thesis's most effective
  false-positive filter was a 3M-form OpenCorpora dump
  (`dict.opcorpora.txt`) -- untracked, 271 MB, not portable to a fresh
  clone. Its role is approximated here by `foreign_words.txt` +
  `rusforms.txt` (the thesis's own hand-built exception list) plus the
  capitalization-boost stage, which the thesis itself found sufficient for
  proper names specifically (§3.3.1 stage 5 achieved ~1 false positive per
  chapter on its own).
- **No deeppavlov case/context disambiguation (§3.3.4).** The thesis's
  final ~20%-residual-ambiguity cases were resolved with deeppavlov's
  syntactic case analysis -- not in this repo's stack. Those cases are
  surfaced as `ambiguous=True` with every surviving candidate lemma,
  rather than forced to a single pick.
- **No cross-lingual Sanskrit<->Russian alignment (ВКР §3.4).** That is a
  distinct deliverable (relating IAST originals to their Russian
  translations token-by-token) outside this handoff's scope, which is
  Russian-side extraction only ("Do NOT: No dictionaries -- running text
  only").
- **`Ramayana_names*.txt` are treated as reference/validation data, not
  inputs.** Cross-checking their provenance against the thesis text
  (§3.3.3: "программа выдала 525 рубрик... 380 рубрик") confirms these are
  Rubanova's own *output* artifacts from running her stemmer over
  Rāmāyaṇa vol. 3 -- not curated inputs to feed forward. `tests/test_sanskritisms.py`'s
  `test_real_extraction_overlaps_thesis_ramayana_reference` uses
  `Ramayana_names_clean_united.txt` (her final 380-rubric output) as a
  soft overlap check against this package's independent run over the same
  source.

## Inputs (tracked, consumed not rebuilt)

All under [`nkrya-parallel/diplom-rubanova/`](https://github.com/gasyoun/SamudraManthanam/tree/main/nkrya-parallel/diplom-rubanova):
`9460-osnov-sanskritskikh-slov.txt`, `3_INDEX_oneword.txt`,
`decl_rules.txt`, `foreign_words.txt`, `rusforms.txt`,
`3_INDEX_phrases.txt`, `3_INDEX_options.txt`, `append if found.txt`,
`rus_index.txt`, `rus_index_declined.txt`. See
[`MANIFEST_LOCAL_ONLY.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/diplom-rubanova/MANIFEST_LOCAL_ONLY.md)
for what else lives in that directory (untracked bulk, not consumed here).

Corpus text: every `web/corpus_builder/jsonl/*.jsonl` source carrying a
`seg=ru` record (131 of 179 sources as of 12-07-2026;
`discover_ru_sources()` re-detects this at run time, not hardcoded).

## Outputs

Per source (`build_all.py`, gitignored -- in-copyright running text, same
rights posture as the H754 export artifacts):

- `<slug>.lexicon.json` -- every extracted lemma: counts, surface forms
  seen, sample verse-group ids, ambiguity flag.
- `<slug>.epithets.json` -- the parallel Russian-epithet-phrase layer.
- `<slug>.index.json` -- the sorted, annotated "printed-index" view.

Corpus-wide, **committed**: [`nkrya-parallel/sanskritisms/COUNTS_REPORT.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/sanskritisms/COUNTS_REPORT.md)
(H760 deliverable 2's "validation/counts report").

## Usage

```sh
# one source
python web/corpus_builder/sanskritisms/build_all.py --out nkrya-parallel/sanskritisms --source 03_mahabharata-aranyakaparva

# every ru-bearing source (regenerates COUNTS_REPORT.md)
python web/corpus_builder/sanskritisms/build_all.py --out nkrya-parallel/sanskritisms
```

## Tests

`web/tests/test_sanskritisms.py`, this repo's hermetic/`-m corpus`
convention:

```sh
cd web; PYTHONPATH=. python -m pytest tests/test_sanskritisms.py            # hermetic
cd web; PYTHONPATH=. python -m pytest tests/test_sanskritisms.py -m corpus  # + real data
```

## Wired into

[`nkrya_export.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/nkrya_export.py)'s
per-source export directory (`<out>/<slug>/`, alongside the para-XML/TMX/TSV
triple) -- see [`export_source`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/nkrya_export.py)'s
`sanskritisms_index` parameter and Wave 5's samskrtam.ru указатели consumer
(roadmap, forthcoming).

_Dr. Mārcis Gasūns_
