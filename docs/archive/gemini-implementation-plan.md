_Created: 25-08-2026 · Last updated: 05-09-2026_

# Gemini Flash Implementation Plan

> **STATUS: SUPERSEDED** — Older long-form Gemini plan. Use `GEMINI_FLASH_IMPLEMENTATION_PLAN.md` as the current index.

## Purpose

This document converts `roadmap.md` into a concrete execution plan for Gemini Flash.

Gemini should use this file as the working implementation brief for the next month of development. The plan is intentionally feature-led and optimized for scholarly search quality.

---

## Operating Principles

1. Ship user-facing improvements first.
2. Prefer small, complete slices over broad unfinished refactors.
3. Preserve the current architecture unless a defect requires change.
4. Keep search, export, and SSE semantics aligned.
5. Keep the current product promise for morphology at **stem/root lookup**, not complete inflection-aware Sanskrit search.
6. Add or update tests whenever behavior changes.
7. Update docs when labels, contracts, or user-facing expectations change.

---

## Execution Order

1. Search quality baseline and golden-query framework
2. Web result UX improvements
3. Stem/root lookup polish
4. Export context improvements
5. Desktop corpus sync bridge
6. Ingest/corpus validation
7. Deployment and operational readiness

---

# Phase 1 - Search Quality Baseline

## Goal

Establish a repeatable regression framework for scholarly search quality before adding more features.

## Primary Files

- `web/tests/test_api.py`
- new tests under `web/tests/` as needed
- optional fixture/helper files under `web/tests/`
- optional documentation section in `roadmap.md` or `README.md`

## Tasks

### 1. Create a Golden Query Pack

Create a compact, maintainable set of representative search scenarios.

Suggested coverage:

- plain Sanskrit search in IAST
- plain Sanskrit search in Devanagari
- Russian plain search
- regex search
- multi-token plain search
- multi-line query search
- source-filtered search
- zero-result search

If durable expected counts depend on the real corpus DB, isolate those checks so the suite still remains usable in local development.

## Output Expectation

Gemini should leave behind:

- a named test section or dedicated test module for golden query behavior
- comments only where fixture purpose is not obvious
- a clear separation between:
  - stable API contract tests
  - data-dependent corpus-quality checks

### 2. Lock Down Search Semantics

Verify and codify:

- plain search token behavior
- multi-query behavior
- source filtering behavior
- `source_ids=[]` behavior
- export parity with POST search
- SSE parity with POST/export where applicable

## Acceptance Criteria

- tests make the intended search semantics explicit
- current behavior is not only "200 OK", but meaningfully asserted
- future regressions in result interpretation become easier to detect

---

# Phase 2 - Web Result UX Improvements

## Goal

Make search results more legible and confidence-building for scholars.

## Primary Files

- `web/templates/result_fragment.html`
- `web/templates/index.html`
- `web/static/search.js`
- `web/app/services/html_service.py`
- relevant tests under `web/tests/`

## Tasks

### 1. Improve Result Summary Wording

The result header should communicate:

- what query was run
- how many results were found
- how many sources were hit
- whether a result limit was reached

Preserve existing grammatical inflection helpers where already working.

### 2. Improve Zero-Result Handling

Add a clear, non-verbose empty-state message in rendered results when no hits are found.

It should:

- avoid sounding like an application error
- help the user understand the query completed normally

### 3. Clarify Source Selection State

If the UI can improve the clarity of:

- all sources selected
- no sources selected
- subset selected

then do so with restrained UI text or control-state behavior.

### 4. Preserve Rendering Guarantees

Do not break:

- safe escaping
- header rendering regression coverage
- highlight behavior
- grouping by source/chapter
- export rendering

## Acceptance Criteria

- users can read the result block and understand search scope quickly
- zero-hit searches no longer feel ambiguous
- existing result rendering tests remain green

---

# Phase 3 - Stem/Root Lookup Polish

## Goal

Turn the current modest morphology-adjacent feature into a polished, trustworthy tool.

## Primary Files

- `web/app/services/morph_service.py`
- `web/app/routers/morph.py`
- `web/app/routers/search.py`
- `web/templates/index.html`
- `web/static/search.js`
- docs if labels or explanations change
- tests under `web/tests/`

## Tasks

### 1. Make Lookup Behavior More Transparent

Where practical, expose or preserve:

- normalized lookup input
- supported variant forms
- predictable fallback behavior

Avoid surfacing noisy internal details that do not help users.

### 2. Improve Cross-Encoding Consistency

Verify behavior for supported equivalent inputs across:

- IAST
- Devanagari
- internal normalized/transliterated forms

### 3. Handle Failure Gracefully

When external lookup support is unavailable:

- fail softly where possible
- preserve a useful search experience
- avoid returning misleading confidence

### 4. Keep Wording Honest

The product term is:

`Stem/Root Lookup`

Do not revert to:

`Morphological Search`

unless the actual capability changes substantially and the docs are updated together.

## Acceptance Criteria

- lookup mode is consistently labeled across UI/docs/API surfaces that users see
- supported cross-script lookup behavior is covered by tests
- fallback behavior is documented in code/tests where needed

---

# Phase 4 - Export And Scholar Workflow Improvements

## Goal

Make exported search results more useful as scholarly artifacts.

## Primary Files

- `web/app/services/html_service.py`
- `web/app/routers/search.py`
- export-related templates
- tests under `web/tests/`

## Tasks

### 1. Add Better Export Context

Include in exported output where reasonable:

- search mode
- original query
- result count
- source-hit count
- whether a result limit was reached
- corpus or export generation context if readily available

### 2. Preserve Offline Utility

Exports should remain:

- self-contained or predictably viewable offline
- readable when opened later
- faithful to the browser result set for the same search

### 3. Add Export Regression Coverage

Tests should verify at least:

- metadata is present
- export still succeeds for valid search types
- special query characters do not break the export

## Acceptance Criteria

- exported HTML tells the reader what it represents
- export/Search result parity remains intact

---

# Phase 5 - Desktop Corpus Sync Bridge

## Goal

Let the legacy desktop application consume the web corpus pipeline in a practical, incremental way.

## Primary Files

- `Units/UpdateChecker.pas`
- related desktop update flow files if necessary
- `web/app/routers/corpus_sync.py`
- ingest or manifest files if contract tweaks are needed
- docs under `README.md` or dedicated sync notes if appropriate

## Tasks

### 1. Complete Manifest-Based Sync

Desktop client should:

- request `/api/corpus-sync/manifest`
- compare remote vs local state
- identify changed files
- download only changed files

### 2. Keep Failure Modes Visible

Add or preserve visible handling for:

- remote manifest unavailable
- partial download failure
- changed file fetch failure
- no updates available

### 3. Preserve Compatibility

Do not casually replace the existing legacy update system. Add or refine the sync path so existing expectations are not broken.

## Acceptance Criteria

- desktop sync flow is implemented or demonstrably end-to-end viable
- changed files can be detected and fetched individually
- failure states are not silent

---

# Phase 6 - Ingest And Corpus Validation

## Goal

Make corpus rebuilds easier to trust and easier to diagnose.

## Primary Files

- `web/ingest/ingest.py`
- `web/ingest/parse_html.py`
- `web/app/db.py`
- tests or validation scripts if needed

## Tasks

### 1. Add Ingest Validation Signals

Gemini should surface:

- missing files named in the source manifest
- stale DB entries caused by removed files
- invalid or empty corpus parse results
- manifest/hash inconsistencies where data is available

### 2. Preserve Idempotency

Re-running ingest should:

- not duplicate content
- not leave stale removed-file data behind
- not bloat the DB unnecessarily

### 3. Add Targeted Coverage

Tests or repeatable local checks should cover:

- added file
- changed file
- removed file
- missing file named in manifest

## Acceptance Criteria

- a corpus curator gets better diagnostics before publication
- rebuild behavior remains safe for scheduled or repeated use

---

# Phase 7 - Deployment And Operations

## Goal

Prepare the system for broader field use without distracting from the search-quality mission.

## Primary Files

- `web/Dockerfile`
- `docker-compose.yml` if present
- `web/nginx.conf`
- deployment notes in docs
- optional operator checklist file if useful

## Tasks

### 1. Rehearse The Production Path

Document and verify:

- DB generation
- service startup
- reverse proxy expectations
- SSE requirements under nginx

### 2. Add Lightweight Operational Notes

Document:

- rebuild/reindex steps
- where the large DB lives
- how to recover from failed ingest/sync incidents

### 3. Confirm Beta Readiness

Run a practical acceptance pass across:

- golden queries
- exports
- lookup mode
- desktop sync
- ingest rebuild

## Acceptance Criteria

- the project has a plausible beta-release operations story
- no critical workflow depends on tribal knowledge only

---

# Cross-Cutting Testing Expectations

Gemini should extend or preserve coverage for:

- `POST /api/search`
- `GET /api/search/export`
- `GET /api/search/stream`
- `/api/morph/{word}`
- `/api/corpus-sync/manifest`
- traversal protection on corpus-sync file serving
- search validation and invalid regex behavior
- rendering safety
- result summary and export wording

Use the current test suite as the base, not as a ceiling.

---

# Definition Of Done For Each Phase

A phase is done only when:

1. code changes are complete
2. tests are updated or added
3. docs are updated if behavior or wording changed
4. no unrelated behavior regressed
5. the change fits the month roadmap rather than inventing a new project

---

# First Suggested Gemini Work Batch

Gemini should begin with this bounded batch:

1. Create the golden query test scaffold.
2. Strengthen current search behavior assertions beyond status-code-only tests.
3. Improve zero-result/result-summary rendering in the web results fragment.
4. Add or update regression tests for those UI semantics.

This is the right first slice because it improves scholar-facing quality immediately and creates guardrails for later phases.

_Dr. Mārcis Gasūns_
