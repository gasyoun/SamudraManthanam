# Documentation Index

Date: 2026-05-15

Purpose: tell humans and Gemini Flash which Markdown files are current, supporting, or historical.

## Current Primary Docs

- `README.md`: project overview and build/use notes.
- `TARGET_ARCHITECTURE.md`: current target architecture.
- `ARCHITECTURE_CRITIQUE_AND_OPEN_QUESTIONS.md`: critique of proposed architecture and open decisions.
- `ARCHITECTURE_REVIEW_6_MONTH_ROADMAP.md`: 6-month roadmap and Gemini backlog.
- `GEMINI_FLASH_IMPLEMENTATION_PLAN.md`: current Gemini Flash index.
- `GEMINI_FLASH_PHASE_01_FOUNDATION.md`: [COMPLETE] foundation tasks.
- `GEMINI_FLASH_PHASE_02_SEARCH_READER.md`: [COMPLETE] search and reader tasks.
- `GEMINI_FLASH_PHASE_03_IDENTITY_CORRECTIONS.md`: [COMPLETE] identity and corrections tasks.
- `GEMINI_FLASH_PHASE_04_AI.md`: [COMPLETE] AI tasks.
- `GEMINI_FLASH_PHASE_05_DEPLOY_OPERATIONS.md`: [COMPLETE] deployment and operations tasks.
- `changelog.md`: notable changes.

## Current Supporting Docs

- `web/SEARCH_CONTRACT.md`: search behavior contract.
- `use_cases.md`: user scenarios.
- `ai_status.md`: previous AI implementation status.
- `CODE_ARCHITECTURE_REVIEW.md`: earlier code/architecture review; useful for historical findings.
- `PRE_GEMINI_AUDIT.md`: full pre-Gemini code and architecture audit (2026-05-15). Lists every bug, security issue, and open architecture problem with fix status. Read before starting Phase 1.

## Historical or Partly Superseded Docs

These files may contain useful context, but Gemini Flash should not treat them as current instructions when they conflict with the primary docs:

- `WEB_PLAN.md`: older from-scratch web architecture plan.
- `roadmap.md`: older 1-month roadmap.
- `gemini-implementation-plan.md`: older long-form Gemini plan.
- `gemini-fix-web.md`: older fix-oriented Gemini note.
- `CLAUDE.md`: general agent guidance; check against current architecture docs.
- `Corpus_builder/CLAUDE.md`: Corpus Builder-specific agent guidance.

## Reading Order For Gemini Flash

1. `DOCUMENTATION_INDEX.md`
2. `PRE_GEMINI_AUDIT.md` ← read this before touching any code
3. `TARGET_ARCHITECTURE.md`
4. `ARCHITECTURE_CRITIQUE_AND_OPEN_QUESTIONS.md`
5. `ARCHITECTURE_REVIEW_6_MONTH_ROADMAP.md`
6. `GEMINI_FLASH_IMPLEMENTATION_PLAN.md`
7. The relevant `GEMINI_FLASH_PHASE_*.md`

## Conflict Rule

When documents conflict:

1. User messages and latest architecture decisions win.
2. `ARCHITECTURE_CRITIQUE_AND_OPEN_QUESTIONS.md` can mark current decisions as provisional.
3. `TARGET_ARCHITECTURE.md` wins over older plans.
4. `GEMINI_FLASH_IMPLEMENTATION_PLAN.md` wins over older Gemini plans.
5. Historical docs are context only.

## Maintenance Rule

When adding a new planning document:

- add it to this index,
- mark whether it is current, supporting, or historical,
- update `changelog.md`.
