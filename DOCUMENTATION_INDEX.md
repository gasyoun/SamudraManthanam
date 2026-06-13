# Documentation Index

Date: 2026-06-12

Purpose: tell humans and implementation agents which Markdown files are current, supporting, or historical.

## Current Primary Docs

- `README.md`: project overview and build/use notes.
- `ROADMAP_2026_H2_DH_MOBILE.md`: **current roadmap** — DH-standards data layer (stable IDs, JSONL canonical, metadata/rights) + cross-platform offline search via PWA/sqlite-wasm.
- `TARGET_ARCHITECTURE.md`: current target architecture.
- `ARCHITECTURE_CRITIQUE_AND_OPEN_QUESTIONS.md`: architecture critique and open decisions (several now settled by `ROADMAP_2026_H2_DH_MOBILE.md`).
- `ARCHITECTURE_REVIEW_6_MONTH_ROADMAP.md`: web-platform hardening roadmap (still current for that scope; mobile/data-model planning superseded by `ROADMAP_2026_H2_DH_MOBILE.md`).
- `changelog.md`: notable changes.
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
- `use_cases.md`: user scenarios.
- `DEPLOYMENT.md`: no-Docker VPS deployment guide.
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
3. `ROADMAP_2026_H2_DH_MOBILE.md`
4. `TARGET_ARCHITECTURE.md`
5. `web/SEARCH_CONTRACT.md`
6. `.ai_state.md`

## Conflict Rule

When documents conflict:

1. User messages and latest architecture decisions win.
2. `ROADMAP_2026_H2_DH_MOBILE.md` wins over older roadmaps.
3. `TARGET_ARCHITECTURE.md` wins over older plans.
4. Historical docs (`docs/archive/`) are context only.

## Maintenance Rule

When adding a new planning document:

- add it to this index,
- mark whether it is current, supporting, or historical,
- update `changelog.md`.
