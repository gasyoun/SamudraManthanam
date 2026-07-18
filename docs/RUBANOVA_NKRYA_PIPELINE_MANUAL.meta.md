# Metadoc — RUBANOVA_NKRYA_PIPELINE_MANUAL.md

_Created: 14-07-2026 · Last updated: 18-07-2026_

Companion record for [`RUBANOVA_NKRYA_PIPELINE_MANUAL.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/RUBANOVA_NKRYA_PIPELINE_MANUAL.md).

## Purpose
The onboarding pack for E. A. Rubanova's НКРЯ pipeline — what her two notebooks
do, mapped to their data inputs, so the RU-morphology ([H905](https://github.com/gasyoun/Uprava/blob/main/handoffs/H905-Opus_SamudraManthanam_nkrya-ru-morphology_14.07.26.md))
and SA-morphology ([H906](https://github.com/gasyoun/Uprava/blob/main/handoffs/H906-Opus_SamudraManthanam_nkrya-sa-morphology-dcs-vidyut_14.07.26.md))
builds start from a documented baseline instead of the current approximation.

## Audience
The next agent/human implementing corpus morphology (H905/H906); anyone auditing
the sanskritism proper-name index or the Кали→кал regression.

## Provenance
- Handoff [H904](https://github.com/gasyoun/Uprava/blob/main/handoffs/H904-Opus_SamudraManthanam_nkrya-rubanova-code-review-manual_14.07.26.md); model **Opus 4.8 (`claude-opus-4-8[1m]`)**.
- Primary sources: [`sans_stemmer.ipynb`](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/diplom-rubanova/sans_stemmer.ipynb) + [`deeppavlov_parsing.ipynb`](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/diplom-rubanova/deeppavlov_parsing.ipynb) (Evgeniya Rubanova, updated by Marsel), read cell-by-cell; cross-checked against the port [`web/corpus_builder/sanskritisms/`](https://github.com/gasyoun/SamudraManthanam/tree/main/web/corpus_builder/sanskritisms) and the tracked diplom data files.

## Improvement backlog (ranked)
1. **Diff Marsel's update vs Evgeniya's original** — only the updated notebooks were provided; if the pre-Marsel version surfaces, document the delta. The declension-specific half (whether `Index_items_declension.ipynb` itself ever surfaces) is now closed by [H1207](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1207-Sonnet_SamudraManthanam_nkrya-ru-rubric-declension-port_17.07.26.md)'s in-port re-derivation — confirmed absent upstream too, generator rebuilt rather than mirrored.
2. **Reconstruct the SA/DCS extraction** (§6) — which DCS export + alignment Rubanova used; currently an honest gap, resolved by H906.
3. **Quantify the port regression** — measure Кали→кал-class false positives on a fixed sample once H905 restores the corpus filter, and record before/after here.
4. **Add worked micro-examples** — one sentence traced end-to-end through `search → unite2 → depppavlov_proc` with real forms.
5. **Local-run recipe** — a non-Colab driver (rewire `path`/`input()`, restore `384000.txt`/`dict.opcorpora.txt` paths) so the pipeline is reproducible from a clone.

## Limitations
- Documents the delivered (Marsel-updated) state, not the original→update diff.
- SA side has no code to review (DCS is the external source); §6 flags what must be reconstructed.
- Pipeline not end-to-end reproducible from a fresh clone (two large inputs are local-only).

## Revision history
| Date | Model | Change |
|---|---|---|
| 14-07-2026 | Opus 4.8 (`claude-opus-4-8[1m]`) | Created from the line-by-line review of both notebooks (H904). |
| 14-07-2026 | Opus 4.8 (`claude-opus-4-8[1m]`) | Added **Stage C** (`corpus_marker.ipynb`, taken from [upstream](https://github.com/evgeniarubanova/sanskrit_stemmer)): RU↔SA word alignment via a hand-built IAST→Cyrillic transliterator over a verse-block-aligned corpus. Corrected §6 — the SA side uses transliteration+alignment, **not** DCS; DCS morphology stays an H906 reproduction target. Noted opcorpora is absent even from upstream (third-party OpenCorpora). |
| 14-07-2026 | Opus 4.8 (`claude-opus-4-8[1m]`) | **H905 executed** — §8 delta table updated: the `rus_words`/Кали→кал row is now ✅ reproduced via pymorphy3, a per-token RU-morphology row added (`ru_morph.py`). See [`RU_MORPHOLOGY_H905_REPORT.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/RU_MORPHOLOGY_H905_REPORT.md). |
| 14-07-2026 | Opus 4.8 (`claude-opus-4-8[1m]`) | **H906 (DCS-gold) executed** — §8 delta table gains a per-token SA-morphology row: `dcs_align.py` aligns verses to DCS gold (`--sa-morph`), MBh ~99% coverage. See [`SA_MORPHOLOGY_H906_REPORT.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/SA_MORPHOLOGY_H906_REPORT.md). vidyut diff = follow-up. |
| 17-07-2026 | Opus 4.8 (`claude-opus-4-8`) | Added **§10 (runtime & the 2026-07 speedup)** — the port's epithet layer went flat-`re`-alternation → Aho-Corasick ([`_aho.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/sanskritisms/_aho.py)), byte-identical, **3.1×** on MBh Āraṇyakaparva; plus output-preserving hot-path fixes in all three notebooks (`open_files`/`search`/`index_unite`/`get_wordforms`/`capital_search`, `translate` memoize). Before/after table + root-cause in §10. [H1204](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1204-Opus_SamudraManthanam_rubanova-nkrya-speedup_17.07.26.md). |
| 18-07-2026 | Sonnet 5 (`claude-sonnet-5`) | **§5.1 updated** — the port now has its own rubric-declension generator ([H1207](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1207-Sonnet_SamudraManthanam_nkrya-ru-rubric-declension-port_17.07.26.md)), re-derived (not ported) since `Index_items_declension.ipynb`/`index_lone_declined_manual.json` are confirmed absent upstream too. Closes backlog item #1's declension-specific half — see the item's revised wording below. |
| 17-07-2026 | Opus 4.8 (`claude-opus-4-8`) | Companion answer doc [`RUBANOVA_NKRYA_RUBRIC_DECLENSION_STATUS_2024_11.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/RUBANOVA_NKRYA_RUBRIC_DECLENSION_STATUS_2024_11.md) — is the 2024-11 rubric-declension work (`Index_items_declension`) in the repo? Result (`rus_index_declined.txt`) yes + used by the epithet layer; generator (notebook / `pyphrasy` / synonym-split / accuracy log) no. Partially answers backlog #1 for the declension piece. |

_Dr. Mārcis Gasūns_
