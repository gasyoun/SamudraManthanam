# Metadoc — RUBANOVA_NKRYA_PIPELINE_MANUAL.md

_Created: 14-07-2026 · Last updated: 14-07-2026_

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
1. **Diff Marsel's update vs Evgeniya's original** — only the updated notebooks were provided; if the pre-Marsel version surfaces, document the delta.
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

_Dr. Mārcis Gasūns_
