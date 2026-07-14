# Rubanova НКРЯ pipeline manual — Russian sanskritism indexing + morphology, and the Sanskrit (DCS) side

_Created: 14-07-2026 · Last updated: 14-07-2026_

The source-of-truth manual for **how E. A. Rubanova's 2020 HSE ВКР pipeline
actually works**, read line-by-line from her two notebooks (as updated by
Marsel) plus the tracked data artifacts. It exists so a future session does not
re-derive the method by trial and error, and so the two follow-on builds
([H905](https://github.com/gasyoun/Uprava/blob/main/handoffs/H905-Opus_SamudraManthanam_nkrya-ru-morphology_14.07.26.md)
RU morphology · [H906](https://github.com/gasyoun/Uprava/blob/main/handoffs/H906-Opus_SamudraManthanam_nkrya-sa-morphology-dcs-vidyut_14.07.26.md)
SA morphology) build on a documented baseline rather than the current
approximation. Produced under
[H904](https://github.com/gasyoun/Uprava/blob/main/handoffs/H904-Opus_SamudraManthanam_nkrya-rubanova-code-review-manual_14.07.26.md);
model Opus 4.8 (`claude-opus-4-8[1m]`).

> **Why this matters (MG, 14-07-2026).** The shipped
> [v0.4.0 export](https://github.com/gasyoun/SamudraManthanam/releases/tag/v0.4.0)
> is sentence-aligned only — the Sanskrit `se` carries an SLP1 transliteration,
> the Russian `se` carries plain text, **neither side is morphologically
> tagged**. "Otherwise it is not a corpus, but only a bilingua edition, not fit
> for НКРЯ." This manual is Wave 0: understand Rubanova's real method before
> re-implementing or extending it.

## 1. Source files and provenance

Rubanova's actual code is **two Colab notebooks**, now tracked in
[`nkrya-parallel/diplom-rubanova/`](https://github.com/gasyoun/SamudraManthanam/tree/main/nkrya-parallel/diplom-rubanova):

| Notebook | Role | Runtime |
|---|---|---|
| [`deeppavlov_parsing.ipynb`](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/diplom-rubanova/deeppavlov_parsing.ipynb) | **Stage A** — morphosyntactic parse of the Russian translation | ~mins; DeepPavlov `ru_syntagrus_joint_parsing` |
| [`sans_stemmer.ipynb`](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/diplom-rubanova/sans_stemmer.ipynb) | **Stage B** — build the sanskritism proper-name index from the Russian running text | ~4–5 min/file (pymorphy2 + nltk) |
| [`corpus_marker.ipynb`](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/diplom-rubanova/corpus_marker.ipynb) | **Stage C** — align each Russian sanskritism to its Sanskrit source word in the parallel corpus + colour-highlight both sides | ~secs/verse-block (pymorphy2 + a hand-built IAST→Cyrillic transliterator) |

**Upstream source.** All of Rubanova's files — the three notebooks, the data
lists, the corpus dumps, and the DeepPavlov outputs — are published at
[**github.com/evgeniarubanova/sanskrit_stemmer**](https://github.com/evgeniarubanova/sanskrit_stemmer)
(no licence stated; the repo description credits the ВКР). The three notebooks
are now mirrored (tracked) in this repo; the bulk data stays upstream / local-only
(§4, [`MANIFEST_LOCAL_ONLY.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/diplom-rubanova/MANIFEST_LOCAL_ONLY.md)).
`corpus_marker.ipynb` came from upstream (the two notebooks MG supplied did not
include it); the tracked `sans_stemmer.ipynb` is the fuller variant with the
consolidated driver cell, not upstream's exploded-cell version. **Marsel's
refactor is expected later** — this manual documents Evgeniya's version so the
two can be diffed.

All three were written for **Google Colab** (`google.colab.drive` mount, `path =
/content/drive/My Drive/Colab Notebooks/диплом/`). Stage A **must run first**:
Stage B's disambiguation consumes Stage A's output file `deeppavlov_<file>`.
Stages B and C share the same lemma-pool + filter setup but are independent runs.

**A/B produce an index; C does the alignment.** Stages A+B build a
printed-index-style автоматический указатель (automatic name index) for one
Russian translation, reproducing (semi-automatically) the hand-built index of
the printed MBh vol. 3. Stage C (`corpus_marker`) is the piece closest to a
*parallel corpus*: it word-aligns Russian sanskritisms to their Sanskrit
originals via a hand-built IAST→Cyrillic transliterator (§6). None of the three
emit this repo's НКРЯ export format; that is our own
[`nkrya_export.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/nkrya_export.py).

## 2. Pipeline at a glance

```
deeppavlov_parsing.ipynb                 sans_stemmer.ipynb
─────────────────────────                ──────────────────────────────────────
Russian translation text                 open_files()   ── 10 data inputs
   │                                         │
   │ nltk sent_tokenize                    decline()      ── pymorphy2 declines the
   │ strip digits/latin/punct                │              Russian-word rubrics
   ▼                                        group_sans()   ── split sanskritism lemmas:
DeepPavlov ru_syntagrus_joint_parsing        │              indeclinable / vowel-stem /
   │ (UD morph + syntax per token)           │              consonant-stem
   ▼                                        search()       ── scan text; match wordforms
deeppavlov_<file>                            │              by stem+ending rules; collect
   (sentence, [UD parse]) per line   ──────► capital_search()  capitalized proper names
                                             index_transform() ── map to printed-index rubrics
                                             unite1/unite2()    ── resolve sing/plur lemma
                                              │                    variants by ending
                                             depppavlov_proc()  ── resolve the residual
                                              │                    ambiguous variants using
                                              │                    Stage A's case tags
                                             index_unite/get_index()  ── merge wordforms,
                                              │                          write the index
                                             get_index_forms()  ── list every attested form
                                                                    per rubric

corpus_marker.ipynb (Stage C — independent, §6)
────────────────────────────────────────────────
verse-block-aligned corpus  ──► translate() IAST→Cyrillic (translation.txt +
  [N] <!--sanskrit--> … <!--rus--> …      correct_trans.txt)
        │                                 search() ── find RU sanskritisms, prefix-match
        ▼                                   each to its transliterated SA source word
  word-level SA↔RU alignment  ──► highlight() ── paral_corp.html (both sides colour-coded)
```

## 3. Stage A — `deeppavlov_parsing.ipynb` (Russian morphosyntax)

A single cell:

1. Prompts for `file` and `path`, mounts Google Drive.
2. Installs DeepPavlov + builds `ru_syntagrus_joint_parsing` (joint UD morphology
   **and** dependency parse, trained on SynTagRus).
3. `nltk.sent_tokenize` splits the translation into sentences.
4. Per sentence: strip a bracketed verse-number artifact
   (`[а-яА-Я](-\s-[0-9]+-\s)[а-яА-Я]+`), then remove digits, Latin letters, and
   punctuation (`reg_punct`), collapse whitespace.
5. `joint_model([text])` → append `(<cleaned sentence>,<predictions>)` to
   `deeppavlov_<file>`, one line per sentence.

The prediction string carries per-token UD fields including `case=nom|gen|dat|
acc|ins|loc`, which Stage B greps by regex (§5.6). Output examples are the
local-only `deeppavlov_*.txt` dumps inventoried in
[`MANIFEST_LOCAL_ONLY.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/diplom-rubanova/MANIFEST_LOCAL_ONLY.md).

## 4. Stage B `open_files()` — the ten data inputs

`sans_stemmer.ipynb` cell `open_files()` loads (numbering matches the code
comments):

| # | File | Tracked? | What it is | Size reported by the run |
|---:|---|:---:|---|---|
| 1 | `9460-osnov-sanskritskikh-slov.txt` | ✅ | **Sørensen's list** — ~9,460 Sanskrit word-stems (proper names, MBh) | 9,460 |
| 2 | `384000.txt` | ❌ local-only | Large sanskritism candidate list (`sans_dict`), items >2 chars, cleaned of Russian lemmas → `sans_dict2` | 352,592 after cleaning |
| 3 | `foreign_words.txt` | ✅ | **Russian dictionary of foreign words** (Абрамович) — loanwords to exclude; +6 hard-coded exceptions (`анил, анупа, ануп, крошу, ванг, прет`) so the Russian corpus does not filter needed sanskritisms | 14,687 |
| 4 | `dict.opcorpora.txt` | ❌ local-only, **271 MB** | **OpenCorpora Russian word corpus (КРС)** — parsed into `rus_words` (2.9M surface forms) + `lem_rus_words` (lemmas). **The primary false-positive filter.** | 2,914,651 |
| 5 | `3_INDEX_phrases.txt` | ✅ | Rubrics with annotations/explanations, hand-picked from the printed MBh vol.3 index → split into `phrase` (multiword/hyphen) + `repl` (single-word renames) | — |
| 6 | `3_INDEX_oneword.txt` | ✅ | Single-word rubrics from the printed index (`ones`) | — |
| 7 | `3_INDEX_options.txt` | ✅ | Epithet rubrics: `lemma: variant - epithet; …` → `opts` (context-disambiguated display) | — |
| 8 | `rus_index.txt` | ✅ | Rubrics that are Russian words/phrases (declined later by pymorphy2) | — |
| 9 | `pluralis_племена.txt` | ✅ | Sanskritisms that appear in the plural (ethnonyms/tribes), `tr` | — |
| 10 | `rusforms.txt` | ✅ | Hand-built exception list of Russian pronoun/adverb/verb forms that collide with generated sanskritism forms | — |

Plus `append if found.txt` (rubrics to add when a trigger name is present) read
inside `capital_search`/`index_transform`.

**Load-bearing detail (§4 #4 → the Кали→кал fix, see §7):** while building
`rus_words`, the code drops eight specific forms that are *really* sanskritisms
but also happen to be Russian words (`даму, дама, кишку, пилу, руру, турья,
турье, кшатрия, кшатрии`), and skips any opcorpora lemma already in
`forn + sans`. This hand-curated interplay between the Russian corpus and the
foreign/exception lists is exactly what suppresses false positives — and is the
piece the current port cannot fully reproduce.

## 5. Stage B — function-by-function

### 5.1 `decline(rus_index)` — pymorphy2
Declines each single-word Russian rubric across six cases
(`nomn gent datv accs ablt loct`) with `pymorphy2`, and hand-codes multiword
rubric declension via curated lists (`both`, `tcsh`, `except_last`, `last`) — a
per-phrase special-case table for the ~50 multiword rubrics. Output: `{rubric:
[declined forms]}`.

### 5.2 `group_sans(...)` — three declension buckets
Every lemma in `index3 + sans + sans_dict2` is bucketed by ending:
- **indeclinable** — ends `и/у/ю/е/о` → matched as-is;
- **vowel-stem (`decl`)** — ends `а/я/ы` → `(stem, lemma)` with the final vowel stripped;
- **consonant-stem (`stem`)** — everything else.
Builds two-letter prefix dicts (`decl_d`, `stem_d`) to speed matching. Removes a
hard exception list `exep` (prepositions, pronouns, conjunctions, adverbs) from
the indeclinables. Extracts hyphenated rubrics (`hyph`).

### 5.3 `search(...)` — the stemmer core
Per sentence (nltk-tokenized): clean text (drop digits/Latin/punct). Then:
1. **Rubric match** — for every Russian-index rubric and its declined forms, and
   every phrase/hyphen rubric, substring-match into the sentence.
2. **Per-word match** — for each text word: if capitalized and not
   sentence-initial → push to `upper_words` (candidate proper name); then match
   against the indeclinable set and the vowel/consonant-stem prefix dicts via the
   **six ending rules** (`-ми` → plural instrumental; `-ам/-ям` → plural dative;
   `-ов/-в` → plural genitive, lemma must be plural; `-ой` → sing.; `-х` →
   plural; `-у/-ю/-е/-о` → sing.). **Every branch is guarded by `word not in
   rus_words and word not in exep`** — the opcorpora filter in action.

### 5.4 `capital_search(...)`
For capitalized tokens not already found, re-run the ending rules against the
Sørensen list + one-word rubrics + plural list (no `rus_words` guard here —
capitalization is trusted as proper-name evidence). Then apply `append if
found.txt` and the epithet `opts` remap.

### 5.5 `index_transform(...)`, `unite1/unite2()`
Normalize to printed-index rubric names, drop `-ам`-final artifacts, apply
epithet options, apply `repl` renames, drop anything in `rusforms`. `unite1`
groups multi-candidate lemmas per (position, sentence); `unite2` resolves
singular/plural variants by the **ending → number** rules (e.g. text form on
`-в/-ми/-ам/-ям/-х` ⇒ pick the plural lemma; on `-у/-ю/-е/-о/-ом/-ем/-ой` ⇒ pick
the singular). Anything still ambiguous is deferred to `for_dpavlov`.

### 5.6 `depppavlov_proc(...)` — residual disambiguation via Stage A
Reads `deeppavlov_<file>`, indexes each sentence → its UD parse. For each
deferred ambiguous wordform, regex-matches the token's `case=` tag in a
±3-token window:
- `case=nom` → keep the wordform as lemma;
- oblique case → pick the variant whose full paradigm is **not** otherwise
  attested in the text (via `get_wordforms`), else fall back to the sing/plur
  ending heuristic.
This is the **only** place DeepPavlov is used in Stage B, and only for the
~20% residual the ending rules cannot settle (matching the thesis's own
measurement).

### 5.7 `index_unite / get_index / get_index_forms`
Merge singular/plural wordform pairs sharing a stem into one lexeme, choose the
consonant-final / non-`и/ы` representative, drop a small stop-list (`эха, свита,
рук, матери, правая`), write `automated_index_<file>` (the rubric list) and
`automated_index_forms_<file>` (every attested surface form per rubric).

## 6. Stage C — `corpus_marker.ipynb`, the RU↔SA aligner (and where DCS fits)

The third notebook is the one that actually touches the Sanskrit side, and it
**does not use DCS** — it aligns by transliteration. Its steps:

**Input — an already-aligned corpus.** `corpus_marker` reads
`aranyakaparva_corpus2.txt`, a manually-aligned parallel file whose verse blocks
carry the shape:

```
[1-4] <! -- sanskrit --> <IAST Sanskrit verse> <! -- rus --> <Russian translation>
```

A single regex splits it into `parts = [(number, sanskrit_part, russian_part)]`
(2,033 blocks for Āraṇyakaparva part 1). This is Rubanova's alignment granularity:
**verse-block**, not sentence or token — the token alignment is what Stage C then derives.

**IAST → Cyrillic transliterator (`translate`).** Driven by two tracked tables:
[`translation.txt`](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/diplom-rubanova/translation.txt)
(`Replace "x","y"` rules, single-char + multi-char digraphs) and
[`correct_trans.txt`](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/diplom-rubanova/correct_trans.txt)
(post-corrections). It converts a Sanskrit surface word to its Russian
spelling — e.g. `janamejaya→джанамеджая`, `vaiśampāyana→вайшампаяна`,
`sūryasyaiva→сурясяйва`. This is a **home-grown romanization-to-Cyrillic map, not
a morphological analyzer** — it produces spelling, not lemma/POS.

**Word alignment (`search`).** For each verse block: (1) run the same
sanskritism stemmer as Stage B over the Russian side to collect Russian
proper-name forms (`found`); (2) for each Sanskrit word, transliterate it and
prefix-match it against the found Russian forms; when they agree, record
`(number, [sans_index, sans_fragment], [rus_index, rus_lemma])`. Helper
functions `proc_short`/`proc_long` clip the matching Sanskrit substring
(compounds can contain several names — e.g. `surapitṛgaṇayakṣasevitaṃ` yields
both *ганы* and *якши*). Output: a **word-level SA↔RU alignment of sanskritisms**.

**Highlight (`highlight`).** Writes `paral_corp.html` colouring each aligned
sanskritism the same hue on both the Sanskrit and the Russian side — the visible
proof of the alignment.

### Where DCS comes in
MG's note that "the Sanskrit side initially used DCS as the markup source" refers
to a step **not present in any of these three notebooks** — Stage C's SA handling
is transliteration+alignment, giving *which Sanskrit word* a Russian name maps to,
**not** its lemma/case/number. So full Sanskrit morphological markup (lemma +
morph per token, the actual НКРЯ requirement) was never authored here; DCS is the
external resource that would supply it.

Consequently [H906](https://github.com/gasyoun/Uprava/blob/main/handoffs/H906-Opus_SamudraManthanam_nkrya-sa-morphology-dcs-vidyut_14.07.26.md)
is a *reproduction*, not a port: anchor per-token lemma+morph on DCS (gold),
verify coverage per corpus text (the Bhagavadgītā is absent from DCS per H848),
then add vidyut as a second opinion and diff. Stage C's transliterator + the
verse-block alignment are a **useful input** to H906 (they give the SA↔RU
token correspondence a DCS lookup can hang morphology on), but the morphology
itself must still be reconstructed — the honest gap is which DCS export Rubanova
(or a later step) intended.

## 7. The Кали→кал failure — root cause and the original's defence

The current port mis-stems the goddess **Кали** to the Russian stem **кал**.
The original does **not**, because of a layered filter the port drops:

1. **The opcorpora Russian corpus (`rus_words`, 2.9M forms).** In `search`,
   every candidate is gated by `word not in rus_words`. Russian inflected forms
   of кал are in opcorpora, so they are rejected as candidates.
2. **The foreign-word list + hard exceptions.** `foreign_words.txt` plus the
   six inline additions ensure genuinely-needed sanskritisms (претa, etc.) are
   not themselves filtered by the corpus.
3. **The `rusforms.txt` exception list** removes known Russian forms that
   collide with generated sanskritism surface forms.
4. **The capitalization rule.** A capitalized, non-sentence-initial token
   (Кали mid-sentence) is trusted as a proper name and routed through
   `capital_search`, where it is matched against Sørensen/rubric lists rather
   than stemmed against Russian vocabulary.

The port keeps (2)–(4) in approximate form but **cannot keep (1)**:
`dict.opcorpora.txt` is 271 MB and untracked, so the port's own `filters.py`
docstring states the corpus filter "is NOT ported… Its role is approximated."
That approximation is the Кали→кал regression. **Fixing it is the heart of
[H905](https://github.com/gasyoun/Uprava/blob/main/handoffs/H905-Opus_SamudraManthanam_nkrya-ru-morphology_14.07.26.md).**

## 8. Original vs current port — the delta (H905 work-list)

The re-implementation in
[`web/corpus_builder/sanskritisms/`](https://github.com/gasyoun/SamudraManthanam/tree/main/web/corpus_builder/sanskritisms)
is honest about being an approximation. What it reproduces, approximates, and
drops:

| Component | Original (notebooks) | Current port | Gap for H905 |
|---|---|---|---|
| Proper-name lemma pool | Sørensen 9,460 **+ `384000.txt` (352k)** + one-word rubrics | Sørensen + one-word only | **Restore the 352k candidate pool** (local-only) or justify dropping it |
| Russian-word filter | **opcorpora 2.9M (`rus_words`)** | ✂️ dropped (271 MB) — approximated by foreign+rusforms+capitalization | **Root cause of Кали→кал** — restore/replace the corpus filter |
| Declension of Russian rubrics | **pymorphy2** (`decline`) + curated multiword table | reverse index from `decl_rules.txt` only | pymorphy2 rubric declension not reproduced |
| Sanskritism form generation | backward stemming (six ending rules) | forward generation from `decl_rules.txt` (avoids pymorphy2 mis-tagging) | port's approach is arguably *better*; keep, but verify against original output |
| Residual case disambiguation | **DeepPavlov** UD `case=` (`depppavlov_proc`) | ✂️ dropped — keeps `ambiguous=True` | **Wire a RU tagger** (deeppavlov or lighter), validate vs local `deeppavlov_*.txt` gold |
| Sentence tokenization | nltk punkt | own regex tokenizer | minor; verify parity |
| Epithet / options / append rubrics | `3_INDEX_options/phrases`, `append if found` | `annotations.py` reproduces | reproduced |
| Sing/plural merge | `unite2` + `index_unite` | `disambiguate.py` (order-independent, H821 fix) | reproduced + hardened |
| RU↔SA word alignment | **`corpus_marker`** — IAST→Cyrillic transliterator + prefix-match over a verse-block-aligned corpus | ✂️ **not ported at all** | new capability for H906: reuse the transliterator + alignment to hang DCS morphology on SA tokens |

**Note on scope.** The notebooks build a *printed-style name index*, not
per-token corpus morphology. H905's actual target — per-token POS/case/number/
lemma on every `seg=ru` segment of the export — needs the DeepPavlov UD parse
(Stage A) applied to the corpus and its tags emitted, which the index pipeline
uses only internally. The sanskritism index is a **second** RU-side deliverable
(proper-name layer), distinct from full morphological tagging; H905 covers both.

## 9. Limitations of this manual

- **No Sanskrit *morphology* was authored** — Stage C aligns and transliterates
  the SA side but produces no lemma/POS; DCS is the external morphology source
  and which DCS export was intended is not in the provided files (§6). H906
  reconstructs it.
- **Marsel's update scope** — the two notebooks MG supplied are "Evgeniya's code
  as updated by Marsel" and `corpus_marker` is from her upstream repo; the
  original pre-Marsel version was not provided, so this manual documents the
  delivered state, not the diff. Marsel's refactor is expected later for
  comparison.
- **Local-only / upstream-only inputs** — `384000.txt` (352k pool) and the corpus
  dumps live at [the upstream repo](https://github.com/evgeniarubanova/sanskrit_stemmer)
  and local-only; **`dict.opcorpora.txt` (271 MB) is not even in the upstream
  repo** — it is third-party [OpenCorpora](http://opencorpora.org/) data and must
  be fetched separately for H905. The pipeline cannot be re-run end-to-end from a
  fresh clone without these (inventoried in `MANIFEST_LOCAL_ONLY.md`).
- **Colab-bound** — paths and the Drive mount are Colab-specific; a local re-run
  needs the `path`/`input()` prompts rewired.

_Dr. Mārcis Gasūns_
