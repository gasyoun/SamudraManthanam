# IMPLEMENTATION — SamudraManthanam residual wave-1

_Created: 26-07-2026 · Last updated: 26-07-2026_

Ordered steps for unattended agents. PLAN:
[PLAN_SAMUDRAMANTHANAM_RESIDUAL_2026H2.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/PLAN_SAMUDRAMANTHANAM_RESIDUAL_2026H2.md).
**Always work in a git worktree** off `origin/main` (main-tree guard).

---

## 0. Common preamble (every handoff)

1. `git fetch origin` · worktree `git worktree add -b <branch> ../SamudraManthanam-h###-<pid> origin/main`.
2. Read this file's section for your lane + VERIFICATION acceptance for that deliverable.
3. Do **not** `git add -A` if `archive_ignatiev_2026/` exists in the checkout.

---

## Lane A1 — JSON/CSV export (H1502)

**Depends on:** none.

1. Open `web/app/routers/search.py` export handler (HTML path).
2. Factor shared `build_export_payload(results, meta)` if not already clean.
3. Add `format` query param: `html` (default) | `json` | `csv`.
4. JSON: serialize payload; CSV: `csv` module, UTF-8, header row, escape snippets.
5. Wire frontend export link optionally (`format=` toggle) — **optional**; API-first is enough.
6. Tests in `web/tests/test_api.py` (or sibling): json/csv parity with HTML result count + meta keys; invalid format → 422; empty query still validated.
7. PR title: `feat(search): JSON/CSV export formats (H1502)`.

---

## Lane A2 — morph_cache drop (H1503)

**Depends on:** none (parallel A1).

1. Grep `morph_cache` under `web/` — confirm only schema CREATE remains.
2. Remove CREATE from `create_schema` in `web/app/db.py` (or equivalent).
3. Add migration helper: `DROP TABLE IF EXISTS morph_cache` for existing DBs (idempotent).
4. Hermetic test: fresh schema has no `morph_cache`; migration drops it.
5. PR: `fix(db): drop dead morph_cache from corpus schema (H1503)`.

---

## Lane A3 — SSE hermetic tests

**Depends on:** none.

1. Read existing stream tests in `web/tests/test_api.py` (validation already covered).
2. Add happy-path: fixture corpus → stream returns `text/event-stream` and ≥1 data event for a known hit query.
3. Add parity: bad mode / overlong query same status family as POST search.
4. Document in module docstring: endpoint kept, UI unwired (PLAN R7).
5. PR: `test(search): hermetic coverage for /api/search/stream keep-path`.

---

## Lane B1 — DBhP canonical-ID uniqueness

**Depends on:** none (parallel A).

1. Run corpus gate that failed 19-07 (`test_gate4_all_ids_unique` or current name) with local full corpus if available; else inspect combined JSONL for `devibhagavata` duplicate IDs.
2. If H941 already cleared all dups → document green proof in PR + strike `.ai_state` blocker; stop.
3. If residual dups: fix generator/combine script (root cause), regenerate affected JSONL, re-ingest test DB, re-run gate.
4. Commit derived JSONL only if repo already tracks that path; never invent IDs without parser evidence.
5. PR: `fix(corpus): DBhP canonical-ID uniqueness for pre-release gate`.

---

## Lane B2 — Cyrillic homoglyphs (#16)

**Depends on:** none (parallel B1).

1. Read issue #16 body for the five-word list + expected fix.
2. Implement normalizer (Cyrillic lookalikes → Latin/IAST where appropriate for SA fields) at convert/ingest path for Sanskrit segments.
3. Optional read-path safety net for already-ingested rows if convert re-run is expensive — prefer convert + re-ingest for affected sources only.
4. Golden tests: the five words from the issue; no false rewrite of legitimate Cyrillic in **Russian** segments.
5. PR: `fix(corpus): strip Cyrillic homoglyphs from #sa fields (#16)`.

---

## Lane C — Ignatiev (H1438 only)

**Do not expand.** Continue H1438 body: Māyā mode design when ready; `.doc` via antiword; next works one-by-one with round-trip tests. No Wave B–D mint from this PLAN.

---

## Docs lane (this session / plan PR)

1. Land PLAN + ROADMAP + ARCHITECTURE + IMPLEMENTATION + VERIFICATION + PLAN.meta.
2. Banner on `ROADMAP_2026_H2_DH_MOBILE.md` top: superseded for **status** by residual ROADMAP.
3. Banner on `docs/ROADMAP_SOMADEVA_KSS_ALIGNMENT_SCALEUP_2026_2027.md`: P1/P3 done; residual = low-conf human sheet only.
4. Short status note on `ARCHITECTURE_REVIEW_6_MONTH_ROADMAP.md` if it still claims open platform work that Phases 2–3 closed.
5. Point `.ai_state.md` Next Steps at residual PLAN (micro-edit).

---

## Wave-2 (H1485) — not this span

See handoff H1485; start only after wave-1 platform PRs merged or on explicit `/go H1485`.

_Dr. Mārcis Gasūns_
