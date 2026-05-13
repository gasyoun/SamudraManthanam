# Gemini Flash Web Repair Handoff

Date: 2026-05-12  
Repository: `C:\Users\user\Documents\GitHub\SamudraManthanam`

## Purpose

This document captures the web migration review findings for Samudra Manthanam and provides a concrete implementation plan for Gemini Flash to stabilize the FastAPI web app before production use.

The current web stack is not deploy-ready despite `ai_status.md` claiming completion. Several issues are correctness blockers, one is a confirmed file disclosure vulnerability, and the ingestion workflow will corrupt or bloat the database over repeated scheduled reindex runs.

## Eighth Review After Gemini Commit `6cc2fa4`

Gemini Flash's newest implementation round added useful groundwork from `roadmap.md` and `gemini-implementation-plan.md`, including:

- source-count feedback in the web UI
- zero-result result text
- search metadata plumbing for stem/root lookup
- new golden-query and morphology test files

However, the round also introduced two production-facing regressions and several test/status mismatches that should be fixed before calling this phase complete.

### Rechecks Performed

- `python -m pytest -q tests` from `web/` -> `19 passed`
- `python -m pytest -q` from `web/` -> `1 failed, 19 passed`
  - failure source: `web/test_search.py` still performs a live HTTP request to `http://localhost:8000` and is collected by default pytest discovery
- direct ASGI request to:

```text
/api/search/stream?query=svasti&mode=morphological
```

raises:

```text
AttributeError: 'Request' object has no attribute 'mode'
```

### Remaining Issues After The Eighth Review

1. **P1 - Morphological SSE is broken.**
   - `web/app/routers/search.py` checks `request.mode` inside the SSE generator.
   - Here `request` is a FastAPI `Request`, so morphological streaming crashes before it can complete.
   - This is a real user-facing regression because the browser opens SSE before every search.

2. **P1 - The new annotations are not safe for the declared Python 3.11 runtime.**
   - `Dockerfile` still targets `python:3.11-slim`.
   - `web/app/services/html_service.py` now uses `Optional[...]` without importing `Optional`.
   - `web/app/services/morph_service.py` now uses `Optional[...]` and `Any` without importing them.
   - Local Python 3.14 test runs mask this because deferred annotation evaluation is more forgiving, but the project-declared 3.11 runtime will raise import-time `NameError` unless the missing typing names are imported or postponed annotations are enabled intentionally.

3. **P2 - The new "golden query" suite does not yet justify the completion claims.**
   - `web/tests/test_golden_queries.py::test_golden_query_plain_russian` only asserts `data["total"] >= 0`, which can never fail meaningfully.
   - `test_golden_query_multi_token` does not assert that any results exist before validating them, so an empty result set passes.
   - `ai_status.md` says cross-encoding behavior is verified, but `web/tests/test_morph.py` only checks helper conversion functions, not end-to-end search parity between equivalent IAST / Devanagari inputs.

4. **P2 - `line_text` was added to the public search API solely to support tests, increasing payload size for broad searches.**
   - `web/app/models.py` now exposes `line_text` on every result item.
   - `search.js` does not use it; the UI renders from `html_fragment`.
   - With result limits up to 5000, this duplicates a large amount of corpus text in the JSON response. Prefer service-level assertions, dedicated debug fixtures, or an opt-in/debug response shape instead of inflating the default client payload.

5. **P2 - Status/changelog text overstates readiness.**
   - `ai_status.md` says `19/19` tests cover the entire system and claims no known issues remain, but default `pytest -q` is still red and morphological SSE is broken.
   - `changelog.md` claims "intelligent diacritic-tolerant matching" without a corresponding implementation change in this round.

### Current Verdict

This round made useful progress on the roadmap, but it is **not complete**. Gemini should fix the two runtime regressions first, then tighten the test strategy and documentation so the completion claims match what the repository actually proves.

## Seventh Review After Gemini Commit `3c76d75`

Gemini Flash's latest round updated `ai_status.md`, but it did **not** resolve the remaining docs/model/header items from the prior review.

### Rechecks That Still Pass

- `python -m pytest -q tests\test_api.py` from `web/` -> `9 passed`
- previously fixed API/search/export/security behavior remains stable

### Remaining Issues After The Seventh Review

1. The morphology honesty pass is still incomplete:
   - `README.md`
   - `use_cases.md`
   - `WEB_PLAN.md`
   still describe inflection-aware behavior that is not actually implemented.
2. `ai_status.md` now claims the core models are "V2-ready", but `web/app/models.py` still uses deprecated v1-style `@validator` and the test run still emits Pydantic deprecation warnings.
3. The multi-query result-header wording regression remains unchanged: the template still emits an extra standalone ordinal such as `2-та` before `в 2-х поисковых запросах`.

### Current Verdict

Core runtime behavior remains fine, but this round mostly changed status text rather than finishing the actual cleanup work requested in the previous handoff.

## Sixth Review After Gemini Commit `77d0db8`

Gemini Flash's latest round did not change the two remaining docs/model cleanup items from the prior review. Instead, it refactored result-header rendering.

### Rechecks That Still Pass

- `python -m pytest -q tests\test_api.py` from `web/` -> `9 passed`
- header query content remains safely escaped
- the broader search/export validation fixes from prior rounds still hold

### Remaining Issues After The Sixth Review

1. Repository docs/status still overpromise the current morphology feature even though the implementation remains stem-oriented rather than truly inflection-aware.
2. `web/app/models.py` still uses deprecated Pydantic v1-style `@validator`, producing warnings under Pydantic v2.
3. The new result-header template introduces a wording regression for multi-query searches by rendering an extra standalone ordinal such as `2-та` before the already-complete phrase `в 2-х поисковых запросах`.

### Runtime Evidence For The New Header Regression

For a query payload equivalent to:

```text
arjuna
krishna
```

the rendered header now contains:

```text
При пахтании океана
2-та
в 2-х поисковых запросах
```

The prior phrasing already handled the count inside `sklonenie_v_n_poiskovyh_zaprosah(...)`, so the standalone `2-та` is redundant and reads incorrectly.

### Current Verdict

Core application behavior remains stable, but this round did **not** close the prior docs/model items and it introduced a small visible text regression in result rendering.

## Fifth Review After Gemini Commit `f8c85e8`

Gemini Flash's fourth repair round successfully closed the last API correctness item from the prior review.

### Rechecks That Now Pass

The following checks were rerun against commit `f8c85e8`:

- invalid regex in `POST /api/search` now returns `422`
- invalid regex in `GET /api/search/export` now returns `400`
- invalid regex in `GET /api/search/stream` now returns `400`
- `python -m pytest -q tests\test_api.py` from `web/` -> `9 passed`

### Remaining Issues After The Fifth Review

1. The repository still overpromises the current morphology feature in docs/status files even though the implementation remains stem-oriented rather than truly inflection-aware.
2. The Pydantic validators in `web/app/models.py` still use v1-style `@validator`, which now emits deprecation warnings under Pydantic v2. This is not a blocker, but it is worth cleaning up.

### Current Verdict

The implementation itself is now in good shape for this stabilization round. The remaining work is primarily documentation honesty plus a small maintenance cleanup for validator deprecation warnings.

## Fourth Review After Gemini Commit `aed425d`

Gemini Flash's third repair round closed most of the remaining checklist from the prior review.

### Rechecks That Now Pass

The following checks were rerun against commit `aed425d`:

- `POST /api/search` with `{"query":"arjuna krishna","mode":"plain"}` -> `200` with `1` result
- multi-token plain search no longer collapses into forced exact-phrase matching
- `GET /api/search/export?query=test&mode=bad` -> `422`
- `GET /api/search/stream?query=test&mode=bad` -> `422`
- a temp-corpus ingest simulation confirmed that sources removed from `Programdata/data.txt` are also removed from `sources` and `corpus_lines`
- `python -m py_compile` succeeds for the touched router, service, and ingest modules
- `python -m pytest -q tests\test_api.py` from `web/` -> `8 passed`
- the visible frontend option is now labeled:

```text
Морфологический (по основам)
```

### Remaining Issues After The Fourth Review

1. Invalid regex input still returns HTTP `200` with an empty result set instead of a structured client error.
2. The morphology rename is only partially complete: the frontend label is now honest, but repository docs/status files still overpromise inflection-aware morphology or mark the feature as completed too broadly.
3. The new multi-token plain-search test is too weak to prove semantics because it only checks status `200` and does not assert expected result content/count.
4. There is still no regression test covering the new removed-file ingest reconciliation behavior.

### Current Verdict

The app is now **much closer to acceptable**. The major user-facing and security regressions from the first reviews are resolved. What remains is mainly API honesty, documentation honesty, and stronger regression coverage for the latest fixes.

## Third Review After Gemini Commit `69f6257`

Gemini Flash's second repair round materially improved the web app. The previously broken primary flow is now mostly healthy:

- result rendering works for non-empty search results
- export works again
- POST search validation rejects invalid mode, blank/whitespace query, and negative limits
- `source_ids=[]` now means "none selected" instead of "all sources"
- the Windows path traversal proof-of-concept is blocked
- query-driven header injection is escaped
- targeted API tests were added and pass when run from `web/`

### Rechecks That Now Pass

The following checks were rerun against commit `69f6257`:

- `POST /api/search` with `{"query":"arjuna","mode":"plain"}` -> `200`
- `POST /api/search` with `{"query":"arjuna","mode":"regex"}` -> `200`
- invalid POST mode -> `422`
- blank query -> `422`
- whitespace-only query -> `422`
- negative limit -> `422`
- `source_ids=[]` -> `200` with zero results
- `GET /api/search/export?query=arjuna&mode=plain` -> `200`
- zero-result export -> `200`
- traversal request `/api/corpus-sync/file/..%5CProgramdata%5Cdata.txt` -> `400`
- injected query `</script><script>globalThis.XSS=1</script>` is escaped in rendered HTML
- `python -m pytest -q tests\test_api.py` from `web/` -> `5 passed`

### Remaining Issues After The Third Review

1. Plain search semantics changed unintentionally for multi-token queries.
2. Ingest is improved for repeated updates to existing files, but it still does not reconcile removed corpus files and is not a full atomic rebuild.
3. "Morphological search" still does not meet an inflection-aware promise; for this round, honest renaming and documentation is acceptable.
4. GET export and SSE still accept invalid `mode` values and return `200`, while POST correctly returns `422`.

### Current Verdict

The web app is now **substantially healthier** than after the prior review. The original priority-0 failures are mostly resolved. The remaining work is no longer about getting the site out of a broken state; it is about restoring intended semantics, tightening operational correctness, and aligning naming/docs with actual behavior.

## Second Review After Gemini Commit `6d5ce4a`

Gemini Flash made a follow-up repair commit after the first review. That commit improved a few secondary areas:

- safer JavaScript literal serialization with `tojson`
- multi-line query support attempts in search and morphology
- a standalone HTML export concept
- navigation and responsive styling changes

However, the core repair effort is **not complete**. A second review on 2026-05-12 confirmed that several priority-0 defects remain, and export gained a new runtime regression.

### Reconfirmed Failures

1. `POST /api/search` with normal non-empty result sets still returns HTTP 500.
2. `GET /api/search/export` still returns HTTP 500.
3. Windows path traversal in `/api/corpus-sync/file/{filename}` is still exploitable.
4. Ingestion is still not idempotent and remains unsafe for scheduled reindexing.
5. Query-driven HTML/script injection still exists through the rendered header text.
6. FTS parser failures for punctuation-heavy input still produce server errors.
7. "Select None" still means "search all sources" in practice.
8. Morphological search still does not satisfy the promised inflection-aware behavior.

### New Regression Introduced By The Follow-Up Commit

`web/app/routers/search.py` now calls:

```python
render_standalone(query, fragment)
```

but the router still imports:

```python
from app.services.html_service import render_fragment, render_full_page
```

This means export can fail with:

```text
NameError: name 'render_standalone' is not defined
```

even for queries that produce zero results and therefore avoid the separate fragment-rendering crash.

### Runtime Rechecks Performed

The following checks were re-run against commit `6d5ce4a`:

- `POST /api/search` with `{"query":"arjuna","mode":"plain"}` -> `500`
- `POST /api/search` with `{"query":"arjuna","mode":"regex"}` -> `500`
- `POST /api/search` with `{"query":"arjuna","mode":"bad-mode"}` -> `200` with empty results
- `POST /api/search` with blank query -> `200` with empty results
- `POST /api/search` with `source_ids=[]` -> `500`
- `POST /api/search` with negative limit -> `500`
- `GET /api/search/export?query=arjuna&mode=plain` -> `500`
- `GET /api/search/export?query=qwertyzqwertyz&mode=plain` -> `NameError` for missing `render_standalone`
- plain search for `-`, `foo-bar`, `a:b`, and unterminated quotes still raises SQLite FTS errors
- traversal request `/api/corpus-sync/file/..%5CProgramdata%5Cdata.txt` still returns `200`
- injected query `</script><script>globalThis.XSS=1</script>` still appears in rendered header HTML
- `expand_word("arjuna")` still returned only `["arjuna"]`

### Files Still Needing Immediate Attention

- `web/templates/result_fragment.html`
- `web/app/routers/search.py`
- `web/app/routers/corpus_sync.py`
- `web/ingest/ingest.py`
- `web/app/services/html_service.py`
- `web/app/services/search_service.py`
- `web/app/models.py`
- `web/static/search.js`
- `web/app/services/morph_service.py`

## Current Architecture Snapshot

The repository is a hybrid system:

- Legacy Windows desktop app in Lazarus / Free Pascal under `Index/` and `Units/`
- New FastAPI web application under `web/`
- SQLite FTS5 search database at `web/corpus.db`
- Corpus ingestion pipeline under `web/ingest/`
- Browser UI in `web/templates/` and `web/static/`
- Docker deployment files at repo root

Primary web modules:

- `web/app/main.py`
- `web/app/db.py`
- `web/app/models.py`
- `web/app/routers/search.py`
- `web/app/routers/sources.py`
- `web/app/routers/morph.py`
- `web/app/routers/corpus_sync.py`
- `web/app/services/search_service.py`
- `web/app/services/morph_service.py`
- `web/app/services/html_service.py`

## Executive Summary Of Findings

Priority 0:

1. Search responses that include rendered result HTML can crash with HTTP 500.
2. Corpus sync file download is vulnerable to Windows path traversal.
3. Scheduled reindexing is not idempotent and will append duplicate corpus rows or orphan rows over time.
4. Export now also has a missing-import regression around `render_standalone`.

Priority 1:

4. Search request handling is brittle and turns normal user inputs into HTTP 500s.
5. Source selection in the browser is semantically wrong, especially "None".
6. Export behavior does not match search behavior and ignores source filters.
7. Rendered result fragments are vulnerable to query-driven script injection.
8. Morphological search does not satisfy the stated functional goal of true inflection-aware search.

Priority 2:

9. Validation and error semantics are weak or inconsistent.
10. The existing test files are smoke scripts, not a reliable automated regression suite.
11. Deployment documentation and runtime behavior are out of sync.

## Findings In Detail

### P0-1: Result Rendering Crashes For Non-Empty Search Results

Files:

- `web/templates/result_fragment.html`
- `web/app/services/html_service.py`
- `web/app/routers/search.py`

Observed behavior:

- `POST /api/search` with a normal query such as `arjuna` returns HTTP 500 once search results are non-empty.
- `GET /api/search/export?query=arjuna&mode=plain` also returns HTTP 500.

Root cause:

- `html_service.render_fragment()` builds groups as dictionaries with an `"items"` list.
- The template uses:

```jinja2
{% for item in group.items %}
```

- Jinja resolves `group.items` to the dictionary method, not the `"items"` key value.
- The runtime error is:

```text
TypeError: 'builtin_function_or_method' object is not iterable
```

Impact:

- Search can technically find rows at the service layer, but the primary API/UI path fails before results reach the browser.
- The "web migration complete" claim is invalid while this remains.

Required fix:

- Change template access to bracket syntax:

```jinja2
{% for item in group["items"] %}
```

- Or rename the key from `"items"` to something that does not collide with a dict method.

Required tests:

- `POST /api/search` returns `200` for a query that yields at least one result.
- Response includes non-empty `results`.
- Response includes non-empty `html_fragment`.
- `GET /api/search/export` returns `200` for the same query.

Second-review status:

- **Still broken in commit `6d5ce4a`.**
- The template still uses `group.items`.
- Direct rendering still raises:

```text
TypeError: 'builtin_function_or_method' object is not iterable
```

### P0-2: Corpus Sync Path Traversal On Windows

File:

- `web/app/routers/corpus_sync.py`

Current code shape:

```python
file_path = os.path.join(CORPUS_PATH, "Data", filename)
if not os.path.exists(file_path):
    raise HTTPException(status_code=404, detail="File not found")
return FileResponse(file_path)
```

Confirmed exploit:

```text
/api/corpus-sync/file/..%5CProgramdata%5Cdata.txt
```

On Windows this successfully returned the contents of:

```text
Programdata/data.txt
```

Impact:

- Any readable file reachable through traversal may be exposed.
- This is a production blocker.

Required fix:

1. Do not trust arbitrary `filename`.
2. Build an allowlist from `sources.filename`.
3. Reject:
   - `..`
   - `/`
   - `\`
   - null bytes
   - names not present in the DB manifest
4. Resolve the candidate path and verify it remains under:

```text
CORPUS_PATH/Data
```

5. Prefer serving by an allowlisted DB record rather than free-form user path input.

Required tests:

- Valid known filename returns `200`.
- Unknown filename returns `404`.
- `..%5CProgramdata%5Cdata.txt` returns `404` or `400`.
- `..%2FProgramdata%2Fdata.txt` returns `404` or `400`.
- Encoded or mixed separators remain blocked.

Second-review status:

- **Still exploitable in commit `6d5ce4a`.**
- Request:

```text
/api/corpus-sync/file/..%5CProgramdata%5Cdata.txt
```

still returned HTTP `200`.

### P0-3: Reindexing Is Not Idempotent And Will Degrade The Database

Files:

- `web/ingest/ingest.py`
- `reindex.sh`

Observed code behavior:

- `reindex.sh` runs ingestion on the live DB:

```bash
docker exec $CONTAINER_NAME python ingest/ingest.py --corpus-path $CORPUS_PATH --db-path $DB_PATH
```

- `ingest.py` inserts sources with:

```python
INSERT OR REPLACE INTO sources (...)
```

- It then inserts fresh `corpus_lines` for every source without deleting or replacing old rows.

Why this is unsafe:

- SQLite `REPLACE` is delete + insert semantics, not a normal update.
- A replaced `sources` row may receive a different `id`.
- Existing `corpus_lines` are never cleaned up.
- Repeated ingestion can create:
  - duplicate indexed lines
  - orphaned `corpus_lines` that reference no current source row
  - inflated query counts
  - steadily growing DB size

Current snapshot checked:

- Existing DB had:
  - 148 sources
  - 460,548 corpus lines
  - 0 orphaned rows at the time of review
  - 0 duplicate `(source_id, line_num)` rows at the time of review

That only proves the checked DB had not yet suffered visible corruption. The ingest algorithm is still unsafe for repeated scheduled runs.

Required fix options:

Preferred:

1. Build a new DB at a temporary path.
2. Run full ingest into the temp DB.
3. Validate row counts and schema.
4. Atomically swap DB files.

Alternative:

1. Wrap rebuild in a transaction.
2. Clear or recreate `corpus_lines`.
3. Replace `sources` deterministically.
4. Reinsert all corpus rows.

Do not keep the current append behavior.

Required tests:

- Run ingest twice against the same corpus.
- Assert equal source counts.
- Assert equal corpus line counts.
- Assert zero duplicate `(source_id, line_num)` groups.
- Assert zero orphan `corpus_lines`.
- Assert manifest data still matches source records.

Second-review status:

- **No meaningful fix was made in commit `6d5ce4a`.**
- `INSERT OR REPLACE INTO sources ...` and unconditional `INSERT INTO corpus_lines ...` remain in place.

### P0-4: Export Has A New Missing-Import Regression

Files:

- `web/app/routers/search.py`
- `web/app/services/html_service.py`

Observed behavior:

- Export now calls `render_standalone(...)`.
- The router still imports `render_fragment, render_full_page`.
- No import for `render_standalone` exists.

Runtime confirmation:

- A query that avoids the result-fragment crash still fails export with:

```text
NameError: name 'render_standalone' is not defined
```

Required fix:

1. Import `render_standalone` correctly.
2. Remove the unused `render_full_page` import if it is no longer used.
3. Add export regression tests for:
   - zero-result export
   - non-empty-result export
   - unsupported mode behavior

Required tests:

- `GET /api/search/export?query=qwertyzqwertyz&mode=plain` returns `200`.
- `GET /api/search/export?query=arjuna&mode=plain` returns `200` after fragment rendering is fixed.

### P1-4: Search Input Causes FTS5 Parser Failures And HTTP 500s

Files:

- `web/app/services/search_service.py`
- `web/app/routers/search.py`
- `web/app/models.py`

Confirmed failing examples:

- Empty query
- `-`
- `foo-bar`
- `a:b`
- `"unterminated`
- Source selection that produces `source_ids=[]`
- Negative `limit`

Observed outcomes:

- Service layer raises SQLite operational errors such as:
  - `fts5: syntax error near ""`
  - `no such column: bar`
  - `unterminated string`
- API returns HTTP 500 instead of a validation error.

Root cause:

- Plain search passes user query directly into:

```sql
WHERE corpus_lines MATCH ?
```

- `MATCH` input is FTS syntax, not plain text.
- Current code assumes ordinary user text is valid FTS syntax.

Required fix:

1. Separate user intent from FTS syntax.
2. For plain search, construct a safe FTS expression from text tokens.
3. Escape or quote terms appropriately.
4. Explicitly decide behavior for:
   - phrase search
   - whole-word search
   - punctuation-containing search terms
   - single-character fallback
5. Return HTTP 422 for invalid request payloads rather than surfacing SQLite exceptions as HTTP 500.

Validation improvements:

- `query` should reject blank or all-whitespace values.
- `limit` should be constrained to a sane positive maximum.
- `mode` should be an enum instead of free-form string.
- Invalid regex should return a structured 4xx response, not an empty success response.

### P1-5: Case-Sensitive Search Is Not Reliably Case-Sensitive

File:

- `web/app/services/search_service.py`

Current behavior:

- `case_sensitive=True` wraps the FTS subquery with:

```sql
WHERE line_text LIKE '%' || ? || '%'
```

The code itself acknowledges this is not reliable:

```python
# Actually, LIKE is case-insensitive in SQLite by default for non-ASCII if not configured otherwise.
```

Observed count:

- `arjuna`, case-insensitive: 480
- `arjuna`, case-sensitive: 475
- `Arjuna`, case-insensitive: 480
- `Arjuna`, case-sensitive: 475

The identical case-sensitive counts for differently cased queries suggest the current semantics are not trustworthy.

Required fix:

- Define exact expected semantics.
- Apply true case-sensitive filtering using a reliable method, likely Python-side substring verification after a narrowed DB query or a carefully designed SQLite expression that is verified against multilingual data.
- Add explicit tests.

### P1-6: Source Selection Semantics Are Wrong

Files:

- `web/static/search.js`
- `web/app/routers/search.py`

Observed behavior:

- "Select None" unchecks all boxes.
- Frontend sends:

```javascript
source_ids: source_ids.length > 0 ? source_ids : null
```

- `null` currently means "all sources".
- Therefore "None" actually searches everything.

SSE has the same problem:

```javascript
const source_ids_str = source_ids.length > 0 ? source_ids.join(',') : '';
```

- Blank query parameter means no filter on backend.

Impact:

- UI semantics are inverted for a common workflow.
- A user may believe they searched nothing or a narrower set while actually searching all content.

Required fix:

Choose one explicit semantic contract:

Option A:

- `null` = all sources
- `[]` = zero sources

Option B:

- Reject `[]` with a clear user-facing validation message

Then make frontend, POST search, SSE stream, and export all obey the same contract.

Recommended:

- Keep `null = all`
- Implement `[] = none`
- Return fast empty result sets for `[]`

### P1-7: Export Ignores Source Filters And Morphological Search

File:

- `web/app/routers/search.py`

Current export endpoint:

```python
async def get_export(query: str, mode: str = "plain", case_sensitive: bool = False, whole_word: bool = False):
```

Problems:

- No `source_ids`
- No morphological mode support
- Else branch silently returns empty results for unsupported mode

Impact:

- Exported HTML may not match what the user saw in search results.
- Morphological results cannot be exported consistently.

Required fix:

- Align export inputs with `SearchRequest` semantics.
- Accept source filters.
- Support morphology or deliberately disable the export button for unsupported modes with explicit product behavior.
- Do not silently return an empty HTML page for unsupported modes.

### P1-8: Query-Driven Script Injection In Rendered HTML Fragment

Files:

- `web/app/services/html_service.py`
- `web/templates/result_fragment.html`
- `web/templates/full_page.html`

Current issues:

1. Custom Jinja environment is created without `autoescape`.
2. `query` is interpolated directly into HTML header content.
3. `query` is also interpolated directly into an inline JS string:

```jinja2
const query = "{{ query }}";
```

Confirmed test:

Input query:

```html
</script><script>globalThis.XSS=1</script>
```

Rendered fragment contained an extra script tag.

Impact:

- This is an injection vulnerability in generated HTML shown back to the searching user.
- Risk grows if result pages are shared, exported, cached, or embedded.

Required fix:

1. Enable Jinja autoescaping for HTML templates.
2. Use JSON-safe serialization for JS literals, for example the Jinja `tojson` filter.
3. Preserve intentional trusted corpus HTML rendering only where appropriate and auditable, such as `item.line_html | safe`.
4. Treat request-derived strings as untrusted.

Required tests:

- Query with script-breaking characters renders safely.
- The inline highlight script remains valid JS.
- No additional `<script>` tag appears from query content.

Second-review status:

- **Only partially addressed in commit `6d5ce4a`.**
- `query | tojson` now protects the JavaScript literal.
- But `header` still embeds raw query text while the custom Jinja `Environment(...)` still lacks autoescape.
- The injected payload remains present in rendered HTML header text.

### P1-9: Morphological Search Does Not Match The Stated Requirement

Files:

- `web/app/services/morph_service.py`
- `web/app/routers/morph.py`
- `WEB_PLAN.md`

Spec says:

- Morphological search should expand a word so related inflected forms are found.
- Acceptance mentions forms like:
  - `arjunam`
  - `arjunasya`

Current implementation:

1. Detect encoding
2. Convert to SLP1
3. Query Heritage endpoint
4. Regex scrape `<stem>...</stem>`
5. Convert stems into IAST / SLP1 / Devanagari
6. Plain-search those variants

Observed example:

- `expand_word("arjuna")` returned only:

```text
["arjuna"]
```

- Search results therefore reflect direct textual appearances of `arjuna` variants, not true morphological expansion.

Impact:

- Feature implementation is materially weaker than the stated product promise.
- `ai_status.md` claims morphology is completed, but the feature does not appear complete.

Required decision:

Gemini Flash should first clarify product scope in code/docs. For the current round, **honest renaming/documentation is enough**; full inflection-aware morphology is not required before the next review.

Option A:

- Rename behavior honestly to something like:
  - "stem lookup search"
  - "morphological lookup"
  - "root/stem-assisted search"
- Update frontend labels, API docs/comments, and handoff/docs so the feature no longer promises inflection expansion it does not provide.

Option B:

- Implement real inflection-aware search:
  - identify stems or lemmas
  - derive inflectional forms or query an API that provides them
  - cache resolved variant lists
  - search across normalized encodings

Recommendation for this round:

- **Choose Option A.**
- Do not keep the public "morphological search" label if the implementation remains stem-oriented only.
- Full inflection-aware search can stay as a future enhancement.

Required tests:

- IAST, SLP1, and Devanagari equivalents resolve consistently if that behavior is still claimed.
- The public label and docs match the implemented feature.
- Cache hit and cache miss paths are both tested if the feature remains exposed.
- API outage degrades gracefully with structured metadata or warning behavior.

Second-review status:

- **Still not fixed functionally.**
- Multi-line handling was added, but the underlying expansion strategy is unchanged.
- `expand_word("arjuna")` still returned only `["arjuna"]` during recheck.

### P2-10: Model Validation And Error Semantics Need Tightening

Files:

- `web/app/models.py`
- `web/app/routers/search.py`

Current issues:

- `mode` is any arbitrary string.
- Invalid mode returns `200` with zero results.
- `limit` accepts invalid negative values.
- Empty `query` is not rejected early.
- Regex compile failures become empty result arrays rather than validation errors.

Required fix:

- Add strong Pydantic validation.
- Convert hidden failure into explicit client-facing 4xx behavior.
- Keep server 500s for actual unexpected failures only.

Recommended model sketch:

```python
class SearchMode(str, Enum):
    plain = "plain"
    regex = "regex"
    morphological = "morphological"
```

- `query`: trimmed non-empty string
- `limit`: constrained integer, for example `1 <= limit <= 5000`
- `source_ids`: distinguish `None` from `[]`

### P2-11: Existing Tests Are Smoke Scripts, Not A Regression Suite

Files:

- `web/test_services.py`
- `web/test_search.py`

Observed:

- `pytest` is not installed in the current environment.
- `test_services.py` prints values but does not assert expected behavior.
- `test_search.py` expects a running local server and also has no assertions.

Required fix:

- Add real automated tests using `pytest` and FastAPI `TestClient`.
- Include fixture DB or a small deterministic temporary DB setup.
- Cover:
  - result rendering
  - export rendering
  - FTS special input handling
  - path traversal defense
  - source filtering semantics
  - ingestion idempotency
  - morphology cache behavior

### P2-12: Deployment State And Documentation Are Inconsistent

Files:

- `ai_status.md`
- `README.md`
- `docker-compose.yml`
- `Dockerfile`

Observed:

- `ai_status.md` says the web migration is complete and ready for deployment.
- The review found multiple release blockers.
- `docker-compose.yml` mounts `./web/corpus.db` into the container, implying a prebuilt DB is expected.
- Fresh deployments may not be self-initializing unless the DB already exists and is correct.

Required fix:

- Update `ai_status.md` to reflect the actual state.
- Decide deployment strategy:
  - mount a prepared DB intentionally
  - or build/ingest a DB as part of a deployment workflow
- Document the chosen lifecycle clearly.

## Runtime Checks Performed During Review

Commands and observations:

1. Repository status:
   - Only untracked file observed: `web/corpus.db`

2. Search smoke:
   - `python test_services.py` completed and printed result counts.
   - This is not sufficient verification because it lacks assertions.

3. Test suite:
   - `python -m pytest -q` failed because `pytest` is not installed.

4. Database snapshot:
   - `sources`: 148
   - `corpus_lines`: 460,548
   - `morph_cache`: 1

5. Rendering failures:
   - `POST /api/search` with normal non-empty queries returned `500`
   - `GET /api/search/export?query=arjuna&mode=plain` returned `500`

6. Input failures:
   - Empty string, punctuation-heavy inputs, and malformed quotes can trigger FTS operational errors.

7. Security checks:
   - Path traversal through encoded Windows backslashes succeeded.
   - Script-tag injection in rendered query content was confirmed.

## Implementation Plan For Gemini Flash

### Phase 1: Restore Broken Core Flow

Goal:

- Make plain search, regex search, and export functional for non-empty results.

Tasks:

1. Fix the Jinja `group.items` issue.
2. Add autoescaping to `html_service`.
3. Serialize `query` safely inside inline JavaScript.
4. Add tests proving:
   - `POST /api/search` works with results
   - export works with results
   - injected query strings remain inert

Exit criteria:

- Search page can display results again.
- Export can generate HTML for ordinary queries.
- No user-controlled query can break the fragment script block.

### Phase 2: Close Security And File Access Risks

Goal:

- Eliminate path traversal and tighten corpus sync behavior.

Tasks:

1. Replace arbitrary filename serving with DB-backed allowlist validation.
2. Resolve and validate file paths against the `Data` root.
3. Add negative tests for traversal forms.
4. Confirm manifest only exposes the intended file set.

Exit criteria:

- Valid corpus files download.
- Traversal attempts fail.

### Phase 3: Make Search Requests Robust

Goal:

- Remove avoidable 500s from normal or malformed user input.

Tasks:

1. Add `SearchMode` enum.
2. Add `query` and `limit` validation.
3. Decide and implement `source_ids=[]` semantics.
4. Build safe FTS expressions from user text.
5. Return explicit 4xx errors for malformed regex or invalid search requests.
6. Revisit case-sensitive matching and make semantics testable.

Exit criteria:

- Previously failing inputs no longer produce HTTP 500.
- Invalid client input produces clear 4xx responses.
- Search semantics are deterministic and documented.

### Phase 4: Align Filters, SSE, And Export

Goal:

- Make the user-visible search behavior consistent across all paths.

Tasks:

1. Ensure browser selection state maps exactly to backend semantics.
2. Fix "Select None".
3. Add `source_ids` to export.
4. Decide whether export supports morphology and implement or explicitly disable.
5. Add consistency tests:
   - same query + same filters = same result set between POST and export
   - SSE progress counts align with selected sources

Exit criteria:

- The UI, POST response, SSE, and export agree.

### Phase 5: Rebuild Ingestion Safely

Goal:

- Make scheduled reindexing correct and repeatable.

Tasks:

1. Replace current append reindex logic.
2. Prefer temp DB rebuild + swap.
3. Preserve or intentionally regenerate manifest data.
4. Add ingest-twice tests.
5. Update `reindex.sh` if the operational flow changes.

Exit criteria:

- Reindexing is repeatable without duplicate or orphan data.
- Daily automation is safe to run unattended.

### Phase 6: Decide And Implement Morphology Properly

Goal:

- Make morphology match the stated product promise or rename the feature honestly.

Tasks:

1. Choose between:
   - stem lookup search
   - true inflection-aware search
2. If true morphology:
   - introduce real variant generation or a richer morphology backend
   - cache variant sets, not only simple stems
   - support export and graceful outage handling
3. Add acceptance tests for known Sanskrit examples.

Exit criteria:

- Behavior matches docs and acceptance criteria.

### Phase 7: Add Real Regression Coverage

Goal:

- Replace demo scripts with confidence-building tests.

Tasks:

1. Add `pytest` to dependencies.
2. Build deterministic tests around a temporary DB or a small fixture corpus.
3. Test:
   - render path
   - security path
   - validation path
   - filters/export parity
   - ingestion idempotency
   - morphology behavior

Exit criteria:

- A single test command gives reliable pass/fail confidence.

### Phase 8: Reconcile Docs And Deployment

Goal:

- Make repo state honest and deployable.

Tasks:

1. Update `ai_status.md`.
2. Update deployment notes in `README.md` if needed.
3. Document DB lifecycle.
4. Ensure Docker/Compose instructions match the final operational model.

Exit criteria:

- A maintainer can understand how to build, ingest, run, reindex, and verify the app.

## Recommended Order Of Execution

1. Fix the two runtime regressions first:
   - replace `request.mode` with the actual `mode` parameter in SSE morphological dispatch
   - restore Python 3.11-safe typing imports in `html_service.py` and `morph_service.py`
2. Add regression tests for the repaired runtime paths:
   - morphological SSE should stream successfully
   - app/module import path should remain compatible with the declared runtime target
3. Repair the test/status accuracy problems:
   - stop default `pytest -q` from collecting the live-server smoke script, or formalize it as an integration test with proper markers
   - strengthen the golden-query tests so they can actually fail on behavior regressions
   - add end-to-end cross-encoding lookup coverage if claiming that behavior is verified
4. Reconsider whether `line_text` belongs in the default public search response. If it is only for tests, remove or gate it.
5. Update `ai_status.md` and `changelog.md` only after the above are true.

## Suggested Acceptance Checklist

- [x] `POST /api/search` returns `200` with HTML fragment for plain search.
- [x] `POST /api/search` returns `200` with HTML fragment for regex search.
- [x] `GET /api/search/export` returns `200` for plain search.
- [x] Zero-result export does not fail with `NameError`.
- [x] Result fragment rendering is safe for query text containing HTML and script delimiters.
- [x] Corpus file traversal attempts are blocked.
- [x] Blank search input returns `422`.
- [x] Invalid POST mode returns `422`.
- [x] Invalid export/SSE mode returns structured 4xx.
- [x] Invalid regex returns structured 4xx.
- [x] Negative limit is rejected on POST search.
- [x] `source_ids=[]` has explicit documented behavior.
- [x] "Select None" in the UI matches the documented behavior.
- [x] Export honors the same source filters as POST search.
- [x] Plain search with multiple tokens preserves the intended non-phrase behavior or is intentionally documented otherwise.
- [x] Reindexing handles files removed from `data.txt` and does not leave stale sources behind.
- [x] The current "morphological" feature is renamed/documented honestly if it remains stem-oriented only.
- [x] Automated API tests run through a documented command from `web/`.
- [x] `ai_status.md` no longer overstates readiness.
- [x] Pydantic validators are migrated from deprecated v1-style `@validator` to v2-style validation APIs.
- [x] Multi-query result headers do not duplicate the query-count ordinal.
- [ ] Morphological SSE does not crash and produces progress/done events.
- [ ] Services import cleanly under the declared Python 3.11 deployment target.
- [ ] Default `python -m pytest -q` from `web/` is not red because of a stray live-server smoke script.
- [ ] Golden-query tests contain meaningful assertions that fail on real regressions.
- [ ] Cross-encoding stem/root search claims are backed by end-to-end tests, not only helper-function tests.
- [ ] Default public search payload is reviewed so test-only observability does not unnecessarily bloat production responses.
- [ ] `ai_status.md` and `changelog.md` match the verified repo state.

## Revised Immediate Task List For Gemini Flash

1. Fix `web/app/routers/search.py` so morphological SSE uses the `mode` query parameter instead of `request.mode`.
2. Fix `web/app/services/html_service.py` and `web/app/services/morph_service.py` typing imports so the Dockerfile's Python 3.11 runtime does not break on import.
3. Add a regression test that exercises `/api/search/stream?...&mode=morphological`.
4. Resolve the stray `web/test_search.py` collection problem so plain `python -m pytest -q` from `web/` is not red.
5. Strengthen `web/tests/test_golden_queries.py`:
   - replace the no-op Russian assertion
   - require non-empty multi-token results before checking row contents
6. Add an end-to-end lookup test showing equivalent supported behavior for an IAST and Devanagari input, or remove the unsupported completion claim from `ai_status.md`.
7. Decide whether `line_text` should remain in the public API response. If not, rewrite tests around service-level validation or a debug-only path.
8. Reconcile `ai_status.md` and `changelog.md` after the fixes land.


## Notes For Gemini Flash

- Do not treat `ai_status.md` as authoritative completion evidence.
- Verify behavior through tests and runtime checks after each phase.
- Preserve existing architecture where reasonable, but prioritize correctness and safety over matching the current scaffolding.
- Avoid widening scope into unrelated frontend redesign work until the API and ingest path are stable.
- Keep generated DB artifacts out of source review decisions unless specifically needed for reproducibility or deployment.
