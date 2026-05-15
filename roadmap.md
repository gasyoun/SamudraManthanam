# Samudra Manthanam - 1-Month Development Roadmap

> **STATUS: SUPERSEDED** — Older 1-month roadmap with stale ordering. Current roadmap: `ARCHITECTURE_REVIEW_6_MONTH_ROADMAP.md`. Current Gemini index: `GEMINI_FLASH_IMPLEMENTATION_PLAN.md`.

## Planning Window

**Dates:** May 13, 2026 to June 12, 2026  
**Primary optimization target:** scholarly search quality  
**Delivery bias:** ship user-facing improvements first, with only the architecture and operational work needed to keep those improvements trustworthy  
**Scope:** web app, legacy desktop app, corpus sync, corpus operations, and deployment

---

## North Star

By June 12, 2026, Samudra Manthanam should feel like a more trustworthy scholarly search tool, not merely a completed web migration.

That means:

- searches are easier to understand and verify
- result sets are clearer and more useful for actual research
- stem/root lookup is polished, honest, and predictable
- exported outputs remain useful outside the browser
- the desktop app can benefit from web-hosted corpus updates
- corpus maintenance and deployment are stable enough to support real use

---

## Product Priorities For This Month

1. Improve perceived and actual search quality.
2. Polish the existing stem/root lookup without expanding scope into full inflection-aware morphology.
3. Improve result review, comparison, and export workflows for scholars.
4. Complete the practical desktop sync bridge.
5. Keep ingest, corpus integrity, and deployment strong enough to support the above.

---

## Weekly Roadmap

### Week 1 - Search Quality Baseline

**Dates:** May 13-19, 2026

**Goal:** Make plain and regex search more trustworthy, easier to inspect, and easier to regression-test.

**Deliverables**

1. Create a curated "golden query" pack covering:
   - Sanskrit IAST queries
   - Devanagari queries
   - Russian queries
   - regex searches
   - multi-query searches
   - source-filtered searches
2. Add regression coverage around:
   - result counts for known queries
   - source filtering behavior
   - export/search consistency
   - multi-query result rendering
3. Improve result readability in the web UI:
   - result summary wording
   - zero-result messaging
   - source-hit visibility
4. Audit and clarify current query semantics:
   - source selection states
67. **(Hardening)** Implement hermetic testing and unified search dispatch.

**Acceptance checks**

- A scholar can tell what was searched, how broadly it searched, and why a result set looks the way it does.
- Existing search API tests remain green.
- Golden queries can be rerun after later changes to catch regressions.

---

### Week 2 - Stem/Root Lookup Polish

**Dates:** May 20-26, 2026

**Goal:** Turn the existing modest morphology-adjacent feature into a clean, trustworthy scholarly tool.

**Deliverables**

1. Improve the `Stem/Root Lookup` workflow:
   - consistent wording across UI, API payloads, docs, and exports
   - clear presentation of lookup variants where the UI exposes them
2. Tighten cross-encoding behavior:
   - IAST input
   - Devanagari input
   - SLP1 or normalized intermediate forms where used internally
3. Improve result explanations for lookup mode where useful:
   - preserve honesty about supported behavior
   - avoid language that implies complete Sanskrit inflection coverage
4. Add focused tests for:
   - cross-encoding consistency
   - malformed or odd input
   - fallback behavior when external lookup support is unavailable

**Acceptance checks**

- Users understand what lookup mode does and does not promise.
- Search results remain stable across equivalent supported script inputs.
- No documentation drifts back into claiming full morphology coverage.

---

### Week 3 - Scholar Workflow Features And Desktop Sync

**Dates:** May 27-June 2, 2026

**Goal:** Improve what users do after search, while making the desktop app a viable participant in the new corpus pipeline.

**Deliverables**

1. Improve exported result usefulness:
   - include search mode
   - include original query
   - include export context or corpus version where practical
2. Make result review easier:
   - maintain source grouping
   - keep TOC and navigation reliable
   - preserve strong highlight behavior
3. Finish the legacy desktop sync bridge:
   - desktop client reads `/api/corpus-sync/manifest`
   - detects changed files
   - downloads only changed corpus files
   - updates local state safely
4. Add operational validation around ingest:
   - missing source files
   - stale manifest entries
   - source removals
   - hash consistency

**Acceptance checks**

- A researcher can export useful search output and understand its context later.
- A desktop user can update corpus data without requiring a full manual reinstall.
- A corpus curator can detect obvious data pipeline problems before publishing.

---

### Week 4 - Launch Candidate And Field Readiness

**Dates:** June 3-12, 2026

**Goal:** Make the system ready for broader scholarly use without losing the sharp focus on search quality.

**Deliverables**

1. Final UX cleanup informed by Week 1-3 usage:
   - unclear wording
   - confusing states
   - small result-review friction points
2. Deployment readiness:
   - TLS/SSL path
   - nginx/SSE behavior checked
   - DB generation and deployment steps rehearsed
3. Add lightweight operational diagnostics:
   - useful logs for search, sync, and ingest failures
   - operator checklist for rebuild/reindex/release steps
4. Run a full internal acceptance pass:
   - golden query suite
   - export flow
   - stem/root lookup flow
   - sync flow
   - corpus rebuild flow

**Acceptance checks**

- The project can credibly be called beta-ready for real scholarly use.
- Search quality and corpus trust are supported by repeatable checks, not memory.

---

## Recommended Execution Order

1. Golden query pack and search regression matrix
2. Search result clarity improvements
3. Stem/root lookup polish and cross-encoding tests
4. Export metadata and result-review quality
5. Desktop corpus sync implementation
6. Corpus validation / ingest reporting
7. Deployment and operator readiness

---

## Scope Guardrails

Do not spend this month on:

- true full inflection-aware morphology
- a major frontend redesign
- broad ranking experiments unless the golden query pack proves they are needed
- desktop modernization beyond sync usefulness
- deep rewrites that do not improve scholar-facing behavior

---

## Architecture Handoff For Gemini Flash

This section is the working architecture brief for Gemini Flash. Preserve these boundaries unless there is a clear defect requiring a change.

### 1. System Shape

The system has four major parts:

1. **Legacy desktop app**
   - Free Pascal / Lazarus
   - primary code under `Index/` and `Units/`
   - important sync/update logic in `Units/UpdateChecker.pas`
2. **Web application**
    - Python ingest under `web/ingest/`
    - generates `web/corpus.db`
5. **Testing & Hardening Infrastructure**
    - Hermetic test suite with SQLite fixtures
    - Centralized `settings.py` for environment management
    - Search contract enforcement
4. **Operational/deployment layer**
   - Docker/nginx/reindex workflow
   - large generated SQLite DB stays out of Git

### 2. Web Application Boundaries

Keep responsibilities split this way:

- `web/app/main.py`
  - app creation
  - router registration
  - static/template setup
- `web/app/models.py`
  - request/response contracts
  - validation rules
- `web/app/routers/search.py`
  - HTTP orchestration for search, export, and SSE progress
  - should delegate search work to services
- `web/app/routers/sources.py`
  - source listing API
- `web/app/routers/morph.py`
  - lookup-preview API only
- `web/app/routers/corpus_sync.py`
  - manifest and file-serving sync endpoints
- `web/app/services/dispatch_service.py`
  - unified search dispatch entry point
- `web/app/services/search_service.py`
  - core FTS5 logic with prefix matching support
- `web/app/services/morph_service.py`
  - encoding normalization
  - lookup expansion
  - morphological-mode search fanout
- `web/app/services/html_service.py`
  - result fragment rendering
  - standalone/export rendering
- `web/app/settings.py`
  - centralized configuration (DB paths, timeouts)
- `web/app/db.py`
  - SQLite connection and schema work

### 3. Search Architecture

The core search contract is:

1. Router validates request.
2. Service performs actual search.
3. HTML service renders output where needed.
4. Router returns API response or exported HTML.

Preserve these traits:

- plain search uses FTS-oriented search logic
- regex search is a distinct explicit path
- `source_ids=[]` means no sources selected, not "all"
- invalid modes and invalid regex patterns must fail with structured 4xx responses
- POST search, export, and SSE should maintain equivalent semantics

### 4. Stem/Root Lookup Constraints

The current product promise is **stem/root lookup**, not complete morphology.

Rules:

- Do not reintroduce docs/UI copy that promises full inflection-aware coverage.
- Keep supported lookup behavior consistent across encodings where the current implementation can do so.
- Cache external lookup results aggressively.
- If external support is unavailable, degrade predictably rather than silently inventing certainty.
- Any future true morphology initiative should be treated as a separate roadmap, not smuggled into this month.

### 5. HTML Rendering And UX Constraints

Rendering must preserve:

- source grouping
- chapter grouping
- downloadable HTML output
- safe escaping of user-controlled input
- stable multi-query wording
- predictable highlight behavior after AJAX injection

Do not break:

- `html_fragment`-driven result injection
- current export flow
- existing regression tests around rendering safety and header wording

### 6. Corpus And Database Architecture

Important facts:

- `web/corpus.db` is generated, large, and intentionally untracked.
- Build workflow is documented in `README.md` and `build-web-db.ps1`.
- Ingest reads desktop corpus structures and produces the SQLite FTS database.
- Source removal reconciliation matters. If a file disappears from the manifest, stale DB entries must not linger.

Operational expectations:

- keep ingest idempotent
- maintain manifest/file consistency
- avoid hardcoding machine-local assumptions
- keep Git clean of generated DB artifacts and cache files

### 7. Desktop Sync Bridge

The desktop app should increasingly consume the web corpus pipeline without losing legacy operability.

Current intended direction:

- web exposes `/api/corpus-sync/manifest`
- desktop compares remote metadata to local state
- desktop downloads only changed corpus files
- desktop avoids unnecessary giant package refreshes

When changing this area:

- preserve backward compatibility where reasonable
- keep failure modes visible to users
- avoid changing the legacy update story more than necessary in this one-month plan

### 8. Deployment And Runtime Notes

Keep in mind:

- SSE needs correct proxy behavior in nginx
- corpus DB generation happens outside normal Git tracking
- deployment should not assume a tiny artifact footprint
- production readiness includes operational clarity, not just a green startup

### 9. Gemini Flash Working Rules

Gemini should:

1. Work from existing repo patterns before inventing new ones.
2. Keep changes tightly scoped to the planned milestone.
3. Update docs when behavior or product wording changes.
4. Add tests whenever a bug fix could plausibly regress.
5. Treat search/export/SSE parity as a shared contract.
6. Avoid widening morphology scope beyond stem/root lookup polish.
7. Prefer improving scholar-visible behavior over speculative infrastructure work.

---

## Suggested Month-End Acceptance Set

By June 12, 2026, the following should be true:

- golden query pack exists and is useful
- search result summaries are clearer
- stem/root lookup feels polished and documented honestly
- exports carry better scholarly context
- desktop sync path is implemented or demonstrably near-complete
- ingest validation catches obvious corpus issues
- deployment and operational notes are sufficient for a beta release

