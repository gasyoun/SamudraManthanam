_Created: 25-08-2026 · Last updated: 05-09-2026_

# Gemini Flash Phase 02: Search and Reader

Goal: make search correct, fast, linkable, and useful for scholarly reading.

## Task 2.1: Search Correctness

Files:

- `web/app/services/search_service.py`
- `web/SEARCH_CONTRACT.md`
- `web/tests/test_contract.py`

Implement:

- Apply final `limit` after whole-word filtering.
- Apply final `limit` after case-sensitive filtering.
- Add tests where early FTS candidates fail Python filtering.
- Clarify Russian prefix vs substring behavior in the contract.

Acceptance:

- Contract, implementation, and tests agree.
- Existing fixture tests pass.

## Task 2.2: Regex Safety

Files:

- `web/app/models.py`
- `web/app/services/search_service.py`
- `web/tests/test_api.py`

Implement:

- Max regex length.
- Max scanned-row budget.
- Controlled timeout/budget metadata.
- No request should hang on one pathological pattern.

Acceptance:

- Bad regex gets a controlled response.
- Normal regex behavior remains.

## Task 2.3: Source Reader

Files:

- new `web/app/routers/reader.py`
- `web/app/main.py`
- templates/tests

Implement:

- Source detail route.
- Line lookup by `source_id` and `line_num`.
- Anchor lookup by `link_id`.
- Context window around a line.
- Result links into reader.

Acceptance:

- A search result opens in source context.
- Reader URLs are shareable.

## Task 2.4: Export v2

Files:

- `web/app/services/html_service.py`
- `web/templates/standalone_page.html`
- `web/app/routers/search.py`
- tests

Implement:

- Include query, mode, source filter summary.
- Include corpus version if available.
- Include generated timestamp.
- Add stable anchors for results.

Acceptance:

- Export is understandable later.
- Safe filename tests remain green.

## Task 2.5: Search Telemetry

Log mode, source filter count, result count, elapsed time, timeout/budget flags, and error class.

Do not log full query text by default in production.

## Checks

```powershell
py -3.10 -m compileall web\app web\ingest
cd web
python -m pytest
node --check static\search.js
```

_Dr. Mārcis Gasūns_
