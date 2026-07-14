# RU-side morphology + Кали→кал filter — build report (H905)

_Created: 14-07-2026 · Last updated: 14-07-2026_

What the RU-morphology pass ([H905](https://github.com/gasyoun/Uprava/blob/main/handoffs/H905-Opus_SamudraManthanam_nkrya-ru-morphology_14.07.26.md))
shipped, verified against the manual's documented behaviour. Model: Opus 4.8
(`claude-opus-4-8[1m]`). Builds on [`docs/RUBANOVA_NKRYA_PIPELINE_MANUAL.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/RUBANOVA_NKRYA_PIPELINE_MANUAL.md) §7–§8.

## The core insight — pymorphy3 IS Rubanova's opcorpora dictionary

Rubanova's primary false-positive filter was `rus_words`, built from
`dict.opcorpora.txt` (271 MB, ~2.9M forms). **pymorphy3 ships that same
OpenCorpora dictionary** (`pymorphy3-dicts-ru`), so `word_is_known(surface)`
answers exactly the "is this a real Russian wordform?" question — without the
271 MB dump, portable to a fresh clone, and faithful (she drove declension with
pymorphy2, the same family). The same library then supplies per-token
morphology. One dependency, both deliverables.

## Deliverable 1 — the Кали→кал filter (precision)

**Root cause** (reproduced live against the port): a lowercase common Russian
word colliding with a Sanskritism surface form was captured as a Sanskritism,
because the port dropped Rubanova's `rus_words` filter and only kept a
two-list approximation. Example: lowercase **«кала»** (genitive of the common
word *кал*) → captured as the Sanskritism **кала** (Kāla/time).

**Fix:** [`sanskritisms/filters.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/sanskritisms/filters.py)
gains `is_russian_word()` (pymorphy3 `word_is_known`, minus Rubanova's curated
collision exceptions); [`extract.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/sanskritisms/extract.py)
drops any **non-capitalized** candidate that is a known Russian word.
Capitalized proper names stay exempt (stage 5), so the goddess survives.

Verified (3-case probe, now a regression test):

| Input | Before | After |
|---|---|---|
| «Богиня **Кали** танцевала» (capitalized) | `кали` ✓ | `кали` ✓ (kept) |
| «собрал **кала** в поле» (lowercase common word) | `кала` ✗ (false pos) | *dropped* ✓ |
| «**Раму**» / «**ракшасов**» (proper name / non-Russian form) | kept | kept ✓ |

**Corpus impact** (`01_atharvaveda`, 1 source): index **41 → 37** lemmas, **4
false positives removed** — `матери`, `меда`, `сама` (genuine Russian words,
correct drops) and `амрита`.

**Honest trade-off:** `амрита` (amṛta) is a *genuine* Sanskritism that also
entered Russian as a loanword, so `word_is_known` drops it when lowercased — a
false negative. This is precisely the precision/recall trade-off Rubanova
documented; she mitigated it with a curated exception list (currently the 9
words she removed, in `RUS_WORD_FILTER_EXCEPTIONS`). **Follow-up:** expand that
exception list with corpus-wide evidence (a bounded review-sheet task) — not
done here to avoid unilaterally widening her curated set without data.

## Deliverable 2 — per-token RU morphology layer

New module [`ru_morph.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/ru_morph.py):
every Cyrillic token → **lemma · POS · case · number** (pymorphy3, top parse
with a hash-independent tie-break). Wired into
[`nkrya_export.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/nkrya_export.py)
behind `--ru-morph`, writing an additive `<slug>.ru_morph.tsv` next to the
para-XML/TMX/TSV.

Real run (`01_atharvaveda`): **3,057 RU tokens tagged**; POS distribution
NOUN 920 · NPRO 405 · VERB 381 · ADJF 350 · PREP 319 · CONJ 197 · PRCL 178 ·
ADVB 114 (well-formed). Determinism: byte-identical across two runs and across
`PYTHONHASHSEED=0` vs `12345` (the export's byte-identical gate).

**Why a sidecar, not inline `<w><ana/>`:** H905's own open question is
"coordinate the emitted markup shape with H906 so both sides land a consistent
per-token attribute scheme." Folding morphology inline into each `<se>` as НКРЯ
`<w><ana lex= gr=/>` would fix the RU scheme before the SA side (H906) agrees on
it. So the layer ships as a companion TSV now; the inline fold is the small,
mechanical H906-coordinated step.

## Reproduced vs still approximated

| Component | Status after H905 |
|---|---|
| `rus_words` opcorpora filter (Кали→кал) | ✅ **reproduced** via pymorphy3 (no 271 MB dump) |
| Per-token RU lemma/POS/case/number | ✅ **new** (`ru_morph.py`, sidecar) |
| pymorphy declension family (Rubanova used pymorphy2) | ✅ same family (pymorphy3) |
| DeepPavlov *residual case disambiguation* (`depppavlov_proc`) | ⚠️ **not ported** — pymorphy3 top-parse is context-free; DeepPavlov's UD parse resolves the ~20% residual ambiguous variants. A quality upgrade, validated against the local `deeppavlov_*.txt` gold, is a follow-up. |
| Inline `<w><ana/>` in the `<se>` | ⏭️ deferred to the H906-coordinated scheme |
| Exception-list tuning (амрита class) | ⏭️ follow-up (corpus-evidence review sheet) |

## Tests

`web/tests/test_nkrya_export.py` (+3, all green — 9 passed): morphology
shape+determinism, the Кали→кал filter regression (capitalized kept / lowercase
common word dropped / non-Russian form kept), and the `--ru-morph` sidecar
(header + shape + byte-identical across runs).

_Dr. Mārcis Gasūns_
