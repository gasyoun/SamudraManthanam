# Samudra Manthanam Code and Architecture Review

Review date: 2026-05-15

## Executive Summary

Samudra Manthanam is in the middle of a sensible migration: the proven Windows/Lazarus corpus search application is still present, while a newer FastAPI web application indexes the same corpus into SQLite FTS5 and exposes browser search/export workflows. The broad direction is good. The current risk is that the migration boundary is porous: legacy release artifacts, generated data, desktop updater binaries, web app code, fixture-like local databases, and exploratory tests all live together without a clear source/build/runtime contract.

The web app has several deploy-blocking and production-readiness issues. Most importantly, the Docker target is `python:3.11-slim`, but the checked-in Python currently depends on Python 3.12+ f-string parsing and on Python 3.14-style lazy annotation behavior in a few modules. The local tests passed mostly because they were run with Python 3.14 and a local 521 MB `web/corpus.db`; the same code path is unlikely to boot in the Docker image as written.

The legacy desktop app is functional but fragile. It loads the full corpus into memory, launches one thread per query, writes HTML directly, and self-updates by downloading and extracting an unsigned zip. Those choices were reasonable for a portable Windows desktop tool, but they should not be carried forward into the web/server architecture without stronger trust, isolation, and test boundaries.

## System Map

### Legacy Desktop Application

- `Index/Index_pr.lpi` / `Index/Index_pr.lpr`: Lazarus project entry point.
- `Index/u_Index.pas`: main form, source selection, options, thread orchestration, file loading, result list management.
- `Index/uabstractthread.pas`: threaded search worker, progress updates, HTML result generation.
- `Units/textu.pas`, `Units/_textu.pas`, `Units/_winutils.pas`, `Units/uTypes.pas`: shared utilities.
- `Units/UpdateChecker.pas`, `Index/uupdateform.pas`, `Index/Updater/POUpdater.lpr`: self-update flow.
- `Index/lib/x86_64-win64/Data`: runtime corpus data used by both the desktop app and the web ingest flow.

### Web Application

- `web/ingest/ingest.py`: reads `Programdata/data.txt`, parses corpus files, and builds `web/corpus.db`.
- `web/ingest/parse_html.py`: strips HTML, extracts source titles, link IDs, and chapter headings.
- `web/app/db.py`: SQLite schema, including `sources`, `corpus_lines` FTS5, and `morph_cache`.
- `web/app/routers/*.py`: API surface for sources, search, morphology, and corpus sync.
- `web/app/services/search_service.py`: plain and regex search implementation.
- `web/app/services/morph_service.py`: Sanskrit transliteration and external Sanskrit Heritage lookup.
- `web/app/services/html_service.py`: Jinja rendering for API fragments and standalone HTML exports.
- `web/templates` and `web/static`: browser UI and legacy-compatible result rendering.
- `Dockerfile` and `docker-compose.yml`: container packaging, expecting a prebuilt host `web/corpus.db`.

### Current Local Corpus DB

The local ignored database is present at `web/corpus.db`, size `521252864` bytes. It currently contains:

- `148` sources
- `460548` FTS corpus rows
- source `sort_order` range `0..147`

That DB is useful for local development, but tests should not require it unless explicitly marked as large/integration tests.

## Findings

### P0: Docker Target Is Not Compatible With Current Python Code

`Dockerfile:1` uses `python:3.11-slim`, but `web/app/services/search_service.py:14` uses nested f-string expression syntax that is accepted by Python 3.12+ and rejected by Python 3.11 and earlier:

```python
tokens = [f'"{t.replace('"', '""')}"' for t in safe.split() if t.strip()]
```

Verified with:

```powershell
py -3.10 -m py_compile web\app\services\search_service.py
```

Result:

```text
SyntaxError: unterminated string literal (detected at line 14)
```

This is a strong proxy for the Docker image because Python 3.10 and 3.11 both predate PEP 701's relaxed f-string grammar.

There are also import-time annotation failures on Python versions that eagerly evaluate annotations. `web/app/services/html_service.py:49` uses `Optional` without importing it, and `web/app/services/morph_service.py:65` uses `Optional` and `Any` without importing them. With dependencies stubbed, Python 3.10 fails with:

```text
NameError: name 'Optional' is not defined
```

Recommended fixes:

- Make the code Python 3.11-compatible or change Docker to a supported Python version intentionally.
- Add the missing typing imports:
  - `from typing import List, Dict, Any, Optional` in `html_service.py`
  - `from typing import List, Dict, Set, Optional, Any` in `morph_service.py`
- Add CI that runs at least `python -m compileall web/app web/ingest` and `pytest` on the same Python version used by Docker.

### P0: Desktop Auto-Update Trust Boundary Is Too Weak

The desktop updater downloads an update manifest and zip from HTTPS, then launches `POUpdater.exe`, which extracts the zip over the application directory:

- `Units/UpdateChecker.pas:17-18`: hard-coded manifest and zip URLs.
- `Units/UpdateChecker.pas:66-68`: `URLDownloadToFileA` downloads the manifest.
- `Index/uupdateform.pas:59-60`: `URLDownloadToFile` downloads the update zip.
- `Index/Updater/POUpdater.lpr:31-34`: `TUnzipper.UnZipAllFiles` extracts every entry.
- `Index/Updater/POUpdater.lpr:61-63`: update is extracted, zip is deleted, and `PO.EXE` is relaunched.

There is no signature verification, no pinned publisher key, no manifest hash verification, and no visible validation that zip entries stay inside `AppPath`. A compromised server, CDN, DNS path, or update package can replace executables. A malicious zip could also attempt path traversal unless `TUnzipper` is wrapped with explicit destination validation.

Recommended fixes:

- Sign update manifests or packages with an offline private key and verify with an embedded public key before extraction.
- Include SHA-256 hashes in the manifest and verify the downloaded zip before running the updater.
- Reject zip entries with absolute paths, drive letters, `..`, or normalized paths outside `AppPath`.
- Extract into a staging directory, validate contents, then perform an atomic swap/rename.
- Prefer Windows Authenticode signing for released executables.

### P1: Search Work Is Duplicated and Can Be Very Expensive

The browser starts an SSE progress request and then sends the real POST search:

- `web/static/search.js:68-72`: opens `/api/search/stream`.
- `web/static/search.js:98-102`: immediately posts `/api/search`.

The stream handler does not reuse final search results. Instead, it scans source by source:

- `web/app/routers/search.py:102-117`: loops over every source and calls the relevant search function.
- `web/app/routers/search.py:141`: returns only progress events, not result data.

On the local DB that means a normal search can run across 148 sources for progress and then run again for the actual response. Regex mode is especially risky because `search_regex` scans rows in Python.

Recommended fixes:

- Make one endpoint own a search job and stream both progress and results, or remove SSE until there is a real background job.
- Cache or share the result set between progress and final response.
- For regex, add a source-level prefilter, timeout, cancellation, and a maximum scanned-row budget.

### P1: User Regex Can Block the Server

`web/app/services/search_service.py:90-128` compiles user-provided Python regexes and applies them to every candidate row. There is no timeout, no safe-regex engine, and no worker isolation. Catastrophic backtracking can monopolize the event loop thread and starve other users.

Recommended fixes:

- Use a regex engine with time limits or safer guarantees.
- Run regex searches in a bounded worker pool with cancellation.
- Add request-level timeouts, maximum pattern length, and maximum scanned-row limits.
- Consider prefiltering with FTS tokens before applying regex.

### P1: Morphological SSE Mode Is Broken

In `web/app/routers/search.py:63-64`, the route receives a FastAPI `Request` object named `request` and a search mode named `mode`. Inside the event generator, the morphological branch checks `request.mode`:

```python
elif request.mode == SearchMode.morphological:
```

This should be `mode == SearchMode.morphological`. As written, morphological streaming progress will not take the intended branch and can fail because `Request` has no `mode` attribute.

Recommended fix:

- Replace `request.mode` with `mode`.
- Add a test for `/api/search/stream?mode=morphological`.

### P1: Plain Search Semantics Diverge From the Desktop App

The desktop search uses substring-style matching through `Pos(SubStr, Str)` in `Index/uabstractthread.pas:134-146`. The web app uses SQLite FTS token matching:

- `web/app/services/search_service.py:5-17`: builds quoted token queries.
- `web/app/services/search_service.py:43-50`: uses `WHERE corpus_lines MATCH ?`.

This means a non-whole-word query can fail to match inside longer words. For example, against the local DB, `arjun` returned `0` while `arjuna` returned hits. That behavior is surprising if the web app is meant to preserve the desktop "plain text" mode.

Recommended fixes:

- Decide and document exact search semantics for:
  - substring
  - token
  - prefix
  - whole word
  - case sensitivity
  - IAST/SLP1/Devanagari normalization
- If desktop compatibility matters, add substring/prefix support explicitly. Options include trigram indexing, an additional normalized text table, FTS prefix indexes, or a bounded fallback scan.
- Add golden tests for partial words in Sanskrit and Russian.

### P1: Legacy Desktop Search Appears to Scan HTML Instead of Stripped Text

`Index/uabstractthread.pas:540` reads the `.no_tags` line into `S2`, but `Index/uabstractthread.pas:548-549` assigns `Str` from `S2` and then immediately overwrites it from `S`:

```pascal
if not bOptionsCaseSensitive then Str:=AnsiLowerCase(S2) else Str:=S2;
if not bOptionsCaseSensitive then Str:=AnsiLowerCase(S) else Str:=S;
```

The second assignment makes the actual search run over the raw HTML line, not the stripped text. This can create false positives from tags/attributes and makes parity with the ingest pipeline harder to reason about.

Recommended fix:

- Remove the second assignment unless searching HTML is intentional.
- Add a regression case where the query appears only in a tag or attribute and must not match.

### P1: Whole-Word Search Is Incomplete Across Both Implementations

The desktop worker only applies whole-word behavior when regex mode is enabled:

- `Index/uabstractthread.pas:140-141`: wraps the regex expression in `\b...\b` when `bOptionsWholeWord` is true.
- `Index/uabstractthread.pas:67-94`: the plain whole-word helper is commented out as not working.
- `Index/u_Index.pas:676-678`: UI options are passed to the worker, but plain mode still reaches `Pos`.

The web app also has weak whole-word semantics:

- `web/app/services/search_service.py:9-17`: whole-word changes FTS quoting, not a true Unicode-aware boundary rule.
- `web/app/services/search_service.py:56-80`: Python-side filtering runs only after the FTS `LIMIT`, so true matches after the first FTS page can be missed.

Recommended fixes:

- Define a Unicode-aware token boundary function shared by tests and implementations.
- Filter before applying the final limit, or over-fetch and continue until enough valid matches are collected.
- Add tests for Russian, IAST diacritics, SLP1, and Devanagari boundaries.

### P1: Test Suite Is Not Hermetic

Running `python -m pytest` from `web/` produced:

```text
1 failed, 19 passed
```

The failing test is `web/test_search.py::test`, which calls a live server at `http://localhost:8000/api/search` (`web/test_search.py:7`). The rest of the passing API/golden tests rely on the ignored local `web/corpus.db`. In a clean checkout or CI environment, those tests will either fail or silently test a different DB.

Recommended fixes:

- Move ad hoc scripts `web/test_search.py` and `web/test_services.py` out of pytest discovery, or rename them so they are not collected.
- Build a tiny fixture SQLite DB in `tmp_path` for unit/API tests.
- Set `DB_PATH` via dependency injection or app factory rather than module-level constants captured at import time.
- Mark full-corpus tests separately, for example `pytest -m corpus`.

### P1: The Repository Tracks Release and Build Artifacts

The repo currently has `780` tracked files. Static inspection found at least:

- `49` tracked build artifacts: `.exe`, `.dcu`, `.o`, `.ppu`, `.dbg`, `.compiled`, `.res`, `.obj`, `.whf`, `.sres`.
- `35` tracked backups: `backup/`, `*.bak`, and `~pas/~dfm` style files.

Examples include:

- `Index/lib/x86_64-win64/PO.exe`
- `Index/lib/x86_64-win64/Index_pr.exe`
- `Index/Updater/POUpdater.exe`
- `Corpus_builder/PSRCBuilder/cb.exe`
- many Lazarus unit/object outputs under `Index/lib/x86_64-win64` and `Corpus_builder/PSRCBuilder/dcu`

This makes code review harder, bloats history, increases supply-chain ambiguity, and blurs whether the repository is source code, release bundle, corpus bundle, or build output.

Recommended fixes:

- Decide the canonical repo boundary:
  - source code
  - corpus source data
  - generated corpus DB
  - desktop release bundle
- Keep generated binaries and DBs out of normal Git history.
- Publish desktop builds as GitHub Release assets.
- Extend `.gitignore` for Lazarus/Delphi outputs, local release folders, and generated search output.
- If large corpus data must remain versioned, consider Git LFS or a dedicated data repository.

### P2: HTML Rendering Trust Boundary Needs a Clear Policy

The web API returns rendered HTML fragments containing corpus HTML:

- `web/templates/result_fragment.html:46`: `{{ item['line_html'] | safe }}`
- `web/templates/full_page.html:13`: `{{ fragment | safe }}`
- `web/templates/standalone_page.html:22`: `{{ fragment | safe }}`
- `web/static/search.js:111`: inserts `data.html_fragment` with `.html(...)`.

If the corpus is strictly curated and trusted, this can be acceptable. If corpus sync or future user/admin ingestion can introduce untrusted HTML, this is an XSS boundary. The frontend also appends source titles directly into template literals in `web/static/search.js:9-14`, which is safe only while source titles are trusted.

Recommended fixes:

- Write down whether corpus HTML is trusted content.
- If it is not fully trusted, sanitize to a strict allowlist before storing or rendering.
- Add a Content Security Policy that blocks inline scripts if possible.
- Avoid returning HTML fragments from JSON APIs for untrusted data; return structured data and render with text-safe DOM APIs.

### P2: CORS Configuration Is Too Broad

`web/app/main.py:13-18` configures:

```python
allow_origins=["*"],
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"],
```

For a public deployment, this is broader than necessary and can produce confusing browser behavior because wildcard origins and credentials are a bad combination.

Recommended fixes:

- Use explicit allowed origins for production.
- Make CORS environment-specific.
- Disable credentials unless the app actually uses cookies or authenticated browser state.

### P2: Ingest Uses Hashes But Does Not Use Them for Incremental Work

`web/ingest/ingest.py:59-61` computes `title`, `sha256`, and `size`, but `web/ingest/ingest.py:63-105` still deletes and reinserts every source in `data.txt`. Reindexing therefore scales with the whole corpus even when no source changed.

The ingest commits source by source. That is pragmatic for long builds, but a failed run can leave the DB partially updated with a mix of old and new source IDs.

Recommended fixes:

- Skip unchanged files when filename, size, and hash match.
- Build into a temporary DB and atomically replace the old DB when the full ingest succeeds.
- If in-place updates are required, record ingest version/build status and expose only a completed generation.
- Add indexes or metadata needed by sync/versioning workflows.

### P2: Database Connections and Configuration Are Repeated Per Request

Every router captures `DB_PATH` at import time and opens a new SQLite connection per request:

- `web/app/routers/search.py:16`
- `web/app/routers/morph.py:8`
- `web/app/routers/sources.py:10`
- `web/app/routers/corpus_sync.py:8`
- `web/app/db.py:4-7`

This is simple, but it makes tests harder to isolate and increases per-request overhead.

Recommended fixes:

- Introduce an application settings object.
- Prefer an app factory: `create_app(settings)`.
- Use FastAPI lifespan to initialize shared read-only resources where appropriate.
- Keep per-request DB connections if SQLite concurrency requires it, but inject the path through a dependency.

### P2: Morphology Depends on a Live External API During Requests

`web/app/services/morph_service.py:43-49` calls the Sanskrit Heritage API during request handling. It has a timeout and cache, which helps, but the first request for a word still depends on an external service. URL parameters are interpolated into the URL string rather than passed through `params=`.

Recommended fixes:

- Use `httpx.AsyncClient(...).get(url, params={...})`.
- Make the external API optional and visibly degraded when unavailable.
- Add negative caching and cache TTL/versioning.
- Avoid live network calls in tests; mock the expansion layer.

### P2: Source Sync File Serving Is Mostly Safe but Narrow

`web/app/routers/corpus_sync.py:24-42` uses `os.path.basename` and checks the filename against the DB manifest before `FileResponse`. That blocks basic path traversal. The route path `/{filename}` only supports simple names, which fits the current manifest.

Recommended improvements:

- Use `pathlib.Path.resolve()` and verify the final path is under `CORPUS_PATH / "Data"` as defense in depth.
- Set explicit media type and download headers.
- Include a manifest version derived from data hashes rather than the static `"2026.05"` in `web/app/routers/corpus_sync.py:18`.

### P2: Unsafe Thread Cancellation in Desktop Updater

`Index/uupdateform.pas:100-103` cancels a download by calling `TerminateThread(Thread.Handle, 0)`. This can leave locks, memory, or file handles in unknown states.

Recommended fixes:

- Use cooperative cancellation if the HTTP client supports it.
- Download to a temporary `.part` file and delete it after the thread exits normally.
- Disable cancellation only at the short critical point where cleanup cannot be safely interrupted.

### P3: Duplicate and Dead Code Should Be Trimmed

There are duplicated update routines and legacy/test snippets:

- `Units/UpdateChecker.pas:126-167` and `Index/u_Index.pas:1484-1525` both define update-check logic.
- `Index/u_Index.pas:807-826` appears to be a regex experiment that mutates the status bar during startup.
- `web/test_services.py` is an executable helper, not a pytest-style test.
- Several `backup/`, `~pas`, `~dfm`, and `.bak` files are tracked.

Recommended fixes:

- Remove or archive dead experiments outside the main source tree.
- Keep one update implementation.
- Move manual scripts to `scripts/` with names that pytest will not collect.

## Strengths

- The migration target is directionally strong: FastAPI + SQLite FTS5 is a reasonable fit for a corpus search service.
- The generated `web/corpus.db` is intentionally ignored, and `README.md` documents how to rebuild it.
- SQL query construction uses placeholders for user values; dynamic `IN (...)` placeholders are generated from integer arrays rather than string-concatenated values.
- Pydantic request validation catches empty queries, invalid modes, and invalid regex for POST requests.
- Search results preserve original HTML output, which helps maintain compatibility with established desktop result pages.
- The existing corpus DB already has useful scale for performance work: 148 sources and roughly 460k searchable rows.

## Recommended Architecture Direction

### 1. Define Source, Data, Build, and Release Boundaries

Use the repository primarily for source and small fixtures. Publish release executables and large generated artifacts separately. A clean boundary will make code review, CI, security scanning, and deployment more predictable.

Proposed split:

- Source repo: Pascal source, Python source, templates/static source, ingest code, small test fixtures.
- Data artifact: full corpus source bundle, if too large or frequently generated.
- Generated artifact: SQLite DB built from a known corpus version.
- Release artifact: signed desktop zip/exe bundle.

### 2. Make the Web App the Canonical Search Contract

Before optimizing implementation, lock down the expected semantics:

- exact vs substring vs prefix
- whole-word rules by script
- case sensitivity by script
- regex behavior and limits
- multi-query `AND`/`OR` rules
- rendering and export format

Once that contract exists, both the desktop app and web app can be tested against the same golden cases.

### 3. Replace Progress-Only SSE With a Real Search Job Model

Current SSE work is extra work. A better model:

- Client starts one search.
- Backend streams progress and result batches from the same execution.
- Client can cancel the search.
- Backend applies a single limit and a single timeout budget.

For simple deployments, remove SSE and return the final JSON/HTML only.

### 4. Harden Public Web Rendering

If the app will be public at `samskrtam.ru`, treat corpus HTML as a content boundary. Either document it as trusted curated HTML or sanitize it. Add CSP, explicit CORS, request limits, and controlled export filenames.

### 5. Modernize Tests and CI

Minimum useful CI gate:

```powershell
python -m compileall web\app web\ingest
python -m pytest web\tests
```

Then add:

- fixture DB tests
- full-corpus integration tests behind a marker
- Docker build smoke test
- a small search parity suite shared with legacy behavior
- updater package validation tests

## Suggested Near-Term Fix Order

1. Fix Python 3.11 compatibility and missing typing imports.
2. Remove or rename `web/test_search.py` from pytest collection.
3. Add a tiny fixture DB and stop requiring local `web/corpus.db` for normal tests.
4. Fix morphological SSE `request.mode` typo.
5. Decide web plain-search semantics and add tests for partial words.
6. Stop duplicate SSE + POST search work.
7. Add regex execution limits.
8. Harden updater package verification before the next desktop release.
9. Clean tracked build/backup artifacts and extend `.gitignore`.
10. Add an app settings/app factory layer for testable DB configuration.

## Verification Performed

Commands run:

```powershell
git status --short --branch
rg --files
python -m pytest
py -3.10 -m py_compile web\app\services\search_service.py
py -3.10 -m py_compile web\app\services\morph_service.py web\app\services\html_service.py web\app\routers\search.py
py -3.12 -m py_compile web\app\services\search_service.py web\app\services\morph_service.py web\app\services\html_service.py web\app\routers\search.py
```

Observed results:

- Git branch: `main...origin/main`; no modified files before this report was added.
- `python -m pytest` from `web/`: `19 passed`, `1 failed`.
- The failed test was `web/test_search.py::test`, caused by `httpx.ConnectError` because no server was listening on `localhost:8000`.
- `py -3.10 -m py_compile web\app\services\search_service.py` failed with a syntax error at line 14.
- Python 3.12+ compile accepted the same Python service files.
- Local `web/corpus.db` exists, is ignored by Git, and contains 148 sources / 460548 FTS rows.

Not performed:

- I did not compile the Lazarus projects because this environment was used for static review and Python verification only.
- I did not rebuild the full 521 MB SQLite DB.
- I did not run a Docker build.
