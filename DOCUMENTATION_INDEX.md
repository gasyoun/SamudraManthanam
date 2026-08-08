# Documentation Index

_Created: 19-06-2026 · Last updated: 08-08-2026_

Purpose: tell humans and implementation agents which Markdown files are current, supporting, or historical.

## Current Primary Docs

- `README.md`: project overview and build/use notes.
- `docs/PLAN_SAMUDRAMANTHANAM_ARCHITECTURE_2026_2027.md`: **canonical
  planning index** — locked decisions, autonomy contract, and links to every
  current architecture/roadmap/implementation/verification layer.
- `docs/ROADMAP_SAMUDRAMANTHANAM_2026_2027.md`: **sole living status roadmap**
  — architecture integrity, corpus growth, and research workbench programme.
- `ROADMAP_2026_H2_DH_MOBILE.md`: historical H2 design and decision record;
  superseded for status.
- `docs/ARCHITECTURE_SAMUDRAMANTHANAM_CANONICAL_PLATFORM.md`: current
  canonical-bundle, stable-identity, dual-deployment, and dual-product
  architecture.
- `TARGET_ARCHITECTURE.md`: previous implementation baseline; consult the
  current architecture above for new work.
- `ARCHITECTURE_CRITIQUE_AND_OPEN_QUESTIONS.md` and
  `ARCHITECTURE_REVIEW_6_MONTH_ROADMAP.md`: historical review inputs.
- `CHANGELOG.md`: notable changes.
- `.ai_state.md`: session journal — queue, WIP, hypotheses.

## Phase 1 Design Specs (frozen — DH data layer)

- `docs/IMPLEMENTATION_HANDOFF_PHASE1.md`: **start here to implement Phase 1** — build order, file targets, gates, definition of done.
- `docs/LINE_ID_SCHEME.md`: frozen `{work}:{passage}` stable-ID contract (S1).
- `docs/CONVERTER_SPEC.md`: HTML→JSONL converter spec (S2).
- `docs/ALIGNMENT_SPEC.md`: Sanskrit↔Russian alignment spec (S3).
- `docs/TAG_CENSUS.md` / `.json`: measured corpus structural inventory (S2 prerequisite).
- `docs/DESIGN_SESSIONS_PLAN.md`: the five-session frontier plan (S1–S3 done, S4–S5 pending).
- `docs/PHASE2_PLAN.md`: Phase 2 plan (responsive + PWA shell + offline reader) — the gate before S4; Sonnet-tier, parallelizable with Phase 1.

## Current Supporting Docs

- `web/SEARCH_CONTRACT.md`: search behavior contract.
- `web/corpus_builder/wisdomlib/README.md`: Wisdomlib crawler operations, rights guardrails, Stage A/B/C commands, Cloudflare/rate-limit reality, and watcher usage.
- `web/corpus_builder/wisdomlib/CATALOG.md`: Wisdomlib bibliographic catalog summary generated from Stage A/B metadata.
- `use_cases.md`: user scenarios.
- `DEPLOYMENT.md`: no-Docker VPS first-time install + corpus publish.
- `OPS.md`: production day-2 operator path (pull/pip/restart/smoke/code rollback) for `/opt/samudra` (H2388).
- `CLAUDE.md`: agent guidance for this repository.
- `Corpus_builder/CLAUDE.md`: Corpus Builder-specific agent guidance.

## Historical Docs (`docs/archive/`)

Context only — do not treat as current instructions:

- `docs/archive/WEB_PLAN.md`: older from-scratch web architecture plan.
- `docs/archive/roadmap.md`: older 1-month roadmap (May–June 2026).
- `docs/archive/gemini-implementation-plan.md`, `docs/archive/gemini-fix-web.md`, `docs/archive/GEMINI_REVIEW.md`: older Gemini-era plans and reviews.
- `docs/archive/GEMINI_FLASH_IMPLEMENTATION_PLAN.md` + `docs/archive/GEMINI_FLASH_PHASE_0[1-5]_*.md`: completed Gemini Flash implementation phases (all [COMPLETE]).
- `docs/archive/CODE_ARCHITECTURE_REVIEW.md`: earlier code/architecture review.
- `docs/archive/PRE_GEMINI_AUDIT.md`: pre-Gemini audit (2026-05-15); all findings fixed.
- `docs/archive/ai_status.md`: previous AI implementation status.

## Reading Order For Implementation Agents

1. `DOCUMENTATION_INDEX.md`
2. `CLAUDE.md`
3. `docs/PLAN_SAMUDRAMANTHANAM_ARCHITECTURE_2026_2027.md`
4. `docs/ROADMAP_SAMUDRAMANTHANAM_2026_2027.md`
5. `docs/ARCHITECTURE_SAMUDRAMANTHANAM_CANONICAL_PLATFORM.md`
6. `web/SEARCH_CONTRACT.md`
7. `.ai_state.md`

## Wisdomlib Status Rule

Current Wisdomlib programme status belongs in
`docs/ROADMAP_SAMUDRAMANTHANAM_2026_2027.md`. Detailed crawler operation belongs
in `web/corpus_builder/wisdomlib/README.md`; the generated bibliographic summary
belongs in `web/corpus_builder/wisdomlib/CATALOG.md`.

## Conflict Rule

When documents conflict:

1. User messages and latest architecture decisions win.
2. `docs/PLAN_SAMUDRAMANTHANAM_ARCHITECTURE_2026_2027.md` and its linked
   living roadmap win over older plans/roadmaps.
3. `docs/ARCHITECTURE_SAMUDRAMANTHANAM_CANONICAL_PLATFORM.md` wins over older
   architecture plans.
4. Historical docs (`docs/archive/`) are context only.

## Maintenance Rule

When adding a new planning document:

- add it to this index,
- mark whether it is current, supporting, or historical,
- update `changelog.md`.

_Dr. Mārcis Gasūns_
