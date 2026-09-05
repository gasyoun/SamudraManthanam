_Created: 25-08-2026 · Last updated: 05-09-2026_

# Gemini Flash Implementation Plan

This is the short index for Gemini Flash. Each linked phase file is under 100 lines.

Read first:

1. `DOCUMENTATION_INDEX.md`
2. `TARGET_ARCHITECTURE.md`
3. `ARCHITECTURE_CRITIQUE_AND_OPEN_QUESTIONS.md`
4. `ARCHITECTURE_REVIEW_6_MONTH_ROADMAP.md`
5. This file
6. The phase file for the current task

## North Star

Build Samudra Manthanam into a Sanskrit/Russian research platform in this order:

1. Stable corpus/search engine.
2. Scholarly reader and export workbench.
3. Email identity, correction proposals, and AI assistance.

## Hard Architecture Decisions

Treat these as defaults. If `ARCHITECTURE_CRITIQUE_AND_OPEN_QUESTIONS.md` marks one as provisional, ask before implementing a large change.

- First serious deploy target: VPS without Docker.
- GitHub stores code, not the generated `corpus.db`.
- `corpus.db` lives on VPS persistent storage.
- Split storage into generated `corpus.db` and mutable `state.db`.
- Keep SQLite FTS5 unless benchmarks prove it is insufficient.
- AI must be provider-agnostic.
- First local AI runner to test manually: Ollama through an OpenAI-compatible endpoint.
- Lead capture uses two unchecked consent boxes.
- Correction proposals are open to email-identified users and reviewed by admins/editors.

## Phase Files

1. `GEMINI_FLASH_PHASE_01_FOUNDATION.md`
2. `GEMINI_FLASH_PHASE_02_SEARCH_READER.md`
3. `GEMINI_FLASH_PHASE_03_IDENTITY_CORRECTIONS.md`
4. `GEMINI_FLASH_PHASE_04_AI.md`
5. `GEMINI_FLASH_PHASE_05_DEPLOY_OPERATIONS.md`

## Working Rules

1. Work in small PR-sized batches.
2. One batch should touch one architecture area.
3. Add or update tests for behavior changes.
4. Do not commit generated `corpus.db`.
5. Do not edit canonical corpus files unless explicitly asked.
6. Keep AI optional; the app must run without AI keys.
7. Keep correction proposals separate from canonical source files.
8. Keep personal-data consent separate from marketing/news consent.
9. Preserve `web/SEARCH_CONTRACT.md` unless intentionally changing search semantics.
10. Update docs when user-facing behavior changes.

## Standard Checks

Run after most web changes:

```powershell
cd C:\Users\user\Documents\GitHub\SamudraManthanam
py -3.10 -m compileall web\app web\ingest
cd web
python -m pytest
node --check static\search.js
```

Run for corpus-sensitive changes:

```powershell
cd C:\Users\user\Documents\GitHub\SamudraManthanam\web
$env:USE_REAL_CORPUS=1
python -m pytest -m corpus
Remove-Item Env:\USE_REAL_CORPUS
```

## Commit Rule

Each Gemini batch should finish with:

- changed files listed,
- checks run,
- remaining risks,
- next recommended phase/task.

_Dr. Mārcis Gasūns_
