# VERIFICATION — SamudraManthanam residual wave-1

_Created: 26-07-2026 · Last updated: 26-07-2026_

Acceptance criteria + commands. PLAN:
[PLAN_SAMUDRAMANTHANAM_RESIDUAL_2026H2.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/PLAN_SAMUDRAMANTHANAM_RESIDUAL_2026H2.md).

Global bar (R9): **hermetic CI green** on the PR + **one local full-corpus
uniqueness gate re-run** after integrity work (or documented proof that dups
are already zero).

---

## Lane A1 — JSON/CSV export (H1502)

| # | Criterion | How |
|---|---|---|
| A1.1 | `format=json` returns same hit count as default HTML export for a fixture query | hermetic test |
| A1.2 | JSON body includes meta: query, mode, corpus_version (or equivalent), source filter | hermetic test |
| A1.3 | `format=csv` has header + one row per hit; UTF-8 | hermetic test |
| A1.4 | Invalid `format` → 4xx; existing HTML export tests still pass | hermetic suite |
| A1.5 | No bulk-text dump endpoint introduced | code review: only search result rows |

```
cd web
python -m pytest tests/test_api.py -q
```

---

## Lane A2 — morph_cache (H1503)

| # | Criterion | How |
|---|---|---|
| A2.1 | Fresh schema: no `morph_cache` table | hermetic test |
| A2.2 | Migration drops table if present | hermetic test |
| A2.3 | `rg morph_cache web/` — only tests/docs migration notes | grep |

---

## Lane A3 — SSE stream

| # | Criterion | How |
|---|---|---|
| A3.1 | Validation failures match search family (bad mode, overlong query) | existing + new tests |
| A3.2 | Happy path: event-stream content-type + ≥1 data event on fixture hit | new hermetic test |
| A3.3 | Frontend still does not call stream (unwired) | grep `search.js` for stream URL = 0 |

---

## Lane B1 — DBhP ID uniqueness

| # | Criterion | How |
|---|---|---|
| B1.1 | Pre-measure: count duplicate ID groups (or gate fails/passes) | corpus gate or script |
| B1.2 | Post-fix: gate green OR documented 0 residual dups with evidence | same command |
| B1.3 | No silent gate skip / threshold weakening | PR review |

```
cd web
# adjust if DB_PATH / marker name differs on host
python -m pytest -m corpus -k gate4 -q
# or scripts/run_corpus_tests.py per .ai_state
```

If full corpus DB absent on the agent host: run ID uniqueness over the tracked
JSONL for `devibhagavata*` and record the method in the PR; do **not** claim
full-corpus green without the DB.

---

## Lane B2 — Homoglyphs (#16)

| # | Criterion | How |
|---|---|---|
| B2.1 | Five issue words no longer contain Cyrillic lookalikes in SA fields | unit tests |
| B2.2 | Russian segments still accept real Cyrillic | unit tests |
| B2.3 | Issue #16 comment with before/after + PR link | `gh issue comment` |

---

## Lane C — H1438

Use H1438's own acceptance (round-trip counts, FTS hits, hermetic parser tests).
This VERIFICATION does not redefine them.

---

## Risks & spikes

| Risk | Mitigation |
|---|---|
| Full corpus DB missing on agent host | JSONL-level uniqueness proof + note; human runs full gate before release |
| Export CSV injects bulk verse text | Cap snippet length to UI-equivalent; rights review in PR |
| Homoglyph fix over-normalizes RU | Script-tag gated: only `sa` / Sanskrit script |
| H1438 thrash with other `corpus_builder` PRs | sequential merges; H1485 wave-2 |
| Stale browser SW after export UI change | existing D4 cache policy; bump SW only if static assets change |

---

## Autonomy-readiness gate (Phase 4 checklist)

| Wave-1 item | Arch | Steps | Accept | Risks |
|---|---|---|---|---|
| H1502 export | ✅ §2.1 | ✅ A1 | ✅ A1.* | ✅ |
| H1503 morph_cache | ✅ §2.2 | ✅ A2 | ✅ A2.* | ✅ |
| SSE tests | ✅ §2.3 | ✅ A3 | ✅ A3.* | ✅ |
| DBhP IDs | ✅ §3.1 | ✅ B1 | ✅ B1.* | ✅ (DB host) |
| Homoglyphs | ✅ §3.2 | ✅ B2 | ✅ B2.* | ✅ |
| H1438 | existing | H1438 body | H1438 | parallel |

**Blocking @DECIDEs in wave-1:** none (R11–R12). Gate = **PASS**.

_Dr. Mārcis Gasūns_
