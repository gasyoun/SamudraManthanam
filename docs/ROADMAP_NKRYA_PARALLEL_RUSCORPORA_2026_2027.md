# НКРЯ / ruscorpora.ru export roadmap — nkrya-parallel (2026–2027)

_Created: 11-07-2026 · Last updated: 11-07-2026_

Scale the [nkrya-parallel](https://github.com/gasyoun/SamudraManthanam/tree/main/nkrya-parallel) subsystem from E. A. Rubanova's 2020 HSE ВКР pilot to an export pipeline covering every running-text source of the Samudra Manthanam corpus (published at [samskrtam.ru/parallel-corpus](https://samskrtam.ru/parallel-corpus/), 123 texts), and deliver a package ready to enter the Russian National Corpus ([ruscorpora.ru](https://ruscorpora.ru)) as the Sanskrit member of the parallel-corpus module. Authored from a `/roadmap-interview` session (audit + 2 interview rounds, 8 rulings), Fable 5 (`claude-fable-5`), 11-07-2026.

## 1. Context — what exists, what is missing

**The channel is warm.** Rubanova's ВКР («Полуавтоматическая морфологическая разметка русско-санскритского параллельного корпуса», HSE 2020, defense video [youtu.be/1qa6Fp-1KMc](https://youtu.be/1qa6Fp-1KMc)) was supervised by D. V. Sichinava (НКРЯ parallel-corpus lead), consulted by M. Yu. Gasūns, and reviewed by T. A. Arkhangelskiy (Hamburg, 7/10). V. A. Plungian himself suggested adding Sanskrit next to Hindi in the НКРЯ «Другие индоевропейские» subsection. Nothing was delivered to НКРЯ since — that is the gap this roadmap closes.

**The hard part is already solved in this repo.** The alignment НКРЯ needs is not a research problem here: the canonical JSONL layer ([web/corpus_builder/jsonl/](https://github.com/gasyoun/SamudraManthanam/tree/main/web/corpus_builder/jsonl)) holds 152 sources / 574,939 segment records, markup-aligned (no statistical aligner), with **≈78k clean 1:1 Sanskrit–Russian verse pairs** (A41 headline: 78,219 in the frozen 148-source frame), SLP1+IAST per Sanskrit segment, and `rights`/`provenance`/`title_en` already classified in every `meta.json`. The descriptor paper [A41](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/A41_parallel_corpus_descriptor.md) (readiness 4/5 as of 11-07-2026, H676) is the citable companion. And the pair-extraction + TMX halves of the exporter **already exist**: `build_l0.py` (L0 verse layer, 99,733 both-sides units / 116 works) and `build_tmx.py` (TMX 1.4b) in `SanskritLexicography/RussianTranslation/src/` — Wave 1 adapts them rather than rewriting.

**What Arkhangelskiy's review demands.** His 2020 criticisms are the engineering spec for this roadmap: ad-hoc solutions hard to scale, undocumented ipynb code, no README. Scaling here means replacing the notebooks with documented, tested exporters fed by the canonical layer — not re-running the thesis code.

**Assets inventory (consume, don't rebuild):**

| Asset | Where | Feeds |
|---|---|---|
| Canonical aligned JSONL (152 sources) | [web/corpus_builder/jsonl/](https://github.com/gasyoun/SamudraManthanam/tree/main/web/corpus_builder/jsonl) | every wave |
| Per-source rights/provenance/title_en | `web/Data/*.meta.json` (H231 pass) | rights table (W4), НКРЯ metadata headers |
| Rubanova artifacts: санскритизм stemmer lists, name indexes, deeppavlov morph outputs for MBh 3 + Rām 1–3 | [nkrya-parallel/diplom-rubanova/](https://github.com/gasyoun/SamudraManthanam/tree/main/nkrya-parallel/diplom-rubanova) (bulk gitignored, curated lists tracked after W0) | W2 gold, W3 |
| DCS morphology (Hellwig), CoNLL-U→SQLite | sibling repo [VisualDCS](https://github.com/gasyoun/VisualDCS) (M1–M8) | W2 path B |
| Sa→Ru word-alignment lexicon (1.09M pairs, SLP1) | sibling repo `SanskritLexicography/RussianTranslation/src/corpus_lexicon.jsonl` | W3 |
| L0 verse-pair extractor + TMX 1.4b exporter ([build_l0.py](https://github.com/gasyoun/SanskritLexicography/blob/master/RussianTranslation/src/build_l0.py), [build_tmx.py](https://github.com/gasyoun/SanskritLexicography/blob/master/RussianTranslation/src/build_tmx.py)) | sibling repo `SanskritLexicography/RussianTranslation/src/` | W1 (adapt, don't rewrite) |
| A41 data descriptor (readiness 3/5) | [papers/A41_parallel_corpus_descriptor.md](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/A41_parallel_corpus_descriptor.md) | W2 write-up, W5 outreach attachment |

## 2. Decisions taken (interview, 11-07-2026)

| # | Fork | Ruling | Rationale residue |
|---|---|---|---|
| 1 | Pilot scope | **MBh 3 + Rāmāyaṇa 1–3** | Continuity with the ВКР: Rubanova's gold data exists for exactly these texts; НКРЯ team saw them at the 2020 defense. Slugs: `03_mahabharata-aranyakaparva`, `01_ramayana-balakanda`, `02_ramayana-ayodhyakanda`, `03_ramayana-aranyakanda`. |
| 2 | Rights strategy | **Full corpus, НКРЯ umbrella** | Offer everything with an honest per-text rights table; НКРЯ's own legal framework decides what they ingest (non-extractable search ≠ open dump, so the locked «rights stay grey» ruling is not violated). |
| 3 | Sanskrit-side annotation | **Try all 3 paths** | Plain IAST/SLP1 vs DCS lemma crosswalk vs fresh tagging (Dharmamitra/vidyut), compared head-to-head on the pilot. |
| 4 | Outreach timing | **Pilot first, then outreach** | First contact with Sichinava/Plungian happens with the artifact attached; format risk absorbed by ruling 7. |
| 5 | Thesis site | **Publish now** | The Docusaurus site over the ВКР + reviews goes public without waiting for consent round-trips (defense was public, video already on YouTube). Notify Rubanova at W5. **Executed same day** by a concurrent session ([PR #38](https://github.com/gasyoun/SamudraManthanam/pull/38)) — live at [gasyoun.github.io/SamudraManthanam](https://gasyoun.github.io/SamudraManthanam/). |
| 6 | Санскритизм layer | **Corpus-wide now** | Rubanova's Sanskrit-loanword lemmatization + name indexes get scaled across all 123 verse sources, not just the pilot. |
| 7 | Export format | **Triple export: НКРЯ-XML + TMX + TSV** | One exporter, three emitters from the same JSONL; whichever format НКРЯ's post-2023 platform actually wants, one of the three is trivially close. |
| 8 | Paper routing | **Fold into A41** | The 3-path annotation comparison becomes an A41 section, not a separate companion paper. |

## 3. Scope framing

- **НКРЯ scope = running text only**: 123 verse + 14 prose = 137 sources. The 15 bilingual dictionaries stay out (a parallel corpus is bitext, not lexicon).
- **Pair unit** = the existing alignment group (one `citation_block`): Sanskrit verse ↔ Russian prose translation. The exporter keeps only groups with **both sides present and non-empty**; translation-only texts (`buddhacharita-balmont`, `mify-drind`) and the Sanskrit-only Hitopadeśa drop out of the bitext naturally via that filter. Monolingual-RU segments inside bilingual texts are flagged, not silently dropped.
- **Commentary segments** are excluded from v1 bitext (they are RU-only annotation, not translation pairs); revisit only if НКРЯ asks.
- **Russian side ships plain** — НКРЯ annotates Russian with their own pipeline; our добавка is the санскритизм lexicon (W3), which fixes exactly the class of words their lemmatizers break on (the ВКР's core finding: baseline lemma accuracy 47% on санскритизмы).

## 4. Waves

### Wave 0 — Finish landing `nkrya-parallel/` in git — **H753** (Sonnet)

**Status correction (same day):** a concurrent session landed the site half of this wave before the roadmap was committed — [PR #38](https://github.com/gasyoun/SamudraManthanam/pull/38) (11-07-2026) tracked the Docusaurus scaffold + the three `.mdx` documents + ВКР media and added [deploy-nkrya-parallel-pages.yml](https://github.com/gasyoun/SamudraManthanam/blob/main/.github/workflows/deploy-nkrya-parallel-pages.yml); the thesis site is **live at [gasyoun.github.io/SamudraManthanam](https://gasyoun.github.io/SamudraManthanam/)** (the Pages ROOT, not the `/nkrya-parallel/` subpath — deploy verified `success`, ruling 5 satisfied). H753's residual scope: track the small curated `diplom-rubanova/` lists (санскритизм indexes, name lists, stemmer rules — the reusable artifacts, ≤500 KB each), `Тайм-коды доклада.txt`, and the two citable PDFs (thesis 0.9 MB + defense presentation 1.1 MB); extend `.gitignore` to *explicitly* exclude the ~600 MB of loose bulk (deeppavlov dumps, `dict.opcorpora.txt` 283 MB, `archive/rus_words.txt` 128 MB) so no future `git add` can swallow it; write `diplom-rubanova/MANIFEST_LOCAL_ONLY.md` inventorying what exists only on disk; record the canonical site URL (root vs subpath — the root placement means any future SamudraManthanam Pages content collides; keep root unless that becomes real, and note the decision in the repo README). Unblocked: immediately.

**H753 done (11-07-2026):** curated lists, `Тайм-коды доклада.txt`, and the two PDFs are tracked; `diplom-rubanova/.gitignore` switched to deny-by-default (only the curated whitelist is un-ignored) so no future `git add` can re-swallow the ~600 MB bulk; `diplom-rubanova/MANIFEST_LOCAL_ONLY.md` inventories every local-only file; the site-root placement + collision caveat is now also in the repo README. Wave 0 fully closed — Wave 1 (H754) is unblocked.

```
Read C:\Users\user\Documents\GitHub\Uprava\handoffs\H753-Sonnet_SamudraManthanam_nkrya-wave0-land-thesis-site_11.07.26.md and execute it.
```

Sonnet 5 (`claude-sonnet-5`), cd `C:\Users\user\Documents\GitHub\SamudraManthanam`.

### Wave 1 — Pilot triple export (MBh 3 + Rām 1–3) — **H754** (Opus)

New `web/corpus_builder/nkrya_export.py`: reads the 4 pilot JSONL sources, emits per text (a) best-guess НКРЯ para-XML — `para` blocks of paired `se` elements (`lang="ru"` / `lang="san"`), bibliographic header from `meta.json` (title, translator, year, edition, rights); (b) TMX 1.4b — **adapting the existing `build_l0.py`/`build_tmx.py` pair-extraction and TMX logic** (per-source output + НКРЯ metadata headers are the new parts); (c) flat aligned TSV (`group_id, sa_iast, sa_slp1, ru, flags`). CI gates: pair count parity vs `conversion_report.json`, XML well-formedness + TMX DTD validity, round-trip stability across two runs, zero empty sides. Exports land under `nkrya-parallel/export/` (gitignored; committed = the validation report + counts table). Unblocked: immediately (independent of W0 file-wise; same folder, so land W0 first to avoid tree contention).

```
Read C:\Users\user\Documents\GitHub\Uprava\handoffs\H754-Opus_SamudraManthanam_nkrya-wave1-pilot-triple-export_11.07.26.md and execute it.
```

Opus 4.8 (`claude-opus-4-8`), cd `C:\Users\user\Documents\GitHub\SamudraManthanam`.

### Wave 2 — Sanskrit-side 3-path comparison → A41 section (mint at W1 close)

On the pilot texts, produce and compare three Sanskrit-side annotation variants: **A** plain IAST/SLP1 (baseline, exists); **B** DCS lemma+morph crosswalk via the VisualDCS SQLite layer (MBh, Rām, RV are in DCS — verify DCS licensing for redistribution inside НКРЯ before shipping); **C** fresh auto-tagging (Dharmamitra or vidyut). Metrics: token coverage per path, B↔C lemma agreement, and a human adjudication sample via `/review-sheet` (interactive HTML, no markdown checkboxes). Write-up lands as a new A41 section per ruling 8; bump A41 readiness. Executor: Fable 5 (`claude-fable-5`) for the comparison design + write-up. Unblocked by: W1 (needs the export frame to annotate into).

### Wave 3 — Санскритизм layer corpus-wide (mint at W1 close; parallelizable with W2)

Port the ВКР's санскритизм extraction + name-index generation from notebooks to a documented, tested package `web/corpus_builder/sanskritisms/` (README + tests — this answers Arkhangelskiy's review directly). Inputs: Rubanova's curated lists (tracked after W0), the corpus lexicon (1.09M Sa–Ru pairs), the 9,460-stem list. Run across all 123 verse sources → per-source санскритизм lexicon + proper-name index, packaged as the Russian-side supplement for НКРЯ and as automatic указатели for samskrtam.ru. Executor: Sonnet 5 (`claude-sonnet-5`) after a short spec pass. Unblocked by: W0 (needs the curated lists tracked).

### Wave 4 — Full-corpus export freeze (mint at W2/W3 close)

Run the triple exporter across all 137 running-text sources; emit the per-text rights table (from `meta.json`: pre-1929 PD vs in-copyright, translator death years where known); validation report with per-source pair counts; freeze as a versioned package (GitHub release artifact, not committed bulk). Mostly mechanical — Sonnet 5 (`claude-sonnet-5`) or Haiku 4.5 (`claude-haiku-4-5-20251001`). Unblocked by: W1 (exporter exists); W2/W3 outputs attach if ready.

### Wave 5 — Outreach + НКРЯ iteration (human, after W1 minimum)

`/outreach-draft` prepares the letter to Sichinava (cc Plungian): pilot package attached, A41 draft + thesis site linked, full-corpus offer with the rights table, ask for the current intake format + ingestion owner. MG sends. Same letter (or a separate note) notifies Rubanova of the published site and invites her onto the НКРЯ submission. Then iterate: their format spec → adjust one emitter → deliver full corpus (W4 package). НКРЯ-side ingestion, Russian-side annotation, and platform work are theirs. Unblocked by: W1 (per ruling 4, artifact in hand); stronger after W4.

## 5. Non-goals (considered, ruled out)

- **Dictionaries into НКРЯ** — the 15 dictionary sources are out of parallel-corpus scope by nature.
- **A statistical/neural aligner** — the corpus is markup-aligned; that is A41's thesis. No aligner is built or needed.
- **Permissions campaign / PD-only tranche** — ruled out 11-07-2026 (ruling 2); rights go to НКРЯ as an honest table, their framework decides.
- **Separate companion paper for the annotation comparison** — folded into A41 (ruling 8).
- **Hosting our own tsakorpus/portal for the parallel corpus** — the web platform already serves search; the НКРЯ track is about their platform.
- **Re-running the ВКР notebooks as-is** — they are the provenance record; production code is written fresh against the canonical layer.

## 6. Risks / open items

- **НКРЯ intake format uncertainty** (their platform changed ~2023; ruscorpora.ru returned HTTP 500 to a probe on 11-07-2026) — absorbed by the triple export (ruling 7) and the W5 format question.
- **DCS licensing** for redistribution of lemma/morph inside НКРЯ — verify at W2 before path B ships anywhere.
- **Rubanova consent risk** — accepted by ruling 5 (publish now); mitigation = W5 notification + collaboration invite.
- **Rights final call sits with НКРЯ** — if their lawyers balk at the in-copyright majority, the fallback is the PD subset (already classified per text, so the filter is one flag).
- **A41 freeze interplay** — W2 adds a section while A41 approaches submission freeze; sequence the A41 readiness bump so the comparison lands before the number freeze, or explicitly defers to a revision.

## 7. Tracking

Handoffs: [H753](https://github.com/gasyoun/Uprava/blob/main/handoffs/H753-Sonnet_SamudraManthanam_nkrya-wave0-land-thesis-site_11.07.26.md) (W0), [H754](https://github.com/gasyoun/Uprava/blob/main/handoffs/H754-Opus_SamudraManthanam_nkrya-wave1-pilot-triple-export_11.07.26.md) (W1); W2–W5 handoffs are minted when their blockers clear. Human rows live in [Uprava/GTD_NEXT_ACTIONS.md](https://github.com/gasyoun/Uprava/blob/main/GTD_NEXT_ACTIONS.md). Paper: [A41](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/A41_parallel_corpus_descriptor.md). Sibling roadmap (web platform, distinct workstream): [ROADMAP_2026_H2_DH_MOBILE.md](https://github.com/gasyoun/SamudraManthanam/blob/main/ROADMAP_2026_H2_DH_MOBILE.md).

_Dr. Mārcis Gasūns_
