# Gemini Flash Web Repair Handoff

Date: 2026-05-12  
Repository: `C:\Users\user\Documents\GitHub\SamudraManthanam`

## Purpose

This document captures the web migration review findings for Samudra Manthanam and provides a concrete implementation plan for Gemini Flash to stabilize the FastAPI web app before production use.

The current web stack is not deploy-ready despite `ai_status.md` claiming completion. Several issues are correctness blockers, one is a confirmed file disclosure vulnerability, and the ingestion workflow will corrupt or bloat the database over repeated scheduled reindex runs.

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

Gemini Flash should first clarify product scope in code/docs, then implement accordingly.

Option A:

- Rename behavior honestly to "stem lookup search" and adjust docs.

Option B:

- Implement real inflection-aware search:
  - identify stems or lemmas
  - derive inflectional forms or query an API that provides them
  - cache resolved variant lists
  - search across normalized encodings

Recommendation:

- Preserve the public "morphological search" name only if real inflection expansion is implemented.

Required tests:

- IAST, SLP1, and Devanagari equivalents resolve consistently.
- Query for `arjuna` returns known inflected forms if that is the required product behavior.
- Cache hit and cache miss paths are both tested.
- API outage degrades gracefully with structured metadata or warning behavior.

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

1. Rendering crash
2. Script injection hardening
3. Corpus sync traversal fix
4. Input validation + FTS hardening
5. Source filter/export consistency
6. Idempotent ingest redesign
7. Morphology decision and implementation
8. Test suite expansion
9. Documentation cleanup

## Suggested Acceptance Checklist

- [ ] `POST /api/search` returns `200` with HTML fragment for plain search.
- [ ] `POST /api/search` returns `200` with HTML fragment for regex search.
- [ ] `GET /api/search/export` returns `200` for plain search.
- [ ] Result fragment rendering is safe for query text containing HTML and script delimiters.
- [ ] Corpus file traversal attempts are blocked.
- [ ] Blank search input returns `422`.
- [ ] Invalid mode returns `422`.
- [ ] Invalid regex returns structured 4xx.
- [ ] Negative limit is rejected.
- [ ] `source_ids=[]` has explicit documented behavior.
- [ ] "Select None" in the UI matches the documented behavior.
- [ ] Export honors the same source filters as POST search.
- [ ] Reindexing twice does not change counts or create duplicates/orphans.
- [ ] Morphological behavior matches its documented promise.
- [ ] Automated tests run through a documented command.
- [ ] `ai_status.md` no longer overstates readiness.

## Notes For Gemini Flash

- Do not treat `ai_status.md` as authoritative completion evidence.
- Verify behavior through tests and runtime checks after each phase.
- Preserve existing architecture where reasonable, but prioritize correctness and safety over matching the current scaffolding.
- Avoid widening scope into unrelated frontend redesign work until the API and ingest path are stable.
- Keep generated DB artifacts out of source review decisions unless specifically needed for reproducibility or deployment.
