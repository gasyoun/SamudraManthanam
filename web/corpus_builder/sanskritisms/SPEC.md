# SPEC — санскритизм layer (W3)

_Created: 14-07-2026 · Last updated: 14-07-2026_

Design spec for `web/corpus_builder/sanskritisms/`, ported from M. Rubanova's
2020 ВКР ("Полуавтоматическая морфологическая разметка параллельного
русско-санскритского корпуса", [`nkrya-parallel/diplom-rubanova/ВКР.mdx`](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/diplom-rubanova/%D0%92%D0%9A%D0%A0.mdx)).
Wave 3 of [`docs/ROADMAP_NKRYA_PARALLEL_RUSCORPORA_2026_2027.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ROADMAP_NKRYA_PARALLEL_RUSCORPORA_2026_2027.md)
§Wave 3. Answers Arkhangelskiy's review (the санскритизм/name-extraction
system existed only as ad-hoc notebooks, not a documented package).

## 1. Goal

Given a canonical-JSONL source (Russian `seg="ru"` segments), detect Sanskrit
loanwords/proper names ("санскритизмы") in the Russian text, resolve each to
a lemma, and emit (a) a per-source санскритизм lexicon and (b) a proper-name
index — the Russian-side supplement for a future НКРЯ submission and the
automatic указатели for samskrtam.ru.

## 2. What the ВКР actually built (5-stage algorithm)

The thesis tested five morphological-analyzer approaches (pymorphy2, mystem,
Snowball stemmer, KRS-difference, deeppavlov) on MBh book 3 ch. 1–5 and found
all of them weak in isolation (best: deeppavlov+KRS, 71/75 correct, still
5 false positives) — §3.1. It then built a **purpose-built rule-based
stemmer** (§3.3), validated end-to-end on MBh book 3 (44k words: 98% recall,
70% correct lemma) and Rāmāyaṇa book 3 (2441 sentences → 380 final entries).
That stemmer, not any of the off-the-shelf analyzers, is what this package
ports.

### 2.1 Inputs (ВКР's four sources → this repo's equivalents)

| ВКР source | This repo | Status |
|---|---|---|
| Sørensen index, >9000 MBh names | [`nkrya-parallel/diplom-rubanova/9460-osnov-sanskritskikh-slov.txt`](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/diplom-rubanova/9460-osnov-sanskritskikh-slov.txt) (9459 lines) | tracked, available |
| 354k-word Sanskrit dictionary dump (Cyrillic-converted) | — | **not in this repo** (never committed; only referenced in the thesis prose). Not rebuilt this pass — see §6 open item. |
| Foreign-words dictionary [Абрамович 1986] | [`.../foreign_words.txt`](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/diplom-rubanova/foreign_words.txt) (14,712 words) | tracked, available |
| OpenCorpora Russian morphological dict (КРС), 3M wordforms | `dict.opcorpora.txt` referenced in [`MANIFEST_LOCAL_ONLY.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/diplom-rubanova/MANIFEST_LOCAL_ONLY.md) but **absent from disk** in this environment (271 MB, gitignored bulk, never re-fetched) | **substituted** — see §3 |

Additionally tracked and reused directly (Rubanova's own finished output,
not raw input): [`3_INDEX.txt`](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/diplom-rubanova/3_INDEX.txt) /
`3_INDEX_oneword.txt` / `3_INDEX_phrases.txt` / `3_INDEX_options.txt` (the
finished MBh book-3 санскритизм index, 1830 rubrics — used as **gold data**
for regression tests, not as a lexicon input), `Ramayana_names_clean_united.txt`
(finished Rāmāyaṇa book-3 index, 380 rubrics — same role), `rus_index.txt` +
`rus_index_declined.txt` (293 Russian epithet phrases + their generated
case-forms, e.g. *самосозерцание → самосозерцания, самосозерцанию, ...*),
`decl_rules.txt` (Russian noun-declension endings table, informational —
the stemmer's 6 conditions in §3.3 already encode the load-bearing part of
this).

Per the roadmap, a third input is now available that didn't exist for the
ВКР: the **Sa→Ru word-alignment lexicon** (1,093,391 rows, confirmed by
direct count against
[`SanskritLexicography/RussianTranslation/src/corpus_lexicon.jsonl`](https://github.com/gasyoun/SanskritLexicography/blob/master/RussianTranslation/src/corpus_lexicon.jsonl)).
Each row is one SLP1/IAST Sanskrit word (`sa`, `slp1` fields) aligned to a
**Russian gloss** (`ru` field — a phrase, not a single transliterated token:
e.g. `vAcaspati` → `"Повелитель Речи"`). This is **not** a drop-in
replacement for the missing 354k Cyrillic-transliteration dictionary — using
it would require an IAST/SLP1→Cyrillic practical-transcription scheme, and
[`SHARED_CODE.md`](https://github.com/gasyoun/github-spine/blob/main/SHARED_CODE.md)
§1-2 confirms **there is still no Cyrillic support at all** anywhere in
`sanskrit-util`, org-wide. Building one accurately (ś/ṣ/ṛ/c handling, long
vowels, etc.) is a nontrivial sub-project on its own. **Deferred to a
follow-up (W3b)** rather than rushed — see §6.

### 2.2 Substituting for the missing КРС (§3, stage 2 of the thesis)

The thesis's "корпус русских слов" (КРС) is a plain word-membership check:
*is this Russian wordform attested in a large dictionary?* `pymorphy3` (the
maintained fork of the `pymorphy2` the ВКР itself used) ships a compact
DAWG-encoded OpenCorpora-derived dictionary via the `pymorphy3-dicts-ru`
package (already installed in this environment) and exposes exactly this
via `MorphAnalyzer().word_is_known(word)` — no 271 MB raw dump needed.
Verified against the thesis's own worked examples: `сома`/`яма`/`брахман`
are `word_is_known() == True` (already-absorbed loanwords — matches the
thesis's stage-2 finding that some санскритизмы are indistinguishable from
Russian dictionary words without the стage-5 capitalization rescue).
`ракшасов` → `False` (correctly not Russian). This substitution is
documented, not silent.

### 2.3 The stemmer algorithm (ported faithfully, §3.3.1–3.3.3)

Given a lowercased candidate word from the Russian text:

1. **Three-way ending class**: (a) ends in a consonant, (b) ends in
   `-а`/`-я`, (c) ends in `-и`/`-у`/`-ю` (treated as indeclinable).
2. **Six stem-matching conditions** against the concatenated lemma lists
   (Sørensen + curated Rubanova name lists; the missing 354k list is simply
   absent from the pool — see §6), checking suffix stripping for
   `-∅/-а/-у/-е/-ю/-о` (nominal endings), `-м`, `-в`, `-ми`, `-й`, `-х`
   with the length-delta rules exactly as specified in ВКР §3.3.1
   conditions 1–6 (worked examples: `вигана`→`виган`, `Ахаром`→`Ахар`,
   `джагудов`→`джагуды`, `Ашвинами`→`Ашвины`, `магхой`→`магха`,
   `сурашатрах`→`сурашатры`).
3. **КРС filter**: drop the candidate if `pymorphy3.word_is_known()` is
   true **and** the word is not in `foreign_words.txt` (§2.2 substitution;
   thesis §3.3.1 stage 2+4 combined — the ВКР's own final/best-performing
   stage-4 already excludes foreign-dictionary words from the КРС
   exclusion, so this package goes straight to that combined form).
4. **Capitalization rescue** (thesis §3.3.1 stage 5): if the *original*
   (non-lowercased) token starts with a capital letter and is not the first
   word of its sentence, run steps 1–2 again **without** the КРС filter —
   recovers loanword/proper-name collisions like `Сома`, `Яма`, `Кала`,
   `Парада`, `Арка` that are also common Russian words.
5. **Exclusion list**: pronouns/adverbs frequently mis-caught by the suffix
   rules (thesis §3.3.1: *тот, меня, нас, ...*) are hard-excluded before
   stage 2 — ported as a small Python constant, not re-derived per corpus
   (the thesis's list, extended if a corpus run surfaces new cases; any
   extension is logged, not silent).

### 2.4 Multi-candidate lemma disambiguation (§3.3.3)

When stage-2 stem matching finds more than one candidate lemma (e.g.
`ракшасов` → `ракшаси`/`ракшас`/`ракшаса`), apply, in order:

1. **The 9 suffix→number rules** from ВКР §3.3.3 (word-final letter of the
   *surface form* constrains whether the lemma must/must-not end in
   `-и`/`-ы`, i.e. be plural) — hardcoded as data, not re-derived from
   `decl_rules.txt` (that file is coarser and doesn't cover the compound
   `-ов`/`-ой`/`-ми`/`-х`/`-ам`/`-ям`/`-ом`/`-ем` cases the 9 rules target).
2. **Nominative-match shortcut**: if one candidate lemma equals the surface
   form itself and the ВКР's deeppavlov nominative-detection step is
   unavailable (see §2.5), skip this sub-step rather than guess.
3. **Attested-elsewhere check** (no deeppavlov needed — a corpus-wide
   wordform index, not context/case tagging): if the surface form appears
   in the source text in *only* this one form, treat it as indeclinable →
   lemma = surface form. If it appears in multiple forms, drop candidate
   lemmas ending in `-и` (indeclinable-only ending, thesis §3.3.3 worked
   example: *ракшас* vs *ракшаси*).
4. **Residual ties**: if more than one candidate remains after 1–3, keep
   all of them and flag the entry `needs_review: true` with
   `lemma_candidates: [...]` rather than fabricate a single answer (see §2.5).
5. **Plural/singular pseudo-duplicate merge** (thesis §3.3.3 final step,
   380-entry Rāmāyaṇa result): after building the index, merge rubrics
   whose first-word stems match (e.g. `апсара`/`апсары`) by keeping the
   plural (`-и`/`-ы`) form as canonical, per the thesis's own rule.

### 2.5 What is explicitly NOT ported

The thesis's residual ~20%-of-multi-candidate-cases resolver (§3.3.3) used
`deeppavlov`'s morphosyntactic case tagger (96% case accuracy, run over the
whole text) to pick a lemma when suffix rules alone were insuf­ficient — e.g.
disambiguating *Лакшмана* (nominative lemma) from *Лакшмана* (oblique form
of *Лакшман*) purely from sentence context. `deeppavlov` is a multi-GB BERT
model; it is not installed in this environment and is not being fetched for
this pass — a heavyweight, network-dependent NLP dependency is a
disproportionate cost for a residual disambiguation tail. Per this
codebase's own convention (`needs_review: true` rather than a fabricated
guess — see `CONVERTER_SPEC.md`/`fill_meta_phase0.py` precedent), unresolved
multi-lemma cases are **flagged, not silently resolved**. Reinstating
deeppavlov (or a lighter case-tagger) to close this gap is a documented
follow-up (§6), not attempted here.

## 3. Package layout

```
web/corpus_builder/sanskritisms/
  SPEC.md              this file
  README.md            usage + limitations (written after implementation)
  __init__.py
  lexicons.py           loads/merges the Cyrillic lemma lists (§2.1) + pymorphy3 KRS wrapper
  stemmer.py             the 6-condition matcher + exclusion list + capitalization rescue (§2.3)
  disambiguate.py        the 9 suffix rules + attested-elsewhere check + merge (§2.4)
  build_index.py         CLI: one JSONL source (or --all) -> lexicon.tsv + name_index.tsv + report.json
```

Output schema per source (`<slug>.sanskritisms.jsonl`, one row per
distinct lemma found):

```json
{"source": "03_mahabharata-aranyakaparva", "lemma": "ракшас",
 "surface_forms": ["ракшасов", "ракшасу"], "count": 7,
 "needs_review": false, "lemma_candidates": null}
```

Plus a `<slug>.sanskritisms_report.json` (counts, КРС-filtered count,
capitalization-rescued count, needs_review count) — mirrors the
`conversion_report.json` convention already used by `html_to_canonical.py`.

## 4. Validation plan (gold data already on disk)

Regression-test against the two texts the ВКР's own gold indices cover:

- **MBh book 3** (`03_mahabharata-aranyakaparva.jsonl`) vs
  `3_INDEX.txt`/`3_INDEX_oneword.txt` (1830 combined rubrics). Thesis's own
  reported final-stage numbers: 98% recall (1794/1827 matched), 785 new
  lines, 33 missing — this package's output is expected to be in that
  neighbourhood, not identical (deeppavlov-tier disambiguation is not
  ported, §2.5), and the test asserts a **floor**, not exact reproduction.
- **Rāmāyaṇa book 3** (`03_ramayana-aranyakanda.jsonl`) vs
  `Ramayana_names_clean_united.txt` (380 entries, the thesis's own final
  merged list).

Tests report precision/recall against these gold files rather than
asserting a hardcoded pass/fail threshold blindly copied from the thesis —
the numbers are logged in the test output and in
`ANNOTATION_3PATH_COMPARISON`-style report so a human can judge whether the
deeppavlov gap (§2.5) matters enough to close.

## 5. Corpus-wide run

`web/ingest` meta.json (`Index/lib/x86_64-win64/Data/*.meta.json`) currently
reports **136** `structure: verse` sources, of which **123** have canonical
JSONL in `web/corpus_builder/jsonl/` — exactly the roadmap's "123 verse
sources" figure. The 13 without canonical JSONL are the DBhP skandha
sources (H558, still HTML-only, `combined file > iRecordLimit`, open per
`.ai_state.md`) — **out of scope for this pass**, not silently dropped: the
build report will list them as skipped-no-jsonl.

## 6. Deferred follow-ups (not this pass)

- **W3b**: an IAST/SLP1→Cyrillic practical-transcription scheme, to unlock
  `corpus_lexicon.jsonl` (1.09M pairs) as a stem-list source beyond
  Sørensen's MBh-scoped 9460 names — would most help non-MBh/non-Rāmāyaṇa
  verse texts (Vedic corpus, Purāṇas, kāvya) where Sørensen has no
  coverage at all. Needs its own design pass (no existing org tool per
  `SHARED_CODE.md` §1-2) — do not build ad hoc inside this package.
- **W3c**: reinstate case-aware residual disambiguation (§2.5) with a
  lighter Russian case-tagger than deeppavlov if the gold-data precision/
  recall gap (§4) proves too large to accept.

_Dr. Mārcis Gasūns_
