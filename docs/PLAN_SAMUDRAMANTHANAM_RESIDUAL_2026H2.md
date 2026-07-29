# PLAN — SamudraManthanam residual replan (2026H2)

_Created: 26-07-2026 · Last updated: 30-07-2026_

> **Status (30-07-2026): SUPERSEDED.** All new Wave-1 residual items below
> shipped. The canonical programme is now
> [PLAN_SAMUDRAMANTHANAM_ARCHITECTURE_2026_2027.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/PLAN_SAMUDRAMANTHANAM_ARCHITECTURE_2026_2027.md).
> Retain this file as the July residual decision/execution record.

**Index for unattended execution.** Full `/ask` pack after a stale-roadmap audit
(`/ask-batch` stale-roadmap slice, Grok 4.5 `grok-4.5`, 26-07-2026).

**One-paragraph goal.** The H2 2026 DH+mobile roadmap is mostly **done**
(Phases 0–3e shipped June 2026; NKРЯ W0–W4 + H906 morphology shipped July;
Somadeva all 18 lambakas aligned and re-keyed). This plan **truth-passes** the
roadmap estate, then drives a **balanced three-lane wave-1**: (A) platform Phase-4
residual — structured search export + small hygiene; (B) integrity — DBhP
canonical-ID uniqueness + cyrillic homoglyphs in `#sa`; (C) Ignatiev ingest
continues via existing 🔵 H1438 without expanding Wave B–D mints. Grey-rights
posture and human/ops gates stay out of agent scope.

## Layer docs

| Layer | Path |
|---|---|
| Living residual roadmap | [ROADMAP_SAMUDRAMANTHANAM_RESIDUAL_2026H2.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ROADMAP_SAMUDRAMANTHANAM_RESIDUAL_2026H2.md) |
| Architecture | [ARCHITECTURE_SAMUDRAMANTHANAM_RESIDUAL.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ARCHITECTURE_SAMUDRAMANTHANAM_RESIDUAL.md) |
| Implementation | [IMPLEMENTATION_SAMUDRAMANTHANAM_RESIDUAL.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/IMPLEMENTATION_SAMUDRAMANTHANAM_RESIDUAL.md) |
| Verification | [VERIFICATION_SAMUDRAMANTHANAM_RESIDUAL.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/VERIFICATION_SAMUDRAMANTHANAM_RESIDUAL.md) |
| This index meta | [PLAN_SAMUDRAMANTHANAM_RESIDUAL_2026H2.meta.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/PLAN_SAMUDRAMANTHANAM_RESIDUAL_2026H2.meta.md) |

Supersedes the *status* claims in
[ROADMAP_2026_H2_DH_MOBILE.md](https://github.com/gasyoun/SamudraManthanam/blob/main/ROADMAP_2026_H2_DH_MOBILE.md)
(banner now points here). Historical design specs remain valid inputs.

## Decisions taken (interview 26-07-2026)

| ID | Ruling | Rationale |
|---|---|---|
| R1 | **Balanced three-lane wave-1** — export + integrity + Ignatiev | Avoid single-lane tunnel vision while platform residual and corpus quality lag banner claims |
| R2 | **One living residual ROADMAP** + archive/supersede banners on siblings | Agents keep rebuilding done work when H2 banner still says "In progress" |
| R3 | **Keep H1485 / H1502 / H1503** as PLAN spine — no re-mint | Harvest already staged them; avoid registry churn |
| R4 | **H1438 parallel; no Wave B–D series mint** | 5/~20 done; Māyā/.doc need design before bulk mint |
| R5 | **Integrity = both** DBhP ID uniqueness **and** issue #16 homoglyphs | Pre-release gate + visible data-quality defect |
| R6 | **H1485 = wave-2 only** | Delphi/GUI must not thrash with H1438 `corpus_builder` churn |
| R7 | **SSE stream: keep + hermetic tests**, still unwired to UI | Preserve experimental surface; do not delete |
| R8 | Living file = `docs/ROADMAP_SAMUDRAMANTHANAM_RESIDUAL_2026H2.md` | Self-identifying; root H2 path keeps history with banner |
| R9 | Accept = **hermetic CI green + one local full-corpus gate re-run** | Release trust without requiring device PWA |
| R10 | Non-goals: Zenodo bulk, wisdomlib Stage C, desktop freeze, PWA device test, NKРЯ W5 outreach, Wave B–D mint | Human/ops only |
| R11 | On ambiguity: **apply PLAN default, log `.ai_state`, continue** | Unattended safe |
| R12 | Commit → PR → merge when CI green (handoff-scoped) | Org default; fence below |

## Autonomy contract

1. **On ambiguity** — apply the marked default in this PLAN / IMPLEMENTATION, log one line under `.ai_state.md` Dev Notes, continue.
2. **Stop conditions** — halt and report if: (a) would commit raw PDFs/docx from `archive_ignatiev_2026/`; (b) would publish bulk corpus / Zenodo dump / wisdomlib chapter text; (c) corpus uniqueness gate fails after fix attempt with no clear root cause; (d) rights or secret exposure.
3. **Commit authority** — worktree off `origin/main` → PR → merge when checks green. No force-push. No `git add -A` in main checkout when `archive_ignatiev_2026/` is present.
4. **Fence** — do not touch: raw Ignatiev archive blobs; wisdomlib downloaded chapter content (gitignored); NKРЯ bulk export re-freeze; Lazarus desktop sources beyond a freeze *note*; production deploy secrets.
5. **Prior-art** — reuse existing `/api/search/export` pipeline for JSON/CSV; do not rebuild search; do not re-align Somadeva or re-run NKРЯ W0–W4.

## Wave-1 handoff map

| Lane | Deliverable | Handoff | Tier |
|---|---|---|---|
| A — platform | JSON/CSV search-result export | 🟡 [H1502](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1502-Sonnet_SamudraManthanam_search-export-json-csv_22.07.26.md) | Sonnet |
| A — hygiene | Drop dead `morph_cache` | 🟡 [H1503](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1503-Sonnet_SamudraManthanam_drop-dead-morph-cache-table_22.07.26.md) | Sonnet |
| A — hygiene | SSE stream hermetic tests (keep endpoint) | 🟡 [H1692](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1692-Sonnet_SamudraManthanam_sse-stream-hermetic-tests-keep_26.07.26.md) | Sonnet |
| B — integrity | DBhP canonical-ID uniqueness re-verify + fix | 🟡 [H1693](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1693-Sonnet_SamudraManthanam_dbhp-canonical-id-uniqueness-gate_26.07.26.md) | Sonnet |
| B — integrity | Cyrillic homoglyphs in `#sa` (issue #16) | 🟡 [H1694](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1694-Sonnet_SamudraManthanam_cyrillic-homoglyph-sa-fields-16_26.07.26.md) | Sonnet |
| C — corpus | Ignatiev remaining (in flight) | 🔵 [H1438](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1438-Sonnet_SamudraManthanam_ignatjev-tantras-puranas-ingest_22.07.26.md) | Sonnet |
| Docs | This PLAN pack + residual ROADMAP + banners | lands with this PR | — |

## Wave-2

| Deliverable | Handoff |
|---|---|
| Corpus_builder engine/GUI decouple | 🟡 [H1485](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1485-Opus_SamudraManthanam_corpus-builder-engine-gui-decouple_22.07.26.md) |

## Human residual (GTD — not agent handoffs)

- NKРЯ W5 outreach (Sichinava/Plungian) after pilot exists — already true; contact only.
- PWA install + airplane-mode device test (Android Chrome / iOS Safari).
- Desktop Lazarus endgame freeze release note.
- Wisdomlib Stage C on residential egress (issue #17).
- Grey rights: no open dump until ruling changes.

## Execution starter (any wave-1 agent)

```
Read C:\Users\user\Documents\GitHub\SamudraManthanam\docs\PLAN_SAMUDRAMANTHANAM_RESIDUAL_2026H2.md and execute it.
```

Scope to the handoff's lane; use IMPLEMENTATION steps for that lane only.

_Dr. Mārcis Gasūns_
