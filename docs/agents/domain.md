# Domain Docs

_Created: 26-08-2026 · Last updated: 26-08-2026_

This repo has no `CONTEXT.md`, `CONTEXT-MAP.md`, or `docs/adr/` — proceed
silently rather than treating their absence as a gap. The domain-context
reading order is fixed instead by
[`DOCUMENTATION_INDEX.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/DOCUMENTATION_INDEX.md)
§ "Reading Order For Implementation Agents":

1. `DOCUMENTATION_INDEX.md`
2. `CLAUDE.md`
3. `docs/PLAN_SAMUDRAMANTHANAM_ARCHITECTURE_2026_2027.md`
4. `docs/ROADMAP_SAMUDRAMANTHANAM_2026_2027.md`
5. `docs/ARCHITECTURE_SAMUDRAMANTHANAM_CANONICAL_PLATFORM.md`
6. `web/SEARCH_CONTRACT.md`
7. `.ai_state.md`

`DOCUMENTATION_INDEX.md` § "Conflict Rule" is the ADR-equivalent for this
repo: user messages and the latest architecture decisions win, then the
current plan/roadmap pair, then the current architecture doc, then
`docs/archive/` is context only, never current instruction.

This repo is **two domains sharing one corpus**, not single-context:

- **Web platform** (`web/`) — FastAPI + SQLite FTS5 search service. See
  `CLAUDE.md` § "How to run — web" for the layout of `dispatch_service.py`,
  `search_service.py`, `morph_service.py`, `html_service.py`.
- **Legacy desktop client** (`Index/`, Lazarus/Free Pascal, `PO.EXE`) — a
  separately versioned, self-updating Windows app. See `CLAUDE.md` § "How to
  run — desktop". Do not conflate its version (`Units/UpdateChecker.pas`
  `CURRENT_VERSION`) with the repository release version in `CHANGELOG.md`.

Both read the same corpus; `CLAUDE.md` § "Do not touch" (no second
search engine/indexer, corpus reindex ≠ app restart, `Index/lib/` is
generated) is the load-bearing cross-domain constraint. When a change spans
both domains, flag it explicitly rather than reviewing one side only.
