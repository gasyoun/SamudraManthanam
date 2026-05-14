# Gemini Flash Implementation Plan

Source review: `CODE_ARCHITECTURE_REVIEW.md`

This plan is written for Gemini Flash or another fast implementation agent. Keep tasks small, scoped, and independently verifiable. Do not attempt the full review in one change.

## Working Rules

1. Work in short PR-sized batches.
2. Prefer fixes that make the web app boot, test, and deploy before broader refactors.
3. Do not edit full corpus data under `Index/lib/x86_64-win64/Data` unless the task explicitly says so.
4. Do not delete tracked binaries or backups in the same PR as application code fixes. Artifact cleanup should be its own PR.
5. Do not change desktop updater behavior casually. Treat updater changes as security-sensitive.
6. Preserve current API shapes unless a task explicitly calls for a contract change.
7. After each task, run the listed verification commands and record results in the PR description.

## Target Outcome

The near-term goal is a web app that:

- imports and runs on the same Python version used by Docker,
- has a hermetic default test suite,
- avoids duplicated search work,
- has safer regex and CORS behavior,
- documents the trusted/untrusted HTML boundary,
- keeps large generated artifacts out of normal development flow.

## Phase 1: Make the Web App Boot Reliably

Priority: P0

### Task 1.1: Fix Python 3.11 Compatibility

Files:

- `web/app/services/search_service.py`
- `web/app/services/html_service.py`
- `web/app/services/morph_service.py`

Changes:

- Replace the nested f-string in `escape_fts` with Python 3.11-compatible code.
- Add missing typing imports:
  - `Optional` in `html_service.py`
  - `Optional` and `Any` in `morph_service.py`
- Keep runtime behavior unchanged.

Acceptance checks:

```powershell
cd C:\Users\user\Documents\GitHub\SamudraManthanam
python -m compileall web\app web\ingest
cd web
python -m pytest tests
```

If Docker is available:

```powershell
docker build -t samudra-manthanam-web .
```

### Task 1.2: Fix Morphological SSE Typo

File:

- `web/app/routers/search.py`

Change:

- In the SSE generator, replace `request.mode == SearchMode.morphological` with `mode == SearchMode.morphological`.

Add or update tests:

- Add a test for `/api/search/stream?query=svasti&mode=morphological`.
- Mock or constrain morphology so the test does not require a live external network call.

Acceptance checks:

```powershell
cd C:\Users\user\Documents\GitHub\SamudraManthanam\web
python -m pytest tests
```

## Phase 2: Make Tests Hermetic

Priority: P1

### Task 2.1: Remove Ad Hoc Scripts From Pytest Collection

Files:

- `web/test_search.py`
- `web/test_services.py`

Preferred change:

- Move these to `web/scripts/manual_search_check.py` and `web/scripts/manual_service_check.py`, or rename them so pytest does not collect them.

Do not:

- Delete useful manual logic unless replaced by a documented command.

Acceptance checks:

```powershell
cd C:\Users\user\Documents\GitHub\SamudraManthanam\web
python -m pytest
```

Expected result:

- No test tries to connect to `localhost:8000`.

### Task 2.2: Add a Tiny SQLite Fixture DB

Files:

- `web/tests/conftest.py`
- `web/tests/test_api.py`
- `web/tests/test_golden_queries.py`
- possibly `web/app/main.py`
- possibly router DB dependency modules

Changes:

- Create a tiny SQLite FTS DB in `tmp_path` for normal tests.
- Include at least:
  - 2 sources
  - Sanskrit/IAST text containing `svasti`, `arjuna`, and `sat tat`
  - one Russian line
  - one line with HTML tags and `id`
- Point app tests at this DB without relying on local `web/corpus.db`.

Implementation note:

- The current routers capture `DB_PATH` at import time. If this blocks test isolation, introduce a small settings/dependency layer or app factory.

Acceptance checks:

```powershell
cd C:\Users\user\Documents\GitHub\SamudraManthanam\web
python -m pytest
```

Expected result:

- Tests pass in a clean checkout without `web/corpus.db`.

### Task 2.3: Split Full-Corpus Tests

Files:

- `web/tests/test_golden_queries.py`
- `pytest.ini` or `pyproject.toml` if introduced

Changes:

- Keep fixture-based tests as default.
- Mark tests requiring the full local DB with a marker such as `corpus`.

Acceptance checks:

```powershell
python -m pytest
python -m pytest -m corpus
```

The default command must not require the 521 MB DB.

## Phase 3: Stabilize Search Semantics

Priority: P1

### Task 3.1: Document Search Contract

File:

- `web/SEARCH_CONTRACT.md`

Cover:

- plain search: token, prefix, or substring behavior
- multi-token query behavior
- multi-line query behavior
- case sensitivity
- whole-word behavior
- regex behavior
- morphological behavior
- expected differences from the desktop app

Acceptance:

- The document answers whether `arjun` should match `arjuna`.
- The document answers whether plain search should search stripped text or raw HTML.

### Task 3.2: Add Contract Tests Before Behavior Changes

Files:

- `web/tests/test_search_contract.py`

Tests to add:

- `arjuna` returns expected hit.
- `arjun` behavior matches `SEARCH_CONTRACT.md`.
- whole-word search does not return inflected/longer token when contract says it should not.
- query present only in HTML tag/attribute does not match plain stripped-text search.
- multi-line query behaves as OR.
- multi-token query behaves as AND.

Acceptance checks:

```powershell
python -m pytest web\tests\test_search_contract.py
```

### Task 3.3: Implement Contracted Plain Search

Files:

- `web/app/services/search_service.py`
- possibly `web/app/db.py`
- possibly `web/ingest/ingest.py`

Implementation options:

- If token search is accepted: update docs and UI wording to avoid promising substring search.
- If substring/prefix compatibility is required: add a deliberate implementation, such as FTS prefix indexes, trigram support, or bounded fallback filtering.

Do not:

- Hide a slow full-table scan behind normal plain search without a clear limit and performance tests.

Acceptance checks:

```powershell
python -m pytest web\tests
```

## Phase 4: Stop Duplicated Search Work

Priority: P1

### Task 4.1: Remove Progress-Only SSE or Make It Own the Search

Files:

- `web/static/search.js`
- `web/app/routers/search.py`

Choose one path:

Path A, simpler:

- Remove SSE progress for now.
- Use only `POST /api/search`.
- Show an indeterminate loading state in the UI.

Path B, fuller:

- Make the SSE endpoint stream result batches and final metadata from the same search execution.
- Do not also send a POST for the same query.

Recommended for Gemini Flash:

- Use Path A first. It is smaller and safer.

Acceptance checks:

- A search triggers one backend search request, not two.
- UI still displays results and export still works.
- Tests pass.

## Phase 5: Add Production Safety Rails

Priority: P1/P2

### Task 5.1: Bound Regex Search

Files:

- `web/app/models.py`
- `web/app/services/search_service.py`
- `web/app/routers/search.py`

Changes:

- Add max regex length validation.
- Add scanned-row or elapsed-time budget.
- Return a clear error or partial-result metadata when the budget is exceeded.
- Consider running regex search in a worker thread if it blocks async responsiveness.

Acceptance tests:

- Invalid catastrophic-looking or overlong regex is rejected or bounded.
- Normal regex still works.
- Source filtering still works.

### Task 5.2: Configure CORS by Environment

Files:

- `web/app/main.py`
- possibly new `web/app/settings.py`

Changes:

- Replace unconditional wildcard CORS with settings-driven origins.
- Default development can allow localhost.
- Production must use explicit origins.
- Disable credentials unless required.

Acceptance:

- Tests confirm CORS middleware is configured.
- App still starts without environment variables.

### Task 5.3: Safe Export Filename

File:

- `web/app/routers/search.py`

Change:

- Do not use raw query text directly in `Content-Disposition`.
- Generate a safe filename such as `samudra-search.html` or a sanitized/truncated slug.

Acceptance tests:

- Query containing quotes, slashes, Unicode, and CR/LF cannot break headers.

### Task 5.4: Document and Enforce HTML Trust Boundary

Files:

- `web/HTML_RENDERING_POLICY.md`
- `web/templates/result_fragment.html`
- `web/static/search.js`
- optionally ingest sanitizer

Changes:

- Document whether corpus HTML is trusted.
- If untrusted, sanitize before rendering.
- If trusted, document why and add a warning around ingestion sources.

Acceptance:

- There is a clear policy document.
- Tests include at least one script-tag or event-handler sample if sanitization is implemented.

## Phase 6: Improve Ingest Reliability

Priority: P2

### Task 6.1: Skip Unchanged Sources

Files:

- `web/ingest/ingest.py`
- `web/tests/test_ingest.py`

Changes:

- Use filename, size, and SHA-256 to skip reinserting unchanged files.
- Preserve current behavior for changed files and removed files.

Acceptance:

- Running ingest twice on the same fixture corpus does not rewrite unchanged rows.
- Changed file updates its rows.
- Removed file removes its rows.

### Task 6.2: Build Into Temporary DB Then Swap

Files:

- `build-web-db.ps1`
- `web/ingest/ingest.py`
- possibly `reindex.sh`

Changes:

- Build `corpus.db.tmp`.
- Validate schema and minimum row/source counts.
- Replace `corpus.db` only after success.

Acceptance:

- Failed ingest leaves the old DB untouched.
- Successful ingest replaces the DB.

## Phase 7: Desktop App Follow-Up

Priority: separate PR stream

### Task 7.1: Fix Desktop Raw-HTML Search Bug

File:

- `Index/uabstractthread.pas`

Change:

- Review lines where `S2` stripped text is assigned to `Str` and then overwritten by raw `S`.
- If stripped text is intended, remove the overwrite.

Acceptance:

- Build Lazarus project.
- Add or document a manual test where a query appears only in an HTML tag/attribute.

### Task 7.2: Harden Updater

Files:

- `Units/UpdateChecker.pas`
- `Index/uupdateform.pas`
- `Index/Updater/POUpdater.lpr`

Changes:

- Verify package hash from manifest.
- Add package signature verification if feasible.
- Reject unsafe zip paths before extraction.
- Extract to staging directory before replacing files.
- Remove `TerminateThread` cancellation if possible.

Acceptance:

- Good package installs.
- Package with wrong hash is rejected.
- Zip entry with `..\` is rejected.
- Cancellation leaves no partial executable replacement.

## Phase 8: Repository Hygiene

Priority: P1, but separate from behavior fixes

### Task 8.1: Extend `.gitignore`

File:

- `.gitignore`

Add patterns for:

- Lazarus/Free Pascal build outputs
- generated search output
- local release folders
- temporary ingest DB files
- Python virtualenvs and caches

Do not remove tracked files in this task.

Acceptance:

```powershell
git status --ignored --short
```

Generated outputs should be ignored after a local build/reindex.

### Task 8.2: Remove Tracked Build Artifacts

Files:

- tracked `.exe`, `.dcu`, `.o`, `.ppu`, `.dbg`, `.compiled`, `.obj`, `.sres`, `.whf`
- tracked backup folders and `.bak` files

Change:

- Remove generated artifacts from Git tracking only after `.gitignore` is updated.
- Keep release binaries as GitHub Release assets instead.

Acceptance:

- Source builds still work from clean checkout using documented steps.
- Release process documents where binaries are published.

## Suggested PR Sequence

1. `web: fix Python 3.11 boot blockers`
2. `web: make tests hermetic`
3. `web: fix morphological SSE and search contract tests`
4. `web: remove duplicated SSE search work`
5. `web: add regex, CORS, and export safety rails`
6. `web: improve ingest reliability`
7. `desktop: fix stripped-text search parity`
8. `desktop: harden update package validation`
9. `repo: ignore and remove generated artifacts`

## PR Description Template

Use this for every implementation PR:

```markdown
## What Changed

- ...

## Why

- ...

## Verification

- [ ] `python -m compileall web\app web\ingest`
- [ ] `python -m pytest`
- [ ] Docker build, if relevant
- [ ] Lazarus build, if relevant

## Risk

- ...

## Follow-Up

- ...
```

## Stop Conditions

Stop and ask for human review if:

- a change requires deleting or rewriting corpus files,
- a task touches updater execution/security and tests cannot be added,
- search semantics are ambiguous after reading `SEARCH_CONTRACT.md`,
- a fix requires replacing SQLite FTS with another search engine,
- Docker build and local tests disagree in a way that cannot be explained.
