# ROADMAP — SamudraManthanam residual (post-H2 truth-pass)

_Created: 26-07-2026 · Last updated: 30-07-2026_

> **Status (30-07-2026): SUPERSEDED.** The residual Wave-1 items shipped. Live
> status moved to
> [ROADMAP_SAMUDRAMANTHANAM_2026_2027.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ROADMAP_SAMUDRAMANTHANAM_2026_2027.md).

Historical PLAN index:
[PLAN_SAMUDRAMANTHANAM_RESIDUAL_2026H2.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/PLAN_SAMUDRAMANTHANAM_RESIDUAL_2026H2.md).

Historical design docs (CONVERTER_SPEC, ALIGNMENT_SPEC, OFFLINE_SEARCH_DESIGN,
PHASE2_PLAN) remain valid **specs**; they are not open work queues.

---

## Done (do not re-open)

| Block | Evidence |
|---|---|
| Phase 0 metadata foundation | `fill_meta_phase0.py`, `structure` backfill, CITATION/rights notes |
| Phase 1 canonical JSONL + ingest | 148 sources, gates green, `html_to_canonical.py` |
| Phase 2 PWA shell + offline reader | manifest, SW, offline.js, 380px audit, font subsets |
| Phase 3a–3e offline search | packs, sqlite-wasm, sahpool, main-page offline bridge, gzip wire |
| Phase 4 partial | citation strings, JSON-LD/hreflang discoverability layers |
| NKРЯ W0–W4 + H906 SA/RU morphology | export freeze, sanskritisms, inline `<w><ana/>` |
| Somadeva KSS all 18 lambakas | H907/H910/H927/H928 — uniform śloka keys |
| Ignatiev Wave A slice | 5 works FTS5-searchable (H1438 partial) |

---

## Wave 1 — residual (agent, this plan)

### Lane A — platform

1. **Structured search-result export** — JSON + CSV on existing export path
   ([H1502](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1502-Sonnet_SamudraManthanam_search-export-json-csv_22.07.26.md)).
   Results only; no bulk corpus dump.
2. **`morph_cache` schema drop**
   ([H1503](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1503-Sonnet_SamudraManthanam_drop-dead-morph-cache-table_22.07.26.md)).
3. **SSE `/api/search/stream`** — keep; strengthen hermetic tests; leave UI unwired.

### Lane B — integrity

4. **DBhP canonical-ID uniqueness** — re-verify post-H941; fix remaining dups;
   green `test_gate4_all_ids_unique` (or documented successor gate).
5. **Cyrillic homoglyphs in `#sa`** — [issue #16](https://github.com/gasyoun/SamudraManthanam/issues/16);
   server-side fix + regression tests.

### Lane C — corpus (in flight)

6. **Ignatiev H1438** — continue current handoff only; Māyā glued-digit front-end
   and `.doc`/`antiword` branch are design-gated *inside* H1438, not new series.

### Docs (this PR)

7. Living residual ROADMAP + supersede banners on H2 / Somadeva / ARCHITECTURE_REVIEW status sections.

---

## Wave 2

8. **Corpus_builder engine/GUI decouple**
   ([H1485](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1485-Opus_SamudraManthanam_corpus-builder-engine-gui-decouple_22.07.26.md)).

---

## Human / blocked (not wave-1 agent)

| Item | Gate |
|---|---|
| NKРЯ W5 outreach | MG `@DO` |
| PWA device install + airplane mode | physical devices |
| Lazarus desktop freeze release | maintainer release |
| Wisdomlib Stage C | residential egress + rights (issue #17) |
| Zenodo bulk corpus / open TEI | rights locked grey |
| Ignatiev Waves B–D full mint | after H1438 design lessons |

---

## Explicit non-goals

- Rebuilding Phases 0–3, Somadeva alignment, or NKРЯ W0–W4.
- Open data dumps, DOI'd corpus, public TEI.
- Native mobile apps; TEI-as-master.
- Expanding Ignatiev to ~14 new handoffs before H1438 closes design debt.

---

## Success for the residual span

Wave-1 lanes A+B merged with hermetic CI green and one successful local
full-corpus uniqueness gate re-run; H1438 continues without blocking platform
PRs; living ROADMAP matches git reality so the next session does not re-plan
done work.

_Dr. Mārcis Gasūns_
