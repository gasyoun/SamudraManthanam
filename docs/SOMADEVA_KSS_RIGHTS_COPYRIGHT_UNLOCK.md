# Somadeva Kathāsaritsāgara — rights status and what a proven copyright unlocks

_Created: 14-07-2026 · Last updated: 14-07-2026_

Companion to [ROADMAP_SOMADEVA_KSS_ALIGNMENT_SCALEUP_2026_2027.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ROADMAP_SOMADEVA_KSS_ALIGNMENT_SCALEUP_2026_2027.md).
Answers the question: **when I show I hold the copyright (or a redistribution
licence) to the Russian translation, what changes?**

## Who owns what

- **Sanskrit text** — GRETIL recension of the Kathāsaritsāgara: **public domain**
  (Somadeva, 11th c.). Never gated; unaffected by anything below.
- **Alignment + derived data** (our JSONL, HTML, śloka keys, the extractor) —
  **our own work**; ours to license.
- **Russian translation** — И. Д. Серебряков et al., published by **Nauka**
  (ГРВЛ), 20th c. **In-copyright.** Economic rights normally vest with the
  translator's heirs and/or the publisher. This is the only gated layer.

"Showing copyright" therefore means producing **either** proof that MG holds the
economic rights **or** a redistribution licence from the rightsholder (heirs
and/or Nauka). Attribution to the translators remains required **regardless** —
proving economic rights does not waive the authors' moral right to be named.

## Current status — "grey per project ruling"

Same standing status as the Grintser Rāmāyaṇa already in the corpus:

| What | Now (grey) |
|---|---|
| Corpus HTML/JSONL in the public repo | **committed** (search-only access, verse-level display) |
| `web/corpus.db` (FTS index) | **gitignored** — not published |
| Bulk exports (НКРЯ para-XML / TMX / TSV) | **gitignored** — not published |
| Redistribution as a bulk dataset | **no** |
| kosha `datasets.json` / Zenodo DOI | **not registered** |
| `kathasaritsagara.meta.json` `rights` | "in-copyright … grey per project ruling; no redistribution, export bulk gitignored" |
| `needs_review` | `true` |

The tolerance that makes "grey" workable: the search platform exposes the text at
verse granularity for scholarly lookup, not as a downloadable copy of the book.

## What a proven copyright / licence unlocks

When rights are demonstrated, flip the following **in one pass** (a
`/publish-safety-check` GO gate first):

1. **Publish the bulk exports.** Un-gitignore the НКРЯ para-XML + TMX 1.4b + TSV
   for the KSS and ship them → the [НКРЯ / ruscorpora submission](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ROADMAP_NKRYA_PARALLEL_RUSCORPORA_2026_2027.md)
   can include the KSS instead of holding it back.
2. **Register a citable dataset.** Add a [kosha `datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)
   row and mint a **Zenodo DOI** for the SA↔RU parallel corpus (all 18 books once
   aligned). Add it to [FEATURES_INDEX.md](https://github.com/gasyoun/SanskritLexicography/blob/master/FEATURES_INDEX.md).
3. **Offer a bulk download** on samskrtam.ru (a built `corpus.db` slice or the
   TMX), not only in-app search.
4. **Rewrite the rights metadata.** `kathasaritsagara.meta.json` `rights` →
   the actual licence (e.g. "redistribution licensed from <holder>, <date>;
   CC BY-NC 4.0" or as agreed); set `needs_review: false` after the per-lambaka
   bibliography is verified.
5. **Enable derivative products.** Reader exports, flashcards, printed
   bilingual editions become distributable (subject to the licence's terms).
6. **Lift the `.gitignore` entries** for the KSS export bulk (keep `corpus.db`
   gitignored only if it is a rebuildable artifact rather than a release asset).

## What does NOT change

- The Sanskrit was always free; no action needed there.
- **Attribution stays mandatory** — Серебряков et al. named on every surface.
- The search platform already works today; unlocking is about *redistribution and
  publication*, not about whether the corpus functions.
- If the licence is **non-commercial** (likely for a Nauka work), commercial
  reuse stays blocked even after the unlock — read the licence terms before
  step 5.

## Plain-language example — what opens up

Picture two people using the corpus.

**A student on samskrtam.ru** searches «океан» and reads the matching verse with
its Russian translation side by side. **This works today, and does not change** —
it works exactly the same before and after any rights clearance.

**A researcher** wants the whole thing as data. Here is the before/after:

| The researcher wants to… | Now (grey) | After copyright shown |
|---|---|---|
| Search + read verse-by-verse in the app | ✅ yes | ✅ yes (unchanged) |
| Download the **full aligned Russian text** (TMX / one file) | ❌ no | ✅ yes |
| **Cite it as a dataset** with a permanent DOI (`10.5281/zenodo.…`) | ❌ no | ✅ yes |
| Find the KSS in the **НКРЯ / ruscorpora** parallel corpus | ❌ held back | ✅ submitted |
| Get a **"Download the parallel text" button** on the site | ❌ no | ✅ yes |
| Reuse it in a **paid** product | ❌ no | ⚠️ only if the licence is not NC |
| Know who translated it | ✅ named | ✅ named (always required) |

In one sentence: **clearing the copyright turns a read-only-in-the-app corpus
into a downloadable, citable, publishable dataset — while the student's reading
experience, and the duty to credit Serebryakov, stay exactly the same.**

## The one-line trigger, when ready

> Rights cleared for the KSS Russian → run **`/corpus-rights-unlock kathasaritsagara`**
> (which starts with `/publish-safety-check`, then flips steps 1–6 above in one
> pass and records the licence in `kathasaritsagara.meta.json`).

The reusable playbook is the [`/corpus-rights-unlock`](https://github.com/gasyoun/claude-config/blob/main/commands/corpus-rights-unlock.md)
skill — it generalises this document to any "grey per project ruling" corpus
(the Grintser Rāmāyaṇa, the НКРЯ export bundle, …), not only the KSS.

_Dr. Mārcis Gasūns_
